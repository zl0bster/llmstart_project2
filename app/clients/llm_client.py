"""
Клиент для работы с LLM через OpenRouter API.

Реализует извлечение структурированных данных из текстовых отчетов ОТК.
"""

import logging
import json
from typing import List, Optional
from openai import OpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from app.clients.base_client import BaseLLMClient
from app.models.schemas import LLMResponse, OrderData
from app.prompts.system_prompts import get_system_prompt

logger = logging.getLogger(__name__)


def normalize_status(status: str) -> str:
    """
    Нормализует статус к одному из разрешенных значений StatusEnum.
    
    Args:
        status: Исходный статус от LLM
        
    Returns:
        str: Нормализованный статус
    """
    if not status:
        return status
    
    status_lower = status.lower().strip()
    
    # Маппинг синонимов к правильным статусам
    status_mapping = {
        # Варианты для "годно"
        "годно": "годно",
        "готов": "годно",
        "готово": "годно",
        "ок": "годно",
        "ok": "годно",
        "норм": "годно",
        "все хорошо": "годно",
        "принято": "годно",
        "одобрено": "годно",
        "все в порядке": "годно",
        
        # Варианты для "в доработку"
        "в доработку": "в доработку",
        "доработка": "в доработку", 
        "доработать": "в доработку",
        "переделать": "в доработку",
        "исправить": "в доработку",
        "ремач": "в доработку",
        "нужна доработка": "в доработку",
        
        # Варианты для "в брак"
        "в брак": "в брак",
        "брак": "в брак",
        "негоден": "в брак",
        "на списание": "в брак",
        "лом": "в брак",
        "все в брак": "в брак",
        "отклонен": "в брак"
    }
    
    normalized = status_mapping.get(status_lower, status)
    
    if normalized != status:
        logger.info(f"Нормализация статуса: '{status}' -> '{normalized}'")
    
    return normalized


class OpenRouterLLMClient(BaseLLMClient):
    """Клиент для работы с LLM через OpenRouter API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", base_url: str = "https://openrouter.ai/api/v1"):
        """
        Инициализация клиента.
        
        Args:
            api_key: API ключ для OpenRouter
            model: Название модели для использования
            base_url: Базовый URL API
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.parser = PydanticOutputParser(pydantic_object=LLMResponse)
        
        # Создаем промпт шаблон
        system_template = get_system_prompt()
        format_instructions = self.parser.get_format_instructions()
        
        # Экранируем фигурные скобки в format_instructions для избежания конфликта с ChatPromptTemplate
        escaped_format_instructions = format_instructions.replace('{', '{{').replace('}', '}}')
        
        # Полностью форматируем системный промпт БЕЗ использования ChatPromptTemplate
        # чтобы избежать повторного форматирования JSON блоков
        self.formatted_system_prompt = system_template.format(format_instructions=escaped_format_instructions)
        
        # Для простоты не используем ChatPromptTemplate - формируем промпт вручную
        self.prompt = None
    
    def process_text(self, text: str, session_history: Optional[List[str]] = None) -> LLMResponse:
        """
        Обрабатывает текст через LLM и возвращает структурированные данные.
        
        Args:
            text: Текст для обработки
            session_history: История сообщений сессии
            
        Returns:
            LLMResponse: Структурированный ответ LLM
        """
        try:
            # Формируем входной текст с учетом истории
            if session_history:
                full_text = "\n".join(session_history + [text])
            else:
                full_text = text
            
            logger.info(f"Отправка запроса к LLM. Длина текста: {len(full_text)} символов")
            
            # Формируем сообщения напрямую без ChatPromptTemplate
            # чтобы избежать повторного форматирования JSON блоков
            system_content = self.formatted_system_prompt
            user_content = full_text
            
            # Отправляем запрос к LLM с ограничениями против зацикливания
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                temperature=0,
                max_tokens=800,  # Уменьшаем лимит чтобы предотвратить зацикливание
                frequency_penalty=0.5,  # Штрафуем повторения
                presence_penalty=0.3    # Поощряем разнообразие
            )
            
            llm_response_text = response.choices[0].message.content
            logger.info(f"Получен ответ от LLM. Длина ответа: {len(llm_response_text) if llm_response_text else 0} символов")
            
            # Проверяем на зацикливание и поврежденный JSON
            if not self._validate_llm_response(llm_response_text):
                logger.error("LLM ответ содержит зацикливание или поврежден, используем fallback")
                return LLMResponse(
                    orders=[],
                    requires_correction=True,
                    clarification_question="Произошла ошибка обработки. Пожалуйста, опишите отчет еще раз."
                )
            
            # Парсим ответ с нормализацией статусов
            try:
                # Сначала нормализуем статусы в JSON
                normalized_response = self._normalize_response_json(llm_response_text)
                parsed_response = self.parser.parse(normalized_response)
                logger.info(f"Успешно извлечено {len(parsed_response.orders)} заказов")
                return parsed_response
            except Exception as parse_error:
                logger.error(f"Ошибка парсинга ответа LLM: {parse_error}")
                logger.error(f"Ответ LLM: {llm_response_text}")
                
                # Fallback: пытаемся извлечь JSON вручную
                return self._fallback_parse(llm_response_text)
                
        except Exception as e:
            logger.error(f"Ошибка при обращении к LLM API: {e}")
            return LLMResponse(
                orders=[],
                requires_correction=True,
                clarification_question="Произошла ошибка при обработке. Пожалуйста, опишите отчет еще раз."
            )
    
    def _clean_json_text(self, text: str) -> str:
        """
        Очищает текст от недопустимых control characters для JSON.
        
        Args:
            text: Исходный текст
            
        Returns:
            str: Очищенный текст
        """
        import re
        # Удаляем недопустимые control characters, кроме \n, \r, \t
        # JSON позволяет только эти control characters в строках
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        return cleaned

    def _validate_llm_response(self, response_text: str) -> bool:
        """
        Валидирует ответ LLM на предмет зацикливания и корректности.
        
        Args:
            response_text: Ответ от LLM
            
        Returns:
            bool: True если ответ валиден
        """
        if not response_text or len(response_text.strip()) == 0:
            return False
        
        # Проверяем максимальную длину
        if len(response_text) > 3000:
            logger.warning(f"LLM ответ слишком длинный: {len(response_text)} символов")
            return False
        
        # Проверяем на базовую корректность JSON
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
                logger.warning("LLM ответ не содержит корректной JSON структуры")
                return False
            
            json_text = response_text[start_idx:end_idx + 1]
            # Очищаем от недопустимых control characters
            json_text = self._clean_json_text(json_text)
            data = json.loads(json_text)
            
            # Проверяем наличие обязательных полей
            required_fields = ['orders', 'requires_correction', 'clarification_question']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"LLM ответ не содержит обязательное поле: {field}")
                    return False
            
            # Проверяем на зацикливание в orders
            if isinstance(data.get('orders'), list):
                orders = data['orders']
                
                # Проверяем разумное количество заказов
                if len(orders) > 20:
                    logger.warning(f"LLM ответ содержит слишком много заказов: {len(orders)}")
                    return False
                
                # Проверяем на повторяющиеся заказы (признак зацикливания)
                order_ids = [order.get('order_id') for order in orders if isinstance(order, dict)]
                if len(order_ids) > 5:  # Если больше 5 заказов, проверяем повторы
                    unique_ids = set(order_ids)
                    if len(unique_ids) == 1 and len(order_ids) > 5:
                        logger.warning(f"Обнаружено зацикливание: {len(order_ids)} раз повторяется заказ {list(unique_ids)[0]}")
                        return False
            
            return True
            
        except json.JSONDecodeError as e:
            logger.warning(f"LLM ответ содержит невалидный JSON: {e}")
            return False
        except Exception as e:
            logger.warning(f"Ошибка валидации LLM ответа: {e}")
            return False

    def _normalize_response_json(self, response_text: str) -> str:
        """
        Нормализует статусы в JSON ответе LLM.
        
        Args:
            response_text: JSON ответ от LLM
            
        Returns:
            str: JSON с нормализованными статусами
        """
        try:
            # Ищем JSON в тексте
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_text = response_text[start_idx:end_idx]
                # Очищаем от недопустимых control characters
                json_text = self._clean_json_text(json_text)
                data = json.loads(json_text)
                
                # Нормализуем статусы в orders
                if 'orders' in data and isinstance(data['orders'], list):
                    for order in data['orders']:
                        if isinstance(order, dict) and 'status' in order and order['status']:
                            original_status = order['status']
                            normalized_status = normalize_status(original_status)
                            order['status'] = normalized_status
                
                # Возвращаем обновленный JSON
                return json.dumps(data, ensure_ascii=False)
            else:
                # Если JSON не найден, возвращаем исходный текст
                return response_text
                
        except Exception as e:
            logger.warning(f"Ошибка нормализации JSON: {e}, возвращаем исходный текст")
            return response_text

    def _fallback_parse(self, response_text: str) -> LLMResponse:
        """
        Fallback парсинг ответа LLM при ошибке основного парсера.
        
        Args:
            response_text: Текст ответа от LLM
            
        Returns:
            LLMResponse: Структурированный ответ
        """
        try:
            # Ищем JSON в тексте
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_text = response_text[start_idx:end_idx]
                # Очищаем от недопустимых control characters
                json_text = self._clean_json_text(json_text)
                data = json.loads(json_text)
                
                # Преобразуем в Pydantic модель с нормализацией статусов
                orders = []
                for order_data in data.get('orders', []):
                    # Нормализуем статус перед созданием объекта
                    if 'status' in order_data and order_data['status']:
                        order_data['status'] = normalize_status(order_data['status'])
                    orders.append(OrderData(**order_data))
                
                return LLMResponse(
                    orders=orders,
                    requires_correction=data.get('requires_correction', False),
                    clarification_question=data.get('clarification_question')
                )
        except Exception as e:
            logger.error(f"Ошибка fallback парсинга: {e}")
        
        # Если ничего не получилось
        return LLMResponse(
            orders=[],
            requires_correction=True,
            clarification_question="Не удалось обработать данные. Пожалуйста, опишите отчет еще раз."
        )
    
    def is_available(self) -> bool:
        """
        Проверяет доступность LLM сервиса.
        
        Returns:
            bool: True если сервис доступен
        """
        try:
            # Простой тестовый запрос
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"LLM сервис недоступен: {e}")
            return False
