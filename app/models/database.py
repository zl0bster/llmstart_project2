"""
SQLAlchemy модели базы данных для OTK Assistant.

Модели данных:
- User: Пользователи бота
- Inspection: Проверки ОТК (заказы)
- Dialogue: Диалоги с пользователями
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Пользователи бота."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="inspector")  # 'inspector', 'admin', 'manager'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    inspections = relationship("Inspection", back_populates="user")
    dialogues = relationship("Dialogue", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, role={self.role})>"


class Inspection(Base):
    """Проверки ОТК (заказы)."""
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=False, index=True)  # ID сессии диалога
    order_id = Column(String(20), nullable=False, index=True)  # номер заказа (4-5 цифр)
    status = Column(String(50), nullable=False)  # 'годно', 'в доработку', 'в брак'
    comment = Column(Text, nullable=True)  # комментарий контролера к статусу
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="inspections")
    
    def __repr__(self):
        return f"<Inspection(id={self.id}, order_id={self.order_id}, status={self.status})>"


class Dialogue(Base):
    """Диалоги с пользователями."""
    __tablename__ = "dialogues"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=True)  # может быть NULL если диалог не завершен
    session_id = Column(String(255), nullable=False, index=True)  # уникальный ID сессии диалога
    user_message = Column(Text, nullable=False)  # сообщение пользователя
    llm_response = Column(Text, nullable=True)  # ответ LLM
    system_prompt = Column(Text, nullable=True)  # системный промпт, использованный для запроса
    status = Column(String(50), nullable=False, default="pending")  # 'pending', 'confirmed', 'corrected'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="dialogues")
    
    def __repr__(self):
        return f"<Dialogue(id={self.id}, session_id={self.session_id}, status={self.status})>"
