"""
Клиент для работы с Vision API (GPT-4 Vision).

Реализует анализ изображений протоколов и извлечение текста для последующей обработки.
"""

import logging
import os
import base64
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from openai import OpenAI
from app.prompts.system_prompts import get_vision_prompt

logger = logging.getLogger(__name__)


class BaseVisionClient(ABC):
    """Базовый интерфейс для клиентов Vision API."""
    
    @abstractmethod
    def analyze_image(self, image_file_path: str, prompt: Optional[str] = None) -> str:
        """
        Анализирует изображение и извлекает текст.
        
        Args:
            image_file_path: Путь к файлу изображения
            prompt: Дополнительный промпт для анализа (опционально)
            
        Returns:
            str: Извлеченный текст или описание изображения
            
        Raises:
            Exception: При ошибках API или обработки файла
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Проверяет доступность Vision API.
        
        Returns:
            bool: True если сервис доступен
        """
        pass


class GPT4VisionClient(BaseVisionClient):
    """Клиент для работы с GPT-4 Vision API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4-vision-preview", base_url: Optional[str] = None):
        """
        Инициализация клиента.
        
        Args:
            api_key: API ключ для OpenAI
            model: Название модели Vision
            base_url: Базовый URL API (для использования с OpenRouter)
        """
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model
        
        # Поддерживаемые форматы изображений
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        Кодирует изображение в base64.
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            str: Изображение в формате base64
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _get_image_mime_type(self, image_path: str) -> str:
        """
        Определяет MIME тип изображения.
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            str: MIME тип
        """
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def analyze_image(self, image_file_path: str, prompt: Optional[str] = None) -> str:
        """
        Анализирует изображение через GPT-4 Vision API.
        
        Args:
            image_file_path: Путь к файлу изображения
            prompt: Дополнительный промпт для анализа
            
        Returns:
            str: Извлеченный текст
        """
        try:
            if not os.path.exists(image_file_path):
                raise FileNotFoundError(f"Файл изображения не найден: {image_file_path}")
            
            # Проверяем формат файла
            file_ext = Path(image_file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                raise ValueError(f"Неподдерживаемый формат изображения: {file_ext}")
            
            file_size = os.path.getsize(image_file_path)
            logger.info(f"Vision API анализ изображения:")
            logger.info(f"  - Файл: {image_file_path}")
            logger.info(f"  - Размер: {file_size} байт ({file_size / (1024*1024):.2f} МБ)")
            logger.info(f"  - Формат: {file_ext}")
            logger.info(f"  - Модель: {self.model}")
            
            # Кодируем изображение в base64
            base64_image = self._encode_image_to_base64(image_file_path)
            mime_type = self._get_image_mime_type(image_file_path)
            
            # Формируем промпт для анализа протокола
            if prompt is None:
                try:
                    prompt = get_vision_prompt()
                except Exception:
                    # Fallback на встроенный промпт
                    prompt = self._get_default_protocol_prompt()
            
            # Формируем сообщения для API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                                "detail": "high"  # Высокое качество для лучшего распознавания текста
                            }
                        }
                    ]
                }
            ]
            
            logger.info(f"Отправляем запрос к GPT-4 Vision API:")
            logger.info(f"  - Модель: {self.model}")
            logger.info(f"  - Размер base64: {len(base64_image)} символов")
            logger.info(f"  - MIME тип: {mime_type}")
            logger.info(f"  - Длина промпта: {len(prompt)} символов")
            
            # Отправляем запрос к Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0
            )
            
            # Получаем результат
            extracted_text = response.choices[0].message.content
            
            logger.info(f"GPT-4 Vision API ответ получен:")
            logger.info(f"  - Длина ответа: {len(extracted_text)} символов")
            logger.info(f"  - Первые 300 символов: {extracted_text[:300]}...")
            logger.debug(f"Полный извлеченный текст: {extracted_text}")
            
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения {image_file_path}: {e}")
            raise
    
    def _get_default_protocol_prompt(self) -> str:
        """
        Возвращает промпт по умолчанию для анализа протоколов.
        
        Returns:
            str: Промпт для анализа протокола
        """
        return """Проанализируй это изображение протокола ОТК и извлеки из него весь текст.

Это может быть:
- Протокол проверки изделий с номерами заказов (например, #с10409, #с10494)
- Отчет о качестве с указанием статусов (годно, в доработку, в брак)
- Документ с техническими комментариями контролера

ВАЖНО:
1. Извлеки ВСЕ текстовые данные с изображения
2. Сохрани структуру документа (заголовки, разделы, списки)
3. Обрати особое внимание на номера заказов (обычно начинаются с #с или №)
4. Точно передай все статусы и комментарии
5. Если есть таблицы - сохрани их структуру
6. Если текст плохо читается - укажи на это

Ответь только извлеченным текстом без дополнительных комментариев."""
    
    def is_available(self) -> bool:
        """
        Проверяет доступность GPT-4 Vision API.
        
        Returns:
            bool: True если сервис доступен
        """
        try:
            # Простой тест - проверяем доступность модели
            models = self.client.models.list()
            available_models = [model.id for model in models.data]
            
            # Проверяем, доступна ли наша модель
            vision_models = [
                "gpt-4-vision-preview", 
                "gpt-4-turbo", 
                "gpt-4o",
                "gpt-4o-mini"
            ]
            
            model_available = any(vm in available_models for vm in vision_models)
            
            if model_available:
                logger.info("GPT-4 Vision API доступен")
                return True
            else:
                logger.warning(f"Vision модели недоступны. Доступные модели: {available_models[:5]}...")
                return False
                
        except Exception as e:
            logger.error(f"GPT-4 Vision API недоступен: {e}")
            return False


class OpenRouterVisionClient(BaseVisionClient):
    """Клиент для работы с Vision моделями через OpenRouter."""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-4-vision-preview"):
        """
        Инициализация клиента для OpenRouter.
        
        Args:
            api_key: API ключ для OpenRouter
            model: Название модели на OpenRouter
        """
        self.client = OpenAI(
            api_key=api_key, 
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Кодирует изображение в base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _get_image_mime_type(self, image_path: str) -> str:
        """Определяет MIME тип изображения."""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def analyze_image(self, image_file_path: str, prompt: Optional[str] = None) -> str:
        """
        Анализирует изображение через OpenRouter Vision API.
        
        Args:
            image_file_path: Путь к файлу изображения
            prompt: Дополнительный промпт для анализа
            
        Returns:
            str: Извлеченный текст
        """
        try:
            if not os.path.exists(image_file_path):
                raise FileNotFoundError(f"Файл изображения не найден: {image_file_path}")
            
            # Проверяем формат файла
            file_ext = Path(image_file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                raise ValueError(f"Неподдерживаемый формат изображения: {file_ext}")
            
            file_size = os.path.getsize(image_file_path)
            logger.info(f"OpenRouter Vision API анализ изображения:")
            logger.info(f"  - Файл: {image_file_path}")
            logger.info(f"  - Размер: {file_size} байт ({file_size / (1024*1024):.2f} МБ)")
            logger.info(f"  - Формат: {file_ext}")
            logger.info(f"  - Модель: {self.model}")
            
            # Кодируем изображение в base64
            base64_image = self._encode_image_to_base64(image_file_path)
            mime_type = self._get_image_mime_type(image_file_path)
            
            # Формируем промпт для анализа протокола
            if prompt is None:
                try:
                    prompt = get_vision_prompt()
                except Exception:
                    # Fallback на встроенный промпт
                    prompt = self._get_default_protocol_prompt()
            
            # Формируем сообщения для API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            logger.info(f"Отправляем запрос к OpenRouter Vision API:")
            logger.info(f"  - Модель: {self.model}")
            logger.info(f"  - Размер base64: {len(base64_image)} символов")
            logger.info(f"  - MIME тип: {mime_type}")
            logger.info(f"  - Длина промпта: {len(prompt)} символов")
            
            # Отправляем запрос к OpenRouter Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0
            )
            
            # Получаем результат
            extracted_text = response.choices[0].message.content
            
            logger.info(f"OpenRouter Vision API ответ получен:")
            logger.info(f"  - Длина ответа: {len(extracted_text)} символов")
            logger.info(f"  - Первые 300 символов: {extracted_text[:300]}...")
            logger.debug(f"Полный извлеченный текст: {extracted_text}")
            
            return extracted_text.strip()
            
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения через OpenRouter {image_file_path}: {e}")
            raise
    
    def _get_default_protocol_prompt(self) -> str:
        """Возвращает промпт по умолчанию для анализа протоколов."""
        return """Проанализируй это изображение протокола ОТК и извлеки из него весь текст.

Это может быть:
- Протокол проверки изделий с номерами заказов (например, #с10409, #с10494)
- Отчет о качестве с указанием статусов (годно, в доработку, в брак)
- Документ с техническими комментариями контролера

ВАЖНО:
1. Извлеки ВСЕ текстовые данные с изображения
2. Сохрани структуру документа (заголовки, разделы, списки)
3. Обрати особое внимание на номера заказов (обычно начинаются с #с или №)
4. Точно передай все статусы и комментарии
5. Если есть таблицы - сохрани их структуру
6. Если текст плохо читается - укажи на это

Ответь только извлеченным текстом без дополнительных комментариев."""
    
    def is_available(self) -> bool:
        """
        Проверяет доступность OpenRouter Vision API.
        
        Returns:
            bool: True если сервис доступен
        """
        try:
            # Простой тест - получаем список моделей
            models = self.client.models.list()
            
            # Ищем vision модели в списке
            available_models = [model.id for model in models.data]
            vision_keywords = ["vision", "gpt-4o", "claude", "gemini"]
            
            has_vision_models = any(
                any(keyword in model_id.lower() for keyword in vision_keywords)
                for model_id in available_models
            )
            
            if has_vision_models:
                logger.info("OpenRouter Vision API доступен")
                return True
            else:
                logger.warning("Vision модели в OpenRouter недоступны")
                return False
                
        except Exception as e:
            logger.error(f"OpenRouter Vision API недоступен: {e}")
            return False


class LocalVisionClient(BaseVisionClient):
    """Клиент для работы с локальными Vision моделями."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Инициализация клиента для локальных Vision моделей.
        
        Args:
            base_url: URL локального Vision сервера (например, Ollama с LLaVA)
        """
        self.base_url = base_url.rstrip('/')
        
    def analyze_image(self, image_file_path: str, prompt: Optional[str] = None) -> str:
        """
        Анализирует изображение через локальную Vision модель.
        
        Args:
            image_file_path: Путь к файлу изображения
            prompt: Дополнительный промпт для анализа
            
        Returns:
            str: Извлеченный текст
        """
        # TODO: Реализовать интеграцию с локальными Vision моделями (LLaVA через Ollama)
        raise NotImplementedError("Локальные Vision модели пока не реализованы")
    
    def is_available(self) -> bool:
        """
        Проверяет доступность локального Vision сервера.
        
        Returns:
            bool: True если сервис доступен
        """
        # TODO: Реализовать проверку доступности
        return False


def create_vision_client(provider: str, **kwargs) -> BaseVisionClient:
    """
    Фабрика для создания Vision клиентов.
    
    Args:
        provider: Тип провайдера ("gpt4_vision", "openrouter", "local")
        **kwargs: Параметры для инициализации клиента
        
    Returns:
        BaseVisionClient: Клиент для работы с Vision API
        
    Raises:
        ValueError: При неизвестном провайдере
    """
    if provider == "gpt4_vision":
        return GPT4VisionClient(**kwargs)
    elif provider == "openrouter":
        return OpenRouterVisionClient(**kwargs)
    elif provider == "local":
        return LocalVisionClient(**kwargs)
    else:
        raise ValueError(f"Неизвестный провайдер Vision API: {provider}")
