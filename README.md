# OTK Assistant

Telegram бот для автоматизации проверок ОТК с использованием ИИ.

## 🚀 Quick Start

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
venv\\Scripts\\activate
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

## 📁 Структура проекта

```
otk-assistant/
├── app/                    # Основной код приложения
│   ├── bot/               # Telegram Bot логика
│   ├── services/          # Бизнес-логика
│   ├── clients/           # Внешние API клиенты
│   ├── models/            # Модели данных
│   ├── core/              # Конфигурация
│   └── utils/             # Утилиты
├── cache/                 # Временные файлы
├── data/                  # База данных
├── logs/                  # Логи приложения
├── prompts/               # Шаблоны промптов
└── tests/                 # Тесты
```

## ⚙️ Конфигурация

Основные переменные окружения в `.env`:

```env
# Обязательные
BOT_TOKEN=your_telegram_bot_token

# LLM провайдер (openrouter|ollama|lmstudio)
LLM_PROVIDER=ollama
TEXT_MODEL=deepseek-r1:7b

# Опциональные (есть значения по умолчанию)
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///data/otk_assistant.db
SESSION_TIMEOUT_MIN=15
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

## 🧪 Тестирование

### Быстрый тест Ollama

```bash
# Тест подключения к Ollama
python quick_ollama_test.py

# Полный тест интеграции
python test_ollama_integration.py

# Или через Makefile
make ollama-test
make ollama-test-full
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

## 📚 Документация

- [Техническое видение](docs/vision.md) - Архитектура и принципы
- [План разработки](docs/tasklist.md) - Итерационный план
- [Сценарии использования](docs/scenario1.md) - Детальные сценарии
- [Настройка Ollama](docs/OLLAMA_SETUP.md) - Подробная инструкция по Ollama
- [Настройка LM Studio](docs/LMSTUDIO_SETUP.md) - Подробная инструкция по LM Studio

## 🚧 Текущий статус

**Итерация 1**: Базовый бот и конфигурация ✅

- ✅ Структура проекта создана
- ✅ Базовые обработчики реализованы
- ✅ Конфигурация настроена
- ✅ Логирование работает
- ✅ Бот отвечает на команды

**Следующие итерации**:
- Итерация 2: Интеграция с LLM
- Итерация 3: Хранение данных и сессии
- Итерация 4: Голосовой пайплайн
- Итерация 5: Фото пайплайн (Vision)

## 🐛 Решение проблем

### Бот не запускается

1. Проверьте, что `BOT_TOKEN` указан в `.env`
2. Убедитесь, что все зависимости установлены
3. Проверьте логи в `logs/app.log`

### Ошибки импорта

```bash
# Убедитесь, что вы в корневой директории проекта
pwd

# Проверьте, что виртуальное окружение активировано
which python
```

## 📄 Лицензия

MIT License
