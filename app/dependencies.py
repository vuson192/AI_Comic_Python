"""
Dependency injection for FastAPI routes.
Services are created once at startup and shared across requests.
"""
from app.services.ollama_service import OllamaService
from app.services.comfyui_service import ComfyUIService
from app.services.pdf_service import PDFService
from app.config import settings

# Singletons – initialized in main.py lifespan
_ollama: OllamaService | None = None
_comfyui: ComfyUIService | None = None
_pdf: PDFService | None = None


def init_services():
    global _ollama, _comfyui, _pdf
    _ollama = OllamaService()
    _comfyui = ComfyUIService()
    _pdf = PDFService(output_dir=settings.comfyui_output_dir)


async def shutdown_services():
    if _ollama:
        await _ollama.close()
    if _comfyui:
        await _comfyui.close()


def get_ollama() -> OllamaService:
    return _ollama


def get_comfyui() -> ComfyUIService:
    return _comfyui


def get_pdf() -> PDFService:
    return _pdf
