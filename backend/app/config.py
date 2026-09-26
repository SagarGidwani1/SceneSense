from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_PATH = BASE_DIR / "storage"


class Settings(BaseSettings):
    groq_api_key: str = ""
    asr_model: str = "whisper-large-v3"
    asr_language: str = "bn"
    groq_llm_model: str = "openai/gpt-oss-120b"

    gemini_api_key: str = ""
    # Comma-separated: tried in order until one answers (models get retired / rate-limited).
    gemini_model: str = "gemini-3.8-flash,gemini-3.5-flash,gemini-3.1-flash-lite"

    # Absolute base used inside the VMAP so external players can resolve media.
    public_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR.parent / ".env", BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def gemini_models(self) -> list[str]:
        return [m.strip() for m in self.gemini_model.split(",") if m.strip()]


settings = Settings()

for sub in ("uploads", "audio", "scenes", "ads", "debug"):
    (STORAGE_PATH / sub).mkdir(parents=True, exist_ok=True)
