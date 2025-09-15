"""Обработчики голосовых сообщений."""

import logging
import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.clients.speech_client import create_speech_client, WhisperClient, WhisperAPIClient
from app.services.media_processor import media_processor
from app.services.session_manager import SessionManager
from app.bot.keyboards import get_processing_keyboard
from app.core.config import settings

# Создаем роутер для голосовых сообщений
router = Router()

# Инициализация компонентов
speech_client = None
session_manager = SessionManager(timeout_minutes=settings.session_timeout_min)

logger = logging.getLogger(__name__)


def init_speech_client():
    """Инициализация Speech клиента."""
    global speech_client
    if speech_client is None:
        try:
            if settings.speech_provider == "whisper":
                if settings.openai_api_key:
                    speech_client = WhisperClient(
                        api_key=settings.openai_api_key,
                        model=settings.speech_model
                    )
                    logger.info(f"Whisper клиент инициализирован с моделью {settings.speech_model}")
                elif settings.openrouter_api_key:
                    # Используем OpenRouter для Whisper
                    speech_client = WhisperClient(
                        api_key=settings.openrouter_api_key,
                        model=settings.speech_model,
                        base_url="https://openrouter.ai/api/v1"
                    )
                    logger.info(f"Whisper через OpenRouter клиент инициализирован")
                else:
                    logger.error("Нет API ключа для Whisper")
                    return False
            elif settings.speech_provider == "whisperapi":
                if settings.whisperapi_api_key:
                    speech_client = WhisperAPIClient(
                        api_key=settings.whisperapi_api_key,
                        model=settings.speech_model
                    )
                    logger.info(f"WhisperAPI клиент инициализирован с моделью {settings.speech_model}")
                else:
                    logger.error("Нет API ключа для WhisperAPI")
                    return False
            else:
                logger.error(f"Неподдерживаемый провайдер речи: {settings.speech_provider}")
                return False
            
            # Проверяем доступность
            if not speech_client.is_available():
                logger.error("Speech клиент недоступен")
                speech_client = None
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации Speech клиента: {e}")
            speech_client = None
            return False
    
    return True


@router.message(F.voice)
async def handle_voice_message(message: Message, bot: Bot) -> None:
    """Обработчик голосовых сообщений."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    session_id = None
    
    logger.info(f"Получено голосовое сообщение от пользователя {user_id}")
    
    try:
        # Инициализируем клиент если нужно
        if not init_speech_client():
            await message.answer(
                "❌ <b>Ошибка обработки голоса</b>\n\n"
                "Сервис транскрипции временно недоступен. "
                "Пожалуйста, отправьте сообщение текстом.",
                parse_mode="HTML"
            )
            return
        
        # Создаем или получаем сессию
        session_id = session_manager.get_or_create_session(user_id)
        
        # Состояние обработки будет управляться автоматически
        
        # Отправляем сообщение о начале обработки
        processing_msg = await message.answer(
            "🎤 <b>Обрабатываю голосовое сообщение...</b>\n\n"
            "⏳ Идет транскрипция через Whisper API...",
            reply_markup=get_processing_keyboard(),
            parse_mode="HTML"
        )
        
        # Получаем информацию о голосовом файле
        voice = message.voice
        file_id = voice.file_id
        file_duration = voice.duration
        
        logger.info(f"Голосовое сообщение: {file_duration}с, file_id: {file_id}")
        
        # Проверяем длительность
        if file_duration > settings.max_audio_min * 60:
            await processing_msg.edit_text(
                f"❌ <b>Файл слишком длинный</b>\n\n"
                f"Длительность {file_duration//60}:{file_duration%60:02d} превышает лимит "
                f"{settings.max_audio_min} минут.",
                parse_mode="HTML"
            )
            state_machine.transition_to_state(user_id, BotState.idle)
            return
        
        # Скачиваем файл
        file = await bot.get_file(file_id)
        file_content = await bot.download_file(file.file_path)
        
        # Сохраняем в кэш
        file_extension = '.ogg'  # Telegram отправляет voice как OGG
        temp_filename = f"voice_{file_id}{file_extension}"
        saved_file_path = media_processor.save_audio_file(
            file_content.read(), temp_filename, user_id
        )
        
        logger.info(f"Голосовой файл сохранен: {saved_file_path}")
        
        # Копируем файл в директорию логов для проверки
        import shutil
        import os
        logs_audio_path = os.path.join(settings.log_dir, f"debug_audio_{os.path.basename(saved_file_path)}")
        try:
            shutil.copy2(saved_file_path, logs_audio_path)
            logger.info(f"Копия аудиофайла для отладки: {logs_audio_path}")
        except Exception as e:
            logger.warning(f"Не удалось скопировать аудиофайл в логи: {e}")
        
        # Валидируем и получаем метаданные
        audio_metadata = media_processor.validate_audio_file(saved_file_path)
        logger.info(f"Метаданные аудио: {audio_metadata}")
        
        # Конвертируем для оптимальной работы с Whisper
        converted_file_path = media_processor.convert_audio_for_whisper(saved_file_path)
        
        # Обновляем статус
        await processing_msg.edit_text(
            "🎤 <b>Обрабатываю голосовое сообщение...</b>\n\n"
            "🔄 Транскрибирую аудио в текст...",
            reply_markup=get_processing_keyboard(),
            parse_mode="HTML"
        )
        
        # Транскрибируем через Whisper
        transcribed_text = speech_client.transcribe_audio(converted_file_path)
        
        logger.info(f"Транскрипция завершена. Длина текста: {len(transcribed_text)} символов")
        logger.debug(f"Транскрибированный текст: {transcribed_text}")
        
        # Очищаем временные файлы
        try:
            os.remove(converted_file_path)
            logger.debug(f"Удален временный файл: {converted_file_path}")
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл {converted_file_path}: {e}")
        
        # Сохраняем транскрипцию в сессию
        session_manager.add_message(session_id, f"[ГОЛОС -> ТЕКСТ]: {transcribed_text}")
        
        # Обновляем сообщение
        await processing_msg.edit_text(
            "🎤 <b>Транскрипция завершена</b>\n\n"
            f"📝 <i>Текст сообщения:</i>\n{transcribed_text[:200]}...\n\n"
            "🔄 Анализирую данные...",
            reply_markup=get_processing_keyboard(),
            parse_mode="HTML"
        )
        
        # Импортируем функцию обработки текста из text_handlers
        from app.bot.handlers.text_handlers import process_text_with_llm
        
        # Передаем транскрибированный текст в текстовый пайплайн
        await process_text_with_llm(
            user_id=user_id,
            chat_id=chat_id,
            session_id=session_id,
            text=transcribed_text,
            original_message=message,
            processing_message=processing_msg,
            is_voice_transcription=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки голосового сообщения от {user_id}: {e}")
        
        # Состояние будет сброшено автоматически
        
        await message.answer(
            "❌ <b>Ошибка обработки голоса</b>\n\n"
            "Произошла ошибка при обработке голосового сообщения. "
            "Пожалуйста, попробуйте еще раз или отправьте сообщение текстом.",
            parse_mode="HTML"
        )
