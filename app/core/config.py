"""Конфигурация приложения OTK Assistant."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # =============================================================================
    # БОТ И БАЗА ДАННЫХ
    # =============================================================================
    
    bot_token: str = Field(..., env="BOT_TOKEN", description="Токен Telegram бота")
    database_url: str = Field(
        "sqlite:///data/otk_assistant.db", 
        env="DATABASE_URL", 
        description="Строка подключения к базе данных"
    )
    session_timeout_min: int = Field(
        15, 
        env="SESSION_TIMEOUT_MIN", 
        description="Таймаут неактивной сессии в минутах"
    )
    
    # =============================================================================
    # ЛОГИ И КЭШ
    # =============================================================================
    
    log_level: str = Field("INFO", env="LOG_LEVEL", description="Уровень логирования")
    log_dir: str = Field("logs/", env="LOG_DIR", description="Директория для логов")
    log_console: bool = Field(True, env="LOG_CONSOLE", description="Вывод логов в консоль")
    log_console_format: str = Field(
        "plain", 
        env="LOG_CONSOLE_FORMAT", 
        description="Формат консольного вывода"
    )
    cache_dir: str = Field("cache/", env="CACHE_DIR", description="Корневая папка кэша")
    cache_photos_dir: str = Field(
        "cache/photos/", 
        env="CACHE_PHOTOS_DIR", 
        description="Кэш фотографий"
    )
    cache_audio_dir: str = Field(
        "cache/audio/", 
        env="CACHE_AUDIO_DIR", 
        description="Кэш аудио файлов"
    )
    prompts_dir: str = Field(
        "prompts/", 
        env="PROMPTS_DIR", 
        description="Директория с текстовыми промптами"
    )
    
    # =============================================================================
    # ОГРАНИЧЕНИЯ МЕДИА
    # =============================================================================
    
    max_image_mb: int = Field(20, env="MAX_IMAGE_MB", description="Максимальный размер фото в МБ")
    max_image_res: str = Field(
        "2048x2048", 
        env="MAX_IMAGE_RES", 
        description="Максимальное разрешение фото"
    )
    max_audio_mb: int = Field(25, env="MAX_AUDIO_MB", description="Максимальный размер аудио в МБ")
    max_audio_min: int = Field(25, env="MAX_AUDIO_MIN", description="Максимальная длительность аудио в минутах")
    audio_min_sample_rate: int = Field(
        16000, 
        env="AUDIO_MIN_SAMPLE_RATE", 
        description="Минимальная частота дискретизации аудио"
    )
    audio_mono: bool = Field(True, env="AUDIO_MONO", description="Приводить аудио к моно")
    
    # =============================================================================
    # ПРОВАЙДЕРЫ И МОДЕЛИ
    # =============================================================================
    
    llm_provider: str = Field("openrouter", env="LLM_PROVIDER", description="Провайдер для текстового анализа")
    text_model: str = Field("gpt-4", env="TEXT_MODEL", description="Текстовая модель")
    vision_provider: str = Field("openrouter", env="VISION_PROVIDER", description="Провайдер для анализа изображений")
    vision_model: str = Field("gpt-4-vision", env="VISION_MODEL", description="Модель для анализа изображений")
    speech_provider: str = Field("whisper", env="SPEECH_PROVIDER", description="Провайдер для обработки речи")
    speech_model: str = Field("whisper-1", env="SPEECH_MODEL", description="Модель для обработки речи")
    
    # =============================================================================
    # КЛЮЧИ И ДОСТУП
    # =============================================================================
    
    openrouter_api_key: Optional[str] = Field(None, env="OPENROUTER_API_KEY", description="API ключ для OpenRouter")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY", description="API ключ для OpenAI")
    lmstudio_base_url: str = Field(
        "http://localhost:1234", 
        env="LMSTUDIO_BASE_URL", 
        description="URL локального LM Studio"
    )
    ollama_base_url: str = Field(
        "http://localhost:11434", 
        env="OLLAMA_BASE_URL", 
        description="URL Ollama"
    )
    
    # =============================================================================
    # СЕТЕВЫЕ ПАРАМЕТРЫ
    # =============================================================================
    
    http_timeout_sec: int = Field(30, env="HTTP_TIMEOUT_SEC", description="Таймаут HTTP запросов в секундах")
    http_retries: int = Field(2, env="HTTP_RETRIES", description="Количество повторов при временных ошибках")
    http_retry_backoff_sec: int = Field(
        2, 
        env="HTTP_RETRY_BACKOFF_SEC", 
        description="Задержка между повторами в секундах"
    )
    
    # =============================================================================
    # ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ OLLAMA
    # =============================================================================
    
    ollama_auto_pull: bool = Field(True, env="OLLAMA_AUTO_PULL", description="Автоматическое скачивание модели при запуске")
    ollama_timeout_sec: int = Field(120, env="OLLAMA_TIMEOUT_SEC", description="Таймаут для Ollama запросов в секундах")
    ollama_num_predict: int = Field(2000, env="OLLAMA_NUM_PREDICT", description="Количество токенов для генерации ответа")
    ollama_temperature: float = Field(0.1, env="OLLAMA_TEMPERATURE", description="Температура для генерации")
    
    class Config:
        """Конфигурация Pydantic."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Глобальный экземпляр настроек
settings = Settings()
