from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CACHE_TTL_SECONDS: int = 300
    REQUEST_TIMEOUT_SECONDS: float = 5.0
    MAX_CONCURRENT_REQUESTS: int = 5
    RATE_LIMIT_STRING: str = "30/minute"

    class Config:
        env_file = ".env"

settings = Settings()