"""
Централизованный сервис для управления сессиями.

Этот модуль предоставляет единый экземпляр SessionManager для всего приложения.
"""

import logging
from app.services.session_manager import SessionManager
from app.core.config import settings

logger = logging.getLogger(__name__)

# Глобальный экземпляр SessionManager
_session_manager = None


def get_session_manager() -> SessionManager:
    """
    Возвращает глобальный экземпляр SessionManager.
    
    Returns:
        SessionManager: Глобальный экземпляр менеджера сессий
    """
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager(timeout_minutes=settings.session_timeout_min)
        logger.info("Создан глобальный экземпляр SessionManager")
    
    return _session_manager


def reset_session_manager() -> None:
    """
    Сбрасывает глобальный экземпляр SessionManager.
    Используется для тестирования.
    """
    global _session_manager
    _session_manager = None
    logger.info("Глобальный экземпляр SessionManager сброшен")
