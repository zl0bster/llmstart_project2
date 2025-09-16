"""Обработчики фото сообщений."""

import logging
import os
from typing import Dict, Any
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.clients.vision_client import create_vision_client, GPT4VisionClient, OpenRouterVisionClient
from app.services.media_processor import media_processor
from app.services.session_service import get_session_manager
from app.bot.keyboards import get_processing_keyboard
from app.core.config import settings

# Создаем роутер для фото сообщений
router = Router()

# Инициализация компонентов
vision_client = None

logger = logging.getLogger(__name__)


def init_vision_client():
    """Инициализация Vision клиента."""
    global vision_client
    if vision_client is None:
        try:
            if settings.vision_provider == "openrouter":
                if settings.openrouter_api_key:
                    vision_client = OpenRouterVisionClient(
                        api_key=settings.openrouter_api_key,
                        model=settings.vision_model
                    )
                    logger.info(f"OpenRouter Vision клиент инициализирован с моделью {settings.vision_model}")
                else:
                    logger.error("Нет API ключа для OpenRouter Vision")
                    return False
            elif settings.vision_provider == "gpt4_vision":
                if settings.openai_api_key:
                    vision_client = GPT4VisionClient(
                        api_key=settings.openai_api_key,
                        model=settings.vision_model
                    )
                    logger.info(f"GPT-4 Vision клиент инициализирован с моделью {settings.vision_model}")
                else:
                    logger.error("Нет API ключа для GPT-4 Vision")
                    return False
            else:
                logger.error(f"Неподдерживаемый провайдер Vision: {settings.vision_provider}")
                return False
            
            # Проверяем доступность
            if not vision_client.is_available():
                logger.error("Vision клиент недоступен")
                vision_client = None
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации Vision клиента: {e}")
            vision_client = None
            return False
    
    return True


def validate_image_file(file_path: str) -> Dict[str, Any]:
    """
    Валидирует изображение и возвращает метаданные.
    
    Args:
        file_path: Путь к файлу изображения
        
    Returns:
        Dict[str, Any]: Метаданные изображения
        
    Raises:
        ValueError: При невалидном файле
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # Проверяем размер файла
        if file_size_mb > settings.max_image_mb:
            raise ValueError(f"Размер файла {file_size_mb:.1f}MB превышает лимит {settings.max_image_mb}MB")
        
        # Попытаемся получить разрешение изображения
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format
                mode = img.mode
                
                # Проверяем разрешение
                max_res_str = settings.max_image_res  # например "2048x2048"
                max_width, max_height = map(int, max_res_str.split('x'))
                
                if width > max_width or height > max_height:
                    raise ValueError(
                        f"Разрешение {width}x{height} превышает лимит {max_width}x{max_height}"
                    )
                
                metadata = {
                    'width': width,
                    'height': height,
                    'format': format_name,
                    'mode': mode,
                    'file_size': file_size,
                    'file_size_mb': round(file_size_mb, 2)
                }
                
        except ImportError:
            # PIL недоступен, используем базовую валидацию
            logger.warning("PIL недоступен, используем базовую валидацию изображений")
            metadata = {
                'width': None,
                'height': None,
                'format': None,
                'mode': None,
                'file_size': file_size,
                'file_size_mb': round(file_size_mb, 2)
            }
        
        logger.info(f"Валидация изображения: {metadata}")
        
        return metadata
        
    except Exception as e:
        logger.error(f"Ошибка валидации изображения {file_path}: {e}")
        raise


@router.message(F.photo)
async def handle_photo_message(message: Message, bot: Bot) -> None:
    """Обработчик фото сообщений."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    session_id = None
    
    logger.info(f"Получено фото сообщение от пользователя {user_id}")
    
    try:
        # Инициализируем клиент если нужно
        if not init_vision_client():
            await message.answer(
                "❌ <b>Ошибка обработки изображения</b>\n\n"
                "Сервис анализа изображений временно недоступен. "
                "Пожалуйста, отправьте сообщение текстом.",
                parse_mode="HTML"
            )
            return
        
        # Создаем или получаем сессию
        session_manager = get_session_manager()
        session_id = session_manager.get_or_create_session(user_id)
        
        # Отправляем сообщение о начале обработки
        processing_msg = await message.answer(
            "📸 <b>Обрабатываю изображение...</b>\n\n"
            "⏳ Идет анализ изображения через Vision API...",
            reply_markup=get_processing_keyboard(),
            parse_mode="HTML"
        )
        
        # Получаем информацию о фото (берем самое большое разрешение)
        photo = message.photo[-1]  # Последнее фото - самое большое
        file_id = photo.file_id
        file_size = photo.file_size
        
        logger.info(f"Фото сообщение: file_id: {file_id}, размер: {file_size} байт")
        
        # Проверяем размер файла
        if file_size and file_size > settings.max_image_mb * 1024 * 1024:
            await processing_msg.edit_text(
                f"❌ <b>Файл слишком большой</b>\n\n"
                f"Размер {file_size/(1024*1024):.1f}MB превышает лимит "
                f"{settings.max_image_mb}MB.",
                parse_mode="HTML"
            )
            return
        
        # Скачиваем файл
        file = await bot.get_file(file_id)
        file_content = await bot.download_file(file.file_path)
        
        # Определяем расширение файла из пути
        file_extension = '.jpg'  # По умолчанию Telegram фото как JPG
        if hasattr(file, 'file_path') and file.file_path:
            import os
            _, ext = os.path.splitext(file.file_path)
            if ext:
                file_extension = ext
        
        # Сохраняем в кэш
        temp_filename = f"photo_{file_id}{file_extension}"
        saved_file_path = media_processor.save_photo_file(
            file_content.read(), temp_filename, user_id
        )
        
        logger.info(f"Фото файл сохранен: {saved_file_path}")
        
        # Копируем файл в директорию логов для отладки
        import shutil
        logs_photo_path = os.path.join(settings.log_dir, f"debug_photo_{os.path.basename(saved_file_path)}")
        try:
            shutil.copy2(saved_file_path, logs_photo_path)
            logger.info(f"Копия изображения для отладки: {logs_photo_path}")
        except Exception as e:
            logger.warning(f"Не удалось скопировать изображение в логи: {e}")
        
        # Валидируем изображение
        try:
            image_metadata = validate_image_file(saved_file_path)
            logger.info(f"Детальные метаданные изображения:")
            logger.info(f"  - Размер файла: {image_metadata.get('file_size', 0)} байт ({image_metadata.get('file_size_mb', 0)} МБ)")
            logger.info(f"  - Разрешение: {image_metadata.get('width', 'неизвестно')}x{image_metadata.get('height', 'неизвестно')}")
            logger.info(f"  - Формат: {image_metadata.get('format', 'неизвестно')}")
            logger.info(f"  - Режим: {image_metadata.get('mode', 'неизвестно')}")
            logger.info(f"  - Путь: {saved_file_path}")
            logger.info(f"  - Копия в логах: {logs_photo_path}")
        except ValueError as e:
            await processing_msg.edit_text(
                f"❌ <b>Ошибка валидации изображения</b>\n\n"
                f"{str(e)}",
                parse_mode="HTML"
            )
            return
        
        # Обновляем статус
        await processing_msg.edit_text(
            "📸 <b>Обрабатываю изображение...</b>\n\n"
            "🔍 Анализирую содержимое изображения...",
            reply_markup=get_processing_keyboard(),
            parse_mode="HTML"
        )
        
        # Анализируем изображение через Vision API
        logger.info(f"Начинаем анализ изображения через Vision API...")
        logger.info(f"  - Клиент: {type(vision_client).__name__}")
        logger.info(f"  - Модель: {getattr(vision_client, 'model', 'неизвестно')}")
        
        extracted_text = vision_client.analyze_image(saved_file_path)
        
        logger.info(f"Vision API анализ завершен:")
        logger.info(f"  - Длина извлеченного текста: {len(extracted_text)} символов")
        logger.info(f"  - Первые 200 символов: {extracted_text[:200]}...")
        logger.debug(f"Полный извлеченный текст: {extracted_text}")
        
        # Сохраняем извлеченный текст в сессию
        session_manager.add_message(user_id, f"[ФОТО -> ТЕКСТ]: {extracted_text}")
        
        # Обновляем сообщение
        preview_text = extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
        await processing_msg.edit_text(
            "📸 <b>Анализ изображения завершен</b>\n\n"
            f"📝 <i>Извлеченный текст:</i>\n{preview_text}\n\n"
            "🔄 Анализирую данные...",
            reply_markup=get_processing_keyboard(),
            parse_mode="HTML"
        )
        
        # Импортируем функцию обработки текста из text_handlers
        from app.bot.handlers.text_handlers import process_text_with_llm
        
        # Передаем извлеченный текст в текстовый пайплайн
        await process_text_with_llm(
            user_id=user_id,
            chat_id=chat_id,
            session_id=session_id,
            text=extracted_text,
            original_message=message,
            processing_message=processing_msg,
            is_photo_extraction=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото сообщения от {user_id}: {e}")
        
        await message.answer(
            "❌ <b>Ошибка обработки изображения</b>\n\n"
            "Произошла ошибка при обработке изображения. "
            "Пожалуйста, попробуйте еще раз или отправьте сообщение текстом.",
            parse_mode="HTML"
        )


@router.message(F.document)
async def handle_document_message(message: Message, bot: Bot) -> None:
    """Обработчик документов (может содержать изображения)."""
    user_id = message.from_user.id
    
    # Проверяем, является ли документ изображением
    document = message.document
    if not document.mime_type or not document.mime_type.startswith('image/'):
        await message.answer(
            "📄 <b>Документ получен</b>\n\n"
            "Я умею обрабатывать только изображения. "
            "Если это изображение, попробуйте отправить его как фото.",
            parse_mode="HTML"
        )
        return
    
    logger.info(f"Получен документ-изображение от пользователя {user_id}: {document.file_name}")
    
    try:
        # Инициализируем клиент если нужно
        if not init_vision_client():
            await message.answer(
                "❌ <b>Ошибка обработки изображения</b>\n\n"
                "Сервис анализа изображений временно недоступен. "
                "Пожалуйста, отправьте сообщение текстом.",
                parse_mode="HTML"
            )
            return
        
        # Создаем или получаем сессию
        session_manager = get_session_manager()
        session_id = session_manager.get_or_create_session(user_id)
        
        # Отправляем сообщение о начале обработки
        processing_msg = await message.answer(
            "📄 <b>Обрабатываю документ-изображение...</b>\n\n"
            "⏳ Идет анализ документа через Vision API...",
            reply_markup=get_processing_keyboard(),
            parse_mode="HTML"
        )
        
        # Получаем информацию о документе
        file_id = document.file_id
        file_size = document.file_size
        file_name = document.file_name or "document.jpg"
        
        logger.info(f"Документ-изображение: {file_name}, file_id: {file_id}, размер: {file_size} байт")
        
        # Проверяем размер файла
        if file_size and file_size > settings.max_image_mb * 1024 * 1024:
            await processing_msg.edit_text(
                f"❌ <b>Файл слишком большой</b>\n\n"
                f"Размер {file_size/(1024*1024):.1f}MB превышает лимит "
                f"{settings.max_image_mb}MB.",
                parse_mode="HTML"
            )
            return
        
        # Скачиваем файл
        file = await bot.get_file(file_id)
        file_content = await bot.download_file(file.file_path)
        
        # Сохраняем в кэш
        saved_file_path = media_processor.save_photo_file(
            file_content.read(), file_name, user_id
        )
        
        logger.info(f"Документ-изображение сохранен: {saved_file_path}")
        
        # Копируем файл в директорию логов для отладки
        logs_photo_path = os.path.join(settings.log_dir, f"debug_document_{os.path.basename(saved_file_path)}")
        try:
            shutil.copy2(saved_file_path, logs_photo_path)
            logger.info(f"Копия документа-изображения для отладки: {logs_photo_path}")
        except Exception as e:
            logger.warning(f"Не удалось скопировать документ-изображение в логи: {e}")
        
        # Валидируем изображение
        try:
            image_metadata = validate_image_file(saved_file_path)
            logger.info(f"Детальные метаданные документа-изображения:")
            logger.info(f"  - Исходное имя: {file_name}")
            logger.info(f"  - Размер файла: {image_metadata.get('file_size', 0)} байт ({image_metadata.get('file_size_mb', 0)} МБ)")
            logger.info(f"  - Разрешение: {image_metadata.get('width', 'неизвестно')}x{image_metadata.get('height', 'неизвестно')}")
            logger.info(f"  - Формат: {image_metadata.get('format', 'неизвестно')}")
            logger.info(f"  - Режим: {image_metadata.get('mode', 'неизвестно')}")
            logger.info(f"  - Путь: {saved_file_path}")
            logger.info(f"  - Копия в логах: {logs_photo_path}")
        except ValueError as e:
            await processing_msg.edit_text(
                f"❌ <b>Ошибка валидации изображения</b>\n\n"
                f"{str(e)}",
                parse_mode="HTML"
            )
            return
        
        # Обновляем статус
        await processing_msg.edit_text(
            "📄 <b>Обрабатываю документ-изображение...</b>\n\n"
            "🔍 Анализирую содержимое документа...",
            reply_markup=get_processing_keyboard(),
            parse_mode="HTML"
        )
        
        # Анализируем изображение через Vision API
        logger.info(f"Начинаем анализ документа-изображения через Vision API...")
        logger.info(f"  - Клиент: {type(vision_client).__name__}")
        logger.info(f"  - Модель: {getattr(vision_client, 'model', 'неизвестно')}")
        
        extracted_text = vision_client.analyze_image(saved_file_path)
        
        logger.info(f"Vision API анализ документа завершен:")
        logger.info(f"  - Длина извлеченного текста: {len(extracted_text)} символов")
        logger.info(f"  - Первые 200 символов: {extracted_text[:200]}...")
        logger.debug(f"Полный извлеченный текст документа: {extracted_text}")
        
        # Сохраняем извлеченный текст в сессию
        session_manager.add_message(user_id, f"[ДОКУМЕНТ -> ТЕКСТ]: {extracted_text}")
        
        # Обновляем сообщение
        preview_text = extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
        await processing_msg.edit_text(
            "📄 <b>Анализ документа завершен</b>\n\n"
            f"📝 <i>Извлеченный текст:</i>\n{preview_text}\n\n"
            "🔄 Анализирую данные...",
            reply_markup=get_processing_keyboard(),
            parse_mode="HTML"
        )
        
        # Импортируем функцию обработки текста из text_handlers
        from app.bot.handlers.text_handlers import process_text_with_llm
        
        # Передаем извлеченный текст в текстовый пайплайн
        await process_text_with_llm(
            user_id=user_id,
            chat_id=message.chat.id,
            session_id=session_id,
            text=extracted_text,
            original_message=message,
            processing_message=processing_msg,
            is_photo_extraction=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки документа-изображения от {user_id}: {e}")
        
        await message.answer(
            "❌ <b>Ошибка обработки документа</b>\n\n"
            "Произошла ошибка при обработке документа. "
            "Пожалуйста, попробуйте еще раз или отправьте сообщение текстом.",
            parse_mode="HTML"
        )