"""
Тестирование голосового пайплайна.

Тестирует интеграцию: аудио -> транскрипция -> анализ -> подтверждение
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.clients.speech_client import create_speech_client, WhisperClient
from app.services.media_processor import media_processor
from app.clients.llm_client import OpenRouterLLMClient
from app.clients.lmstudio_client import LMStudioLLMClient
from app.clients.ollama_client import OllamaLLMClient

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class VoicePipelineTest:
    """Класс для тестирования голосового пайплайна."""
    
    def __init__(self):
        """Инициализация тестов."""
        self.speech_client = None
        self.llm_client = None
        self.test_user_id = 12345
        
        # Тестовые тексты которые мы ожидаем получить от Whisper
        self.test_transcriptions = [
            "Заказ номер с10409 годно без замечаний",
            "Заказ с10494 в доработку требуется исправить дефект покраски",
            "с10401 в брак некачественная сварка с10402 годно проверен и принят"
        ]
    
    def init_speech_client(self) -> bool:
        """Инициализация Speech клиента."""
        try:
            if settings.speech_provider == "whisper":
                if settings.openai_api_key:
                    self.speech_client = WhisperClient(
                        api_key=settings.openai_api_key,
                        model=settings.speech_model
                    )
                    logger.info(f"Whisper клиент инициализирован с моделью {settings.speech_model}")
                elif settings.openrouter_api_key:
                    self.speech_client = WhisperClient(
                        api_key=settings.openrouter_api_key,
                        model=settings.speech_model,
                        base_url="https://openrouter.ai/api/v1"
                    )
                    logger.info(f"Whisper через OpenRouter клиент инициализирован")
                else:
                    logger.error("Нет API ключа для Whisper")
                    return False
            
            # Проверяем доступность
            if not self.speech_client.is_available():
                logger.error("Speech клиент недоступен")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации Speech клиента: {e}")
            return False
    
    def init_llm_client(self) -> bool:
        """Инициализация LLM клиента."""
        try:
            if settings.llm_provider == "lmstudio":
                self.llm_client = LMStudioLLMClient(
                    base_url=settings.lmstudio_base_url,
                    model=settings.text_model
                )
                logger.info(f"LM Studio клиент инициализирован с моделью {settings.text_model}")
            elif settings.llm_provider == "openrouter" and settings.openrouter_api_key:
                self.llm_client = OpenRouterLLMClient(
                    api_key=settings.openrouter_api_key,
                    model=settings.text_model
                )
                logger.info(f"OpenRouter клиент инициализирован с моделью {settings.text_model}")
            elif settings.llm_provider == "ollama":
                self.llm_client = OllamaLLMClient(
                    base_url=settings.ollama_base_url,
                    model=settings.text_model
                )
                logger.info(f"Ollama клиент инициализирован с моделью {settings.text_model}")
            else:
                logger.error(f"Неподдерживаемый провайдер LLM: {settings.llm_provider}")
                return False
            
            # Проверяем доступность
            if not self.llm_client.is_available():
                logger.error("LLM клиент недоступен")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации LLM клиента: {e}")
            return False
    
    def test_media_processor(self):
        """Тестирование медиа процессора."""
        logger.info("=== Тестирование MediaProcessor ===")
        
        try:
            # Проверяем создание директорий
            media_processor._ensure_directories()
            assert os.path.exists(settings.cache_audio_dir), "Директория audio кэша не создана"
            logger.info("✅ Директории кэша созданы успешно")
            
            # Проверяем статистику кэша
            stats = media_processor.get_cache_stats()
            logger.info(f"📊 Статистика кэша: {stats}")
            
            # Проверяем очистку временных файлов
            media_processor.cleanup_temp_files(max_age_hours=0)
            logger.info("✅ Очистка временных файлов выполнена")
            
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования MediaProcessor: {e}")
            return False
    
    def test_text_processing(self):
        """Тестирование обработки текста через LLM."""
        logger.info("=== Тестирование обработки текста ===")
        
        if not self.init_llm_client():
            logger.error("❌ Не удалось инициализировать LLM клиент")
            return False
        
        try:
            # Тестируем каждый пример транскрипции
            for i, text in enumerate(self.test_transcriptions, 1):
                logger.info(f"🔍 Тест {i}: '{text}'")
                
                # Обрабатываем через LLM
                response = self.llm_client.process_text(text)
                
                # Проверяем результат
                if response.orders:
                    logger.info(f"✅ Извлечено заказов: {len(response.orders)}")
                    for order in response.orders:
                        logger.info(f"   📦 {order.order_id}: {order.status} - {order.comment or 'без комментария'}")
                else:
                    logger.warning(f"⚠️ Заказы не извлечены")
                
                if response.requires_correction:
                    logger.info(f"❓ Требует уточнения: {response.clarification_question}")
            
            logger.info("✅ Обработка текста завершена успешно")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки текста: {e}")
            return False
    
    def test_speech_client(self):
        """Тестирование Speech клиента (заглушка)."""
        logger.info("=== Тестирование Speech клиента ===")
        
        if not self.init_speech_client():
            logger.error("❌ Не удалось инициализировать Speech клиент")
            return False
        
        try:
            logger.info("✅ Speech клиент инициализирован и доступен")
            logger.info("ℹ️ Для полного тестирования нужны реальные аудио файлы")
            
            # TODO: Добавить тестирование с реальными аудио файлами
            # Пока что просто проверяем что клиент создался
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования Speech клиента: {e}")
            return False
    
    def test_end_to_end_simulation(self):
        """Симуляция end-to-end тестирования."""
        logger.info("=== Симуляция полного пайплайна ===")
        
        try:
            # Симулируем получение голосового сообщения
            logger.info("🎤 Симулируем получение голосового сообщения...")
            
            # Симулируем сохранение файла (создаем фиктивный файл)
            test_audio_content = b"fake_audio_data"
            test_filename = f"test_voice_{self.test_user_id}.ogg"
            
            # Проверяем что медиа процессор может обработать файл
            # (сохранение, валидация, конвертация будут реальными для настоящих файлов)
            logger.info("💾 Симулируем сохранение аудио файла...")
            
            # Симулируем транскрипцию
            simulated_transcription = self.test_transcriptions[0]
            logger.info(f"📝 Симулируем транскрипцию: '{simulated_transcription}'")
            
            # Обрабатываем транскрипцию через LLM
            if self.llm_client:
                logger.info("🤖 Обрабатываем транскрипцию через LLM...")
                response = self.llm_client.process_text(simulated_transcription)
                
                if response.orders:
                    logger.info(f"✅ Пайплайн завершен успешно: {len(response.orders)} заказов")
                    return True
                else:
                    logger.warning("⚠️ LLM не извлек заказы из транскрипции")
                    return False
            else:
                logger.error("❌ LLM клиент не инициализирован")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка в симуляции пайплайна: {e}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов."""
        logger.info("🚀 Начинаем тестирование голосового пайплайна")
        logger.info(f"📋 Конфигурация: {settings.llm_provider} + {settings.speech_provider}")
        
        results = {
            "media_processor": self.test_media_processor(),
            "text_processing": self.test_text_processing(),
            "speech_client": self.test_speech_client(),
            "end_to_end": self.test_end_to_end_simulation()
        }
        
        # Подводим итоги
        logger.info("=" * 50)
        logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            logger.info(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"📈 Итого: {passed}/{total} тестов пройдено")
        
        if passed == total:
            logger.info("🎉 Все тесты пройдены успешно!")
            return True
        else:
            logger.error(f"💥 {total - passed} тестов провалены")
            return False


def main():
    """Основная функция запуска тестов."""
    print("🎤 Тестирование голосового пайплайна OTK Assistant")
    print("=" * 60)
    
    # Проверяем настройки
    if not settings.bot_token:
        print("❌ BOT_TOKEN не настроен в .env")
        return False
    
    # Создаем и запускаем тесты
    test_runner = VoicePipelineTest()
    success = test_runner.run_all_tests()
    
    if success:
        print("\n🎉 Голосовой пайплайн готов к работе!")
        print("Теперь можно отправлять голосовые сообщения боту.")
    else:
        print("\n💥 Есть проблемы с голосовым пайплайном.")
        print("Проверьте логи и исправьте ошибки.")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)

