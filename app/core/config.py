from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_mode: str = "mock"
    spark_app_id: str = ""
    spark_api_key: str = ""
    spark_api_secret: str = ""
    spark_api_url: str = ""
    chroma_persist_dir: str = "./chroma_db"
    knowledge_base_dir: str = "./knowledge_base"


@lru_cache
def get_settings() -> Settings:
    return Settings()
