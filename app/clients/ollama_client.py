"""
Клиент для работы с LLM через Ollama.

Реализует извлечение структурированных данных из текстовых отчетов ОТК через локальный Ollama.
"""

import logging
import json
import requests
from typing import List, Optional
from langchain.output_parsers import PydanticOutputParser

from app.clients.base_client import BaseLLMClient
from app.models.schemas import LLMResponse, OrderData
from app.prompts.system_prompts import get_system_prompt

logger = logging.getLogger(__name__)


class OllamaLLMClient(BaseLLMClient):
    """Клиент для работы с LLM через Ollama."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b", 
                 auto_pull: bool = True, timeout_sec: int = 120, num_predict: int = 2000, 
                 temperature: float = 0.1):
        """
        Инициализация клиента.
        
        Args:
            base_url: URL локального Ollama сервера
            model: Название модели для использования
            auto_pull: Автоматическое скачивание модели при запуске
            timeout_sec: Таймаут для запросов в секундах
            num_predict: Количество токенов для генерации ответа
            temperature: Температура для генерации
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.auto_pull = auto_pull
        self.timeout_sec = timeout_sec
        self.num_predict = num_predict
        self.temperature = temperature
        self.parser = PydanticOutputParser(pydantic_object=LLMResponse)
        
        logger.info(f"Ollama клиент инициализирован: {base_url}, модель: {model}")
    
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
            
            logger.info(f"Отправка запроса к Ollama. Длина текста: {len(full_text)} символов")
            
            # Формируем системный промпт без LangChain форматирования
            system_prompt = get_system_prompt()
            format_instructions = self.parser.get_format_instructions()
            
            # Заменяем {format_instructions} в системном промпте
            system_content = system_prompt.replace("{format_instructions}", format_instructions)
            
            # Подготавливаем сообщения для Ollama API
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": full_text}
            ]
            
            # Отправляем запрос к Ollama
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "top_p": 0.9,
                    "num_predict": self.num_predict
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout_sec
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Проверяем, что ответ корректный
            if not response_data.get("message") or not response_data["message"].get("content"):
                logger.error("Ollama вернул пустой ответ")
                raise Exception("Ollama вернул пустой ответ")
            
            llm_response_text = response_data["message"]["content"]
            logger.info(f"Получен ответ от Ollama. Длина ответа: {len(llm_response_text)} символов")
            
            # Парсим ответ
            try:
                parsed_response = self.parser.parse(llm_response_text)
                logger.info(f"Успешно извлечено {len(parsed_response.orders)} заказов")
                return parsed_response
            except Exception as parse_error:
                logger.error(f"Ошибка парсинга ответа Ollama: {parse_error}")
                logger.error(f"Тип ошибки: {type(parse_error).__name__}")
                logger.error(f"Ответ Ollama: {llm_response_text}")
                
                # Fallback: пытаемся извлечь JSON вручную
                return self._fallback_parse(llm_response_text)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при обращении к Ollama API: {e}")
            return LLMResponse(
                orders=[],
                requires_correction=True,
                clarification_question="Сервис обработки временно недоступен. Пожалуйста, попробуйте позже."
            )
        except Exception as e:
            logger.error(f"Ошибка при обращении к Ollama API: {e}")
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
            # Удаляем <think> теги если есть
            cleaned_text = response_text
            if '<think>' in cleaned_text and '</think>' in cleaned_text:
                start_think = cleaned_text.find('<think>')
                end_think = cleaned_text.find('</think>') + len('</think>')
                cleaned_text = cleaned_text[:start_think] + cleaned_text[end_think:]
            
            # Ищем JSON в тексте
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_text = cleaned_text[start_idx:end_idx]
                
                # Исправляем частые ошибки JSON
                json_text = self._fix_json_errors(json_text)
                
                data = json.loads(json_text)
                
                # Преобразуем в Pydantic модель
                orders = []
                for order_data in data.get('orders', []):
                    # Преобразуем строковые статусы в enum
                    if isinstance(order_data.get('status'), str):
                        status_map = {
                            'годно': 'approved',
                            'в доработку': 'rework', 
                            'в брак': 'reject'
                        }
                        order_data['status'] = status_map.get(order_data['status'], order_data['status'])
                    
                    orders.append(OrderData(**order_data))
                
                return LLMResponse(
                    orders=orders,
                    requires_correction=data.get('requires_correction', False),
                    clarification_question=data.get('clarification_question')
                )
        except Exception as e:
            logger.error(f"Ошибка fallback парсинга: {e}")
            logger.error(f"Исходный текст: {response_text[:500]}...")
        
        # Если ничего не получилось
        return LLMResponse(
            orders=[],
            requires_correction=True,
            clarification_question="Не удалось обработать данные. Пожалуйста, опишите отчет еще раз."
        )
    
    def _fix_json_errors(self, json_text: str) -> str:
        """
        Исправляет частые ошибки JSON.
        
        Args:
            json_text: Текст JSON
            
        Returns:
            str: Исправленный JSON
        """
        # Исправляем отсутствие закрывающей скобки массива orders
        if '"orders": [' in json_text and not json_text.rstrip().endswith(']'):
            # Ищем последний элемент в массиве orders
            lines = json_text.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('"order_id"') and i + 2 < len(lines):
                    next_line = lines[i + 2].strip()
                    if next_line.startswith('},'):
                        # Заменяем }, на ]
                        lines[i + 2] = '    ]'
                        break
            
            json_text = '\n'.join(lines)
        
        return json_text
    
    def is_available(self) -> bool:
        """
        Проверяет доступность Ollama сервиса.
        
        Returns:
            bool: True если сервис доступен
        """
        try:
            # Проверяем доступность модели
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            response.raise_for_status()
            
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            # Проверяем, что нужная модель доступна
            if self.model not in model_names:
                logger.error(f"Модель {self.model} не найдена в Ollama. Доступные модели: {model_names}")
                return False
            
            # Простой тестовый запрос
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "stream": False,
                "options": {"num_predict": 1}
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout_sec
            )
            response.raise_for_status()
            
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama сервис недоступен: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки доступности Ollama: {e}")
            return False
    
    def pull_model(self) -> bool:
        """
        Скачивает модель из Ollama реестра.
        
        Returns:
            bool: True если модель успешно скачана
        """
        try:
            logger.info(f"Начинаем скачивание модели {self.model}...")
            
            payload = {
                "name": self.model,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=600  # 10 минут на скачивание
            )
            response.raise_for_status()
            
            logger.info(f"Модель {self.model} успешно скачана")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при скачивании модели {self.model}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при скачивании модели: {e}")
            return False
