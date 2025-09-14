"""Обработчики фотографий."""

import logging
from aiogram import Router, F
from aiogram.types import Message

# Создаем роутер для фотографий
router = Router()


@router.message(F.photo)
async def handle_photo_message(message: Message) -> None:
    """Обработчик фотографий."""
    user_id = message.from_user.id
    
    logging.info(f"Получена фотография от пользователя {user_id}")
    
    response = (
        "📸 <b>Получена фотография</b>\n\n"
        "✅ Фото принято к обработке. В следующих итерациях здесь будет "
        "анализ изображения через Vision API для извлечения данных из протоколов ОТК."
    )
    
    await message.answer(response)
    
    logging.info(f"Отправлен ответ пользователю {user_id}")
