"""Внешние API клиенты."""

from typing import Optional
from app.core.config import settings
from app.clients.base_client import BaseLLMClient
from app.clients.llm_client import OpenRouterLLMClient
from app.clients.lmstudio_client import LMStudioLLMClient
from app.clients.ollama_client import OllamaLLMClient


def create_llm_client() -> Optional[BaseLLMClient]:
    """
    Создает клиент LLM в зависимости от настроек.
    
    Returns:
        BaseLLMClient: Клиент для работы с LLM или None если провайдер не поддерживается
    """
    provider = settings.llm_provider.lower()
    
    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY не установлен для провайдера OpenRouter")
        return OpenRouterLLMClient(
            api_key=settings.openrouter_api_key,
            model=settings.text_model
        )
    
    elif provider == "lmstudio":
        return LMStudioLLMClient(
            base_url=settings.lmstudio_base_url,
            model=settings.text_model
        )
    
    elif provider == "ollama":
        client = OllamaLLMClient(
            base_url=settings.ollama_base_url,
            model=settings.text_model,
            auto_pull=settings.ollama_auto_pull,
            timeout_sec=settings.ollama_timeout_sec,
            num_predict=settings.ollama_num_predict,
            temperature=settings.ollama_temperature
        )
        
        # Проверяем доступность и при необходимости скачиваем модель
        if not client.is_available():
            if settings.ollama_auto_pull:
                print(f"Модель {settings.text_model} не найдена. Начинаем скачивание...")
                if client.pull_model():
                    print(f"Модель {settings.text_model} успешно скачана")
                else:
                    print(f"Ошибка при скачивании модели {settings.text_model}")
                    return None
            else:
                print(f"Модель {settings.text_model} не найдена. Установите модель вручную или включите OLLAMA_AUTO_PULL=true")
                return None
        
        return client
    
    else:
        raise ValueError(f"Неподдерживаемый провайдер LLM: {provider}")


__all__ = [
    "BaseLLMClient",
    "OpenRouterLLMClient", 
    "LMStudioLLMClient",
    "OllamaLLMClient",
    "create_llm_client"
]