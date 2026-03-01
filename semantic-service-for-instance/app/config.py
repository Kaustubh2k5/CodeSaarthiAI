from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central configuration for semantic semantic-service.
    Reads automatically from environment variables or .env.
    """

    # =====================================================
    # LLM MODEL CONFIG (LOCAL INFERENCE)
    # =====================================================

    # HuggingFace model name OR local path
    LLM_MODEL_NAME: str = "deepseek-ai/deepseek-coder-6.7b-instruct"

    # generation stability
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 120

    # vLLM runtime controls
    LLM_DTYPE: str = "auto"          # auto | float16 | bfloat16
    LLM_GPU_MEMORY_UTILIZATION: float = 0.9
    LLM_TRUST_REMOTE_CODE: bool = True

    # =====================================================
    # WORKER / QUEUE CONFIG
    # =====================================================

    # keep 1 initially (GPU inference prefers batching over concurrency)
    WORKER_CONCURRENCY: int = 1
    QUEUE_MAX_SIZE: int = 10000

    # future batching support (VERY useful later)
    LLM_BATCH_SIZE: int = 1

    # =====================================================
    # CONTEXT BUILDING
    # =====================================================

    MAX_IMPORTS: int = 5
    MAX_CALLS: int = 5

    # =====================================================
    # CACHE SETTINGS
    # =====================================================

    CACHE_ENABLED: bool = True
    CACHE_PATH: str = "./.semantic_cache.json"

    # =====================================================
    # API SETTINGS
    # =====================================================

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # =====================================================
    # LOGGING (you'll want this soon)
    # =====================================================

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# ---------------------------------------------------------
# Singleton Settings Object
# ---------------------------------------------------------
@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()