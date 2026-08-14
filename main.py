"""
Root entry point for Duolingo Speak
Exposes 'app' from app.main for Render / Uvicorn compatibility.
"""

import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    reload_flag = os.getenv("ENV", "development").lower() != "production"
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload_flag)  # nosec B104
