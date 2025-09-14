"""Обработчики текстовых сообщений."""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.clients.llm_client import OpenRouterLLMClient
from app.clients.lmstudio_client import LMStudioLLMClient
from app.services.session_manager import SessionManager
from app.bot.keyboards import (
    get_validation_keyboard, 
    get_processing_keyboard,
    get_clarification_keyboard,
    get_confirmation_keyboard,
    get_cancellation_confirmation_keyboard
)
from app.prompts.system_prompts import format_orders_for_validation
from app.core.config import settings

# Создаем роутер для текстовых сообщений
router = Router()

# Инициализация компонентов
llm_client = None
session_manager = SessionManager(timeout_minutes=settings.session_timeout_min)


def init_llm_client():
    """Инициализация LLM клиента."""
    global llm_client
    if llm_client is None:
        if settings.llm_provider == "lmstudio":
            llm_client = LMStudioLLMClient(
                base_url=settings.lmstudio_base_url,
                model=settings.text_model
            )
            logging.info(f"LM Studio клиент инициализирован с моделью {settings.text_model}")
        elif settings.llm_provider == "openrouter" and settings.openrouter_api_key:
            llm_client = OpenRouterLLMClient(
                api_key=settings.openrouter_api_key,
                model=settings.text_model
            )
            logging.info(f"OpenRouter клиент инициализирован с моделью {settings.text_model}")
        else:
            logging.error(f"Не удалось инициализировать LLM клиент. Провайдер: {settings.llm_provider}")


@router.message(F.text)
async def handle_text_message(message: Message) -> None:
    """Обработчик текстовых сообщений."""
    user_id = message.from_user.id
    text = message.text
    
    logging.info(f"Получено текстовое сообщение от пользователя {user_id}: {text[:100]}...")
    
    # Инициализируем LLM клиент если нужно
    init_llm_client()
    
    if llm_client is None:
        await message.answer(
            "❌ LLM сервис недоступен. Проверьте настройки API ключей."
        )
        return
    
    # Получаем или создаем сессию
    session_id = session_manager.get_or_create_session(user_id)
    
    # Добавляем сообщение в историю сессии
    session_manager.add_message(user_id, text)
    
    # Отправляем сообщение о начале обработки
    processing_msg = await message.answer(
        "🔄 Идёт обработка...",
        reply_markup=get_processing_keyboard()
    )
    
    try:
        # Получаем историю сессии
        session_history = session_manager.get_session_history(user_id)
        
        # Обрабатываем текст через LLM
        llm_response = llm_client.process_text(text, session_history)
        
        if llm_response.requires_correction:
            # Требуется уточнение
            await processing_msg.edit_text(
                f"❓ {llm_response.clarification_question}",
                reply_markup=get_clarification_keyboard()
            )
        else:
            # Данные извлечены успешно
            if llm_response.orders:
                # Сохраняем извлеченные заказы в сессии
                session_manager.set_extracted_orders(user_id, llm_response.orders)
                
                # Форматируем данные для подтверждения
                validation_text = format_orders_for_validation(llm_response.orders)
                
                await processing_msg.edit_text(
                    validation_text,
                    reply_markup=get_confirmation_keyboard()
                )
            else:
                await processing_msg.edit_text(
                    "❌ Не удалось извлечь данные о заказах из текста. "
                    "Пожалуйста, опишите отчет еще раз."
                )
    
    except Exception as e:
        logging.error(f"Ошибка при обработке текста: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка при обработке. Попробуйте еще раз."
        )


@router.callback_query(F.data == "confirm_data")
async def handle_confirm_data(callback: CallbackQuery) -> None:
    """Обработчик подтверждения данных."""
    user_id = callback.from_user.id
    
    # Получаем извлеченные заказы из сессии
    orders = session_manager.get_extracted_orders(user_id)
    
    if orders:
        # TODO: В итерации 3 здесь будет сохранение в БД
        orders_text = "\n".join([
            f"• Заказ #{order.order_id}: {order.status} - {order.comment or 'без комментария'}"
            for order in orders
        ])
        
        await callback.message.edit_text(
            f"✅ <b>Данные подтверждены и сохранены:</b>\n\n{orders_text}\n\n"
            f"📝 Отправьте следующий отчет или используйте /reports для просмотра отчетов."
        )
        
        # Очищаем сессию после успешного сохранения
        session_manager.clear_session(user_id)
        
        logging.info(f"Пользователь {user_id} подтвердил {len(orders)} заказов")
    else:
        await callback.message.edit_text(
            "❌ Нет данных для подтверждения. Попробуйте отправить отчет еще раз."
        )
    
    await callback.answer()


@router.callback_query(F.data == "correct_data")
async def handle_correct_data(callback: CallbackQuery) -> None:
    """Обработчик запроса на исправление данных."""
    await callback.message.edit_text(
        "✏️ <b>Исправление данных</b>\n\n"
        "Пожалуйста, опишите, что именно нужно исправить в извлеченных данных. "
        "Например: \"Измени статус заказа 10409 на 'годно'\" или \"Добавь комментарий к заказу 10494\"."
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_data")
async def handle_cancel_data(callback: CallbackQuery) -> None:
    """Обработчик отмены данных."""
    await callback.message.edit_text(
        "⚠️ <b>Подтверждение отмены</b>\n\n"
        "Вы уверены? Все несохраненные данные будут утеряны.",
        reply_markup=get_cancellation_confirmation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_cancel")
async def handle_confirm_cancel(callback: CallbackQuery) -> None:
    """Обработчик подтверждения отмены."""
    user_id = callback.from_user.id
    
    # Очищаем сессию
    session_manager.clear_session(user_id)
    
    await callback.message.edit_text(
        "❌ <b>Операция отменена</b>\n\n"
        "Все несохраненные данные удалены. Отправьте новый отчет когда будете готовы."
    )
    
    logging.info(f"Пользователь {user_id} отменил операцию")
    await callback.answer()


@router.callback_query(F.data == "stop_processing")
async def handle_stop_processing(callback: CallbackQuery) -> None:
    """Обработчик остановки обработки."""
    user_id = callback.from_user.id
    
    # Очищаем сессию
    session_manager.clear_session(user_id)
    
    await callback.message.edit_text(
        "⏹️ <b>Обработка остановлена</b>\n\n"
        "Отправьте новый отчет когда будете готовы."
    )
    
    logging.info(f"Пользователь {user_id} остановил обработку")
    await callback.answer()
