#!/usr/bin/env python3
"""
Скрипт для проверки статуса LM Studio.
"""

import requests
import json

def check_lm_studio():
    """Проверяет статус LM Studio сервера."""
    print("=== Проверка LM Studio ===")
    
    # Проверяем доступность сервера
    try:
        response = requests.get('http://localhost:1234/v1/models', timeout=5)
        if response.status_code == 200:
            models = response.json()
            print("✅ LM Studio сервер работает")
            print("📋 Доступные модели:")
            for model in models.get('data', []):
                print(f"  - {model['id']}")
        else:
            print(f"❌ LM Studio сервер недоступен: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к LM Studio")
        print("💡 Убедитесь, что LM Studio запущен и сервер работает на порту 1234")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    # Тестируем простой запрос
    try:
        print("\n=== Тест простого запроса ===")
        response = requests.post('http://localhost:1234/v1/chat/completions',
            json={
                'model': 'openai/gpt-oss-20b',
                'messages': [
                    {'role': 'user', 'content': 'Привет! Ответь одним словом: "работает"'}
                ],
                'temperature': 0,
                'max_tokens': 10
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                print(f"✅ LM Studio отвечает: {content}")
                return True
            else:
                print("❌ LM Studio вернул пустой ответ")
                return False
        else:
            print(f"❌ Ошибка запроса: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса - LM Studio не отвечает")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестового запроса: {e}")
        return False

if __name__ == "__main__":
    if check_lm_studio():
        print("\n🎉 LM Studio настроен правильно!")
    else:
        print("\n🔧 Требуется настройка LM Studio:")
        print("1. Откройте LM Studio")
        print("2. Перейдите на вкладку 'Local Server'")
        print("3. Выберите модель openai/gpt-oss-20b")
        print("4. Нажмите 'Start Server'")
        print("5. Убедитесь, что сервер работает на порту 1234")
