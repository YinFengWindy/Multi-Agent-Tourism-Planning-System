from functools import lru_cache
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    api_title: str = "Multi-Agent Tourism Planning System"
    planner_service_url: str = Field(
        default_factory=lambda: os.getenv("PLANNER_SERVICE_URL", "http://localhost:8001")
    )
    agent_workers_url: str = Field(
        default_factory=lambda: os.getenv("AGENT_WORKERS_URL", "http://localhost:8003")
    )
    mcp_gateway_url: str = Field(
        default_factory=lambda: os.getenv("MCP_GATEWAY_URL", "http://localhost:8002")
    )
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", ""))
    mongodb_uri: str = Field(default_factory=lambda: os.getenv("MONGODB_URI", ""))
    mongodb_db: str = Field(default_factory=lambda: os.getenv("MONGODB_DB", "tourism_planner"))
    rate_limit_per_minute: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
            if origin.strip()
        ]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

