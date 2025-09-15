"""
Подключение к базе данных и управление сессиями SQLAlchemy.

Этот модуль настраивает соединение с SQLite базой данных и предоставляет
функции для работы с сессиями базы данных.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.models.database import Base


def get_database_url() -> str:
    """Получить URL базы данных."""
    return settings.database_url


def create_database_engine():
    """Создать движок базы данных."""
    database_url = get_database_url()
    
    # Настройки для SQLite
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {
            "check_same_thread": False,  # Для работы с aiogram
        }
        # Создаем директорию для БД если её нет
        db_path = database_url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        poolclass=StaticPool if database_url.startswith("sqlite") else None,
        echo=False,  # Включить для debug SQL запросов
    )
    
    return engine


# Создаем движок и фабрику сессий
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Создать все таблицы в базе данных."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Получить сессию базы данных.
    
    Yields:
        Session: Сессия SQLAlchemy для работы с БД
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Получить сессию базы данных (синхронный способ).
    
    Внимание: Не забудьте закрыть сессию после использования!
    
    Returns:
        Session: Сессия SQLAlchemy
    """
    return SessionLocal()


def init_database():
    """
    Инициализация базы данных.
    
    Создает все таблицы если они не существуют.
    """
    try:
        create_tables()
        print(f"✅ База данных инициализирована: {get_database_url()}")
        
        # Проверяем подключение
        with get_db_session() as db:
            db.execute("SELECT 1")
            print("✅ Подключение к базе данных работает")
            
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        raise


def reset_database():
    """
    Сбросить базу данных (удалить все таблицы и создать заново).
    
    ВНИМАНИЕ: Все данные будут удалены!
    """
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ База данных сброшена")
    except Exception as e:
        print(f"❌ Ошибка сброса базы данных: {e}")
        raise
