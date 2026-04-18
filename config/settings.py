from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(alias="APP_NAME")
    app_env: str = Field(alias="APP_ENV")
    app_host: str = Field(alias="APP_HOST")
    app_port: int = Field(alias="APP_PORT")
    app_debug: bool = Field(alias="APP_DEBUG")

    database_url: str = Field(alias="DATABASE_URL")
    database_echo: bool = Field(alias="DATABASE_ECHO")

    llm_provider: str = Field(alias="LLM_PROVIDER")
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_base_url: str = Field(alias="OPENAI_BASE_URL")
    openai_model: str = Field(alias="OPENAI_MODEL")

    dashscope_api_key: str = Field(alias="DASHSCOPE_API_KEY")
    qwen_model: str = Field(alias="QWEN_MODEL")
    qwen_embedding_model: str = Field(alias="QWEN_EMBEDDING_MODEL")

    vector_dimension: int = Field(alias="VECTOR_DIMENSION")
    knowledge_docs_dir: str = Field(alias="KNOWLEDGE_DOCS_DIR")
    log_level: str = Field(alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def knowledge_docs_path(self) -> Path:
        return Path(self.knowledge_docs_dir).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
