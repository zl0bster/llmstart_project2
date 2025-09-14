"""
Менеджер сессий пользователей.

Управляет сессиями диалогов с пользователями, включая историю сообщений и таймауты.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models.schemas import SessionData, OrderData

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
    
    def get_or_create_session(self, user_id: int) -> str:
        """
        Получает или создает сессию для пользователя.
        
        Args:
            user_id: ID пользователя Telegram
            
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
            messages=[],
            extracted_orders=[],
            created_at=current_time,
            last_activity=current_time
        )
        
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
            "messages_count": len(session.messages),
            "orders_count": len(session.extracted_orders),
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
