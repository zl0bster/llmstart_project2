# Руководство по развертыванию OTK Assistant

## Обзор

OTK Assistant поддерживает несколько вариантов развертывания:
- **Локальная разработка** с Docker Compose
- **Продакшн** в Railway.com
- **Собственный сервер** с Docker

## Быстрый старт

### 1. Локальная разработка

```bash
# Клонирование репозитория
git clone <repository-url>
cd llmstart_project2

# Настройка окружения
make setup

# Запуск с Docker Compose
make build
make run

# Проверка статуса
make check-status
```

### 2. Развертывание в Railway

```bash
# Подготовка к деплою
make prod-build

# Деплой (автоматически при push в main)
make prod-deploy
```

## Детальное руководство

### Локальная разработка с Docker Compose

#### Предварительные требования

- Docker и Docker Compose
- Git
- Make (опционально, для удобства)

#### Настройка

1. **Клонирование проекта:**
   ```bash
   git clone <repository-url>
   cd llmstart_project2
   ```

2. **Создание .env файла:**
   ```bash
   cp env.example .env
   # Отредактируйте .env файл с вашими настройками
   ```

3. **Создание необходимых директорий:**
   ```bash
   make setup-dirs
   ```

4. **Запуск сервисов:**
   ```bash
   # Сборка и запуск всех сервисов
   make build
   make run
   
   # Или только основного приложения с Ollama
   docker-compose up -d otk-assistant ollama
   ```

#### Доступные сервисы

- **otk-assistant** (порт 8000) - основное приложение
- **ollama** (порт 11434) - локальные LLM модели
- **lmstudio** (порт 1234) - альтернативный LLM сервис
- **postgres** (порт 5432) - PostgreSQL база данных
- **redis** (порт 6379) - кэширование и сессии

#### Полезные команды

```bash
# Просмотр логов
make logs

# Остановка сервисов
make stop

# Очистка
make clean

# Проверка статуса
make check-status

# Health check
make health
```

### Развертывание в Railway

Railway.com - рекомендуемый вариант для продакшн развертывания.

#### Настройка проекта в Railway

1. **Создание проекта:**
   - Зайдите на [railway.app](https://railway.app)
   - Создайте новый проект
   - Подключите GitHub репозиторий

2. **Настройка переменных окружения:**
   
   В Railway Dashboard → Variables добавьте:
   
   ```env
   # Обязательные
   BOT_TOKEN=your_telegram_bot_token
   
   # API ключи (выберите нужные провайдеры)
   OPENROUTER_API_KEY=your_openrouter_key
   OPENAI_API_KEY=your_openai_key
   WHISPERAPI_API_KEY=your_whisperapi_key
   
   # Настройки провайдеров
   LLM_PROVIDER=openrouter
   TEXT_MODEL=openai/gpt-4o-mini
   VISION_PROVIDER=openrouter
   VISION_MODEL=openai/gpt-4o
   SPEECH_PROVIDER=whisperapi
   SPEECH_MODEL=large-v2
   
   # Настройки логирования
   LOG_LEVEL=INFO
   LOG_CONSOLE=true
   LOG_CONSOLE_FORMAT=json
   ```

3. **Автоматический деплой:**
   - Railway автоматически развернет приложение при push в main ветку
   - Health check доступен по адресу: `https://your-app.railway.app/health`

#### Рекомендуемые настройки для Railway

- **Провайдер LLM:** OpenRouter (стабильный, быстрый)
- **Провайдер Vision:** OpenRouter с GPT-4o
- **Провайдер Speech:** WhisperAPI (дешевле OpenAI)
- **База данных:** Встроенная SQLite (Railway предоставляет постоянное хранилище)

### Развертывание на собственном сервере

#### Предварительные требования

- Docker и Docker Compose
- Домен (опционально)
- SSL сертификат (для HTTPS)

#### Настройка

1. **Подготовка сервера:**
   ```bash
   # Установка Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   
   # Установка Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Клонирование и настройка:**
   ```bash
   git clone <repository-url>
   cd llmstart_project2
   cp env.example .env
   # Настройте .env файл
   ```

3. **Запуск:**
   ```bash
   docker-compose up -d
   ```

#### Настройка с PostgreSQL

Для продакшн рекомендуется использовать PostgreSQL:

```bash
# Запуск с PostgreSQL
docker-compose --profile postgres up -d

# Обновите DATABASE_URL в .env:
DATABASE_URL=postgresql://otk:otk_password@localhost:5432/otk_assistant
```

#### Настройка с Redis

Для кэширования и сессий:

```bash
# Запуск с Redis
docker-compose --profile redis up -d
```

## Мониторинг и обслуживание

### Health Check

Приложение предоставляет health check endpoint:

- **Полный health check:** `GET /health`
- **Простой health check:** `GET /health/simple`

```bash
# Проверка локально
curl http://localhost:8000/health

# Проверка в Railway
curl https://your-app.railway.app/health
```

### Логирование

#### Локальная разработка

```bash
# Просмотр логов
make logs

# Мониторинг в реальном времени
make watch-logs
```

#### Продакшн

- **Railway:** Логи доступны в Dashboard → Deployments → Logs
- **Собственный сервер:** `docker-compose logs -f`

### Бэкапы базы данных

#### Создание бэкапа

```bash
# Автоматический бэкап
make db-backup

# Ручной бэкап с настройками
python scripts/backup_db.py --output-dir backups --archive --cleanup-days 30
```

#### Восстановление из бэкапа

```bash
# Восстановление из бэкапа
python scripts/restore_db.py backups/otk_assistant_backup_20240101_120000.db

# Принудительное восстановление
python scripts/restore_db.py backups/otk_assistant_backup_20240101_120000.db --force
```

### Обновление приложения

#### Локальная разработка

```bash
# Получение обновлений
git pull origin main

# Пересборка и перезапуск
make build
make stop
make run
```

#### Railway

```bash
# Автоматическое обновление при push
git push origin main
```

#### Собственный сервер

```bash
# Получение обновлений
git pull origin main

# Пересборка и перезапуск
docker-compose down
docker-compose build
docker-compose up -d
```

## Устранение неполадок

### Частые проблемы

#### 1. Бот не отвечает

**Проверьте:**
- Токен бота в переменных окружения
- Доступность интернета
- Логи приложения

```bash
# Проверка конфигурации
make check-config

# Проверка health check
make health
```

#### 2. Ошибки LLM провайдера

**Для OpenRouter:**
- Проверьте API ключ
- Убедитесь в наличии кредитов

**Для Ollama:**
- Проверьте доступность сервиса: `curl http://localhost:11434/api/tags`
- Убедитесь в установке модели: `ollama list`

#### 3. Проблемы с базой данных

```bash
# Проверка подключения к БД
python -c "from app.core.database import init_database; init_database()"

# Сброс БД (ОСТОРОЖНО!)
make db-reset
```

#### 4. Проблемы с Docker

```bash
# Очистка Docker
make clean

# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов
docker-compose logs
```

### Логи и диагностика

#### Уровни логирования

- `DEBUG` - детальная отладочная информация
- `INFO` - общая информация о работе
- `WARNING` - предупреждения
- `ERROR` - ошибки
- `CRITICAL` - критические ошибки

#### Форматы логов

- `plain` - читаемый формат для разработки
- `json` - структурированный формат для продакшна

## Безопасность

### Рекомендации для продакшна

1. **Переменные окружения:**
   - Никогда не коммитьте .env файлы
   - Используйте сильные пароли для БД
   - Регулярно ротируйте API ключи

2. **Сеть:**
   - Используйте HTTPS в продакшне
   - Настройте firewall
   - Ограничьте доступ к портам

3. **Мониторинг:**
   - Настройте алерты на критические ошибки
   - Мониторьте использование ресурсов
   - Ведите аудит доступа

4. **Бэкапы:**
   - Регулярно создавайте бэкапы БД
   - Тестируйте восстановление
   - Храните бэкапы в безопасном месте

## Производительность

### Оптимизация для продакшна

1. **LLM провайдеры:**
   - OpenRouter: быстрый, стабильный
   - Ollama: бесплатный, но требует ресурсов
   - LM Studio: для локального использования

2. **База данных:**
   - SQLite: для небольших нагрузок
   - PostgreSQL: для высоких нагрузок

3. **Кэширование:**
   - Redis: для сессий и кэша
   - Локальный кэш: для медиа файлов

4. **Мониторинг:**
   - Health checks
   - Метрики производительности
   - Логирование ошибок

## Поддержка

### Получение помощи

1. **Документация:** Изучите docs/ директорию
2. **Логи:** Проверьте логи приложения
3. **Health check:** Используйте /health endpoint
4. **Issues:** Создайте issue в репозитории

### Полезные команды

```bash
# Полная диагностика
make check-status

# Проверка всех сервисов
make health

# Создание бэкапа
make db-backup

# Очистка системы
make clean
```
