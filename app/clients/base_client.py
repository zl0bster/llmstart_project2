"""
Базовый интерфейс для клиентов LLM.

Абстрактный базовый класс для всех клиентов работы с LLM.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.schemas import LLMResponse


class BaseLLMClient(ABC):
    """Базовый интерфейс для клиентов LLM."""
    
    @abstractmethod
    def process_text(self, text: str, session_history: Optional[List[str]] = None) -> LLMResponse:
        """
        Обрабатывает текст через LLM и возвращает структурированные данные.
        
        Args:
            text: Текст для обработки
            session_history: История сообщений сессии
            
        Returns:
            LLMResponse: Структурированный ответ LLM
            
        Raises:
            Exception: При ошибках API или парсинга
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Проверяет доступность LLM сервиса.
        
        Returns:
            bool: True если сервис доступен
        """
        pass
