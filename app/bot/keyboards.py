"""
Клавиатуры для Telegram бота.

Inline и Reply клавиатуры для взаимодействия с пользователями.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import Dict, Optional

from app.models.schemas import BotState


# Устаревшая функция - используйте get_confirmation_keyboard()
def get_validation_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для подтверждения извлеченных данных.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками подтверждения
    """
    return get_confirmation_keyboard()


def get_cancellation_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для подтверждения отмены.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения отмены
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтверждаю отмену", callback_data="confirm_cancel")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_validation")
        ]
    ])
    return keyboard


def get_reports_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для меню отчетов.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с типами отчетов
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Сводка за сегодня", callback_data="report_summary_today"),
            InlineKeyboardButton(text="📈 Сводка за неделю", callback_data="report_summary_week")
        ],
        [
            InlineKeyboardButton(text="📋 Данные за сегодня", callback_data="report_data_today"),
            InlineKeyboardButton(text="📄 Данные за неделю", callback_data="report_data_week")
        ],
        [
            InlineKeyboardButton(text="🚪 Выход", callback_data="exit_reports")
        ]
    ])
    return keyboard


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает основную клавиатуру бота.
    
    Returns:
        ReplyKeyboardMarkup: Основная клавиатура
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 ОТЧЕТЫ")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_processing_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для состояния обработки.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой отмены
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏹️ СТОП / ОТМЕНА", callback_data="stop_processing")
        ]
    ])
    return keyboard


def get_clarification_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для состояния уточнения.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой отмены
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏹️ СТОП / ОТМЕНА", callback_data="stop_processing")
        ]
    ])
    return keyboard


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для состояния подтверждения.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками подтверждения
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ ПОДТВЕРЖДАЮ", callback_data="confirm_data"),
            InlineKeyboardButton(text="✏️ ИСПРАВИТЬ", callback_data="correct_data")
        ],
        [
            InlineKeyboardButton(text="⏹️ СТОП / ОТМЕНА", callback_data="stop_processing")
        ]
    ])
    return keyboard


def get_cancellation_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для подтверждения отмены.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура подтверждения отмены
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ ПОДТВЕРЖДАЮ ОТМЕНУ", callback_data="confirm_cancel")
        ]
    ])
    return keyboard


def get_keyboard_for_state(state: BotState) -> Optional[InlineKeyboardMarkup]:
    """
    Получает клавиатуру для указанного состояния.
    
    Args:
        state: Состояние системы
        
    Returns:
        Optional[InlineKeyboardMarkup]: Клавиатура для состояния или None
    """
    keyboards = {
        BotState.processing: get_processing_keyboard(),
        BotState.clarification: get_clarification_keyboard(),
        BotState.confirmation: get_confirmation_keyboard(),
        BotState.cancellation: get_cancellation_confirmation_keyboard(),
        BotState.reports_menu: get_reports_keyboard()
    }
    
    return keyboards.get(state)


def get_state_message(state: BotState, context: Dict = None) -> str:
    """
    Получает сообщение для указанного состояния согласно scen1_user_flow.md.
    
    Args:
        state: Состояние системы
        context: Дополнительный контекст для формирования сообщения
        
    Returns:
        str: Текст сообщения для состояния
    """
    context = context or {}
    
    messages = {
        BotState.idle: "Отправьте данные проверки: текст, голосовое сообщение или фото.",
        
        BotState.processing: "Идёт обработка...",
        
        BotState.clarification: context.get(
            'clarification_question', 
            "Пожалуйста, уточните данные. Отправьте дополнительную информацию."
        ),
        
        BotState.confirmation: _format_confirmation_message(context),
        
        BotState.cancellation: "Вы уверены? Все несохраненные данные будут утеряны.",
        
        BotState.reports_menu: "Выберите тип отчета:",
        
        BotState.report_processing: "Формирую отчет... Это займет несколько секунд."
    }
    
    return messages.get(state, f"Неизвестное состояние: {state}")


def _format_confirmation_message(context: Dict) -> str:
    """
    Форматирует сообщение подтверждения с данными заказов.
    
    Args:
        context: Контекст с данными заказов
        
    Returns:
        str: Отформатированное сообщение
    """
    orders = context.get('orders', [])
    
    if not orders:
        return "Проверьте данные перед записью. Всё верно?"
    
    message_parts = ["Проверьте данные перед записью:"]
    
    for order in orders:
        order_info = f"• Заказ: {order.order_id}"
        if order.status:
            order_info += f" - {order.status.value}"
        if order.comment:
            order_info += f" ({order.comment})"
        message_parts.append(order_info)
    
    message_parts.append("\nВсё верно?")
    
    return "\n".join(message_parts)


def get_idle_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру для состояния idle.
    
    Returns:
        ReplyKeyboardMarkup: Клавиатура с основными действиями
    """
    return get_main_keyboard()


def remove_keyboard() -> Dict:
    """
    Убирает клавиатуру.
    
    Returns:
        Dict: Параметры для удаления клавиатуры
    """
    return {"reply_markup": None}
