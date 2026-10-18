from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MCSTORE_",
        extra="ignore",
    )

    database_url: str = "sqlite:///./mcstore.db"
    api_url: str = "http://127.0.0.1:8000"
    bot_token: SecretStr | None = None
    grpc_endpoint: str = "127.0.0.1:20706"
    grpc_tls: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
