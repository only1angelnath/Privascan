from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    secret_key: str = "change_me"
    log_level: str = "INFO"

    # Cache TTLs (seconds)
    score_cache_ttl_curated: int = 21600
    score_cache_ttl_community: int = 86400
    score_cache_ttl_dune: int = 172800

    # Database
    database_url: str = "postgresql+asyncpg://privascan:privascan@localhost:5432/privascan"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = ""
    celery_result_backend: str = "redis://localhost:6379/1"

    # External APIs
    etherscan_api_key: str = ""
    alchemy_api_key: str = ""
    dune_api_key: str = ""
    coingecko_api_key: str = ""

    # Telegram
    telegram_bot_token: str = ""

    # Admin
    admin_api_key: str = "change_me"

    # Rate limits (requests/hour)
    rate_limit_anonymous: int = 10
    rate_limit_free: int = 500
    rate_limit_pro: int = 1000

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if v == "change_me":
            import warnings
            warnings.warn("SECRET_KEY is not set. Use a real key in production.")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
