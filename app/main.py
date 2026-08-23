"""
Main FastAPI Application for Duolingo Speak
Follows Clean Architecture with decoupled APIRouters, Domain Services, and Persistence Adapters.
"""

import logging
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import (
    analytics_router,
    audio_router,
    chat_router,
    dictionary_router,
    scenarios_router,
)

logger = logging.getLogger("duolingo_speak.api")

app = FastAPI(
    title="Duolingo Speak - Unlimited AI Roleplays",
    description="Adaptive AI-driven IELTS Speaking and Conversation practice platform.",
    version="1.0.0",
)

# Include Presentation Layer Routers
app.include_router(scenarios_router)
app.include_router(chat_router)
app.include_router(audio_router)
app.include_router(dictionary_router)
app.include_router(analytics_router)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def read_root():
    """Serves the main single-page web app."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {"message": "Duolingo Speak API Server Running"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)  # nosec B104
