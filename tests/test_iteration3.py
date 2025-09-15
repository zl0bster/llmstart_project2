"""
Тестирование итерации 3: Хранение данных и сессии.

Проверяет работу базы данных, состояний системы и сессий.
"""

import os
import sys
import tempfile
from datetime import datetime

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import init_database, reset_database
from app.core.migrations import run_migrations, create_default_admin_user
from app.services.session_manager import SessionManager
from app.services.data_service import DataService
from app.services.state_machine import StateMachine, state_machine
from app.models.schemas import BotState, OrderData, StatusEnum
from app.core.config import settings


def test_database_initialization():
    """Тестирует инициализацию базы данных."""
    print("🧪 Тестирование инициализации базы данных...")
    
    try:
        # Используем временную БД для тестов
        settings.database_url = "sqlite:///test_otk_assistant.db"
        
        # Запускаем миграции
        success = run_migrations(reset=True)
        assert success, "Миграции должны пройти успешно"
        
        # Создаем тестового администратора
        admin_user = create_default_admin_user(telegram_id=12345, name="Test Admin")
        assert admin_user is not None, "Администратор должен быть создан"
        assert admin_user.role == "admin", "Роль должна быть admin"
        
        print("✅ База данных инициализирована успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return False


def test_session_manager():
    """Тестирует работу менеджера сессий."""
    print("🧪 Тестирование менеджера сессий...")
    
    try:
        sm = SessionManager(timeout_minutes=15)
        user_id = 12345
        user_name = "Test User"
        
        # Создаем сессию
        session_id = sm.get_or_create_session(user_id, user_name)
        assert session_id is not None, "Сессия должна быть создана"
        print(f"✅ Сессия создана: {session_id}")
        
        # Проверяем состояние по умолчанию
        current_state = sm.get_state(user_id)
        assert current_state == BotState.idle, "Начальное состояние должно быть idle"
        print(f"✅ Начальное состояние: {current_state}")
        
        # Тестируем переходы состояний
        success = sm.set_state(user_id, BotState.processing)
        assert success, "Переход в processing должен быть успешным"
        
        current_state = sm.get_state(user_id)
        assert current_state == BotState.processing, "Состояние должно быть processing"
        print(f"✅ Переход в состояние: {current_state}")
        
        # Добавляем сообщение
        success = sm.add_message(user_id, "Тестовое сообщение")
        assert success, "Сообщение должно быть добавлено"
        
        messages = sm.get_session_history(user_id)
        assert len(messages) == 1, "Должно быть одно сообщение"
        print(f"✅ Сообщение добавлено: {len(messages)} сообщений")
        
        # Тестируем извлеченные заказы
        test_orders = [
            OrderData(order_id="12345", status=StatusEnum.approved, comment="Тест")
        ]
        success = sm.set_extracted_orders(user_id, test_orders)
        assert success, "Заказы должны быть сохранены"
        
        orders = sm.get_extracted_orders(user_id)
        assert len(orders) == 1, "Должен быть один заказ"
        assert orders[0].order_id == "12345", "ID заказа должен совпадать"
        print(f"✅ Заказы сохранены: {len(orders)} заказов")
        
        # Проверяем информацию о сессии
        session_info = sm.get_session_info(user_id)
        assert session_info is not None, "Информация о сессии должна быть доступна"
        assert session_info['current_state'] == BotState.processing.value, "Состояние должно быть processing"
        print(f"✅ Информация о сессии получена")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования сессий: {e}")
        return False


def test_data_service():
    """Тестирует работу сервиса данных."""
    print("🧪 Тестирование сервиса данных...")
    
    try:
        ds = DataService()
        sm = SessionManager()
        
        user_id = 12345
        user_name = "Test User"
        
        # Создаем сессию и добавляем данные
        session_id = sm.get_or_create_session(user_id, user_name)
        
        test_orders = [
            OrderData(order_id="12345", status=StatusEnum.approved, comment="Тест годно"),
            OrderData(order_id="12346", status=StatusEnum.rework, comment="Доработать")
        ]
        
        # Сохраняем диалог
        success = sm.save_dialogue_to_db(
            user_id=user_id,
            user_message="Заказ 12345 - годно, заказ 12346 - в доработку",
            llm_response='{"orders": [...]}',
            system_prompt="Ты ассистент ОТК",
            status="confirmed"
        )
        assert success, "Диалог должен быть сохранен"
        print("✅ Диалог сохранен в БД")
        
        # Сохраняем проверки
        inspections = ds.save_inspections(user_id, session_id, test_orders)
        assert len(inspections) == 2, "Должно быть сохранено 2 проверки"
        print(f"✅ Проверки сохранены: {len(inspections)} записей")
        
        # Связываем диалоги с проверками
        success = ds.link_dialogues_to_inspections(session_id, inspections)
        assert success, "Диалоги должны быть связаны с проверками"
        print("✅ Диалоги связаны с проверками")
        
        # Обновляем статус диалогов
        success = ds.update_dialogue_status(session_id, "confirmed")
        assert success, "Статус диалогов должен быть обновлен"
        print("✅ Статус диалогов обновлен")
        
        # Получаем статистику пользователя
        stats = ds.get_user_statistics(user_id, days=7)
        assert stats is not None, "Статистика должна быть получена"
        assert stats['total_inspections'] == 2, "Должно быть 2 проверки"
        assert stats['approved'] == 1, "Должна быть 1 одобренная проверка"
        assert stats['rework'] == 1, "Должна быть 1 проверка в доработку"
        print(f"✅ Статистика получена: {stats['total_inspections']} проверок")
        
        # Получаем проверки пользователя
        user_inspections = ds.get_user_inspections(user_id, limit=5)
        assert len(user_inspections) == 2, "Должно быть 2 проверки"
        print(f"✅ Проверки пользователя получены: {len(user_inspections)} записей")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования сервиса данных: {e}")
        return False


def test_state_machine():
    """Тестирует работу автомата состояний."""
    print("🧪 Тестирование автомата состояний...")
    
    try:
        # Тестируем разрешенные переходы
        assert state_machine.can_transition(
            BotState.idle, BotState.processing, 
            {"has_input_data": True}
        ), "Переход idle -> processing должен быть разрешен"
        
        assert state_machine.can_transition(
            BotState.processing, BotState.confirmation,
            {"data_extracted": True}
        ), "Переход processing -> confirmation должен быть разрешен"
        
        assert not state_machine.can_transition(
            BotState.idle, BotState.confirmation,
            {}
        ), "Переход idle -> confirmation должен быть запрещен"
        
        print("✅ Проверка переходов состояний прошла успешно")
        
        # Тестируем получение доступных переходов
        available = state_machine.get_available_transitions(
            BotState.idle, 
            {"has_input_data": True, "requested_reports": True}
        )
        assert BotState.processing in available, "processing должен быть доступен"
        assert BotState.reports_menu in available, "reports_menu должен быть доступен"
        print(f"✅ Доступные переходы: {[s.value for s in available]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования автомата состояний: {e}")
        return False


def cleanup_test_db():
    """Очищает тестовую базу данных."""
    try:
        test_db_path = "test_otk_assistant.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("🧹 Тестовая база данных удалена")
    except Exception as e:
        print(f"⚠️ Ошибка удаления тестовой БД: {e}")


def main():
    """Запускает все тесты итерации 3."""
    print("🚀 Начинаем тестирование итерации 3: Хранение данных и сессии\n")
    
    tests = [
        test_database_initialization,
        test_session_manager,
        test_data_service,
        test_state_machine
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()  # Пустая строка между тестами
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test_func.__name__}: {e}\n")
    
    # Очищаем тестовые данные
    cleanup_test_db()
    
    # Результаты
    print(f"📊 Результаты тестирования:")
    print(f"✅ Прошло тестов: {passed}/{total}")
    print(f"❌ Ошибок: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 Все тесты итерации 3 прошли успешно!")
        print("✅ Система хранения данных и состояний работает корректно")
        return True
    else:
        print(f"\n⚠️ Некоторые тесты не прошли ({total - passed} ошибок)")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
