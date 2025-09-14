"""Обработчики голосовых сообщений."""

import logging
from aiogram import Router, F
from aiogram.types import Message

# Создаем роутер для голосовых сообщений
router = Router()


@router.message(F.voice)
async def handle_voice_message(message: Message) -> None:
    """Обработчик голосовых сообщений."""
    user_id = message.from_user.id
    
    logging.info(f"Получено голосовое сообщение от пользователя {user_id}")
    
    response = (
        "🎤 <b>Получено голосовое сообщение</b>\n\n"
        "✅ Аудио принято к обработке. В следующих итерациях здесь будет "
        "транскрипция через Whisper API и анализ текста для извлечения данных о проверках ОТК."
    )
    
    await message.answer(response)
    
    logging.info(f"Отправлен ответ пользователю {user_id}")
