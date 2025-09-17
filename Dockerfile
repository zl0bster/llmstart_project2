# OTK Assistant - Dockerfile
# Многоэтапная сборка для оптимизации размера образа

# =============================================================================
# ЭТАП 1: БАЗОВЫЙ ОБРАЗ
# =============================================================================
FROM python:3.11-slim as base

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN groupadd -r otk && useradd -r -g otk otk

# Установка рабочей директории
WORKDIR /app

# =============================================================================
# ЭТАП 2: УСТАНОВКА ЗАВИСИМОСТЕЙ
# =============================================================================
FROM base as dependencies

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# ЭТАП 3: ПРОДАКШН ОБРАЗ
# =============================================================================
FROM base as production

# Копирование установленных зависимостей
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Копирование исходного кода
COPY app/ ./app/
COPY prompts/ ./prompts/

# Создание необходимых директорий
RUN mkdir -p cache/photos cache/audio cache/temp logs data/migrations downloads

# Установка прав доступа
RUN chown -R otk:otk /app

# Переключение на пользователя otk
USER otk

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV LOG_DIR=logs/
ENV CACHE_DIR=cache/
ENV DATABASE_URL=sqlite:///data/otk_assistant.db

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Открытие порта (если потребуется для health check)
EXPOSE 8000

# Команда запуска
CMD ["python", "app/main.py"]
