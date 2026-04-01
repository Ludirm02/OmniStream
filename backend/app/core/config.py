from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OMNISTREAM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    db_url: str = "sqlite:///./omnistream.db"
    frontend_origin: str = "http://localhost:3000"
    seed_on_start: bool = True
    embedding_dim: int = 192


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
