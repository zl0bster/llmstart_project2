"""
Конечный автомат для управления состояниями системы ОТК.

Реализует переходы между состояниями согласно scen1_user_flow.md
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from app.models.schemas import BotState

logger = logging.getLogger(__name__)


class StateTransition:
    """Класс для описания перехода между состояниями."""
    
    def __init__(self, from_state: BotState, to_state: BotState, 
                 condition: Optional[Callable] = None, action: Optional[Callable] = None):
        """
        Инициализация перехода.
        
        Args:
            from_state: Исходное состояние
            to_state: Целевое состояние
            condition: Функция-условие для перехода (опционально)
            action: Функция-действие при переходе (опционально)
        """
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.action = action
    
    def can_transition(self, context: Dict[str, Any] = None) -> bool:
        """
        Проверяет, возможен ли переход.
        
        Args:
            context: Контекст для проверки условий
            
        Returns:
            bool: True если переход возможен
        """
        if self.condition is None:
            return True
        
        try:
            return self.condition(context or {})
        except Exception as e:
            logger.error(f"Ошибка проверки условия перехода {self.from_state} -> {self.to_state}: {e}")
            return False
    
    def execute_action(self, context: Dict[str, Any] = None) -> bool:
        """
        Выполняет действие при переходе.
        
        Args:
            context: Контекст для выполнения действия
            
        Returns:
            bool: True если действие выполнено успешно
        """
        if self.action is None:
            return True
        
        try:
            return self.action(context or {})
        except Exception as e:
            logger.error(f"Ошибка выполнения действия при переходе {self.from_state} -> {self.to_state}: {e}")
            return False


class StateMachine:
    """Конечный автомат для управления состояниями бота."""
    
    def __init__(self):
        """Инициализация автомата состояний."""
        self.transitions: Dict[BotState, List[StateTransition]] = {}
        self._setup_transitions()
    
    def _setup_transitions(self):
        """Настройка разрешенных переходов согласно scen1_user_flow.md."""
        
        # Переходы из состояния idle
        self._add_transition(BotState.idle, BotState.processing, 
                           condition=lambda ctx: ctx.get('has_input_data', False))
        self._add_transition(BotState.idle, BotState.reports_menu,
                           condition=lambda ctx: ctx.get('requested_reports', False))
        
        # Переходы из состояния processing
        self._add_transition(BotState.processing, BotState.clarification,
                           condition=lambda ctx: ctx.get('requires_clarification', False))
        self._add_transition(BotState.processing, BotState.confirmation,
                           condition=lambda ctx: ctx.get('data_extracted', False))
        self._add_transition(BotState.processing, BotState.cancellation,
                           condition=lambda ctx: ctx.get('user_cancelled', False))
        self._add_transition(BotState.processing, BotState.idle,
                           condition=lambda ctx: ctx.get('processing_failed', False))
        
        # Переходы из состояния clarification
        self._add_transition(BotState.clarification, BotState.processing,
                           condition=lambda ctx: ctx.get('clarification_provided', False))
        self._add_transition(BotState.clarification, BotState.cancellation,
                           condition=lambda ctx: ctx.get('user_cancelled', False))
        
        # Переходы из состояния confirmation
        self._add_transition(BotState.confirmation, BotState.idle,
                           condition=lambda ctx: ctx.get('user_confirmed', False),
                           action=self._save_confirmed_data)
        self._add_transition(BotState.confirmation, BotState.idle,
                           condition=lambda ctx: ctx.get('user_rejected', False),
                           action=self._clear_session_data)
        self._add_transition(BotState.confirmation, BotState.cancellation,
                           condition=lambda ctx: ctx.get('user_cancelled', False))
        
        # Переходы из состояния cancellation
        self._add_transition(BotState.cancellation, BotState.idle,
                           condition=lambda ctx: ctx.get('cancellation_confirmed', False),
                           action=self._clear_session_data)
        # Возврат к предыдущему состоянию при отмене cancellation
        for state in [BotState.processing, BotState.clarification, BotState.confirmation]:
            self._add_transition(BotState.cancellation, state,
                               condition=lambda ctx, target=state: ctx.get('return_to_previous', False) and 
                                         ctx.get('previous_state') == target)
        
        # Переходы из состояния reports_menu
        self._add_transition(BotState.reports_menu, BotState.report_processing,
                           condition=lambda ctx: ctx.get('report_selected', False))
        self._add_transition(BotState.reports_menu, BotState.idle,
                           condition=lambda ctx: ctx.get('exit_reports', False))
        
        # Переходы из состояния report_processing
        self._add_transition(BotState.report_processing, BotState.reports_menu,
                           condition=lambda ctx: ctx.get('report_completed', False))
        self._add_transition(BotState.report_processing, BotState.idle,
                           condition=lambda ctx: ctx.get('exit_reports', False))
    
    def _add_transition(self, from_state: BotState, to_state: BotState,
                       condition: Optional[Callable] = None, action: Optional[Callable] = None):
        """
        Добавляет переход в автомат состояний.
        
        Args:
            from_state: Исходное состояние
            to_state: Целевое состояние
            condition: Условие перехода
            action: Действие при переходе
        """
        if from_state not in self.transitions:
            self.transitions[from_state] = []
        
        transition = StateTransition(from_state, to_state, condition, action)
        self.transitions[from_state].append(transition)
    
    def can_transition(self, from_state: BotState, to_state: BotState, 
                      context: Dict[str, Any] = None) -> bool:
        """
        Проверяет, возможен ли переход между состояниями.
        
        Args:
            from_state: Исходное состояние
            to_state: Целевое состояние
            context: Контекст для проверки условий
            
        Returns:
            bool: True если переход возможен
        """
        if from_state not in self.transitions:
            return False
        
        for transition in self.transitions[from_state]:
            if transition.to_state == to_state:
                return transition.can_transition(context)
        
        return False
    
    def get_available_transitions(self, from_state: BotState, 
                                 context: Dict[str, Any] = None) -> List[BotState]:
        """
        Получает список доступных состояний для перехода.
        
        Args:
            from_state: Исходное состояние
            context: Контекст для проверки условий
            
        Returns:
            List[BotState]: Список доступных состояний
        """
        available_states = []
        
        if from_state not in self.transitions:
            return available_states
        
        for transition in self.transitions[from_state]:
            if transition.can_transition(context):
                available_states.append(transition.to_state)
        
        return available_states
    
    def execute_transition(self, from_state: BotState, to_state: BotState,
                          context: Dict[str, Any] = None) -> bool:
        """
        Выполняет переход между состояниями.
        
        Args:
            from_state: Исходное состояние
            to_state: Целевое состояние
            context: Контекст для выполнения действий
            
        Returns:
            bool: True если переход выполнен успешно
        """
        if not self.can_transition(from_state, to_state, context):
            logger.warning(f"Переход {from_state} -> {to_state} невозможен с текущим контекстом")
            return False
        
        # Находим соответствующий переход
        for transition in self.transitions[from_state]:
            if transition.to_state == to_state and transition.can_transition(context):
                success = transition.execute_action(context)
                if success:
                    logger.info(f"Выполнен переход: {from_state} -> {to_state}")
                else:
                    logger.error(f"Ошибка выполнения действия при переходе {from_state} -> {to_state}")
                return success
        
        return False
    
    def _save_confirmed_data(self, context: Dict[str, Any]) -> bool:
        """
        Действие для сохранения подтвержденных данных.
        
        Args:
            context: Контекст с данными для сохранения
            
        Returns:
            bool: True если сохранение прошло успешно
        """
        logger.info("Выполняется сохранение подтвержденных данных")
        
        # Здесь будет вызов DataService для сохранения в БД
        # Пока просто логируем
        data_service = context.get('data_service')
        session_manager = context.get('session_manager')
        user_id = context.get('user_id')
        
        if not all([data_service, session_manager, user_id]):
            logger.error("Недостаточно данных для сохранения")
            return False
        
        try:
            # Получаем данные из сессии
            orders = session_manager.get_extracted_orders(user_id)
            session_info = session_manager.get_session_info(user_id)
            
            if not orders or not session_info:
                logger.error("Нет данных для сохранения")
                return False
            
            # Сохраняем проверки
            inspections = data_service.save_inspections(
                user_id=user_id,
                session_id=session_info['session_id'],
                orders=orders
            )
            
            if inspections:
                # Обновляем статус диалогов
                data_service.update_dialogue_status(session_info['session_id'], 'confirmed')
                data_service.link_dialogues_to_inspections(session_info['session_id'], inspections)
                logger.info(f"Успешно сохранено {len(inspections)} проверок")
                return True
            else:
                logger.error("Не удалось сохранить проверки")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")
            return False
    
    def _clear_session_data(self, context: Dict[str, Any]) -> bool:
        """
        Действие для очистки данных сессии.
        
        Args:
            context: Контекст с данными сессии
            
        Returns:
            bool: True если очистка прошла успешно
        """
        logger.info("Выполняется очистка данных сессии")
        
        session_manager = context.get('session_manager')
        data_service = context.get('data_service')
        user_id = context.get('user_id')
        
        if not all([session_manager, user_id]):
            logger.error("Недостаточно данных для очистки сессии")
            return False
        
        try:
            # Получаем информацию о сессии
            session_info = session_manager.get_session_info(user_id)
            
            if session_info and data_service:
                # Удаляем незавершенные данные из БД
                data_service.delete_session_data(session_info['session_id'])
            
            # Очищаем сессию в памяти
            session_manager.clear_session(user_id)
            
            logger.info(f"Сессия пользователя {user_id} очищена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки сессии: {e}")
            return False
    
    def get_state_description(self, state: BotState) -> str:
        """
        Получает описание состояния для отладки.
        
        Args:
            state: Состояние для описания
            
        Returns:
            str: Описание состояния
        """
        descriptions = {
            BotState.idle: "Ожидание ввода от пользователя",
            BotState.processing: "Обработка введенных данных",
            BotState.clarification: "Запрос уточняющих данных",
            BotState.confirmation: "Подтверждение извлеченных данных",
            BotState.cancellation: "Подтверждение отмены операции",
            BotState.reports_menu: "Меню выбора отчетов",
            BotState.report_processing: "Формирование отчета"
        }
        
        return descriptions.get(state, f"Неизвестное состояние: {state}")


# Глобальный экземпляр автомата состояний
state_machine = StateMachine()
