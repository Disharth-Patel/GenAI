from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Maharashtra OBC Education Voice AI Chatbot"
    APP_ENV: str = "development"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    DATABASE_URL: str = "sqlite:///./storage/obc_chatbot.db"

    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: float = 120.0

    # Storage
    UPLOAD_DIR: str = "storage/uploads"
    MAX_UPLOAD_MB: int = 15

    # AI/RAG Configuration
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    VECTOR_DB_PATH: str = "storage/chroma_db"

    class Config:
        env_file = ".env"

settings = Settings()
