"""
Pydantic модели для структурирования данных LLM.

Схемы данных для извлечения информации о проверках ОТК из текстовых сообщений.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class StatusEnum(str, Enum):
    """Статусы проверки изделий."""
    approved = "годно"
    rework = "в доработку"
    reject = "в брак"


class OrderData(BaseModel):
    """Данные о заказе и его проверке."""
    order_id: str = Field(
        description="Номер заказа, строка из 4-5 цифр, извлеченная из текста"
    )
    status: Optional[StatusEnum] = Field(
        description="Статус проверки изделия"
    )
    comment: Optional[str] = Field(
        description="Комментарий контролера к статусу"
    )


class LLMResponse(BaseModel):
    """Ответ LLM с извлеченными данными о проверках."""
    orders: List[OrderData] = Field(
        description="Список распознанных заказов и их статусов"
    )
    requires_correction: bool = Field(
        description="Флаг, что данные неполные и требуется уточнение у пользователя"
    )
    clarification_question: Optional[str] = Field(
        description="Сформулированный вопрос пользователю для уточнения, если requires_correction=True"
    )


class SessionData(BaseModel):
    """Данные сессии пользователя."""
    session_id: str
    user_id: int
    messages: List[str] = Field(default_factory=list)
    extracted_orders: List[OrderData] = Field(default_factory=list)
    created_at: str
    last_activity: str
