from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./orchestrator.db"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct"
    OLLAMA_TIMEOUT: int = 120
    CORS_ORIGINS: str = "http://localhost:5173"
    MAX_WORKERS: int = 1
    TIMEOUT_SECONDS: int = 300
    MAX_RETRIES: int = 2
    EXECUTOR_MAX_ITERATIONS: int = 10
    PLANNER_MAX_ITERATIONS: int = 3
    REVIEWER_MAX_ITERATIONS: int = 3

    class Config:
        env_file = ".env"


settings = Settings()
