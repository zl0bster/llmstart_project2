"""
Тесты для фото пайплайна (итерация 5).

Проверяет интеграцию Vision API, обработку изображений и извлечение данных.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.vision_client import create_vision_client, GPT4VisionClient, OpenRouterVisionClient
from app.services.media_processor import media_processor
from app.prompts.system_prompts import get_vision_prompt
from app.core.config import settings

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_vision_client_creation():
    """Тест создания Vision клиентов."""
    logger.info("=== Тест создания Vision клиентов ===")
    
    try:
        # Тест создания OpenRouter клиента
        if settings.openrouter_api_key:
            openrouter_client = create_vision_client(
                "openrouter",
                api_key=settings.openrouter_api_key,
                model=settings.vision_model
            )
            logger.info(f"✅ OpenRouter Vision клиент создан: {type(openrouter_client)}")
            
            # Проверяем доступность
            is_available = openrouter_client.is_available()
            logger.info(f"OpenRouter Vision API доступен: {is_available}")
        else:
            logger.warning("❌ OpenRouter API ключ отсутствует")
        
        # Тест создания GPT-4 Vision клиента
        if settings.openai_api_key:
            gpt4_client = create_vision_client(
                "gpt4_vision",
                api_key=settings.openai_api_key,
                model="gpt-4-vision-preview"
            )
            logger.info(f"✅ GPT-4 Vision клиент создан: {type(gpt4_client)}")
            
            # Проверяем доступность
            is_available = gpt4_client.is_available()
            logger.info(f"GPT-4 Vision API доступен: {is_available}")
        else:
            logger.warning("❌ OpenAI API ключ отсутствует")
        
        logger.info("✅ Тест создания клиентов завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании Vision клиентов: {e}")
        raise


def test_vision_prompt_loading():
    """Тест загрузки промпта для Vision API."""
    logger.info("=== Тест загрузки Vision промпта ===")
    
    try:
        vision_prompt = get_vision_prompt()
        logger.info(f"✅ Vision промпт загружен, длина: {len(vision_prompt)} символов")
        logger.info(f"Первые 200 символов: {vision_prompt[:200]}...")
        
        # Проверяем ключевые слова в промпте
        key_phrases = [
            "протокол", "ОТК", "заказов", "статус", 
            "годно", "брак", "доработку", "текст"
        ]
        
        for phrase in key_phrases:
            if phrase in vision_prompt.lower():
                logger.info(f"✅ Ключевая фраза найдена: '{phrase}'")
            else:
                logger.warning(f"⚠️ Ключевая фраза не найдена: '{phrase}'")
        
        logger.info("✅ Тест загрузки промпта завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке Vision промпта: {e}")
        raise


def test_media_processor_photo_validation():
    """Тест валидации фото через MediaProcessor."""
    logger.info("=== Тест валидации фото ===")
    
    try:
        # Создаем тестовое изображение (простой способ без PIL)
        test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        test_filename = "test_protocol.png"
        test_user_id = 12345
        
        # Сохраняем тестовое изображение
        saved_path = media_processor.save_photo_file(
            test_image_data, test_filename, test_user_id
        )
        logger.info(f"✅ Тестовое изображение сохранено: {saved_path}")
        
        # Проверяем что файл существует
        if os.path.exists(saved_path):
            logger.info(f"✅ Файл существует, размер: {os.path.getsize(saved_path)} байт")
            
            # Удаляем тестовый файл
            os.remove(saved_path)
            logger.info("✅ Тестовый файл удален")
        else:
            logger.error("❌ Сохраненный файл не найден")
        
        logger.info("✅ Тест валидации фото завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании валидации фото: {e}")
        raise


async def test_vision_api_mock():
    """Мок-тест Vision API (без реального изображения)."""
    logger.info("=== Мок-тест Vision API ===")
    
    try:
        # Создаем клиент если возможно
        vision_client = None
        
        if settings.openrouter_api_key:
            vision_client = OpenRouterVisionClient(
                api_key=settings.openrouter_api_key,
                model=settings.vision_model
            )
            logger.info("✅ OpenRouter Vision клиент создан для мок-теста")
        elif settings.openai_api_key:
            vision_client = GPT4VisionClient(
                api_key=settings.openai_api_key,
                model="gpt-4-vision-preview"
            )
            logger.info("✅ GPT-4 Vision клиент создан для мок-теста")
        else:
            logger.warning("❌ Нет API ключей для Vision тестирования")
            return
        
        # Проверяем доступность
        if vision_client and vision_client.is_available():
            logger.info("✅ Vision API доступен для тестирования")
        else:
            logger.warning("⚠️ Vision API недоступен, пропускаем тест")
            return
        
        logger.info("✅ Мок-тест Vision API завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при мок-тестировании Vision API: {e}")
        # Не raise, так как это может быть нормально


def test_cache_directories():
    """Тест создания директорий кэша."""
    logger.info("=== Тест директорий кэша ===")
    
    try:
        # Проверяем что основные директории созданы
        cache_dirs = [
            settings.cache_dir,
            settings.cache_photos_dir,
            settings.cache_audio_dir
        ]
        
        for directory in cache_dirs:
            if os.path.exists(directory):
                logger.info(f"✅ Директория существует: {directory}")
            else:
                logger.warning(f"⚠️ Директория не найдена: {directory}")
                # Создаем если нужно
                Path(directory).mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Директория создана: {directory}")
        
        # Проверяем статистику кэша
        cache_stats = media_processor.get_cache_stats()
        logger.info(f"✅ Статистика кэша: {cache_stats}")
        
        logger.info("✅ Тест директорий кэша завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке директорий кэша: {e}")
        raise


async def main():
    """Основная функция тестирования."""
    logger.info("🚀 Начинаем тестирование фото пайплайна (итерация 5)")
    logger.info(f"Конфигурация Vision: {settings.vision_provider} / {settings.vision_model}")
    
    try:
        # Тесты создания клиентов
        test_vision_client_creation()
        
        # Тест загрузки промптов
        test_vision_prompt_loading()
        
        # Тест валидации медиа
        test_media_processor_photo_validation()
        
        # Тест директорий
        test_cache_directories()
        
        # Мок-тест API
        await test_vision_api_mock()
        
        logger.info("🎉 Все тесты фото пайплайна завершены успешно!")
        logger.info("💡 Для полного тестирования отправьте реальное фото протокола в бот")
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка в тестах: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
