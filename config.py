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
    reranker_model_name:str = Field(default="ms-marco-MultiBERT-L-12", alias="RERANKER_MODEL_NAME")
    
    docs_path:str = Field(default="data/docs", alias="DOCS_PATH")
    
    #Tracing
    langfuse_public_key:str = Field(default=" ",alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key :str = Field(default=" ",alias="LANGFUSE_SECRET_KEY")
    langfuse_host :str = Field(default="https://us.cloud.langfuse.com",alias="LANGFUSE_BASE_URL")
    
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

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: str = Field(default="logs", alias="LOG_DIR")
    log_retention_days: int = Field(default=7, alias="LOG_RETENTION_DAYS")
    log_file_name: str = Field(default="crm", alias="LOG_FILE_NAME")
    log_to_console: bool = Field(default=True, alias="LOG_TO_CONSOLE")
    log_color: bool = Field(default=True, alias="LOG_COLOR")

    # MCP servers
    # Blank interpreter -> reuse the app's own interpreter, so servers always
    # run with the same dependencies as the app (no separate "python" on PATH).
    mcp_python: str = Field(default="", alias="MCP_PYTHON")
    # Importable module paths, launched with `python -m` from the project root.
    mcp_sql_server: str = Field(default="mcp_servers.sql_server", alias="MCP_SQL_SERVER")
    mcp_rag_server: str = Field(default="mcp_servers.rag_server", alias="MCP_RAG_SERVER")


settings = Settings()
