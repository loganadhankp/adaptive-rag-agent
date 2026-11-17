from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GOOGLE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-3.5-flash-lite"
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    CHROMA_COLLECTION_NAME: str = "knowledge_base"
    MAX_RETRIEVAL_RESULTS: int = 8
    MAX_RETRIES: int = 2

    SQLITE_DB_PATH: str = "data/chat_history.db"
    DOCUMENTS_DIR: str = "data/documents"
    CHROMA_PERSIST_DIR: str = "data/vector_db"

    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


def get_settings() -> Settings:
    return settings
