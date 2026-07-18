import json
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Handles communication with Ollama for story generation."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.chat_model = settings.ollama_chat_model
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def generate_story(
        self,
        concept: str,
        num_panels: int = 4,
        style: str = "realistic photo",
        language: str = "vi",
        character_description: Optional[str] = None,
    ) -> dict:
        """
        Generate a comic story script with panel descriptions and image prompts.
        Returns structured JSON with title, panels[], each with description + image_prompt.
        """
        char_note = ""
        if character_description:
            char_note = f"\nNhân vật chính: {character_description}. Luôn bao gồm mô tả này trong mỗi image_prompt để giữ nhất quán."

        system_prompt = f"""Bạn là một biên kịch truyện tranh chuyên nghiệp. 
Nhiệm vụ: tạo kịch bản truyện tranh với {num_panels} panel.
Style hình ảnh: {style}
{char_note}

QUAN TRỌNG - Trả về JSON THUẦN (không markdown, không ```):
{{
  "title": "Tên truyện",
  "panels": [
    {{
      "panel_number": 1,
      "description": "Mô tả nội dung panel bằng tiếng Việt",
      "image_prompt": "Detailed English prompt for image generation, include style: {style}, include character details, scene, lighting, composition",
      "dialogue": "Lời thoại nếu có, hoặc null"
    }}
  ]
}}

Quy tắc cho image_prompt:
- Viết bằng tiếng Anh
- Chi tiết: nhân vật, hành động, bối cảnh, ánh sáng, góc camera
- Luôn bao gồm style "{style}" trong mỗi prompt
- Nếu có nhân vật chính, mô tả ngoại hình nhất quán giữa các panel
- Thêm các từ khóa chất lượng: masterpiece, best quality, ultra detailed"""

        user_message = f"Tạo kịch bản truyện tranh {num_panels} panel về: {concept}"

        logger.info("Generating story script for: %s (%d panels)", concept, num_panels)

        response = await self._client.post(
            "/api/chat",
            json={
                "model": self.chat_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {"temperature": 0.8},
                "format": "json",
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["message"]["content"]

        # Parse JSON response
        try:
            story = json.loads(content)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON: %s", content[:200])
            # Fallback: try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                story = json.loads(json_match.group())
            else:
                raise ValueError("LLM did not return valid JSON")

        return story

    async def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Simple chat with Ollama (for general use)."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        response = await self._client.post(
            "/api/chat",
            json={
                "model": self.chat_model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.7},
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    async def close(self):
        await self._client.aclose()
