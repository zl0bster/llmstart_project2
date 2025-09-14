"""
Клавиатуры для Telegram бота.

Inline и Reply клавиатуры для взаимодействия с пользователями.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_validation_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для подтверждения извлеченных данных.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками подтверждения
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Согласен", callback_data="confirm_data"),
            InlineKeyboardButton(text="✏️ Исправить", callback_data="correct_data")
        ],
        [
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_data")
        ]
    ])
    return keyboard


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
