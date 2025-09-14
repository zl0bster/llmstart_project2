"""
Клиент для работы с LLM через LM Studio.

Реализует извлечение структурированных данных из текстовых отчетов ОТК через локальный LM Studio.
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


class LMStudioLLMClient(BaseLLMClient):
    """Клиент для работы с LLM через LM Studio."""
    
    def __init__(self, base_url: str = "http://localhost:1234", model: str = "openai/gpt-oss-20b"):
        """
        Инициализация клиента.
        
        Args:
            base_url: URL локального LM Studio сервера
            model: Название модели для использования
        """
        self.client = OpenAI(base_url=base_url, api_key="lm-studio")  # LM Studio не требует реального API ключа
        self.model = model
        self.parser = PydanticOutputParser(pydantic_object=LLMResponse)
        
        # Создаем промпт шаблон
        system_template = get_system_prompt()
        format_instructions = self.parser.get_format_instructions()
        
        self.prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    system_template.format(format_instructions=format_instructions)
                ),
                HumanMessagePromptTemplate.from_template("{user_input}")
            ],
            input_variables=["user_input"]
        )
        
        logger.info(f"LM Studio клиент инициализирован: {base_url}, модель: {model}")
    
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
            
            logger.info(f"Отправка запроса к LM Studio. Длина текста: {len(full_text)} символов")
            
            # Формируем промпт
            formatted_prompt = self.prompt.format(user_input=full_text)
            
            # Отправляем запрос к LM Studio
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": formatted_prompt.split("Human:")[0].replace("System:", "").strip()},
                    {"role": "user", "content": formatted_prompt.split("Human:")[1].strip()}
                ],
                temperature=0,
                max_tokens=2000
            )
            
            # Проверяем, что ответ корректный
            if not response.choices or len(response.choices) == 0:
                logger.error("LM Studio вернул пустой ответ")
                raise Exception("LM Studio вернул пустой ответ")
            
            if not response.choices[0].message or not response.choices[0].message.content:
                logger.error("LM Studio вернул ответ без содержимого")
                raise Exception("LM Studio вернул ответ без содержимого")
            
            llm_response_text = response.choices[0].message.content
            logger.info(f"Получен ответ от LM Studio. Длина ответа: {len(llm_response_text)} символов")
            
            # Парсим ответ
            try:
                parsed_response = self.parser.parse(llm_response_text)
                logger.info(f"Успешно извлечено {len(parsed_response.orders)} заказов")
                return parsed_response
            except Exception as parse_error:
                logger.error(f"Ошибка парсинга ответа LM Studio: {parse_error}")
                logger.error(f"Тип ошибки: {type(parse_error).__name__}")
                logger.error(f"Ответ LM Studio: {llm_response_text}")
                
                # Fallback: пытаемся извлечь JSON вручную
                return self._fallback_parse(llm_response_text)
                
        except Exception as e:
            logger.error(f"Ошибка при обращении к LM Studio API: {e}")
            return LLMResponse(
                orders=[],
                requires_correction=True,
                clarification_question="Произошла ошибка при обработке. Пожалуйста, опишите отчет еще раз."
            )
    
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
                data = json.loads(json_text)
                
                # Преобразуем в Pydantic модель
                orders = []
                for order_data in data.get('orders', []):
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
        Проверяет доступность LM Studio сервиса.
        
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
            logger.error(f"LM Studio сервис недоступен: {e}")
            return False
