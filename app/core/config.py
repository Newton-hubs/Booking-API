from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost:5432/fitness_studio"
    secret_key: str = "changeme-use-a-real-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    timezone: str = "Asia/Kolkata"
    app_env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
