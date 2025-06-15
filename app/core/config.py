# Centralized settings management via Pydantic ensures environment portability and cleaner configuration handling.

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Central configuration class loading variables from .env
    postgres_user: str
    postgres_password: str
    postgres_db: str
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    class Config:
        env_file = ".env"

settings = Settings()
