"""Health check endpoint для мониторинга состояния приложения."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from aiohttp import web, ClientSession
from aiohttp.web import Request, Response

from app.core.config import settings
from app.core.database import get_db_session


class HealthChecker:
    """Класс для проверки состояния различных компонентов системы."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def check_database(self) -> Dict[str, Any]:
        """Проверка состояния базы данных."""
        try:
            async with get_db_session() as session:
                # Простой запрос для проверки подключения
                result = await session.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "message": "Database connection successful"
                }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
    
    async def check_llm_provider(self) -> Dict[str, Any]:
        """Проверка состояния LLM провайдера."""
        try:
            if settings.llm_provider == "ollama":
                return await self._check_ollama()
            elif settings.llm_provider == "openrouter":
                return await self._check_openrouter()
            elif settings.llm_provider == "lmstudio":
                return await self._check_lmstudio()
            else:
                return {
                    "status": "unknown",
                    "message": f"Unknown LLM provider: {settings.llm_provider}"
                }
        except Exception as e:
            self.logger.error(f"LLM provider health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"LLM provider check failed: {str(e)}"
            }
    
    async def _check_ollama(self) -> Dict[str, Any]:
        """Проверка Ollama."""
        try:
            async with ClientSession() as session:
                async with session.get(
                    f"{settings.ollama_base_url}/api/tags",
                    timeout=5
                ) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "Ollama is accessible"
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "message": f"Ollama returned status {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Ollama connection failed: {str(e)}"
            }
    
    async def _check_openrouter(self) -> Dict[str, Any]:
        """Проверка OpenRouter."""
        if not settings.openrouter_api_key:
            return {
                "status": "unhealthy",
                "message": "OpenRouter API key not configured"
            }
        
        try:
            async with ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json"
                }
                async with session.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "OpenRouter is accessible"
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "message": f"OpenRouter returned status {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"OpenRouter connection failed: {str(e)}"
            }
    
    async def _check_lmstudio(self) -> Dict[str, Any]:
        """Проверка LM Studio."""
        try:
            async with ClientSession() as session:
                async with session.get(
                    f"{settings.lmstudio_base_url}/v1/models",
                    timeout=5
                ) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "LM Studio is accessible"
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "message": f"LM Studio returned status {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"LM Studio connection failed: {str(e)}"
            }
    
    async def check_vision_provider(self) -> Dict[str, Any]:
        """Проверка Vision провайдера."""
        if settings.vision_provider == "openrouter":
            return await self._check_openrouter()
        elif settings.vision_provider == "ollama":
            return await self._check_ollama()
        else:
            return {
                "status": "unknown",
                "message": f"Unknown vision provider: {settings.vision_provider}"
            }
    
    async def check_speech_provider(self) -> Dict[str, Any]:
        """Проверка Speech провайдера."""
        if settings.speech_provider == "whisperapi":
            if not settings.whisperapi_api_key:
                return {
                    "status": "unhealthy",
                    "message": "WhisperAPI key not configured"
                }
            return {
                "status": "healthy",
                "message": "WhisperAPI key configured"
            }
        elif settings.speech_provider == "whisper":
            if not settings.openai_api_key:
                return {
                    "status": "unhealthy",
                    "message": "OpenAI API key not configured for Whisper"
                }
            return {
                "status": "healthy",
                "message": "OpenAI API key configured for Whisper"
            }
        else:
            return {
                "status": "unknown",
                "message": f"Unknown speech provider: {settings.speech_provider}"
            }


# Глобальный экземпляр health checker
health_checker = HealthChecker()


async def health_check_handler(request: Request) -> Response:
    """Обработчик health check endpoint."""
    try:
        # Выполняем все проверки параллельно
        checks = await asyncio.gather(
            health_checker.check_database(),
            health_checker.check_llm_provider(),
            health_checker.check_vision_provider(),
            health_checker.check_speech_provider(),
            return_exceptions=True
        )
        
        # Обрабатываем результаты
        database_check, llm_check, vision_check, speech_check = checks
        
        # Определяем общий статус
        all_healthy = all(
            check.get("status") == "healthy" 
            for check in [database_check, llm_check, vision_check, speech_check]
            if isinstance(check, dict)
        )
        
        overall_status = "healthy" if all_healthy else "unhealthy"
        
        # Формируем ответ
        response_data = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "checks": {
                "database": database_check if isinstance(database_check, dict) else {"status": "error", "message": str(database_check)},
                "llm_provider": llm_check if isinstance(llm_check, dict) else {"status": "error", "message": str(llm_check)},
                "vision_provider": vision_check if isinstance(vision_check, dict) else {"status": "error", "message": str(vision_check)},
                "speech_provider": speech_check if isinstance(speech_check, dict) else {"status": "error", "message": str(speech_check)}
            },
            "configuration": {
                "llm_provider": settings.llm_provider,
                "text_model": settings.text_model,
                "vision_provider": settings.vision_provider,
                "vision_model": settings.vision_model,
                "speech_provider": settings.speech_provider,
                "speech_model": settings.speech_model
            }
        }
        
        status_code = 200 if overall_status == "healthy" else 503
        
        return web.json_response(response_data, status=status_code)
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return web.json_response(
            {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Health check failed: {str(e)}"
            },
            status=500
        )


async def simple_health_handler(request: Request) -> Response:
    """Простой health check для Docker."""
    return web.json_response({"status": "ok"}, status=200)


def create_health_app() -> web.Application:
    """Создание приложения для health check."""
    app = web.Application()
    app.router.add_get("/health", health_check_handler)
    app.router.add_get("/health/simple", simple_health_handler)
    return app
