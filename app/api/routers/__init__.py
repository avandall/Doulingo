"""FastAPI Modular Routers."""
from app.api.routers.scenarios import router as scenarios_router
from app.api.routers.chat import router as chat_router
from app.api.routers.audio import router as audio_router
from app.api.routers.dictionary import router as dictionary_router
from app.api.routers.analytics import router as analytics_router

__all__ = [
    "scenarios_router",
    "chat_router",
    "audio_router",
    "dictionary_router",
    "analytics_router",
]
