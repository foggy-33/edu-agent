from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_mode: str = "mock"
    spark_app_id: str = ""
    spark_api_key: str = ""
    spark_api_secret: str = ""
    spark_api_url: str = ""
    spark_api_password: str = ""
    spark_base_url: str = "https://spark-api-open.xf-yun.com/x2"
    spark_model: str = "spark-x"
    spark_lite_api_password: str = ""
    spark_lite_base_url: str = "https://spark-api-open.xf-yun.com/v1"
    spark_lite_model: str = "lite"
    siliconflow_api_key: str = ""
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    siliconflow_model: str = "Pro/deepseek-ai/DeepSeek-V3.2"
    chroma_persist_dir: str = "./chroma_db"
    knowledge_base_dir: str = "./knowledge_base"
    rag_auto_ingest: bool = True
    rag_top_k: int = 5
    rag_embedding_dimension: int = 384
    profile_data_dir: str = "./data/profiles"
    resource_data_dir: str = "./data/resources"
    user_data_file: str = "./data/auth/users.json"
    avatar_dir: str = "./data/avatars"
    course_source_dir: str = "./sourse"
    course_annotation_dir: str = "./data/course_annotations"


@lru_cache
def get_settings() -> Settings:
    return Settings()
