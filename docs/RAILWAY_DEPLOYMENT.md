# Развертывание на Railway

## Настройка проекта в Railway

### 1. Переменные окружения

Обязательно настройте следующие переменные в Railway Dashboard:

#### Обязательные:
```bash
BOT_TOKEN=your_telegram_bot_token_here
```

#### Рекомендуемые для OpenRouter:
```bash
OPENROUTER_API_KEY=your_openrouter_api_key
LLM_PROVIDER=openrouter
TEXT_MODEL=openai/gpt-4o-mini
VISION_PROVIDER=openrouter
VISION_MODEL=openai/gpt-4o
```

#### Рекомендуемые для WhisperAPI:
```bash
WHISPERAPI_API_KEY=your_whisperapi_key
SPEECH_PROVIDER=whisperapi
SPEECH_MODEL=large-v2
```

### 2. Настройки Railway

В Railway Dashboard настройте:

- **Port**: Railway автоматически определит порт из переменной `PORT`
- **Health Check Path**: `/` (уже настроено в railway.toml)
- **Health Check Timeout**: 30 секунд

### 3. Логи и отладка

#### Просмотр логов:
```bash
# В Railway Dashboard
# Или через CLI:
railway logs
```

#### Типичные проблемы:

1. **Health check fails** - проверьте логи на наличие ошибок инициализации БД
2. **Bot token invalid** - убедитесь, что BOT_TOKEN правильно настроен
3. **API keys missing** - проверьте наличие всех необходимых API ключей

### 4. Мониторинг

Health check endpoints:
- `/` - простой health check для Railway
- `/health/simple` - проверка БД + базовая информация
- `/health` - полная проверка всех компонентов
- `/health/railway` - альтернативный простой endpoint

### 5. Структура файлов для Railway

Railway использует следующие файлы:
- `railway.toml` - основная конфигурация
- `railway.json` - альтернативная конфигурация (JSON формат)
- `Dockerfile` - сборка образа
- `.env` - переменные окружения (НЕ коммитится)

### 6. Автоматический деплой

Railway автоматически развертывает проект при push в main ветку GitHub.

### 7. Troubleshooting

#### Health check не проходит:
1. Проверьте логи: `railway logs`
2. Убедитесь, что порт 8000 доступен
3. Проверьте, что все переменные окружения настроены
4. Убедитесь, что БД инициализируется корректно

#### Бот не отвечает:
1. Проверьте BOT_TOKEN
2. Убедитесь, что бот не заблокирован в Telegram
3. Проверьте логи на наличие ошибок API

#### Ошибки LLM:
1. Проверьте API ключи
2. Убедитесь, что модель доступна
3. Проверьте баланс на OpenRouter/WhisperAPI

### 8. Рекомендуемая конфигурация для продакшна

```bash
# Основные настройки
LOG_LEVEL=INFO
LOG_CONSOLE=true
LOG_CONSOLE_FORMAT=json

# Провайдеры
LLM_PROVIDER=openrouter
TEXT_MODEL=openai/gpt-4o-mini
VISION_PROVIDER=openrouter
VISION_MODEL=openai/gpt-4o
SPEECH_PROVIDER=whisperapi
SPEECH_MODEL=large-v2

# Сетевые параметры
HTTP_TIMEOUT_SEC=30
HTTP_RETRIES=3
HTTP_RETRY_BACKOFF_SEC=2

# Ограничения
MAX_IMAGE_MB=20
MAX_AUDIO_MB=25
SESSION_TIMEOUT_MIN=15
```
