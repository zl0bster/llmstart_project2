"""
Pydantic модели для структурирования данных LLM.

Схемы данных для извлечения информации о проверках ОТК из текстовых сообщений.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class BotState(str, Enum):
    """Состояния системы согласно vision.md и scen1_user_flow.md."""
    idle = "idle"                           # Ожидание ввода
    processing = "processing"               # Обработка данных
    clarification = "clarification"         # Уточнение данных
    confirmation = "confirmation"           # Подтверждение данных
    cancellation = "cancellation"           # Отмена действия
    reports_menu = "reports_menu"           # Меню отчетов
    report_processing = "report_processing" # Формирование отчета


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
        default=None,
        description="Статус проверки изделия"
    )
    comment: Optional[str] = Field(
        default=None,
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
    current_state: BotState = Field(default=BotState.idle)
    previous_state: Optional[BotState] = Field(default=None)
    messages: List[str] = Field(default_factory=list)
    extracted_orders: List[OrderData] = Field(default_factory=list)
    pending_data: Optional[dict] = Field(default=None)  # Временные данные для обработки
    created_at: str
    last_activity: str
