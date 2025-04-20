from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from loguru import logger

class Settings(BaseSettings):
    """Pydantic settings for the application.
    """
    model_config : SettingsConfigDict = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8"
    )

    # Notion settings
    NOTION_API_KEY : str | None = Field(
        default=None,
        env="NOTION_API_KEY",
        description="Notion API key for authentication."
    )


try:
    settings = Settings()
except Exception as e:
    logger.error(f"Error loading settings: {e}")
    raise SystemExit(e) 