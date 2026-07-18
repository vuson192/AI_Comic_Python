from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ollama (story generation)
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "CognitiveComputations/dolphin-llama3.1:8b"

    # ComfyUI (image generation)
    comfyui_base_url: str = "http://localhost:8188"
    comfyui_output_dir: str = "./output"

    # Image generation defaults
    image_width: int = 1024
    image_height: int = 1024
    image_steps: int = 25
    image_cfg: float = 7.0
    checkpoint_model: str = "realvisxlV50_v50Bakedvae.safetensors"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "info"


settings = Settings()
