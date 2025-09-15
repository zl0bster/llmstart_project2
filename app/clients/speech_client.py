"""
Клиент для работы с Speech API (Whisper).

Реализует транскрипцию голосовых сообщений в текст.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class BaseSpeechClient(ABC):
    """Базовый интерфейс для клиентов Speech API."""
    
    @abstractmethod
    def transcribe_audio(self, audio_file_path: str, language: Optional[str] = None) -> str:
        """
        Транскрибирует аудио файл в текст.
        
        Args:
            audio_file_path: Путь к аудио файлу
            language: Язык аудио (опционально)
            
        Returns:
            str: Транскрибированный текст
            
        Raises:
            Exception: При ошибках API или обработки файла
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Проверяет доступность Speech API.
        
        Returns:
            bool: True если сервис доступен
        """
        pass


class WhisperClient(BaseSpeechClient):
    """Клиент для работы с OpenAI Whisper API."""
    
    def __init__(self, api_key: str, model: str = "whisper-1", base_url: Optional[str] = None):
        """
        Инициализация клиента.
        
        Args:
            api_key: API ключ для OpenAI
            model: Название модели Whisper
            base_url: Базовый URL API (для использования с OpenRouter)
        """
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def transcribe_audio(self, audio_file_path: str, language: Optional[str] = "ru") -> str:
        """
        Транскрибирует аудио файл в текст через Whisper API.
        
        Args:
            audio_file_path: Путь к аудио файлу
            language: Язык аудио (по умолчанию русский)
            
        Returns:
            str: Транскрибированный текст
        """
        try:
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Аудио файл не найден: {audio_file_path}")
            
            file_size = os.path.getsize(audio_file_path)
            logger.info(f"Начинаем транскрипцию файла {audio_file_path} (размер: {file_size} байт)")
            
            with open(audio_file_path, "rb") as audio_file:
                # Формируем параметры запроса
                transcription_params = {
                    "file": audio_file,
                    "model": self.model,
                    "response_format": "text"
                }
                
                # Добавляем язык если указан
                if language:
                    transcription_params["language"] = language
                
                # Отправляем запрос к Whisper API
                response = self.client.audio.transcriptions.create(**transcription_params)
                
                # Получаем текст
                if isinstance(response, str):
                    transcribed_text = response
                else:
                    transcribed_text = response.text if hasattr(response, 'text') else str(response)
                
                logger.info(f"Транскрипция завершена. Длина текста: {len(transcribed_text)} символов")
                logger.debug(f"Транскрибированный текст: {transcribed_text[:200]}...")
                
                return transcribed_text.strip()
                
        except Exception as e:
            logger.error(f"Ошибка при транскрипции аудио файла {audio_file_path}: {e}")
            raise
    
    def is_available(self) -> bool:
        """
        Проверяет доступность Whisper API.
        
        Returns:
            bool: True если сервис доступен
        """
        try:
            # Простой тест - получаем список моделей
            models = self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Whisper API недоступен: {e}")
            return False


class WhisperAPIClient(BaseSpeechClient):
    """Клиент для работы с WhisperAPI.com."""
    
    def __init__(self, api_key: str, model: str = "large-v2", base_url: str = "https://api.whisper-api.com"):
        """
        Инициализация клиента для WhisperAPI.
        
        Args:
            api_key: API ключ для WhisperAPI
            model: Размер модели (tiny, base, small, medium, large, large-v2)
            base_url: Базовый URL WhisperAPI
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip('/')
        
    def transcribe_audio(self, audio_file_path: str, language: Optional[str] = "ru") -> str:
        """
        Транскрибирует аудио файл через WhisperAPI.
        
        Args:
            audio_file_path: Путь к аудио файлу
            language: Язык аудио
            
        Returns:
            str: Транскрибированный текст
        """
        try:
            import requests
            
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Аудио файл не найден: {audio_file_path}")
            
            file_size = os.path.getsize(audio_file_path)
            logger.info(f"Начинаем транскрипцию через WhisperAPI: {audio_file_path} (размер: {file_size} байт)")
            
            # Подготавливаем данные для запроса
            with open(audio_file_path, "rb") as audio_file:
                files = {
                    'file': audio_file
                }
                data = {
                    'language': language if language else 'ru',
                    'format': 'text',  # Получаем простой текст
                    'model_size': self.model
                }
                headers = {
                    'X-API-Key': self.api_key
                }
                
                # Логируем параметры запроса
                logger.info(f"Отправляем запрос к WhisperAPI: {self.base_url}/transcribe")
                logger.info(f"Параметры: {data}")
                logger.info(f"Размер файла: {len(audio_file.read())} байт")
                audio_file.seek(0)  # Возвращаем указатель в начало
                
                # Отправляем запрос к WhisperAPI
                response = requests.post(
                    f"{self.base_url}/transcribe",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=300  # 5 минут на транскрипцию
                )
                
                # Детальное логирование ответа
                logger.info(f"Ответ WhisperAPI: статус {response.status_code}")
                logger.info(f"Заголовки ответа: {dict(response.headers)}")
                logger.info(f"Содержимое ответа (первые 500 символов): {response.text[:500]}")
                
                response.raise_for_status()
                
                # Получаем результат
                if response.headers.get('content-type', '').startswith('application/json'):
                    result = response.json()
                    logger.info(f"JSON ответ: {result}")
                    transcribed_text = result.get('text', '').strip()
                else:
                    # Если возвращается простой текст
                    transcribed_text = response.text.strip()
                
                logger.info(f"WhisperAPI транскрипция завершена. Длина текста: {len(transcribed_text)} символов")
                logger.debug(f"Транскрибированный текст: {transcribed_text[:200]}...")
                
                return transcribed_text
                
        except Exception as e:
            logger.error(f"Ошибка при транскрипции через WhisperAPI {audio_file_path}: {e}")
            raise
    
    def is_available(self) -> bool:
        """
        Проверяет доступность WhisperAPI.
        
        Returns:
            bool: True если сервис доступен
        """
        try:
            import requests
            
            # Проверяем доступность основного URL
            status_url = f"{self.base_url}/status"
            logger.info(f"Проверяем доступность WhisperAPI: {status_url}")
            
            response = requests.get(status_url, timeout=10)
            logger.info(f"Ответ от WhisperAPI status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("WhisperAPI доступен")
                return True
            else:
                logger.warning(f"WhisperAPI вернул код {response.status_code}")
                # Если эндпоинт статуса недоступен, считаем что API работает
                return True
                
        except Exception as e:
            logger.warning(f"Не удалось проверить статус WhisperAPI: {e}")
            logger.info("Считаем WhisperAPI доступным (эндпоинт статуса может отсутствовать)")
            # Считаем сервис доступным если нет эндпоинта статуса
            return True


class LocalWhisperClient(BaseSpeechClient):
    """Клиент для работы с локальным Whisper (whisper.cpp или другие)."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Инициализация клиента для локального Whisper.
        
        Args:
            base_url: URL локального Whisper сервера
        """
        self.base_url = base_url.rstrip('/')
        
    def transcribe_audio(self, audio_file_path: str, language: Optional[str] = "ru") -> str:
        """
        Транскрибирует аудио файл через локальный Whisper.
        
        Args:
            audio_file_path: Путь к аудио файлу
            language: Язык аудио
            
        Returns:
            str: Транскрибированный текст
        """
        # TODO: Реализовать интеграцию с локальным Whisper
        raise NotImplementedError("Локальный Whisper пока не реализован")
    
    def is_available(self) -> bool:
        """
        Проверяет доступность локального Whisper сервера.
        
        Returns:
            bool: True если сервис доступен
        """
        # TODO: Реализовать проверку доступности
        return False


def create_speech_client(provider: str, **kwargs) -> BaseSpeechClient:
    """
    Фабрика для создания Speech клиентов.
    
    Args:
        provider: Тип провайдера ("whisper", "whisperapi", "whisper_local")
        **kwargs: Параметры для инициализации клиента
        
    Returns:
        BaseSpeechClient: Клиент для работы с Speech API
        
    Raises:
        ValueError: При неизвестном провайдере
    """
    if provider == "whisper":
        return WhisperClient(**kwargs)
    elif provider == "whisperapi":
        return WhisperAPIClient(**kwargs)
    elif provider == "whisper_local":
        return LocalWhisperClient(**kwargs)
    else:
        raise ValueError(f"Неизвестный провайдер Speech API: {provider}")
