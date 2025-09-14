"""Обработчики текстовых сообщений."""

import logging
from aiogram import Router, F
from aiogram.types import Message

# Создаем роутер для текстовых сообщений
router = Router()


@router.message(F.text)
async def handle_text_message(message: Message) -> None:
    """Обработчик текстовых сообщений."""
    user_id = message.from_user.id
    text = message.text
    
    logging.info(f"Получено текстовое сообщение от пользователя {user_id}: {text[:100]}...")
    
    # Простой эхо-ответ для базовой функциональности
    response = (
        f"📝 <b>Получено сообщение:</b>\n\n"
        f"{text}\n\n"
        f"✅ Сообщение обработано. В следующих итерациях здесь будет "
        f"анализ через LLM для извлечения данных о проверках ОТК."
    )
    
    await message.answer(response)
    
    logging.info(f"Отправлен ответ пользователю {user_id}")
