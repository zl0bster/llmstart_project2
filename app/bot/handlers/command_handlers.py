"""Обработчики команд бота."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from pathlib import Path

from app.services.session_service import get_session_manager
from app.services.data_service import DataService
from app.services.report_service import report_service
from app.bot.keyboards import get_idle_keyboard, get_reports_keyboard, get_keyboard_for_state, get_state_message
from app.models.schemas import BotState

# Создаем роутер для команд
router = Router()

# Глобальные сервисы (будут инициализированы в main.py)
data_service: DataService = None
session_manager = None


def init_services(ds: DataService):
    """
    Инициализирует сервисы для обработчиков команд.
    
    Args:
        ds: Сервис данных
    """
    global data_service, session_manager
    data_service = ds
    session_manager = get_session_manager()
    logging.info("Сервисы инициализированы для обработчиков команд")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start."""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    logging.info(f"Пользователь {user_id} ({user_name}) запустил бота")
    
    # Создаем пользователя в БД и сессию
    session_manager = get_session_manager()
    # Очищаем текущую сессию и создаем новую
    session_manager.clear_session(user_id)
    session_id = session_manager.get_or_create_session(user_id, user_name)
    logging.info(f"Создана новая сессия {session_id} для пользователя {user_id}")
    
    welcome_text = (
        "🤖 <b>OTK Assistant</b>\n\n"
        "Добро пожаловать! Я помогу вам автоматизировать проверки ОТК.\n\n"
        "📋 <b>Что я умею:</b>\n"
        "• Анализировать текстовые сообщения с результатами проверок\n"
        "• Обрабатывать голосовые сообщения\n"
        "• Анализировать фотографии протоколов\n"
        "• Генерировать отчеты\n\n"
        "💡 <b>Как начать:</b>\n"
        "Просто отправьте мне данные о проверке в любом удобном формате!\n\n"
        "Используйте /help для получения справки."
    )
    
    await message.answer(welcome_text, reply_markup=get_idle_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработчик команды /help."""
    logging.info(f"Пользователь {message.from_user.id} запросил справку")
    
    help_text = (
        "📖 <b>Справка по OTK Assistant</b>\n\n"
        "🔧 <b>Доступные команды:</b>\n"
        "/start - Запуск бота и приветствие\n"
        "/help - Показать эту справку\n"
        "/status - Проверить статус системы\n"
        "/reports - Меню отчетов\n\n"
        "📝 <b>Как использовать:</b>\n"
        "1. Отправьте текстовое сообщение с результатами проверки\n"
        "2. Или отправьте голосовое сообщение\n"
        "3. Или отправьте фотографию протокола\n\n"
        "🤖 Бот автоматически извлечет данные и попросит подтверждение."
    )
    
    await message.answer(help_text)


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    """Обработчик команды /status."""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    logging.info(f"Пользователь {user_id} запросил статус")
    
    status_parts = ["✅ <b>Статус системы</b>\n"]
    
    # Общий статус системы
    status_parts.extend([
        "🟢 Бот работает нормально",
        "🟢 Все сервисы доступны",
        "🟢 Готов к обработке данных\n"
    ])
    
    # Информация о пользователе
    status_parts.extend([
        "📊 <b>Информация о пользователе:</b>",
        f"👤 ID: {user_id}",
        f"📝 Имя: {user_name}",
        f"📅 Время: {message.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
    ])
    
    # Информация о сессии
    session_manager = get_session_manager()
    session_info = session_manager.get_session_info(user_id)
    if session_info:
        current_state = session_manager.get_state(user_id)
        status_parts.extend([
            "🔄 <b>Текущая сессия:</b>",
            f"🆔 ID сессии: {session_info['session_id'][:8]}...",
            f"📊 Состояние: {current_state.value if current_state else 'не определено'}",
            f"💬 Сообщений: {session_info['messages_count']}",
            f"📦 Заказов: {session_info['orders_count']}",
            f"⏰ Последняя активность: {session_info['last_activity'][:19]}\n"
        ])
    else:
        status_parts.append("🔄 <b>Сессия:</b> не активна\n")
    
    # Статистика пользователя
    if data_service:
        stats = data_service.get_user_statistics(user_id, days=7)
        if stats:
            status_parts.extend([
                "📈 <b>Статистика за неделю:</b>",
                f"🔍 Всего проверок: {stats['total_inspections']}",
                f"✅ Годно: {stats['approved']}",
                f"🔧 В доработку: {stats['rework']}",
                f"❌ В брак: {stats['reject']}",
                f"📊 Успешность: {stats['success_rate']}%"
            ])
    
    status_text = "\n".join(status_parts)
    await message.answer(status_text)


@router.message(Command("reports"))
async def cmd_reports(message: Message) -> None:
    """Обработчик команды /reports."""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    logging.info(f"Пользователь {user_id} ({user_name}) запросил меню отчетов")
    
    # Устанавливаем состояние меню отчетов
    if session_manager:
        session_manager.set_state(user_id, BotState.reports_menu)
        logging.info(f"Состояние пользователя {user_id} изменено на reports_menu")
    
    # Показываем меню отчетов
    menu_text = get_state_message(BotState.reports_menu)
    keyboard = get_keyboard_for_state(BotState.reports_menu)
    
    await message.answer(menu_text, reply_markup=keyboard)


@router.message(F.text == "📊 ОТЧЕТЫ")
async def handle_reports_button(message: Message) -> None:
    """Обработчик кнопки отчетов."""
    await cmd_reports(message)


@router.callback_query(F.data.startswith("report_"))
async def handle_report_callbacks(callback: CallbackQuery) -> None:
    """Обработчик callback-запросов отчетов."""
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    
    logging.info(f"Пользователь {user_id} выбрал отчет: {callback.data}")
    
    # Устанавливаем состояние обработки отчета
    if session_manager:
        session_manager.set_state(user_id, BotState.report_processing)
    
    # Отвечаем на callback
    await callback.answer()
    
    # Показываем сообщение о формировании отчета
    processing_text = get_state_message(BotState.report_processing)
    await callback.message.edit_text(processing_text)
    
    try:
        # Обрабатываем разные типы отчетов
        if callback.data == "report_summary_today":
            report_text = report_service.generate_daily_summary(user_id)
            await callback.message.edit_text(report_text, parse_mode="HTML")
            
        elif callback.data == "report_summary_week":
            report_text = report_service.generate_weekly_summary(user_id)
            await callback.message.edit_text(report_text, parse_mode="HTML")
            
        elif callback.data == "report_data_today":
            file_path = report_service.generate_daily_csv(user_id)
            if file_path and Path(file_path).exists():
                # Отправляем CSV файл
                document = FSInputFile(file_path, filename=Path(file_path).name)
                await callback.message.answer_document(
                    document=document,
                    caption="📄 Детальные данные проверок за сегодня"
                )
                await callback.message.edit_text("✅ CSV файл отправлен выше")
            else:
                await callback.message.edit_text(
                    "📄 <b>Данные за сегодня</b>\n\n"
                    "За сегодня проверок не проводилось.\n\n"
                    "Отправьте данные о проверке для формирования отчетов.",
                    parse_mode="HTML"
                )
                
        elif callback.data == "report_data_week":
            file_path = report_service.generate_weekly_csv(user_id)
            if file_path and Path(file_path).exists():
                # Отправляем CSV файл
                document = FSInputFile(file_path, filename=Path(file_path).name)
                await callback.message.answer_document(
                    document=document,
                    caption="📋 Детальные данные проверок за неделю"
                )
                await callback.message.edit_text("✅ CSV файл отправлен выше")
            else:
                await callback.message.edit_text(
                    "📋 <b>Данные за неделю</b>\n\n"
                    "За неделю проверок не проводилось.\n\n"
                    "Отправьте данные о проверке для формирования отчетов.",
                    parse_mode="HTML"
                )
        
        # Возвращаемся в состояние idle после отправки отчета
        if session_manager:
            session_manager.set_state(user_id, BotState.idle)
            
        # Показываем кнопку возврата к отчетам
        return_keyboard = get_reports_keyboard()
        await callback.message.answer(
            "Вернуться к отчетам?", 
            reply_markup=return_keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка генерации отчета {callback.data} для пользователя {user_id}: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при формировании отчета.\n\n"
            "Попробуйте еще раз позже."
        )
        
        # Возвращаемся в состояние idle при ошибке
        if session_manager:
            session_manager.set_state(user_id, BotState.idle)


@router.callback_query(F.data == "exit_reports")
async def handle_exit_reports(callback: CallbackQuery) -> None:
    """Обработчик выхода из меню отчетов."""
    user_id = callback.from_user.id
    
    logging.info(f"Пользователь {user_id} вышел из меню отчетов")
    
    # Возвращаемся в состояние idle
    if session_manager:
        session_manager.set_state(user_id, BotState.idle)
    
    await callback.answer()
    await callback.message.edit_text(
        "Выход из меню отчетов.\n\n"
        "Отправьте данные проверки: текст, голосовое сообщение или фото.",
        reply_markup=None
    )
