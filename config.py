## MODEL Tiering
"""
Production configuration maintain in below methodalogy , not is getenv fallbacks
    - Pydanctic settings - validates config at startup,fails fast if missing
    - Secret managers - AWS Secrer Manager,Azure Key vault,not in .env files
"""
import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def load_secrets():
    """Load Secrets based on enviroment"""
    env = os.getenv("APP_ENV", "local")

    if env == "local":
        # .env file only have local dev
        pass
    elif env == "docker":
        # Docker inject env vars - nothing to do
        pass
    elif env == "aws":
        # Aws Inject env vars
        pass


# Loads secrets BEFORE Pydantic reads
load_secrets()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")
    db_path: str = Field(default="data/crm.db", alias="DB_PATH")
    
    docs_path:str = Field(default="data/docs", alias="DOCS_PATH")
    
    #Tracing
    langchain_tracing_v2: bool = Field(default=False,alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(
        default="",
        alias="LANGCHAIN_API_KEY"
    )
    langchain_project: str = Field(
        default="crm_multiagent",
        alias="LANGCHAIN_PROJECT"
    )
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        alias="LANGCHAIN_ENDPOINT"
    )

    # Local Ollama settings from .env
    ollama_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    embedding_model: str = Field(default="nomic-embed-text", alias="EMBEDDING_MODEL")

    # MODEL_TIER
    router_model: str = Field(default="ollama/qwen2.5:latest", alias="ROUTER_MODEL")
    sql_model: str = Field(default="ollama/qwen2.5:latest", alias="SQL_MODEL")
    rag_model: str = Field(default="ollama/qwen3.5:latest", alias="RAG_MODEL")
    synthesize_model: str = Field(default="ollama/qwen3.5:latest", alias="SYNTHESIZE_MODEL")
    fallback_model: str = Field(default="ollama/llama3:latest", alias="FALLBACK_MODEL")

    # Groq
    groq_api_key: str = ""

    # Vector store
    vector_path: str = Field(default="data/vectorstore", alias="VECTORSTORE_PATH")
    chunk_size: int = Field(default=300, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=300, alias="CHUNK_OVERLAP")
    retriver_k: int = Field(default=3, alias="RETRIVER_K")

    # Cache
    cache_enabled: bool = False


settings = Settings()

if settings.langchain_tracing_v2:
    os.environ["LANGSMITH_API_KEY"] = settings.langchain_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langchain_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langchain_endpoint