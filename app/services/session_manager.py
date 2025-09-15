"""
Менеджер сессий пользователей.

Управляет сессиями диалогов с пользователями, включая историю сообщений и таймауты.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models.schemas import SessionData, OrderData, BotState
from app.models.database import User, Dialogue
from app.core.database import get_db_session

logger = logging.getLogger(__name__)


class SessionManager:
    """Менеджер сессий пользователей."""
    
    def __init__(self, timeout_minutes: int = 15):
        """
        Инициализация менеджера сессий.
        
        Args:
            timeout_minutes: Таймаут неактивной сессии в минутах
        """
        self.sessions: Dict[int, SessionData] = {}
        self.timeout = timedelta(minutes=timeout_minutes)
        logger.info(f"SessionManager инициализирован с таймаутом {timeout_minutes} минут")
    
    def get_or_create_user(self, telegram_id: int, name: str = None) -> Optional[User]:
        """
        Получает или создает пользователя в базе данных.
        
        Args:
            telegram_id: Telegram ID пользователя
            name: Имя пользователя (опционально)
            
        Returns:
            Optional[User]: Пользователь или None при ошибке
        """
        try:
            with get_db_session() as db:
                # Ищем существующего пользователя
                user = db.query(User).filter(User.telegram_id == telegram_id).first()
                
                if not user:
                    # Создаем нового пользователя
                    user = User(
                        telegram_id=telegram_id,
                        name=name or f"User_{telegram_id}",
                        role="inspector"  # По умолчанию - инспектор
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                    logger.info(f"Создан новый пользователь: {user.name} (telegram_id: {telegram_id})")
                elif name and user.name != name:
                    # Обновляем имя если передано
                    user.name = name
                    db.commit()
                    logger.debug(f"Обновлено имя пользователя {telegram_id}: {name}")
                
                return user
        except Exception as e:
            logger.error(f"Ошибка получения/создания пользователя {telegram_id}: {e}")
            return None
    
    def get_or_create_session(self, user_id: int, name: str = None) -> str:
        """
        Получает или создает сессию для пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            name: Имя пользователя (для создания в БД)
            
        Returns:
            str: ID сессии
        """
        current_time = datetime.now().isoformat()
        
        # Проверяем существующую сессию
        if user_id in self.sessions:
            session = self.sessions[user_id]
            
            # Проверяем таймаут
            last_activity = datetime.fromisoformat(session.last_activity)
            if datetime.now() - last_activity < self.timeout:
                # Обновляем время последней активности
                session.last_activity = current_time
                logger.debug(f"Обновлена активность сессии {session.session_id} для пользователя {user_id}")
                return session.session_id
            else:
                # Сессия истекла, создаем новую
                logger.info(f"Сессия {session.session_id} истекла для пользователя {user_id}")
                del self.sessions[user_id]
        
        # Создаем новую сессию
        session_id = f"s-{uuid.uuid4().hex[:8]}"
        new_session = SessionData(
            session_id=session_id,
            user_id=user_id,
            current_state=BotState.idle,
            previous_state=None,
            messages=[],
            extracted_orders=[],
            pending_data=None,
            created_at=current_time,
            last_activity=current_time
        )
        
        # Убеждаемся, что пользователь есть в БД
        self.get_or_create_user(user_id, name)
        
        self.sessions[user_id] = new_session
        logger.info(f"Создана новая сессия {session_id} для пользователя {user_id}")
        return session_id
    
    def add_message(self, user_id: int, message: str) -> bool:
        """
        Добавляет сообщение в историю сессии.
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            
        Returns:
            bool: True если сообщение добавлено успешно
        """
        if user_id not in self.sessions:
            logger.warning(f"Попытка добавить сообщение в несуществующую сессию для пользователя {user_id}")
            return False
        
        session = self.sessions[user_id]
        session.messages.append(message)
        session.last_activity = datetime.now().isoformat()
        
        logger.debug(f"Добавлено сообщение в сессию {session.session_id}. Всего сообщений: {len(session.messages)}")
        return True
    
    def get_session_history(self, user_id: int) -> List[str]:
        """
        Получает историю сообщений сессии.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[str]: История сообщений
        """
        if user_id not in self.sessions:
            return []
        
        return self.sessions[user_id].messages.copy()
    
    def set_extracted_orders(self, user_id: int, orders: List[OrderData]) -> bool:
        """
        Сохраняет извлеченные заказы в сессии.
        
        Args:
            user_id: ID пользователя
            orders: Список извлеченных заказов
            
        Returns:
            bool: True если заказы сохранены успешно
        """
        if user_id not in self.sessions:
            logger.warning(f"Попытка сохранить заказы в несуществующую сессию для пользователя {user_id}")
            return False
        
        session = self.sessions[user_id]
        session.extracted_orders = orders.copy()
        session.last_activity = datetime.now().isoformat()
        
        logger.debug(f"Сохранено {len(orders)} заказов в сессии {session.session_id}")
        return True
    
    def get_extracted_orders(self, user_id: int) -> List[OrderData]:
        """
        Получает извлеченные заказы из сессии.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[OrderData]: Список извлеченных заказов
        """
        if user_id not in self.sessions:
            return []
        
        return self.sessions[user_id].extracted_orders.copy()
    
    def clear_session(self, user_id: int) -> bool:
        """
        Очищает сессию пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если сессия очищена успешно
        """
        if user_id in self.sessions:
            session_id = self.sessions[user_id].session_id
            del self.sessions[user_id]
            logger.info(f"Сессия {session_id} очищена для пользователя {user_id}")
            return True
        
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Очищает истекшие сессии.
        
        Returns:
            int: Количество очищенных сессий
        """
        current_time = datetime.now()
        expired_users = []
        
        for user_id, session in self.sessions.items():
            last_activity = datetime.fromisoformat(session.last_activity)
            if current_time - last_activity >= self.timeout:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            session_id = self.sessions[user_id].session_id
            del self.sessions[user_id]
            logger.info(f"Очищена истекшая сессия {session_id} для пользователя {user_id}")
        
        if expired_users:
            logger.info(f"Очищено {len(expired_users)} истекших сессий")
        
        return len(expired_users)
    
    def get_session_info(self, user_id: int) -> Optional[Dict]:
        """
        Получает информацию о сессии пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[Dict]: Информация о сессии или None
        """
        if user_id not in self.sessions:
            return None
        
        session = self.sessions[user_id]
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "current_state": session.current_state.value,
            "previous_state": session.previous_state.value if session.previous_state else None,
            "messages_count": len(session.messages),
            "orders_count": len(session.extracted_orders),
            "has_pending_data": session.pending_data is not None,
            "created_at": session.created_at,
            "last_activity": session.last_activity
        }
    
    def get_active_sessions_count(self) -> int:
        """
        Получает количество активных сессий.
        
        Returns:
            int: Количество активных сессий
        """
        return len(self.sessions)
    
    def set_state(self, user_id: int, new_state: BotState) -> bool:
        """
        Устанавливает состояние бота для пользователя.
        
        Args:
            user_id: ID пользователя
            new_state: Новое состояние
            
        Returns:
            bool: True если состояние установлено успешно
        """
        if user_id not in self.sessions:
            logger.warning(f"Попытка установить состояние для несуществующей сессии пользователя {user_id}")
            return False
        
        session = self.sessions[user_id]
        session.previous_state = session.current_state
        session.current_state = new_state
        session.last_activity = datetime.now().isoformat()
        
        logger.info(f"Состояние изменено для пользователя {user_id}: {session.previous_state} -> {new_state}")
        return True
    
    def get_state(self, user_id: int) -> Optional[BotState]:
        """
        Получает текущее состояние бота для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[BotState]: Текущее состояние или None
        """
        if user_id not in self.sessions:
            return None
        
        return self.sessions[user_id].current_state
    
    def can_transition_to(self, user_id: int, target_state: BotState) -> bool:
        """
        Проверяет, возможен ли переход в указанное состояние.
        
        Args:
            user_id: ID пользователя
            target_state: Целевое состояние
            
        Returns:
            bool: True если переход возможен
        """
        current_state = self.get_state(user_id)
        if current_state is None:
            return target_state == BotState.idle
        
        # Определяем разрешенные переходы
        allowed_transitions = {
            BotState.idle: [BotState.processing, BotState.reports_menu],
            BotState.processing: [BotState.clarification, BotState.confirmation, BotState.cancellation, BotState.idle],
            BotState.clarification: [BotState.processing, BotState.cancellation],
            BotState.confirmation: [BotState.idle, BotState.cancellation],
            BotState.cancellation: [BotState.idle],  # Возврат к предыдущему состоянию будет обработан отдельно
            BotState.reports_menu: [BotState.report_processing, BotState.idle],
            BotState.report_processing: [BotState.reports_menu, BotState.idle]
        }
        
        return target_state in allowed_transitions.get(current_state, [])
    
    def set_pending_data(self, user_id: int, data: dict) -> bool:
        """
        Сохраняет временные данные в сессии.
        
        Args:
            user_id: ID пользователя
            data: Данные для сохранения
            
        Returns:
            bool: True если данные сохранены успешно
        """
        if user_id not in self.sessions:
            logger.warning(f"Попытка сохранить данные в несуществующую сессию для пользователя {user_id}")
            return False
        
        session = self.sessions[user_id]
        session.pending_data = data
        session.last_activity = datetime.now().isoformat()
        
        logger.debug(f"Сохранены временные данные в сессии {session.session_id}")
        return True
    
    def get_pending_data(self, user_id: int) -> Optional[dict]:
        """
        Получает временные данные из сессии.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[dict]: Временные данные или None
        """
        if user_id not in self.sessions:
            return None
        
        return self.sessions[user_id].pending_data
    
    def save_dialogue_to_db(self, user_id: int, user_message: str, llm_response: str = None, 
                           system_prompt: str = None, status: str = "pending") -> bool:
        """
        Сохраняет диалог в базу данных.
        
        Args:
            user_id: ID пользователя
            user_message: Сообщение пользователя
            llm_response: Ответ LLM (опционально)
            system_prompt: Системный промпт (опционально)
            status: Статус диалога
            
        Returns:
            bool: True если диалог сохранен успешно
        """
        if user_id not in self.sessions:
            logger.warning(f"Попытка сохранить диалог для несуществующей сессии пользователя {user_id}")
            return False
        
        try:
            session = self.sessions[user_id]
            
            with get_db_session() as db:
                # Получаем пользователя из БД
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if not user:
                    logger.error(f"Пользователь {user_id} не найден в БД")
                    return False
                
                # Создаем запись диалога
                dialogue = Dialogue(
                    user_id=user.id,
                    session_id=session.session_id,
                    user_message=user_message,
                    llm_response=llm_response,
                    system_prompt=system_prompt,
                    status=status
                )
                
                db.add(dialogue)
                db.commit()
                
                logger.debug(f"Диалог сохранен в БД для сессии {session.session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка сохранения диалога в БД: {e}")
            return False
