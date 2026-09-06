"""
Main FastAPI Application for Duolingo Speak
Follows Clean Architecture with decoupled APIRouters, Domain Services, and Persistence Adapters.
"""

import logging
import os

import inngest.fast_api
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import (
    analytics_router,
    audio_router,
    chat_router,
    dictionary_router,
    feedback_router,
    jobs_router,
    reports_router,
    scenarios_router,
)
from app.services.background_job_service import (
    cleanup_audio_cache_job,
    evaluate_speaking_exam,
    inngest_client,
)

logger = logging.getLogger("haku_hakus.api")

app = FastAPI(
    title="Haku Haku's - Unlimited AI Roleplays",
    description="Adaptive AI-driven IELTS Speaking and Conversation practice platform.",
    version="1.0.0",
)

# Enable CORS for universal frontend access (web, mobile PWA, Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include Presentation Layer Routers
app.include_router(scenarios_router)
app.include_router(chat_router)
app.include_router(audio_router)
app.include_router(dictionary_router)
app.include_router(analytics_router)
app.include_router(feedback_router)
app.include_router(reports_router)
app.include_router(jobs_router)

# Mount Inngest Background Job Endpoint at /api/inngest
inngest.fast_api.serve(app, inngest_client, [evaluate_speaking_exam, cleanup_audio_cache_job])


@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint for Render, uptime monitors, and keep-alive pings."""
    print("[Keep-Alive] Periodic ping received from GitHub Actions!", flush=True)
    return {"status": "ok", "app": "Haku Haku's", "version": "1.0.0"}

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
    return {"message": "Haku Haku's API Server Running"}


LLMS_TXT_CONTENT = """# Haku Haku's — AI English Speaking & IELTS Assessment Platform

> Haku Haku's is an interactive English conversational practice platform featuring AI roleplays, real-time voice synthesis, and official IELTS & CEFR speaking test evaluations.

## Core Capabilities
- **Interactive AI Roleplay**: Practice everyday, academic, and professional conversation topics with expressive AI voice partners.
- **IELTS & CEFR Exam Simulator**: Full speaking mock exams with turn-by-turn transcription, pronunciation diagnosis, acoustic fluency metrics (WPM, pause count), and CEFR scoring.
- **Official A4 PDF Reporting**: Instant generation of multi-page printable speaking scorecards with subscores and dialogue logs.
- **Vocabulary Book & Flashcards**: Contextual word saving, CEFR difficulty levels, and spaced-repetition flashcard practice.

## API & Endpoints
- [API Documentation](https://haku-hakus.onrender.com/docs): Interactive OpenAPI Swagger documentation.
- [Speaking Scenarios](https://haku-hakus.onrender.com/api/scenarios): Explore speaking practice topics and IELTS categories.
- [Speaking Reports](https://haku-hakus.onrender.com/api/reports/speaking): Generate and retrieve printable scorecards.
- [Health Check](https://haku-hakus.onrender.com/health): Service uptime and health status.
"""

ROBOTS_TXT_CONTENT = """User-agent: *
Allow: /

Sitemap: https://haku-hakus.onrender.com/
# LLMs and AI Agents Discovery
# llms.txt: https://haku-hakus.onrender.com/llms.txt
"""


@app.get("/robots.txt", response_class=PlainTextResponse)
def read_robots_txt():
    """Serve robots.txt for search engines & AI crawlers with instant in-memory cache."""
    return PlainTextResponse(
        content=ROBOTS_TXT_CONTENT,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400, s-maxage=86400"},
    )


@app.get("/llms.txt", response_class=PlainTextResponse)
@app.get("/.well-known/llms.txt", response_class=PlainTextResponse)
def read_llms_txt():
    """Serve standard llms.txt for AI agents and agentic web browsing with instant in-memory cache."""
    return PlainTextResponse(
        content=LLMS_TXT_CONTENT,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400, s-maxage=86400"},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)  # nosec B104
