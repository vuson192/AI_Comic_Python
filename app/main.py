import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.dependencies import init_services, shutdown_services
from app.routers import story_router, image_router, comic_router, chat_router

logging.basicConfig(
    level=getattr(logging, settings.app_log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, clean up on shutdown."""
    logger.info("Starting Comic Generator Service...")
    init_services()
    yield
    logger.info("Shutting down Comic Generator Service...")
    await shutdown_services()


app = FastAPI(
    title="Comic Generator API",
    description=(
        "AI-powered comic/manga generator\n\n"
        "- **Story**: LLM generates story script with panel descriptions\n"
        "- **Image**: ComfyUI + RealVisXL generates realistic images\n"
        "- **Comic**: Full pipeline - story + images combined\n\n"
        "Architecture: **this service** → Ollama (story) + ComfyUI (images)"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount output directory for serving generated images
import os
os.makedirs(settings.comfyui_output_dir, exist_ok=True)
app.mount("/output", StaticFiles(directory=settings.comfyui_output_dir), name="output")

# Register routers
app.include_router(story_router.router, prefix="/api")
app.include_router(image_router.router, prefix="/api")
app.include_router(comic_router.router, prefix="/api")
app.include_router(chat_router.router, prefix="/api")


@app.get("/health", tags=["Health"])
async def health():
    from app.dependencies import get_comfyui
    comfyui = get_comfyui()
    comfyui_ok = await comfyui.health_check() if comfyui else False

    return {
        "status": "ok",
        "ollama": f"{settings.ollama_base_url} (model: {settings.ollama_chat_model})",
        "comfyui": f"{settings.comfyui_base_url} ({'connected' if comfyui_ok else 'not available'})",
        "checkpoint": settings.checkpoint_model,
        "output_dir": os.path.abspath(settings.comfyui_output_dir),
    }
