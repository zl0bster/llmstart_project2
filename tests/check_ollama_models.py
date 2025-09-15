#!/usr/bin/env python3
"""
Скрипт для проверки загруженных моделей в Ollama.
"""

import requests
import json
import sys
from typing import List, Dict, Any


def get_ollama_models(base_url: str = "http://localhost:11434") -> List[Dict[str, Any]]:
    """
    Получает список загруженных моделей из Ollama.
    
    Args:
        base_url: URL Ollama сервера
        
    Returns:
        List[Dict]: Список моделей с их метаданными
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data.get("models", [])
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к Ollama: {e}")
        return []
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return []


def format_model_info(model: Dict[str, Any]) -> str:
    """
    Форматирует информацию о модели для вывода.
    
    Args:
        model: Словарь с информацией о модели
        
    Returns:
        str: Отформатированная строка с информацией
    """
    name = model.get("name", "Неизвестно")
    size = model.get("size", 0)
    modified_at = model.get("modified_at", "")
    
    # Конвертируем размер в читаемый формат
    if size > 0:
        if size >= 1024**3:  # GB
            size_str = f"{size / (1024**3):.1f} GB"
        elif size >= 1024**2:  # MB
            size_str = f"{size / (1024**2):.1f} MB"
        else:
            size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = "Неизвестно"
    
    # Форматируем дату
    if modified_at:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(modified_at.replace('Z', '+00:00'))
            date_str = dt.strftime("%d.%m.%Y %H:%M")
        except:
            date_str = modified_at
    else:
        date_str = "Неизвестно"
    
    return f"📦 {name}\n   Размер: {size_str}\n   Изменено: {date_str}"


def main():
    """Основная функция."""
    print("🔍 Проверка загруженных моделей в Ollama...")
    print("=" * 50)
    
    # Получаем модели
    models = get_ollama_models()
    
    if not models:
        print("❌ Не удалось получить список моделей.")
        print("\n💡 Возможные причины:")
        print("   • Ollama не запущен")
        print("   • Неверный URL (по умолчанию: http://localhost:11434)")
        print("   • Проблемы с сетью")
        print("\n🔧 Для запуска Ollama выполните:")
        print("   ollama serve")
        sys.exit(1)
    
    if len(models) == 0:
        print("📭 Модели не загружены.")
        print("\n💡 Для загрузки модели выполните:")
        print("   ollama pull <название_модели>")
        print("\n📋 Популярные модели:")
        print("   • qwen2.5:7b")
        print("   • llama3.1:8b")
        print("   • mistral:7b")
        print("   • codellama:7b")
        sys.exit(0)
    
    print(f"✅ Найдено моделей: {len(models)}")
    print()
    
    # Выводим информацию о каждой модели
    for i, model in enumerate(models, 1):
        print(f"{i}. {format_model_info(model)}")
        print()
    
    # Проверяем, есть ли модель, используемая в проекте
    project_model = "qwen2.5:7b"
    model_names = [model.get("name", "") for model in models]
    
    if project_model in model_names:
        print(f"✅ Модель проекта '{project_model}' загружена и готова к использованию!")
    else:
        print(f"⚠️  Модель проекта '{project_model}' не найдена.")
        print(f"💡 Для загрузки выполните: ollama pull {project_model}")


if __name__ == "__main__":
    main()
