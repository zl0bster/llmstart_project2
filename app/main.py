"""Точка входа приложения OTK Assistant."""

import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from app.core.config import settings
from app.core.database import init_database
from app.bot.handlers import command_handlers, text_handlers, voice_handlers, photo_handlers
from app.health import create_health_app


def setup_logging() -> None:
    """Настройка логирования."""
    # Создаем директорию для логов если её нет
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Настройка форматирования
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Настройка уровня логирования
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Настройка консольного вывода
    if settings.log_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(console_handler)
    
    # Настройка файлового вывода
    file_handler = logging.FileHandler(
        log_dir / "app.log", 
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)
    
    # Настройка корневого логгера
    logging.getLogger().setLevel(log_level)
    
    # Логирование конфигурации (без секретов)
    logging.info("OTK Assistant запускается...")
    logging.info(f"Уровень логирования: {settings.log_level}")
    logging.info(f"Директория логов: {settings.log_dir}")
    logging.info(f"Провайдер LLM: {settings.llm_provider}")
    logging.info(f"Модель текста: {settings.text_model}")


async def main() -> None:
    """Основная функция приложения."""
    try:
        # Настройка логирования
        setup_logging()
        
        # Инициализация базы данных
        logging.info("Инициализация базы данных...")
        init_database()
        
        # Инициализация бота
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Инициализация диспетчера
        dp = Dispatcher()
        
        # Регистрация обработчиков
        dp.include_router(command_handlers.router)
        dp.include_router(text_handlers.router)
        dp.include_router(voice_handlers.router)
        dp.include_router(photo_handlers.router)
        
        # Создание health check приложения
        health_app = create_health_app()
        
        # Запуск health check сервера
        health_runner = web.AppRunner(health_app)
        await health_runner.setup()
        health_site = web.TCPSite(health_runner, '0.0.0.0', 8000)
        await health_site.start()
        
        logging.info("Health check сервер запущен на порту 8000")
        logging.info("Бот инициализирован, начинаем polling...")
        
        # Запуск бота
        await dp.start_polling(bot)
        
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
        sys.exit(1)
    finally:
        if 'bot' in locals():
            await bot.session.close()
        if 'health_runner' in locals():
            await health_runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Получен сигнал прерывания, завершаем работу...")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        sys.exit(1)
