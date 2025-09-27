#!/usr/bin/env python3
"""
Простой тест для проверки запуска приложения.
Используется для диагностики проблем в Railway.
"""

import os
import sys
import asyncio
import logging

# Настройка базового логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_startup():
    """Тест запуска приложения."""
    try:
        print("🚀 Тест запуска OTK Assistant...")
        
        # Проверка переменных окружения
        print(f"📍 PORT: {os.environ.get('PORT', '8000')}")
        print(f"📍 BOT_TOKEN: {'✅ Настроен' if os.environ.get('BOT_TOKEN') else '❌ Не настроен'}")
        print(f"📍 DATABASE_URL: {os.environ.get('DATABASE_URL', 'sqlite:///data/otk_assistant.db')}")
        
        # Тест импорта модулей
        print("📦 Тест импорта модулей...")
        
        try:
            import app.core.config
            print("✅ app.core.config импортирован")
        except ImportError as e:
            print(f"❌ Ошибка импорта app.core.config: {e}")
            return False
            
        try:
            from app.health import create_health_app
            print("✅ app.health импортирован")
        except ImportError as e:
            print(f"❌ Ошибка импорта app.health: {e}")
            return False
            
        # Тест создания health app
        print("🏥 Тест создания health app...")
        health_app = create_health_app()
        print("✅ Health app создан")
        
        # Тест запуска простого HTTP сервера
        print("🌐 Тест запуска HTTP сервера...")
        from aiohttp import web, web_runner
        
        port = int(os.environ.get("PORT", 8000))
        runner = web.AppRunner(health_app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        print(f"✅ HTTP сервер запущен на порту {port}")
        print("✅ Все тесты пройдены успешно!")
        
        # Останавливаем сервер
        await runner.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_startup())
    sys.exit(0 if success else 1)
