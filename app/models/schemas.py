from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ─── Story Schemas ────────────────────────────────────────────────────────────

class StoryRequest(BaseModel):
    """Request to generate a comic story script."""
    concept: str = Field(..., description="Ý tưởng truyện (vd: '2 ninja đánh nhau trong mưa')")
    num_panels: int = Field(default=4, ge=1, le=12, description="Số panel/khung hình")
    style: str = Field(default="realistic photo", description="Art style (realistic photo, anime, manga...)")
    language: str = Field(default="vi", description="Ngôn ngữ output (vi/en)")


class Panel(BaseModel):
    """A single panel in the comic."""
    panel_number: int
    description: str = Field(description="Mô tả nội dung panel (tiếng Việt)")
    image_prompt: str = Field(description="Prompt tiếng Anh cho image generation")
    dialogue: Optional[str] = Field(default=None, description="Lời thoại nhân vật (nếu có)")


class StoryResponse(BaseModel):
    """Generated story script with panels."""
    title: str
    panels: list[Panel]
    concept: str


# ─── Image Generation Schemas ─────────────────────────────────────────────────

class GenerateImageRequest(BaseModel):
    """Request to generate a single image via ComfyUI."""
    prompt: str = Field(..., description="Positive prompt mô tả ảnh")
    negative_prompt: str = Field(
        default="ugly, blurry, low quality, deformed, disfigured, bad anatomy, watermark, text",
        description="Negative prompt (những gì không muốn có)"
    )
    width: int = Field(default=1024, ge=512, le=2048)
    height: int = Field(default=1024, ge=512, le=2048)
    steps: int = Field(default=25, ge=10, le=50)
    cfg_scale: float = Field(default=7.0, ge=1.0, le=20.0)
    seed: int = Field(default=-1, description="-1 = random seed")


class GenerateImageResponse(BaseModel):
    """Response with generated image info."""
    image_path: str
    prompt: str
    seed: int
    width: int
    height: int


# ─── Comic Generation (Combo) ────────────────────────────────────────────────

class ComicRequest(BaseModel):
    """Full comic generation: story + images."""
    concept: str = Field(..., description="Ý tưởng truyện")
    num_panels: int = Field(default=4, ge=1, le=12)
    style: str = Field(default="realistic photo, cinematic lighting, detailed skin texture")
    character_description: Optional[str] = Field(
        default=None,
        description="Mô tả nhân vật chính để giữ nhất quán (vd: 'young man, short black hair, scar on left cheek')"
    )
    negative_prompt: str = Field(
        default="ugly, blurry, low quality, deformed, disfigured, bad anatomy, watermark, text, cartoon, anime",
        description="Negative prompt chung cho tất cả panels"
    )


class ComicPanel(BaseModel):
    """A panel with both story and image."""
    panel_number: int
    description: str
    dialogue: Optional[str] = None
    image_prompt: str
    image_path: Optional[str] = None
    status: str = Field(default="pending", description="pending/generating/done/failed")


class ComicResponse(BaseModel):
    """Full comic with story and images."""
    title: str
    concept: str
    panels: list[ComicPanel]
    output_dir: str
    pdf_path: Optional[str] = None
