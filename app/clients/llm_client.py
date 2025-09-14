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
        
        self.prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    system_template.format(format_instructions=format_instructions)
                ),
                HumanMessagePromptTemplate.from_template("{user_input}")
            ],
            input_variables=["user_input"]
        )
    
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
            
            # Формируем промпт
            formatted_prompt = self.prompt.format(user_input=full_text)
            
            # Отправляем запрос к LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": formatted_prompt.split("Human:")[0].replace("System:", "").strip()},
                    {"role": "user", "content": formatted_prompt.split("Human:")[1].strip()}
                ],
                temperature=0,
                max_tokens=2000
            )
            
            llm_response_text = response.choices[0].message.content
            logger.info(f"Получен ответ от LLM. Длина ответа: {len(llm_response_text)} символов")
            
            # Парсим ответ
            try:
                parsed_response = self.parser.parse(llm_response_text)
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
