from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Stock Analysis Agent")
    env: str = Field(default="dev")
    tool_mode: str = Field(default="mock")
    news_api_key: Optional[str] = Field(default=None)
    finnhub_api_key: Optional[str] = Field(default=None)
    max_iterations: int = Field(default=3)
    rag_top_k: int = Field(default=3)
    context_char_budget: int = Field(default=2400)
    rag_chunk_size: int = Field(default=500)
    rag_chunk_overlap: int = Field(default=80)

    model_config = SettingsConfigDict(
        env_prefix="STOCK_AGENT_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
