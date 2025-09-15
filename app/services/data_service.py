"""
Сервис для работы с данными проверок ОТК.

Содержит бизнес-логику для сохранения, получения и управления данными проверок.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.database import User, Inspection, Dialogue
from app.models.schemas import OrderData, BotState
from app.core.database import get_db_session

logger = logging.getLogger(__name__)


class DataService:
    """Сервис для работы с данными проверок."""
    
    def save_inspections(self, user_id: int, session_id: str, orders: List[OrderData]) -> List[Inspection]:
        """
        Сохраняет подтвержденные проверки в базу данных.
        
        Args:
            user_id: Telegram ID пользователя
            session_id: ID сессии диалога
            orders: Список данных о заказах
            
        Returns:
            List[Inspection]: Список созданных записей проверок
        """
        saved_inspections = []
        
        try:
            with get_db_session() as db:
                # Получаем пользователя из БД
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if not user:
                    logger.error(f"Пользователь {user_id} не найден в БД")
                    return []
                
                # Создаем записи проверок
                for order in orders:
                    if not order.status:
                        logger.warning(f"Пропускаем заказ {order.order_id} без статуса")
                        continue
                    
                    inspection = Inspection(
                        user_id=user.id,
                        session_id=session_id,
                        order_id=order.order_id,
                        status=order.status.value,
                        comment=order.comment
                    )
                    
                    db.add(inspection)
                    saved_inspections.append(inspection)
                
                # Сохраняем все изменения
                db.commit()
                
                # Обновляем объекты после commit
                for inspection in saved_inspections:
                    db.refresh(inspection)
                
                logger.info(f"Сохранено {len(saved_inspections)} проверок для пользователя {user_id} в сессии {session_id}")
                
        except Exception as e:
            logger.error(f"Ошибка сохранения проверок: {e}")
            return []
        
        return saved_inspections
    
    def get_user_inspections(self, user_id: int, limit: int = 10) -> List[Inspection]:
        """
        Получает последние проверки пользователя.
        
        Args:
            user_id: Telegram ID пользователя
            limit: Максимальное количество записей
            
        Returns:
            List[Inspection]: Список проверок
        """
        try:
            with get_db_session() as db:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if not user:
                    return []
                
                inspections = (
                    db.query(Inspection)
                    .filter(Inspection.user_id == user.id)
                    .order_by(Inspection.created_at.desc())
                    .limit(limit)
                    .all()
                )
                
                return inspections
                
        except Exception as e:
            logger.error(f"Ошибка получения проверок пользователя {user_id}: {e}")
            return []
    
    def get_inspections_by_session(self, session_id: str) -> List[Inspection]:
        """
        Получает все проверки по ID сессии.
        
        Args:
            session_id: ID сессии диалога
            
        Returns:
            List[Inspection]: Список проверок
        """
        try:
            with get_db_session() as db:
                inspections = (
                    db.query(Inspection)
                    .filter(Inspection.session_id == session_id)
                    .order_by(Inspection.created_at.desc())
                    .all()
                )
                
                return inspections
                
        except Exception as e:
            logger.error(f"Ошибка получения проверок для сессии {session_id}: {e}")
            return []
    
    def update_dialogue_status(self, session_id: str, status: str) -> bool:
        """
        Обновляет статус всех диалогов в сессии.
        
        Args:
            session_id: ID сессии диалога
            status: Новый статус ('confirmed', 'corrected', 'cancelled')
            
        Returns:
            bool: True если обновление прошло успешно
        """
        try:
            with get_db_session() as db:
                updated_count = (
                    db.query(Dialogue)
                    .filter(Dialogue.session_id == session_id)
                    .update({"status": status})
                )
                
                db.commit()
                
                logger.info(f"Обновлен статус {updated_count} диалогов в сессии {session_id} на '{status}'")
                return updated_count > 0
                
        except Exception as e:
            logger.error(f"Ошибка обновления статуса диалогов в сессии {session_id}: {e}")
            return False
    
    def link_dialogues_to_inspections(self, session_id: str, inspections: List[Inspection]) -> bool:
        """
        Связывает диалоги с созданными проверками.
        
        Args:
            session_id: ID сессии диалога
            inspections: Список созданных проверок
            
        Returns:
            bool: True если связывание прошло успешно
        """
        if not inspections:
            return True
        
        try:
            # Берем ID первой проверки для связи (так как все относятся к одной сессии)
            inspection_id = inspections[0].id
            
            with get_db_session() as db:
                updated_count = (
                    db.query(Dialogue)
                    .filter(Dialogue.session_id == session_id)
                    .update({"inspection_id": inspection_id})
                )
                
                db.commit()
                
                logger.debug(f"Связано {updated_count} диалогов с проверкой {inspection_id}")
                return updated_count > 0
                
        except Exception as e:
            logger.error(f"Ошибка связывания диалогов с проверками в сессии {session_id}: {e}")
            return False
    
    def get_user_statistics(self, user_id: int, days: int = 7) -> Dict[str, Any]:
        """
        Получает статистику по пользователю за указанный период.
        
        Args:
            user_id: Telegram ID пользователя
            days: Количество дней для анализа
            
        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        try:
            from datetime import timedelta
            
            with get_db_session() as db:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if not user:
                    return {}
                
                # Дата начала периода
                start_date = datetime.utcnow() - timedelta(days=days)
                
                # Общее количество проверок
                total_inspections = (
                    db.query(Inspection)
                    .filter(
                        Inspection.user_id == user.id,
                        Inspection.created_at >= start_date
                    )
                    .count()
                )
                
                # Статистика по статусам
                approved_count = (
                    db.query(Inspection)
                    .filter(
                        Inspection.user_id == user.id,
                        Inspection.status == "годно",
                        Inspection.created_at >= start_date
                    )
                    .count()
                )
                
                rework_count = (
                    db.query(Inspection)
                    .filter(
                        Inspection.user_id == user.id,
                        Inspection.status == "в доработку",
                        Inspection.created_at >= start_date
                    )
                    .count()
                )
                
                reject_count = (
                    db.query(Inspection)
                    .filter(
                        Inspection.user_id == user.id,
                        Inspection.status == "в брак",
                        Inspection.created_at >= start_date
                    )
                    .count()
                )
                
                return {
                    "user_name": user.name,
                    "user_role": user.role,
                    "period_days": days,
                    "total_inspections": total_inspections,
                    "approved": approved_count,
                    "rework": rework_count,
                    "reject": reject_count,
                    "success_rate": round(approved_count / total_inspections * 100, 1) if total_inspections > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики для пользователя {user_id}: {e}")
            return {}
    
    def delete_session_data(self, session_id: str) -> bool:
        """
        Удаляет все данные сессии (используется при отмене).
        
        Args:
            session_id: ID сессии для удаления
            
        Returns:
            bool: True если удаление прошло успешно
        """
        try:
            with get_db_session() as db:
                # Удаляем диалоги (проверки НЕ удаляем, только если они уже сохранены)
                deleted_dialogues = (
                    db.query(Dialogue)
                    .filter(
                        Dialogue.session_id == session_id,
                        Dialogue.status == "pending"  # Удаляем только незавершенные
                    )
                    .delete()
                )
                
                db.commit()
                
                logger.info(f"Удалено {deleted_dialogues} незавершенных диалогов для сессии {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка удаления данных сессии {session_id}: {e}")
            return False
