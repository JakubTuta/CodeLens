import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )

    # Add your settings here, for example:
    # PROJECT_NAME: str = "My WebSocket App"
    # MONGO_DB_URL: str


settings = Settings()
