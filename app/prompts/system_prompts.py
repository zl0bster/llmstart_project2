"""
Системные промпты для LLM.

Промпты для извлечения структурированных данных из текстовых отчетов ОТК.
Читает тексты промптов из файлов в директории, указанной в PROMPTS_DIR.
"""

import os
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Кэш для загруженных промптов
_prompt_cache: Dict[str, str] = {}


def _load_prompt_file(filename: str) -> str:
    """
    Загружает текст промпта из файла.
    
    Args:
        filename: Имя файла с промптом
        
    Returns:
        str: Текст промпта
        
    Raises:
        FileNotFoundError: Если файл не найден
        IOError: Если ошибка чтения файла
    """
    if filename in _prompt_cache:
        return _prompt_cache[filename]
    
    prompt_path = os.path.join(settings.prompts_dir, filename)
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            _prompt_cache[filename] = content
            logger.debug(f"Загружен промпт из файла: {prompt_path}")
            return content
    except FileNotFoundError:
        logger.error(f"Файл промпта не найден: {prompt_path}")
        raise
    except IOError as e:
        logger.error(f"Ошибка чтения файла промпта {prompt_path}: {e}")
        raise


def get_system_prompt() -> str:
    """
    Возвращает системный промпт для извлечения данных о проверках ОТК.
    
    Returns:
        str: Системный промпт для LLM
    """
    return _load_prompt_file("system_prompt.txt")


def get_clarification_prompt() -> str:
    """
    Возвращает промпт для запроса уточнения у пользователя.
    
    Returns:
        str: Промпт для уточнения
    """
    return _load_prompt_file("clarification_prompt.txt")


def get_validation_prompt() -> str:
    """
    Возвращает промпт для валидации извлеченных данных.
    
    Returns:
        str: Промпт для валидации
    """
    return _load_prompt_file("validation_prompt.txt")


def clear_prompt_cache() -> None:
    """
    Очищает кэш загруженных промптов.
    Полезно для перезагрузки промптов без перезапуска приложения.
    """
    global _prompt_cache
    _prompt_cache.clear()
    logger.info("Кэш промптов очищен")


def format_orders_for_validation(orders: list) -> str:
    """
    Форматирует список заказов для отображения пользователю.
    
    Args:
        orders: Список объектов OrderData
        
    Returns:
        str: Отформатированный текст для валидации
    """
    if not orders:
        return "Заказы не найдены в тексте."
    
    result = "**Проверьте, пожалуйста, данные:**\n\n"
    
    for order in orders:
        result += f"**Заказ #{order.order_id}:**\n"
        result += f"• Статус: `{order.status or 'не указан'}`\n"
        if order.comment:
            result += f"• Комментарий: {order.comment}\n"
        result += "\n"
    
    result += "Всё верно?"
    return result
