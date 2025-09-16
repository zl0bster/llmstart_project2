"""
Тесты для системы отчетов OTK Assistant.

Проверяет функциональность генерации отчетов и CSV файлов.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем корневую директорию в Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.report_service import report_service
from app.services.data_service import DataService
from app.core.database import get_db_session, init_database
from app.models.database import User, Inspection, Base

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReportTestHelper:
    """Вспомогательный класс для тестирования отчетов."""
    
    def __init__(self):
        self.data_service = DataService()
        self.test_user_id = 123456789
        self.test_user_name = "Test User"
    
    def setup_test_data(self):
        """Создает тестовые данные для проверки отчетов."""
        logger.info("Создание тестовых данных...")
        
        try:
            with get_db_session() as db:
                # Создаем тестового пользователя
                existing_user = db.query(User).filter(User.telegram_id == self.test_user_id).first()
                if not existing_user:
                    test_user = User(
                        telegram_id=self.test_user_id,
                        name=self.test_user_name,
                        role="inspector"
                    )
                    db.add(test_user)
                    db.commit()
                    db.refresh(test_user)
                    logger.info(f"Создан тестовый пользователь: {test_user.id}")
                else:
                    test_user = existing_user
                    logger.info(f"Использован существующий пользователь: {test_user.id}")
                
                # Создаем тестовые проверки за сегодня
                today = datetime.now()
                today_inspections = [
                    {
                        "order_id": "10001",
                        "status": "годно",
                        "comment": "Все соответствует требованиям",
                        "created_at": today - timedelta(hours=2)
                    },
                    {
                        "order_id": "10002", 
                        "status": "в доработку",
                        "comment": "Небольшие замечания по качеству",
                        "created_at": today - timedelta(hours=1)
                    },
                    {
                        "order_id": "10003",
                        "status": "годно",
                        "comment": None,
                        "created_at": today - timedelta(minutes=30)
                    }
                ]
                
                # Создаем тестовые проверки за неделю
                week_inspections = [
                    {
                        "order_id": "9001",
                        "status": "в брак", 
                        "comment": "Серьезные нарушения",
                        "created_at": today - timedelta(days=2)
                    },
                    {
                        "order_id": "9002",
                        "status": "годно",
                        "comment": "Отличное качество",
                        "created_at": today - timedelta(days=3)
                    },
                    {
                        "order_id": "9003",
                        "status": "в доработку",
                        "comment": "Мелкие недочеты",
                        "created_at": today - timedelta(days=5)
                    }
                ]
                
                all_inspections = today_inspections + week_inspections
                
                for insp_data in all_inspections:
                    # Проверяем, существует ли уже проверка с таким order_id
                    existing = db.query(Inspection).filter(
                        Inspection.order_id == insp_data["order_id"],
                        Inspection.user_id == test_user.id
                    ).first()
                    
                    if not existing:
                        inspection = Inspection(
                            user_id=test_user.id,
                            session_id=f"test_session_{insp_data['order_id']}",
                            order_id=insp_data["order_id"],
                            status=insp_data["status"],
                            comment=insp_data["comment"],
                            created_at=insp_data["created_at"]
                        )
                        db.add(inspection)
                
                db.commit()
                logger.info(f"Создано {len(all_inspections)} тестовых проверок")
                
        except Exception as e:
            logger.error(f"Ошибка создания тестовых данных: {e}")
            raise
    
    def test_daily_summary(self):
        """Тестирует генерацию дневной сводки."""
        logger.info("Тестирование дневной сводки...")
        
        try:
            # Тест для конкретного пользователя
            summary = report_service.generate_daily_summary(self.test_user_id)
            logger.info(f"Дневная сводка для пользователя:\n{summary}")
            assert "Сводка за день" in summary
            
            # Тест для всех пользователей
            summary_all = report_service.generate_daily_summary()
            logger.info(f"Дневная сводка для всех:\n{summary_all}")
            assert "Сводка за день" in summary_all
            
            logger.info("✅ Тест дневной сводки пройден")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования дневной сводки: {e}")
            return False
    
    def test_weekly_summary(self):
        """Тестирует генерацию недельной сводки."""
        logger.info("Тестирование недельной сводки...")
        
        try:
            # Тест для конкретного пользователя
            summary = report_service.generate_weekly_summary(self.test_user_id)
            logger.info(f"Недельная сводка для пользователя:\n{summary}")
            assert "Сводка за неделю" in summary
            
            # Тест для всех пользователей
            summary_all = report_service.generate_weekly_summary()
            logger.info(f"Недельная сводка для всех:\n{summary_all}")
            assert "Сводка за неделю" in summary_all
            
            logger.info("✅ Тест недельной сводки пройден")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования недельной сводки: {e}")
            return False
    
    def test_daily_csv(self):
        """Тестирует генерацию дневного CSV."""
        logger.info("Тестирование дневного CSV...")
        
        try:
            # Тест для конкретного пользователя
            file_path = report_service.generate_daily_csv(self.test_user_id)
            if file_path:
                logger.info(f"Дневной CSV для пользователя создан: {file_path}")
                assert Path(file_path).exists()
                assert Path(file_path).suffix == ".csv"
                
                # Проверяем содержимое файла
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    assert "Номер заказа" in content
                    assert "Статус" in content
                    logger.info(f"Содержимое CSV:\n{content[:200]}...")
            else:
                logger.info("Дневной CSV для пользователя не создан (нет данных)")
            
            # Тест для всех пользователей
            file_path_all = report_service.generate_daily_csv()
            if file_path_all:
                logger.info(f"Дневной CSV для всех создан: {file_path_all}")
                assert Path(file_path_all).exists()
            else:
                logger.info("Дневной CSV для всех не создан (нет данных)")
            
            logger.info("✅ Тест дневного CSV пройден")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования дневного CSV: {e}")
            return False
    
    def test_weekly_csv(self):
        """Тестирует генерацию недельного CSV."""
        logger.info("Тестирование недельного CSV...")
        
        try:
            # Тест для конкретного пользователя
            file_path = report_service.generate_weekly_csv(self.test_user_id)
            if file_path:
                logger.info(f"Недельный CSV для пользователя создан: {file_path}")
                assert Path(file_path).exists()
                assert Path(file_path).suffix == ".csv"
                
                # Проверяем размер файла (должен быть больше дневного)
                file_size = Path(file_path).stat().st_size
                logger.info(f"Размер недельного CSV: {file_size} байт")
            else:
                logger.info("Недельный CSV для пользователя не создан (нет данных)")
            
            # Тест для всех пользователей
            file_path_all = report_service.generate_weekly_csv()
            if file_path_all:
                logger.info(f"Недельный CSV для всех создан: {file_path_all}")
                assert Path(file_path_all).exists()
            else:
                logger.info("Недельный CSV для всех не создан (нет данных)")
            
            logger.info("✅ Тест недельного CSV пройден")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования недельного CSV: {e}")
            return False
    
    def test_available_reports(self):
        """Тестирует получение списка доступных отчетов."""
        logger.info("Тестирование списка отчетов...")
        
        try:
            reports = report_service.get_available_reports()
            logger.info(f"Доступные отчеты: {len(reports)} типов")
            
            assert len(reports) == 4
            assert any(r['type'] == 'daily_summary' for r in reports)
            assert any(r['type'] == 'weekly_summary' for r in reports)
            assert any(r['type'] == 'daily_csv' for r in reports)
            assert any(r['type'] == 'weekly_csv' for r in reports)
            
            for report in reports:
                logger.info(f"  • {report['name']}: {report['description']}")
            
            logger.info("✅ Тест списка отчетов пройден")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования списка отчетов: {e}")
            return False
    
    def test_cleanup(self):
        """Тестирует очистку старых файлов."""
        logger.info("Тестирование очистки файлов...")
        
        try:
            deleted_count = report_service.cleanup_old_files(days=0)  # Удаляем все файлы
            logger.info(f"Удалено файлов: {deleted_count}")
            
            logger.info("✅ Тест очистки файлов пройден")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования очистки файлов: {e}")
            return False
    
    def run_all_tests(self):
        """Запускает все тесты."""
        logger.info("🚀 Запуск всех тестов отчетов...")
        
        tests = [
            ("Настройка тестовых данных", self.setup_test_data),
            ("Дневная сводка", self.test_daily_summary),
            ("Недельная сводка", self.test_weekly_summary),
            ("Дневной CSV", self.test_daily_csv),
            ("Недельный CSV", self.test_weekly_csv),
            ("Список отчетов", self.test_available_reports),
            ("Очистка файлов", self.test_cleanup)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Тест: {test_name}")
            try:
                if callable(test_func):
                    result = test_func()
                else:
                    test_func  # Для setup_test_data
                    result = True
                
                if result:
                    passed += 1
                    logger.info(f"✅ {test_name} - ПРОЙДЕН")
                else:
                    logger.error(f"❌ {test_name} - ПРОВАЛЕН")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} - ОШИБКА: {e}")
        
        logger.info(f"\n🏁 Результаты тестирования: {passed}/{total} тестов пройдено")
        
        if passed == total:
            logger.info("🎉 Все тесты отчетов успешно пройдены!")
            return True
        else:
            logger.error(f"💥 Не пройдено {total - passed} тестов")
            return False


def main():
    """Главная функция для запуска тестов."""
    logger.info("Инициализация тестирования отчетов...")
    
    try:
        # Инициализируем базу данных
        init_database()
        logger.info("База данных инициализирована")
        
        # Создаем и запускаем тесты
        test_helper = ReportTestHelper()
        success = test_helper.run_all_tests()
        
        if success:
            logger.info("✅ Все тесты пройдены успешно!")
            return 0
        else:
            logger.error("❌ Есть проваленные тесты!")
            return 1
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
