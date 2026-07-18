import logging
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.dependencies import get_ollama, get_comfyui, get_pdf
from app.models.schemas import ComicRequest, ComicResponse, ComicPanel
from app.services.ollama_service import OllamaService
from app.services.comfyui_service import ComfyUIService
from app.services.pdf_service import PDFService
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/comic", tags=["Comic Generation"])


@router.post("", response_model=ComicResponse)
async def generate_comic(
    request: ComicRequest,
    ollama: OllamaService = Depends(get_ollama),
    comfyui: ComfyUIService = Depends(get_comfyui),
    pdf: PDFService = Depends(get_pdf),
):
    """
    Full comic generation pipeline:
    1. LLM generates story script with image prompts
    2. ComfyUI generates images for each panel
    3. Generate PDF with story + images
    Returns the complete comic with story + image paths + PDF.
    """
    # Check ComfyUI availability
    comfyui_available = await comfyui.health_check()
    if not comfyui_available:
        raise HTTPException(
            status_code=503,
            detail="ComfyUI is not running. Start ComfyUI first (port 8188).",
        )

    logger.info("=== Generating comic: '%s' (%d panels) ===", request.concept, request.num_panels)

    # Step 1: Generate story script
    logger.info("Step 1: Generating story script...")
    story = await ollama.generate_story(
        concept=request.concept,
        num_panels=request.num_panels,
        style=request.style,
        character_description=request.character_description,
    )

    title = story.get("title", "Untitled")
    raw_panels = story.get("panels", [])

    # Step 2: Generate images for each panel
    logger.info("Step 2: Generating images for %d panels...", len(raw_panels))
    comic_panels = []

    for i, panel_data in enumerate(raw_panels):
        panel_num = panel_data.get("panel_number", i + 1)
        image_prompt = panel_data.get("image_prompt", "")

        # Append character description to keep consistency
        if request.character_description and request.character_description not in image_prompt:
            image_prompt = f"{image_prompt}, {request.character_description}"

        comic_panel = ComicPanel(
            panel_number=panel_num,
            description=panel_data.get("description", ""),
            dialogue=panel_data.get("dialogue"),
            image_prompt=image_prompt,
            status="generating",
        )

        try:
            logger.info("Generating panel %d/%d...", panel_num, len(raw_panels))
            result = await comfyui.generate_image(
                prompt=image_prompt,
                negative_prompt=request.negative_prompt,
                width=settings.image_width,
                height=settings.image_height,
                steps=settings.image_steps,
                cfg_scale=settings.image_cfg,
            )
            comic_panel.image_path = result["image_path"]
            comic_panel.status = "done"
            logger.info("Panel %d done: %s", panel_num, result["image_path"])

        except Exception as e:
            logger.error("Panel %d failed: %s", panel_num, str(e))
            comic_panel.status = "failed"

        comic_panels.append(comic_panel)

    # Step 3: Generate PDF
    logger.info("Step 3: Generating PDF...")
    pdf_panels = [
        {
            "panel_number": p.panel_number,
            "description": p.description,
            "dialogue": p.dialogue,
            "image_path": p.image_path,
        }
        for p in comic_panels
    ]
    pdf_path = pdf.generate_comic_pdf(title=title, panels=pdf_panels)

    logger.info("=== Comic complete: %s (PDF: %s) ===", title, pdf_path)

    return ComicResponse(
        title=title,
        concept=request.concept,
        panels=comic_panels,
        output_dir=os.path.abspath(settings.comfyui_output_dir),
        pdf_path=pdf_path,
    )


@router.post("/story-only", response_model=ComicResponse)
async def generate_story_only(
    request: ComicRequest,
    ollama: OllamaService = Depends(get_ollama),
):
    """
    Generate story script only (no images).
    Useful for previewing the story before generating images.
    Does NOT require ComfyUI to be running.
    """
    logger.info("Generating story only: '%s' (%d panels)", request.concept, request.num_panels)

    story = await ollama.generate_story(
        concept=request.concept,
        num_panels=request.num_panels,
        style=request.style,
        character_description=request.character_description,
    )

    panels = [
        ComicPanel(
            panel_number=p.get("panel_number", i + 1),
            description=p.get("description", ""),
            dialogue=p.get("dialogue"),
            image_prompt=p.get("image_prompt", ""),
            status="pending",
        )
        for i, p in enumerate(story.get("panels", []))
    ]

    return ComicResponse(
        title=story.get("title", "Untitled"),
        concept=request.concept,
        panels=panels,
        output_dir=os.path.abspath(settings.comfyui_output_dir),
    )


@router.get("/download/{filename}")
async def download_pdf(filename: str):
    """Download a generated PDF file."""
    file_path = os.path.join(settings.comfyui_output_dir, filename)
    if not os.path.exists(file_path) or not filename.endswith(".pdf"):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)
