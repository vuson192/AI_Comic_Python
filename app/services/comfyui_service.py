import json
import logging
import os
import uuid
import asyncio
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ComfyUIService:
    """Handles communication with ComfyUI API for image generation."""

    def __init__(self):
        self.base_url = settings.comfyui_base_url
        self.output_dir = settings.comfyui_output_dir
        self.checkpoint = settings.checkpoint_model
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=300.0)

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "ugly, blurry, low quality, deformed, disfigured, bad anatomy, watermark, text",
        width: int = 1024,
        height: int = 1024,
        steps: int = 25,
        cfg_scale: float = 7.0,
        seed: int = -1,
    ) -> dict:
        """
        Generate an image using ComfyUI API.
        Returns dict with image_path, seed, etc.
        """
        if seed == -1:
            seed = int.from_bytes(os.urandom(4), "big") % (2**32)

        # Build ComfyUI workflow (API format)
        workflow = self._build_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            seed=seed,
        )

        client_id = str(uuid.uuid4())
        logger.info("Submitting image generation job (seed=%d)", seed)

        # Queue the prompt
        response = await self._client.post(
            "/prompt",
            json={"prompt": workflow, "client_id": client_id},
        )
        if response.status_code != 200:
            error_detail = response.text
            logger.error("ComfyUI rejected workflow: %s", error_detail)
            raise RuntimeError(f"ComfyUI error: {error_detail}")

        result = response.json()
        prompt_id = result["prompt_id"]

        logger.info("Job queued: prompt_id=%s", prompt_id)

        # Poll for completion
        image_path = await self._wait_and_download(prompt_id)

        return {
            "image_path": image_path,
            "prompt": prompt,
            "seed": seed,
            "width": width,
            "height": height,
        }

    async def _wait_and_download(self, prompt_id: str, timeout: int = 300) -> str:
        """Poll ComfyUI history until the image is ready, then download it."""
        elapsed = 0
        poll_interval = 2

        while elapsed < timeout:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            response = await self._client.get(f"/history/{prompt_id}")
            if response.status_code != 200:
                continue

            history = response.json()
            if prompt_id not in history:
                continue

            job = history[prompt_id]
            if "outputs" not in job:
                continue

            # Find the output image
            for node_id, node_output in job["outputs"].items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        filename = img["filename"]
                        subfolder = img.get("subfolder", "")
                        img_type = img.get("type", "output")

                        # Download the image
                        img_response = await self._client.get(
                            "/view",
                            params={
                                "filename": filename,
                                "subfolder": subfolder,
                                "type": img_type,
                            },
                        )
                        img_response.raise_for_status()

                        # Save to local output dir
                        local_filename = f"{prompt_id}_{filename}"
                        local_path = os.path.join(self.output_dir, local_filename)
                        with open(local_path, "wb") as f:
                            f.write(img_response.content)

                        logger.info("Image saved: %s", local_path)
                        return local_path

        raise TimeoutError(f"Image generation timed out after {timeout}s")

    def _build_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        cfg_scale: float,
        seed: int,
    ) -> dict:
        """
        Build a ComfyUI workflow (API format) for txt2img with RealVisXL.
        This is a standard SDXL workflow.
        """
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": self.checkpoint,
                },
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1,
                },
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": prompt,
                    "clip": ["4", 1],
                },
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["4", 1],
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2],
                },
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "comic_panel",
                    "images": ["8", 0],
                },
            },
        }

    async def health_check(self) -> bool:
        """Check if ComfyUI is running."""
        try:
            response = await self._client.get("/system_stats")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        await self._client.aclose()
