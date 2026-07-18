import logging
from fastapi import APIRouter, Depends

from app.dependencies import get_ollama
from app.models.schemas import StoryRequest, StoryResponse, Panel
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/story", tags=["Story"])


@router.post("", response_model=StoryResponse)
async def generate_story(
    request: StoryRequest,
    ollama: OllamaService = Depends(get_ollama),
):
    """
    Generate a comic story script using LLM.
    Returns structured panels with descriptions and image prompts.
    """
    logger.info("Generating story: '%s' (%d panels)", request.concept, request.num_panels)

    story = await ollama.generate_story(
        concept=request.concept,
        num_panels=request.num_panels,
        style=request.style,
        language=request.language,
    )

    panels = [
        Panel(
            panel_number=p.get("panel_number", i + 1),
            description=p.get("description", ""),
            image_prompt=p.get("image_prompt", ""),
            dialogue=p.get("dialogue"),
        )
        for i, p in enumerate(story.get("panels", []))
    ]

    return StoryResponse(
        title=story.get("title", "Untitled"),
        panels=panels,
        concept=request.concept,
    )
