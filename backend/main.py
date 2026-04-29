"""
ElectIQ — Election Process Education Assistant
FastAPI Application Entrypoint
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="ElectIQ",
    description="Election Process Education Assistant — AI-powered, gamified civic education",
    version="1.0.0"
)

# CORS middleware
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from backend.routers import chat, timeline, quiz, scenarios

app.include_router(chat.router)
app.include_router(timeline.router)
app.include_router(quiz.router)
app.include_router(scenarios.router)

# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


@app.get("/")
async def serve_index():
    """Serve the main index.html."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
async def health_check():
    """Health check for Cloud Run."""
    return {
        "status": "healthy",
        "service": "ElectIQ",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))
    }
