import logging
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_comfyui
from app.models.schemas import GenerateImageRequest, GenerateImageResponse
from app.services.comfyui_service import ComfyUIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generate", tags=["Image Generation"])


@router.post("", response_model=GenerateImageResponse)
async def generate_image(
    request: GenerateImageRequest,
    comfyui: ComfyUIService = Depends(get_comfyui),
):
    """
    Generate a single image using ComfyUI + RealVisXL.
    Provide a detailed prompt for best results.
    """
    # Check ComfyUI is available
    is_healthy = await comfyui.health_check()
    if not is_healthy:
        raise HTTPException(
            status_code=503,
            detail="ComfyUI is not running. Start ComfyUI first (port 8188).",
        )

    logger.info("Generating image: '%s'", request.prompt[:80])

    try:
        result = await comfyui.generate_image(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            steps=request.steps,
            cfg_scale=request.cfg_scale,
            seed=request.seed,
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Image generation timed out")
    except Exception as e:
        logger.error("Image generation failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    return GenerateImageResponse(**result)
