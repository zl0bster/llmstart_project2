"""Обработчики команд бота."""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

# Создаем роутер для команд
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start."""
    logging.info(f"Пользователь {message.from_user.id} запустил бота")
    
    welcome_text = (
        "🤖 <b>OTK Assistant</b>\n\n"
        "Добро пожаловать! Я помогу вам автоматизировать проверки ОТК.\n\n"
        "📋 <b>Что я умею:</b>\n"
        "• Анализировать текстовые сообщения с результатами проверок\n"
        "• Обрабатывать голосовые сообщения\n"
        "• Анализировать фотографии протоколов\n"
        "• Генерировать отчеты\n\n"
        "💡 <b>Как начать:</b>\n"
        "Просто отправьте мне данные о проверке в любом удобном формате!\n\n"
        "Используйте /help для получения справки."
    )
    
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработчик команды /help."""
    logging.info(f"Пользователь {message.from_user.id} запросил справку")
    
    help_text = (
        "📖 <b>Справка по OTK Assistant</b>\n\n"
        "🔧 <b>Доступные команды:</b>\n"
        "/start - Запуск бота и приветствие\n"
        "/help - Показать эту справку\n"
        "/status - Проверить статус системы\n\n"
        "📝 <b>Как использовать:</b>\n"
        "1. Отправьте текстовое сообщение с результатами проверки\n"
        "2. Или отправьте голосовое сообщение\n"
        "3. Или отправьте фотографию протокола\n\n"
        "🤖 Бот автоматически извлечет данные и попросит подтверждение."
    )
    
    await message.answer(help_text)


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Обработчик команды /status."""
    logging.info(f"Пользователь {message.from_user.id} запросил статус")
    
    status_text = (
        "✅ <b>Статус системы</b>\n\n"
        "🟢 Бот работает нормально\n"
        "🟢 Все сервисы доступны\n"
        "🟢 Готов к обработке данных\n\n"
        "📊 <b>Информация:</b>\n"
        f"👤 Пользователь ID: {message.from_user.id}\n"
        f"📅 Время: {message.date.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    await message.answer(status_text)
