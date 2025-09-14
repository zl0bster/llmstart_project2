"""
Тесты для проверки извлечения данных LLM из примеров @scen1_use_cases.md.

Простой скрипт для тестирования извлечения данных о заказах из текстовых примеров.
"""

import os
import sys
import logging
from typing import List

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.clients.llm_client import OpenRouterLLMClient
from app.models.schemas import LLMResponse, OrderData, StatusEnum

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Тестовые данные из @scen1_use_cases.md
TEST_CASES = [
    # Прямой текст
    "#с10409 Отверстия м3 не все проходят га обеих деталях. Продувка не помогла",
    "#с10494 #с10495 Годно",
    "#с8516 Стенки акб. Перебрали возвращенную отправку. 39 штук годны, рекомендуется галтовка. 23 штуки с неисправимыми забоями - брак. Годные стоят на полке галтовки",
    "#с10343\n\tУшел размер толщины лепестка, на нижнем пределе 6,87-6,88\n\tРазмер 9 в + на 0,01-0,02 (максимально допустимое значение 9,07\n\tИ размер 16,3 в одном месте на нижнем пределе\n\tВ остальном годно",
    "#с10343\n\tГодно, но нет калибра М3-6G, резьбу не проверить\n\tКалибр 6Н не подходит, разные допуска и значения",
    "6 #с10417 Годно",
    
    # Аудио-транскрипция
    "строка 10409 Отверстия м3 не все проходят га обеих деталях. Продувка не помогла",
    "8516 строчка Стенки акб. Перебрали возвращенную отправку. 39 штук годны, рекомендуется галтовка. 23 штуки с неисправимыми забоями - брак. Годные стоят на полке галтовки",
    "строки 10494 и 10495 Годно",
    "10343\n\tУшел размер толщины лепестка, на нижнем пределе 6,87-6,88\n\tРазмер 9 в + на 0,01-0,02 (максимально допустимое значение 9,07\n\tИ размер 16,3 в одном месте на нижнем пределе\n\tВ остальном годно",
    
    # OCR текст
    "10432 - годно",
    "9587 - все в брак",
    "10456\n\t- 39 штук годны, рекомендуется галтовка\n\t- 23 штуки с неисправимыми забоями - брак",
    "8567 - норм"
]


def test_llm_extraction():
    """Тестирует извлечение данных через LLM."""
    
    # Проверяем наличие API ключа
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY не установлен. Установите переменную окружения для тестирования.")
        return False
    
    # Инициализируем клиент
    try:
        client = OpenRouterLLMClient(api_key=api_key, model="gpt-4")
        logger.info("LLM клиент инициализирован успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации LLM клиента: {e}")
        return False
    
    # Проверяем доступность сервиса
    if not client.is_available():
        logger.error("LLM сервис недоступен")
        return False
    
    logger.info("LLM сервис доступен, начинаем тестирование...")
    
    success_count = 0
    total_count = len(TEST_CASES)
    
    for i, test_text in enumerate(TEST_CASES, 1):
        logger.info(f"\n--- Тест {i}/{total_count} ---")
        logger.info(f"Входной текст: {test_text[:100]}...")
        
        try:
            # Обрабатываем текст
            response = client.process_text(test_text)
            
            if response.requires_correction:
                logger.warning(f"Требуется уточнение: {response.clarification_question}")
            else:
                logger.info(f"Извлечено заказов: {len(response.orders)}")
                for order in response.orders:
                    logger.info(f"  - Заказ #{order.order_id}: {order.status} - {order.comment or 'без комментария'}")
                
                if response.orders:
                    success_count += 1
            
        except Exception as e:
            logger.error(f"Ошибка при обработке теста {i}: {e}")
    
    logger.info(f"\n--- Результаты тестирования ---")
    logger.info(f"Успешно обработано: {success_count}/{total_count} тестов")
    logger.info(f"Процент успеха: {success_count/total_count*100:.1f}%")
    
    return success_count >= total_count * 0.8  # 80% успешных тестов


def test_specific_cases():
    """Тестирует конкретные случаи из примеров."""
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY не установлен")
        return False
    
    client = OpenRouterLLMClient(api_key=api_key, model="gpt-4")
    
    # Тест 1: Простой случай с одним заказом
    logger.info("\n=== Тест 1: Простой случай ===")
    text1 = "#с10409 Отверстия м3 не все проходят га обеих деталях. Продувка не помогла"
    response1 = client.process_text(text1)
    
    if response1.orders and len(response1.orders) == 1:
        order = response1.orders[0]
        if order.order_id == "10409" and order.status == StatusEnum.rework:
            logger.info("✅ Тест 1 пройден: заказ 10409, статус 'в доработку'")
        else:
            logger.warning(f"❌ Тест 1 не пройден: ожидался заказ 10409 со статусом 'в доработку', получен {order.order_id} со статусом {order.status}")
    else:
        logger.warning("❌ Тест 1 не пройден: не извлечен заказ")
    
    # Тест 2: Множественные заказы
    logger.info("\n=== Тест 2: Множественные заказы ===")
    text2 = "#с10494 #с10495 Годно"
    response2 = client.process_text(text2)
    
    if response2.orders and len(response2.orders) == 2:
        order_ids = [order.order_id for order in response2.orders]
        if "10494" in order_ids and "10495" in order_ids:
            logger.info("✅ Тест 2 пройден: извлечены заказы 10494 и 10495")
        else:
            logger.warning(f"❌ Тест 2 не пройден: ожидались заказы 10494 и 10495, получены {order_ids}")
    else:
        logger.warning(f"❌ Тест 2 не пройден: ожидалось 2 заказа, получено {len(response2.orders) if response2.orders else 0}")
    
    # Тест 3: OCR формат
    logger.info("\n=== Тест 3: OCR формат ===")
    text3 = "10432 - годно"
    response3 = client.process_text(text3)
    
    if response3.orders and len(response3.orders) == 1:
        order = response3.orders[0]
        if order.order_id == "10432" and order.status == StatusEnum.approved:
            logger.info("✅ Тест 3 пройден: заказ 10432, статус 'годно'")
        else:
            logger.warning(f"❌ Тест 3 не пройден: ожидался заказ 10432 со статусом 'годно', получен {order.order_id} со статусом {order.status}")
    else:
        logger.warning("❌ Тест 3 не пройден: не извлечен заказ")


if __name__ == "__main__":
    logger.info("Запуск тестов извлечения данных LLM...")
    
    # Основное тестирование
    success = test_llm_extraction()
    
    if success:
        logger.info("\n🎉 Основные тесты пройдены успешно!")
        
        # Детальное тестирование
        test_specific_cases()
    else:
        logger.error("\n❌ Основные тесты не пройдены")
    
    logger.info("\nТестирование завершено.")
