# OTK Assistant - Makefile
# Команды для разработки и развертывания

.PHONY: help install dev build run stop logs clean test lint format db-migrate db-reset db-backup db-export ollama-setup ollama-test ollama-pull health check-status

# Переменные
PYTHON := python
PIP := pip
VENV := venv

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Показать справку по командам
	@echo "$(GREEN)OTK Assistant - Доступные команды:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	$(PIP) install -r requirements.txt

dev: ## Запуск в режиме разработки (без Docker)
	@echo "$(GREEN)Запуск в режиме разработки...$(NC)"
	$(PYTHON) app/main.py

build: ## Сборка Docker образа
	@echo "$(GREEN)Сборка Docker образа...$(NC)"
	docker-compose build

run: ## Запуск контейнера
	@echo "$(GREEN)Запуск контейнера...$(NC)"
	docker-compose up -d

stop: ## Остановка контейнера
	@echo "$(GREEN)Остановка контейнера...$(NC)"
	docker-compose down

logs: ## Просмотр логов контейнера
	@echo "$(GREEN)Просмотр логов...$(NC)"
	docker-compose logs -f

clean: ## Очистка временных файлов и образов
	@echo "$(GREEN)Очистка временных файлов...$(NC)"
	docker-compose down --rmi all --volumes --remove-orphans
	docker system prune -f
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

test: ## Запуск тестов
	@echo "$(GREEN)Запуск тестов...$(NC)"
	$(PYTHON) -m pytest tests/ -v

lint: ## Проверка кода линтером
	@echo "$(GREEN)Проверка кода...$(NC)"
	$(PYTHON) -m flake8 app/
	$(PYTHON) -m mypy app/

format: ## Форматирование кода
	@echo "$(GREEN)Форматирование кода...$(NC)"
	$(PYTHON) -m black app/
	$(PYTHON) -m isort app/

db-migrate: ## Применение миграций БД
	@echo "$(GREEN)Применение миграций...$(NC)"
	$(PYTHON) -m alembic upgrade head

db-reset: ## Сброс базы данных
	@echo "$(RED)Сброс базы данных...$(NC)"
	rm -f data/otk_assistant.db
	$(PYTHON) -c "from app.core.database import create_tables; create_tables()"

db-backup: ## Создание бэкапа БД (архив в downloads/)
	@echo "$(GREEN)Создание бэкапа БД...$(NC)"
	mkdir -p downloads
	tar -czf downloads/otk_assistant_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz data/

db-export: ## Экспорт БД в CSV для пользователя (в downloads/)
	@echo "$(GREEN)Экспорт БД в CSV...$(NC)"
	mkdir -p downloads
	$(PYTHON) -c "from app.services.report_service import export_to_csv; export_to_csv()"

# =============================================================================
# OLLAMA КОМАНДЫ
# =============================================================================

ollama-setup: ## Настройка Ollama и установка модели qwen2.5:7b
	@echo "$(GREEN)Настройка Ollama...$(NC)"
	@echo "$(YELLOW)Убедитесь, что Ollama установлен и запущен$(NC)"
	@echo "$(YELLOW)Для установки: https://ollama.com/download$(NC)"
	@echo ""
	@echo "$(GREEN)Установка модели qwen2.5:7b...$(NC)"
	ollama pull qwen2.5:7b
	@echo "$(GREEN)Модель установлена. Проверка...$(NC)"
	ollama list | grep qwen2.5:7b || echo "$(RED)Модель не найдена$(NC)"

ollama-test: ## Быстрый тест Ollama без полной интеграции
	@echo "$(GREEN)Быстрый тест Ollama...$(NC)"
	$(PYTHON) tests/check_ollama_models.py

ollama-test-full: ## Полный тест интеграции с Ollama
	@echo "$(GREEN)Полный тест интеграции Ollama...$(NC)"
	$(PYTHON) test_ollama_integration.py

ollama-pull: ## Скачивание модели qwen2.5:7b
	@echo "$(GREEN)Скачивание модели qwen2.5:7b...$(NC)"
	ollama pull qwen2.5:7b

ollama-list: ## Список установленных моделей Ollama
	@echo "$(GREEN)Установленные модели Ollama:$(NC)"
	ollama list

ollama-info: ## Информация о модели qwen2.5:7b
	@echo "$(GREEN)Информация о модели qwen2.5:7b:$(NC)"
	ollama show qwen2.5:7b

ollama-run: ## Запуск интерактивного чата с моделью
	@echo "$(GREEN)Запуск интерактивного чата с qwen2.5:7b...$(NC)"
	ollama run qwen2.5:7b

ollama-serve: ## Запуск Ollama сервера
	@echo "$(GREEN)Запуск Ollama сервера...$(NC)"
	ollama serve

# =============================================================================
# НАСТРОЙКА ПРОЕКТА
# =============================================================================

setup-env: ## Создание .env файла из примера
	@echo "$(GREEN)Создание .env файла...$(NC)"
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "$(YELLOW).env файл создан. Отредактируйте его перед запуском.$(NC)"; \
	else \
		echo "$(YELLOW).env файл уже существует.$(NC)"; \
	fi

setup-dirs: ## Создание необходимых директорий
	@echo "$(GREEN)Создание директорий...$(NC)"
	mkdir -p cache/photos cache/audio cache/temp
	mkdir -p logs
	mkdir -p data/migrations
	mkdir -p downloads

setup: setup-dirs setup-env install ## Полная настройка проекта
	@echo "$(GREEN)Настройка проекта завершена!$(NC)"
	@echo "$(YELLOW)Следующие шаги:$(NC)"
	@echo "1. Отредактируйте .env файл"
	@echo "2. Настройте Ollama: make ollama-setup"
	@echo "3. Запустите тест: make ollama-test"

# =============================================================================
# МОНИТОРИНГ И ДИАГНОСТИКА
# =============================================================================

health: ## Проверка health check endpoint
	@echo "$(GREEN)Проверка health check...$(NC)"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "$(RED)❌ Health check недоступен$(NC)"

check-ollama: ## Проверка статуса Ollama
	@echo "$(GREEN)Проверка Ollama...$(NC)"
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "$(GREEN)✅ Ollama доступен$(NC)" || echo "$(RED)❌ Ollama недоступен$(NC)"

check-model: ## Проверка наличия модели qwen2.5:7b
	@echo "$(GREEN)Проверка модели qwen2.5:7b...$(NC)"
	@ollama list | grep -q qwen2.5:7b && echo "$(GREEN)✅ Модель установлена$(NC)" || echo "$(RED)❌ Модель не найдена$(NC)"

check-config: ## Проверка конфигурации
	@echo "$(GREEN)Проверка конфигурации...$(NC)"
	@$(PYTHON) -c "from app.core.config import settings; print(f'Провайдер: {settings.llm_provider}'); print(f'Модель: {settings.text_model}'); print(f'Ollama URL: {settings.ollama_base_url}')"

check-status: check-ollama check-model check-config health ## Полная проверка статуса системы

# =============================================================================
# РАЗРАБОТКА
# =============================================================================

dev-install: ## Установка зависимостей для разработки
	@echo "$(GREEN)Установка зависимостей для разработки...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt 2>/dev/null || echo "$(YELLOW)requirements-dev.txt не найден$(NC)"

dev-setup: setup dev-install ## Настройка среды разработки
	@echo "$(GREEN)Среда разработки настроена!$(NC)"

watch-logs: ## Мониторинг логов в реальном времени
	@echo "$(GREEN)Мониторинг логов...$(NC)"
	tail -f logs/app.log logs/error.log

# =============================================================================
# ПРОДАКШН
# =============================================================================

prod-build: ## Сборка для продакшна
	@echo "$(GREEN)Сборка для продакшна...$(NC)"
	docker build -t otk-assistant:latest .

prod-deploy: ## Деплой в продакшн (Railway)
	@echo "$(GREEN)Деплой в продакшн...$(NC)"
	git push origin main

push: ## Отправка изменений в удаленный репозиторий
	@echo "$(GREEN)Отправка изменений в Git...$(NC)"
	git push origin main

# =============================================================================
# УТИЛИТЫ
# =============================================================================

requirements: ## Обновление requirements.txt
	@echo "$(GREEN)Обновление requirements.txt...$(NC)"
	$(PIP) freeze > requirements.txt

clean-cache: ## Очистка кэша
	@echo "$(GREEN)Очистка кэша...$(NC)"
	rm -rf cache/photos/* cache/audio/* cache/temp/*

clean-logs: ## Очистка логов
	@echo "$(GREEN)Очистка логов...$(NC)"
	rm -f logs/*.log

reset-all: clean clean-cache clean-logs db-reset ## Полный сброс проекта
	@echo "$(GREEN)Полный сброс выполнен!$(NC)"

# Показать справку по умолчанию
.DEFAULT_GOAL := help
