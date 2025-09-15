"""
Простая система миграций для базы данных.

Обеспечивает создание и обновление структуры базы данных.
"""

import logging
from typing import Optional

from app.core.database import get_db_session, init_database, reset_database
from app.models.database import User, Inspection, Dialogue

logger = logging.getLogger(__name__)


def run_migrations(reset: bool = False) -> bool:
    """
    Запускает миграции базы данных.
    
    Args:
        reset: Если True, сбрасывает БД и создает заново
        
    Returns:
        bool: True если миграции прошли успешно
    """
    try:
        if reset:
            logger.info("Сброс базы данных...")
            reset_database()
        else:
            logger.info("Инициализация базы данных...")
            init_database()
        
        # Проверяем, что все таблицы созданы
        with get_db_session() as db:
            # Проверяем наличие таблиц через попытку выборки
            try:
                db.query(User).limit(1).all()
                db.query(Inspection).limit(1).all()
                db.query(Dialogue).limit(1).all()
                logger.info("✅ Все таблицы созданы успешно")
            except Exception as e:
                logger.error(f"❌ Ошибка проверки таблиц: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка выполнения миграций: {e}")
        return False


def create_default_admin_user(telegram_id: int, name: str = "Admin") -> Optional[User]:
    """
    Создает администратора по умолчанию.
    
    Args:
        telegram_id: Telegram ID администратора
        name: Имя администратора
        
    Returns:
        Optional[User]: Созданный пользователь или None при ошибке
    """
    try:
        with get_db_session() as db:
            # Проверяем, не существует ли уже
            existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if existing_user:
                logger.info(f"Пользователь с telegram_id {telegram_id} уже существует")
                return existing_user
            
            # Создаем нового администратора
            admin_user = User(
                telegram_id=telegram_id,
                name=name,
                role="admin"
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            logger.info(f"✅ Создан администратор: {name} (ID: {telegram_id})")
            return admin_user
            
    except Exception as e:
        logger.error(f"❌ Ошибка создания администратора: {e}")
        return None


if __name__ == "__main__":
    # Запуск миграций из командной строки
    import sys
    
    reset_flag = "--reset" in sys.argv
    success = run_migrations(reset=reset_flag)
    
    if success:
        print("✅ Миграции выполнены успешно")
    else:
        print("❌ Ошибка выполнения миграций")
        sys.exit(1)
