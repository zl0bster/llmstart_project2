"""
Сервис для генерации отчетов по проверкам ОТК.

Содержит функциональность для создания различных типов отчетов:
- Сводки (текстовые отчеты с основными показателями)
- CSV файлы (детальные данные для экспорта)
Поддерживает периоды: день, неделя
"""

import csv
import logging
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.models.database import User, Inspection
from app.core.database import get_db_session
from sqlalchemy import and_, func

logger = logging.getLogger(__name__)


class ReportService:
    """Сервис для генерации отчетов."""
    
    def __init__(self):
        """Инициализация сервиса отчетов."""
        self.temp_dir = Path(tempfile.gettempdir()) / "otk_reports"
        self.temp_dir.mkdir(exist_ok=True)
        logger.info("ReportService инициализирован")
    
    def generate_daily_summary(self, user_id: Optional[int] = None) -> str:
        """
        Генерирует текстовую сводку за день.
        
        Args:
            user_id: ID пользователя (если None, то для всех пользователей)
            
        Returns:
            str: Текстовая сводка
        """
        logger.info(f"Генерация дневной сводки для пользователя {user_id}")
        
        try:
            start_date, end_date = self._get_date_range('day')
            stats = self._get_statistics(start_date, end_date, user_id)
            
            if not stats['total_inspections']:
                return self._format_empty_report('день')
            
            summary = self._format_summary_report(stats, 'день')
            
            logger.info(f"Дневная сводка сгенерирована: {stats['total_inspections']} проверок")
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка генерации дневной сводки: {e}")
            return "❌ Ошибка при генерации отчета"
    
    def generate_weekly_summary(self, user_id: Optional[int] = None) -> str:
        """
        Генерирует текстовую сводку за неделю.
        
        Args:
            user_id: ID пользователя (если None, то для всех пользователей)
            
        Returns:
            str: Текстовая сводка
        """
        logger.info(f"Генерация недельной сводки для пользователя {user_id}")
        
        try:
            start_date, end_date = self._get_date_range('week')
            stats = self._get_statistics(start_date, end_date, user_id)
            
            if not stats['total_inspections']:
                return self._format_empty_report('неделю')
            
            summary = self._format_summary_report(stats, 'неделю')
            
            logger.info(f"Недельная сводка сгенерирована: {stats['total_inspections']} проверок")
            return summary
            
        except Exception as e:
            logger.error(f"Ошибка генерации недельной сводки: {e}")
            return "❌ Ошибка при генерации отчета"
    
    def generate_daily_csv(self, user_id: Optional[int] = None) -> Optional[str]:
        """
        Генерирует CSV файл с данными за день.
        
        Args:
            user_id: ID пользователя (если None, то для всех пользователей)
            
        Returns:
            Optional[str]: Путь к созданному файлу или None при ошибке
        """
        logger.info(f"Генерация дневного CSV для пользователя {user_id}")
        
        try:
            start_date, end_date = self._get_date_range('day')
            inspections = self._get_inspections(start_date, end_date, user_id)
            
            if not inspections:
                logger.warning("Нет данных для дневного CSV отчета")
                return None
            
            date_str = start_date.strftime('%Y-%m-%d')
            filename = f"otk_daily_report_{date_str}.csv"
            if user_id:
                filename = f"otk_daily_report_user{user_id}_{date_str}.csv"
            
            file_path = self.temp_dir / filename
            self._write_csv_file(file_path, inspections)
            
            logger.info(f"Дневной CSV сгенерирован: {file_path}, {len(inspections)} записей")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Ошибка генерации дневного CSV: {e}")
            return None
    
    def generate_weekly_csv(self, user_id: Optional[int] = None) -> Optional[str]:
        """
        Генерирует CSV файл с данными за неделю.
        
        Args:
            user_id: ID пользователя (если None, то для всех пользователей)
            
        Returns:
            Optional[str]: Путь к созданному файлу или None при ошибке
        """
        logger.info(f"Генерация недельного CSV для пользователя {user_id}")
        
        try:
            start_date, end_date = self._get_date_range('week')
            inspections = self._get_inspections(start_date, end_date, user_id)
            
            if not inspections:
                logger.warning("Нет данных для недельного CSV отчета")
                return None
            
            week_str = start_date.strftime('%Y-W%W')
            filename = f"otk_weekly_report_{week_str}.csv"
            if user_id:
                filename = f"otk_weekly_report_user{user_id}_{week_str}.csv"
            
            file_path = self.temp_dir / filename
            self._write_csv_file(file_path, inspections)
            
            logger.info(f"Недельный CSV сгенерирован: {file_path}, {len(inspections)} записей")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Ошибка генерации недельного CSV: {e}")
            return None
    
    def get_available_reports(self) -> List[Dict[str, str]]:
        """
        Возвращает список доступных типов отчетов.
        
        Returns:
            List[Dict[str, str]]: Список отчетов с описаниями
        """
        return [
            {
                'type': 'daily_summary',
                'name': '📊 Сводка за день',
                'description': 'Краткая статистика проверок за сегодня'
            },
            {
                'type': 'weekly_summary',
                'name': '📈 Сводка за неделю',
                'description': 'Краткая статистика проверок за неделю'
            },
            {
                'type': 'daily_csv',
                'name': '📄 CSV за день',
                'description': 'Детальные данные за день в формате CSV'
            },
            {
                'type': 'weekly_csv',
                'name': '📋 CSV за неделю',
                'description': 'Детальные данные за неделю в формате CSV'
            }
        ]
    
    def cleanup_old_files(self, days: int = 1) -> int:
        """
        Удаляет старые временные файлы отчетов.
        
        Args:
            days: Количество дней для хранения файлов
            
        Returns:
            int: Количество удаленных файлов
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for file_path in self.temp_dir.glob("*.csv"):
                if file_path.stat().st_mtime < cutoff_date.timestamp():
                    file_path.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Удалено {deleted_count} старых файлов отчетов")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка очистки старых файлов: {e}")
            return 0
    
    def _get_date_range(self, period: str) -> Tuple[datetime, datetime]:
        """
        Возвращает диапазон дат для указанного периода.
        
        Args:
            period: 'day' или 'week'
            
        Returns:
            Tuple[datetime, datetime]: Начальная и конечная даты
        """
        now = datetime.now()
        
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        elif period == 'week':
            # Начало недели (понедельник)
            days_since_monday = now.weekday()
            start_date = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_date = start_date + timedelta(days=7)
        else:
            raise ValueError(f"Неподдерживаемый период: {period}")
        
        return start_date, end_date
    
    def _get_statistics(self, start_date: datetime, end_date: datetime, 
                       user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Получает статистику проверок за указанный период.
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            user_id: ID пользователя (опционально)
            
        Returns:
            Dict[str, Any]: Статистика
        """
        try:
            with get_db_session() as db:
                # Базовый запрос
                query = db.query(Inspection).filter(
                    and_(
                        Inspection.created_at >= start_date,
                        Inspection.created_at < end_date
                    )
                )
                
                # Фильтр по пользователю
                if user_id:
                    user = db.query(User).filter(User.telegram_id == user_id).first()
                    if user:
                        query = query.filter(Inspection.user_id == user.id)
                    else:
                        return self._empty_stats()
                
                # Получаем все проверки
                inspections = query.all()
                
                if not inspections:
                    return self._empty_stats()
                
                # Подсчитываем статистику
                total = len(inspections)
                approved = sum(1 for i in inspections if i.status == "годно")
                rework = sum(1 for i in inspections if i.status == "в доработку")
                reject = sum(1 for i in inspections if i.status == "в брак")
                
                # Статистика по пользователям (только для общих отчетов)
                users_stats = {}
                if not user_id:
                    for inspection in inspections:
                        user_id_key = inspection.user_id
                        if user_id_key not in users_stats:
                            users_stats[user_id_key] = {
                                'name': inspection.user.name or f"User_{inspection.user.telegram_id}",
                                'total': 0,
                                'approved': 0,
                                'rework': 0,
                                'reject': 0
                            }
                        
                        users_stats[user_id_key]['total'] += 1
                        if inspection.status == "годно":
                            users_stats[user_id_key]['approved'] += 1
                        elif inspection.status == "в доработку":
                            users_stats[user_id_key]['rework'] += 1
                        elif inspection.status == "в брак":
                            users_stats[user_id_key]['reject'] += 1
                
                return {
                    'total_inspections': total,
                    'approved': approved,
                    'rework': rework,
                    'reject': reject,
                    'success_rate': round(approved / total * 100, 1) if total > 0 else 0,
                    'period_start': start_date,
                    'period_end': end_date,
                    'users_stats': users_stats,
                    'unique_orders': len(set(i.order_id for i in inspections)),
                    'with_comments': sum(1 for i in inspections if i.comment)
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return self._empty_stats()
    
    def _get_inspections(self, start_date: datetime, end_date: datetime,
                        user_id: Optional[int] = None) -> List[Inspection]:
        """
        Получает список проверок за период для CSV экспорта.
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата  
            user_id: ID пользователя (опционально)
            
        Returns:
            List[Inspection]: Список проверок
        """
        try:
            with get_db_session() as db:
                query = (
                    db.query(Inspection)
                    .join(User)
                    .filter(
                        and_(
                            Inspection.created_at >= start_date,
                            Inspection.created_at < end_date
                        )
                    )
                    .order_by(Inspection.created_at.desc())
                )
                
                if user_id:
                    user = db.query(User).filter(User.telegram_id == user_id).first()
                    if user:
                        query = query.filter(Inspection.user_id == user.id)
                    else:
                        return []
                
                return query.all()
                
        except Exception as e:
            logger.error(f"Ошибка получения списка проверок: {e}")
            return []
    
    def _write_csv_file(self, file_path: Path, inspections: List[Inspection]) -> None:
        """
        Записывает данные проверок в CSV файл.
        
        Args:
            file_path: Путь к файлу
            inspections: Список проверок
        """
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Дата создания',
                'Номер заказа', 
                'Статус',
                'Комментарий',
                'Контролер',
                'ID сессии'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for inspection in inspections:
                writer.writerow({
                    'Дата создания': inspection.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'Номер заказа': inspection.order_id,
                    'Статус': inspection.status,
                    'Комментарий': inspection.comment or '',
                    'Контролер': inspection.user.name or f"User_{inspection.user.telegram_id}",
                    'ID сессии': inspection.session_id[:8] + '...'  # Сокращенный ID
                })
    
    def _format_summary_report(self, stats: Dict[str, Any], period: str) -> str:
        """
        Форматирует статистику в текстовый отчет.
        
        Args:
            stats: Статистика
            period: Период отчета
            
        Returns:
            str: Отформатированный отчет
        """
        report_lines = [
            f"📊 <b>Сводка за {period}</b>",
            f"📅 {stats['period_start'].strftime('%d.%m.%Y')} - {stats['period_end'].strftime('%d.%m.%Y')}",
            "",
            "📈 <b>Общая статистика:</b>",
            f"🔍 Всего проверок: {stats['total_inspections']}",
            f"📦 Уникальных заказов: {stats['unique_orders']}",
            f"💬 С комментариями: {stats['with_comments']}",
            "",
            "📊 <b>Результаты проверок:</b>",
            f"✅ Годно: {stats['approved']} ({stats['approved']/stats['total_inspections']*100:.1f}%)",
            f"🔧 В доработку: {stats['rework']} ({stats['rework']/stats['total_inspections']*100:.1f}%)",
            f"❌ В брак: {stats['reject']} ({stats['reject']/stats['total_inspections']*100:.1f}%)",
            "",
            f"🎯 <b>Общая успешность: {stats['success_rate']}%</b>"
        ]
        
        # Добавляем статистику по пользователям для общих отчетов
        if stats['users_stats']:
            report_lines.extend([
                "",
                "👥 <b>По контролерам:</b>"
            ])
            
            for user_stat in stats['users_stats'].values():
                success_rate = round(user_stat['approved'] / user_stat['total'] * 100, 1) if user_stat['total'] > 0 else 0
                report_lines.append(
                    f"• {user_stat['name']}: {user_stat['total']} проверок ({success_rate}% успешных)"
                )
        
        return "\n".join(report_lines)
    
    def _format_empty_report(self, period: str) -> str:
        """
        Форматирует сообщение о пустом отчете.
        
        Args:
            period: Период отчета
            
        Returns:
            str: Сообщение о пустом отчете
        """
        return f"📊 <b>Сводка за {period}</b>\n\n" \
               f"📈 За {period} проверок не проводилось.\n\n" \
               f"Отправьте данные о проверке для формирования отчетов."
    
    def _empty_stats(self) -> Dict[str, Any]:
        """
        Возвращает пустую статистику.
        
        Returns:
            Dict[str, Any]: Пустая статистика
        """
        return {
            'total_inspections': 0,
            'approved': 0,
            'rework': 0,
            'reject': 0,
            'success_rate': 0,
            'period_start': datetime.now(),
            'period_end': datetime.now(),
            'users_stats': {},
            'unique_orders': 0,
            'with_comments': 0
        }


# Глобальный экземпляр сервиса
report_service = ReportService()
