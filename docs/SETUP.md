# Установка и настройка OTK Assistant

Подробная инструкция по подготовке к работе с ботом.

## 🚀 Быстрый старт

### 1. Создание Telegram бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 2. Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv

# Активация окружения
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Настройка конфигурации

```bash
# Копирование файла конфигурации
copy env.example .env

# Редактирование .env файла
# Укажите ваш BOT_TOKEN
```

### 4. Запуск бота

```bash
python -m app.main
```

## ⚙️ Конфигурация

Основные переменные окружения в `.env`:

```env
# Обязательные
BOT_TOKEN=your_telegram_bot_token

# LLM провайдер (openrouter|ollama|lmstudio)
LLM_PROVIDER=ollama
TEXT_MODEL=qwen2.5:7b

# Голосовой пайплайн (Whisper API)
SPEECH_PROVIDER=whisper
SPEECH_MODEL=whisper-1
OPENAI_API_KEY=your_openai_key  # Для Whisper API

# Фото пайплайн (Vision API)
VISION_PROVIDER=openrouter
VISION_MODEL=gpt-4-vision
OPENROUTER_API_KEY=your_openrouter_key  # Для Vision API

# Опциональные (есть значения по умолчанию)
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///data/otk_assistant.db
SESSION_TIMEOUT_MIN=15
MAX_AUDIO_MB=25
MAX_IMAGE_MB=20
```

Полный список переменных см. в `env.example`.

## 🤖 Настройка LLM провайдеров

### Ollama (рекомендуется для локальной работы)

```bash
# Установка Ollama
# Windows: https://ollama.com/download
# Linux/Mac: curl -fsSL https://ollama.com/install.sh | sh

# Установка модели deepseek-r1:7b
ollama pull deepseek-r1:7b

# Проверка
ollama list
```

### LM Studio

1. Скачайте LM Studio с https://lmstudio.ai/
2. Загрузите модель `openai/gpt-oss-20b`
3. Запустите локальный сервер

### OpenRouter

1. Получите API ключ на https://openrouter.ai/
2. Укажите в `.env`: `OPENROUTER_API_KEY=your_key`

## 🎤 Настройка голосового пайплайна

### Whisper API (OpenAI)

```bash
# Получите API ключ на https://platform.openai.com/
# Укажите в .env:
SPEECH_PROVIDER=whisper
OPENAI_API_KEY=your_openai_key
SPEECH_MODEL=whisper-1
```

### WhisperAPI.com (альтернатива)

```bash
# Получите API ключ на https://whisper-api.com/
# Укажите в .env:
SPEECH_PROVIDER=whisperapi
WHISPERAPI_API_KEY=your_whisperapi_key
SPEECH_MODEL=large-v2
```

**Поддерживаемые форматы аудио:** OGG, MP3, WAV, M4A, AAC, FLAC

## 📸 Настройка фото пайплайна

### GPT-4 Vision (OpenAI)

```bash
# Укажите в .env:
VISION_PROVIDER=gpt4_vision
OPENAI_API_KEY=your_openai_key
VISION_MODEL=gpt-4-vision-preview
```

### OpenRouter Vision

```bash
# Укажите в .env:
VISION_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_key
VISION_MODEL=openai/gpt-4-vision-preview
```

**Поддерживаемые форматы изображений:** JPG, PNG, WebP, GIF

## 🧪 Тестирование

### Быстрый тест Ollama

```bash
# Тест подключения к Ollama
python tests/check_ollama_models.py

# Полный тест LLM извлечения
python tests/test_llm_extraction.py

# Или через Makefile
make ollama-test
make ollama-test-full
```

### Тестирование пайплайнов

```bash
# Тест голосового пайплайна
python tests/test_voice_pipeline.py

# Тест фото пайплайна
python tests/test_photo_pipeline.py

# Тест полной итерации
python tests/test_iteration3.py
```

### Базовое тестирование бота

1. Запустите бота
2. Найдите вашего бота в Telegram
3. Отправьте команду `/start`
4. Проверьте, что бот отвечает приветствием
5. Отправьте текстовое сообщение
6. Проверьте, что бот отвечает эхо

### Проверка логов

```bash
# Просмотр логов
tail -f logs/app.log

# Проверка ошибок
grep ERROR logs/app.log
```

## 📋 Доступные команды

- `/start` - Запуск бота и приветствие
- `/help` - Справка по использованию
- `/status` - Проверка статуса системы
- `/reports` - Меню отчетов и статистики

## 🎯 Функции бота

### 💬 Текстовый ввод
- Отправьте текстовое описание проверки
- Бот извлечет номера заказов и статусы
- Подтвердите данные через интерактивные кнопки

### 🎤 Голосовые сообщения
- Запишите голосовое сообщение с отчетом
- Автоматическая транскрипция через Whisper API
- Анализ извлеченного текста

### 📸 Фото протоколов
- Отправьте фото протокола ОТК
- Автоматическое извлечение текста через Vision API
- Анализ и обработка как текстовых данных

### 📄 Документы-изображения
- Поддержка документов в формате изображений
- Автоматическое распознавание содержимого
- Интеграция в общий пайплайн обработки

### 📊 Система отчетов
- **Сводные отчеты**: Статистика за день и неделю
- **CSV экспорт**: Детальные данные для анализа
- **Персональные отчеты**: Каждый пользователь видит свои данные
- **Автоматическая очистка**: Удаление старых временных файлов

## 🔧 Разработка

### Установка в режиме разработки

```bash
# Установка с зависимостями для разработки
pip install -r requirements.txt

# Запуск в режиме отладки
LOG_LEVEL=DEBUG python -m app.main
```

### Структура кода

- **app/bot/handlers/** - Обработчики сообщений Telegram
- **app/core/config.py** - Конфигурация приложения
- **app/main.py** - Точка входа приложения

### Makefile команды

```bash
# Настройка проекта
make setup              # Полная настройка проекта
make setup-env          # Создание .env файла
make install            # Установка зависимостей

# Ollama
make ollama-setup       # Настройка Ollama и установка модели
make ollama-test        # Быстрый тест Ollama
make ollama-test-full   # Полный тест интеграции
make ollama-pull        # Скачивание модели deepseek-r1:7b

# Разработка
make dev                # Запуск в режиме разработки
make test               # Запуск тестов
make lint               # Проверка кода
make format             # Форматирование кода

# Docker
make build              # Сборка Docker образа
make run                # Запуск контейнера
make stop               # Остановка контейнера
make logs               # Просмотр логов

# База данных
make db-migrate         # Применение миграций
make db-reset           # Сброс базы данных
make db-backup          # Создание бэкапа

# Очистка
make clean              # Очистка временных файлов
make clean-cache        # Очистка кэша
make clean-logs         # Очистка логов

# Справка
make help               # Показать все доступные команды
```

## 🐛 Решение проблем

### Бот не запускается

1. Проверьте, что `BOT_TOKEN` указан в `.env`
2. Убедитесь, что все зависимости установлены
3. Проверьте логи в `logs/app.log`

### Проблемы с голосовыми сообщениями

1. Убедитесь, что указан `OPENAI_API_KEY` или `WHISPERAPI_API_KEY`
2. Проверьте настройки `SPEECH_PROVIDER` в `.env`
3. Максимальный размер аудио: 25 МБ, длительность: 25 минут

### Проблемы с фото

1. Убедитесь, что указан API ключ для Vision провайдера
2. Проверьте настройки `VISION_PROVIDER` в `.env`
3. Максимальный размер изображения: 20 МБ
4. Поддерживаемые форматы: JPG, PNG, WebP, GIF
5. Максимальное разрешение: 2048x2048

### Отладка медиа файлов

```bash
# Проверка копий файлов в логах
ls -la logs/debug_*

# Просмотр детальных логов обработки
tail -f logs/app.log | grep -E "(Vision|Whisper|photo|voice)"
```

### Ошибки импорта

```bash
# Убедитесь, что вы в корневой директории проекта
pwd

# Проверьте, что виртуальное окружение активировано
which python
```

## 📚 Дополнительные руководства

- [🏗 Техническое видение](vision.md) - Архитектура и принципы разработки
- [📊 Система отчетов](REPORTS.md) - Руководство по отчетам и статистике
- [🎯 Сценарии использования](scenario1.md) - Детальные пользовательские сценарии
- [📝 План разработки](tasklist.md) - Итерационный план развития
- [🤖 Настройка Ollama](OLLAMA_SETUP.md) - Подробная инструкция по Ollama
- [🖥 Настройка LM Studio](LMSTUDIO_SETUP.md) - Подробная инструкция по LM Studio
