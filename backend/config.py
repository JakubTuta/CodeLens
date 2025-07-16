from functools import lru_cache
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    PROJECT_NAME: str = "My WebSocket App"
    ANTHROPIC_API_KEY: str = ""


@lru_cache
def get_settings():
    return Settings()
