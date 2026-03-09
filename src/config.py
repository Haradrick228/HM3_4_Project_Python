from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/urlshortener"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    CACHE_TTL: int = 3600  # 1 hour

    # JWT
    # ВАЖНО: Для прода надо установить случайный SECRET_KEY в .env файле
    SECRET_KEY: str = "dev-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # App
    APP_NAME: str = "URL Shortener"
    SHORT_CODE_LENGTH: int = 6
    UNUSED_LINK_DAYS: int = 30  

    class Config:
        env_file = ".env"

settings = Settings()
