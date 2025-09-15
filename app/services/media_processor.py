"""
Сервис для обработки медиа файлов.

Реализует сохранение, валидацию и обработку аудио и фото файлов.
"""

import logging
import os
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
# from pydub import AudioSegment
# from pydub.utils import which

from app.core.config import settings

logger = logging.getLogger(__name__)


class MediaProcessor:
    """Сервис для обработки медиа файлов."""
    
    def __init__(self):
        """Инициализация сервиса."""
        # Создаем директории если не существуют
        self._ensure_directories()
        
        # Поддерживаемые форматы аудио
        self.supported_audio_formats = [
            '.ogg', '.oga', '.mp3', '.wav', '.m4a', '.aac', '.flac'
        ]
        
        # Поддерживаемые форматы изображений
        self.supported_image_formats = [
            '.jpg', '.jpeg', '.png', '.webp', '.gif'
        ]
    
    def _ensure_directories(self):
        """Создает необходимые директории для кэша."""
        cache_dirs = [
            settings.cache_dir,
            settings.cache_audio_dir,
            settings.cache_photos_dir,
            os.path.join(settings.cache_dir, "temp")
        ]
        
        for directory in cache_dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Директория создана или существует: {directory}")
    
    def save_audio_file(self, file_content: bytes, filename: str, user_id: int) -> str:
        """
        Сохраняет аудио файл в кэше.
        
        Args:
            file_content: Содержимое файла
            filename: Оригинальное имя файла
            user_id: ID пользователя
            
        Returns:
            str: Путь к сохраненному файлу
            
        Raises:
            ValueError: При неподдерживаемом формате или превышении лимитов
        """
        try:
            # Получаем расширение файла
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.supported_audio_formats:
                raise ValueError(f"Неподдерживаемый формат аудио: {file_ext}")
            
            # Проверяем размер файла
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > settings.max_audio_mb:
                raise ValueError(f"Размер файла {file_size_mb:.1f}MB превышает лимит {settings.max_audio_mb}MB")
            
            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(file_content).hexdigest()[:8]
            unique_filename = f"{timestamp}_{user_id}_{file_hash}{file_ext}"
            
            # Путь для сохранения
            file_path = os.path.join(settings.cache_audio_dir, unique_filename)
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"Аудио файл сохранен: {file_path} (размер: {file_size_mb:.1f}MB)")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Ошибка сохранения аудио файла {filename}: {e}")
            raise
    
    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Валидирует аудио файл и возвращает метаданные.
        
        Args:
            file_path: Путь к аудио файлу
            
        Returns:
            Dict[str, Any]: Метаданные файла
            
        Raises:
            ValueError: При невалидном файле
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            # Простая валидация без pydub (временное решение для Python 3.13)
            file_size = os.path.getsize(file_path)
            
            # Базовые метаданные
            metadata = {
                'duration_seconds': 0.0,  # Будет определено Whisper API
                'duration_minutes': 0.0,
                'sample_rate': 16000,  # Предполагаем стандартную частоту
                'channels': 1,  # Предполагаем моно
                'file_size': file_size,
                'is_mono': True
            }
            
            logger.info(f"Валидация аудио (базовая): размер {file_size} байт")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Ошибка валидации аудио файла {file_path}: {e}")
            raise
    
    def convert_audio_for_whisper(self, input_path: str) -> str:
        """
        Конвертирует аудио файл для оптимальной обработки в Whisper.
        
        Args:
            input_path: Путь к исходному файлу
            
        Returns:
            str: Путь к исходному файлу (временное решение без конвертации)
        """
        try:
            # Временное решение: возвращаем исходный файл без конвертации
            # Whisper API может обрабатывать многие форматы напрямую
            logger.info(f"Используем исходный файл для Whisper (без конвертации): {input_path}")
            
            return input_path
            
        except Exception as e:
            logger.error(f"Ошибка при подготовке файла для Whisper {input_path}: {e}")
            raise
    
    def save_photo_file(self, file_content: bytes, filename: str, user_id: int) -> str:
        """
        Сохраняет фото файл в кэше.
        
        Args:
            file_content: Содержимое файла
            filename: Оригинальное имя файла
            user_id: ID пользователя
            
        Returns:
            str: Путь к сохраненному файлу
            
        Raises:
            ValueError: При неподдерживаемом формате или превышении лимитов
        """
        try:
            # Получаем расширение файла
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.supported_image_formats:
                raise ValueError(f"Неподдерживаемый формат изображения: {file_ext}")
            
            # Проверяем размер файла
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > settings.max_image_mb:
                raise ValueError(f"Размер файла {file_size_mb:.1f}MB превышает лимит {settings.max_image_mb}MB")
            
            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(file_content).hexdigest()[:8]
            unique_filename = f"{timestamp}_{user_id}_{file_hash}{file_ext}"
            
            # Путь для сохранения
            file_path = os.path.join(settings.cache_photos_dir, unique_filename)
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"Фото файл сохранен: {file_path} (размер: {file_size_mb:.1f}MB)")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Ошибка сохранения фото файла {filename}: {e}")
            raise
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Очищает временные файлы старше указанного возраста.
        
        Args:
            max_age_hours: Максимальный возраст файлов в часах
        """
        try:
            temp_dir = os.path.join(settings.cache_dir, "temp")
            current_time = datetime.now().timestamp()
            
            cleaned_count = 0
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_hours * 3600:  # часы в секунды
                        os.remove(file_path)
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Очищено {cleaned_count} временных файлов")
            
        except Exception as e:
            logger.error(f"Ошибка очистки временных файлов: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику использования кэша.
        
        Returns:
            Dict[str, Any]: Статистика кэша
        """
        try:
            stats = {
                'audio_files': 0,
                'audio_size_mb': 0,
                'photo_files': 0,
                'photo_size_mb': 0,
                'temp_files': 0,
                'temp_size_mb': 0
            }
            
            # Статистика аудио
            if os.path.exists(settings.cache_audio_dir):
                for filename in os.listdir(settings.cache_audio_dir):
                    file_path = os.path.join(settings.cache_audio_dir, filename)
                    if os.path.isfile(file_path):
                        stats['audio_files'] += 1
                        stats['audio_size_mb'] += os.path.getsize(file_path) / (1024 * 1024)
            
            # Статистика фото
            if os.path.exists(settings.cache_photos_dir):
                for filename in os.listdir(settings.cache_photos_dir):
                    file_path = os.path.join(settings.cache_photos_dir, filename)
                    if os.path.isfile(file_path):
                        stats['photo_files'] += 1
                        stats['photo_size_mb'] += os.path.getsize(file_path) / (1024 * 1024)
            
            # Статистика временных файлов
            temp_dir = os.path.join(settings.cache_dir, "temp")
            if os.path.exists(temp_dir):
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    if os.path.isfile(file_path):
                        stats['temp_files'] += 1
                        stats['temp_size_mb'] += os.path.getsize(file_path) / (1024 * 1024)
            
            # Округляем размеры
            for key in ['audio_size_mb', 'photo_size_mb', 'temp_size_mb']:
                stats[key] = round(stats[key], 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики кэша: {e}")
            return {}


# Глобальный экземпляр процессора
media_processor = MediaProcessor()
