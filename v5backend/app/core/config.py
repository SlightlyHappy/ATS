from __future__ import annotations
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Load environment from .env if present
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Web
    APP_NAME: str = Field(default="Resume Analyzer API")
    ENV: str = Field(default=os.getenv("ENV", "production"))
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=int(os.getenv("PORT", "8000")))
    LOG_LEVEL: str = Field(default=os.getenv("LOG_LEVEL", "info"))

    # DB
    DATABASE_URL: str = Field(default="postgresql+psycopg2://postgres:postgres@localhost:5432/postgres")

    # Redis / Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # MinIO / S3
    STORAGE_BACKEND: str = Field(default="s3")  # s3 | filesystem
    S3_ENDPOINT: str = Field(default="http://localhost:9000")
    S3_BUCKET: str = Field(default="resumes")
    S3_BUCKET_TMP: str = Field(default="tmp-uploads")
    S3_ACCESS_KEY: str = Field(default="minioadmin")
    S3_SECRET_KEY: str = Field(default="minioadmin")
    S3_REGION: str = Field(default="us-east-1")
    S3_PATH_STYLE: bool = Field(default=True)

    # Ollama - Optimized for 32-core system
    OLLAMA_HOST: str = Field(default="http://127.0.0.1:11434")
    OLLAMA_MODELS: str = Field(default="qwen2.5:3b-instruct-q5_0,qwen2.5:7b-instruct-q4_K_M,bge-m3")
    OLLAMA_NUM_CTX: int = Field(default=4096)
    OLLAMA_NUM_PARALLEL: int = Field(default=8)  # Increased from 1 to 8 for much better parallelism

    # Embeddings / retrieval
    EMBEDDING_MODEL: str = Field(default="bge-m3")
    EMBEDDING_DIM: int = Field(default=1024)
    TOP_K: int = Field(default=20)
    RETRIEVAL_PER_RESUME_LIMIT: int = Field(default=3)
    CONTEXT_CHAR_LIMIT: int = Field(default=6000)

    # Concurrency
    IO_CONCURRENCY: int = Field(default=32)    # Increased from 24 to 32 for aggressive I/O
    LLM_CONCURRENCY: int = Field(default=16)   # Massively increased from 3 to 16 for 32-core system

    # Uploads
    MAX_FILE_SIZE_MB: int = Field(default=30)
    ALLOWED_EXTS: str = Field(default=".pdf,.docx,.zip")

    # Chat
    CHAT_MAX_TOKENS: int = Field(default=800)

    # OCR
    TESSERACT_CMD: str = Field(default=os.getenv("TESSERACT_CMD", ""))

    # Vector/pgvector Configuration - Optimized for Railway pgvector service
    ENABLE_VECTOR_SEARCH: bool = Field(default=True)  # Enable vector functionality on pgvector service
    PGVECTOR_RETRY_COUNT: int = Field(default=3)  # Moderate retries for pgvector service
    PGVECTOR_RETRY_DELAY: int = Field(default=5)  # Reasonable delay for pgvector service
    SKIP_PGVECTOR_ON_FAILURE: bool = Field(default=False)  # Don't skip vector on pgvector service - should work
    FORCE_PGVECTOR_CREATION: bool = Field(default=True)  # Enabled for pgvector service - extension available

    # Database Migration Configuration
    AUTO_MIGRATE_ON_STARTUP: bool = Field(default=True)  # Automatically run migrations on app startup

    def model_post_init(self, __context: dict) -> None:
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL

        # Prefer explicit DATABASE_URL if provided
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            # Next prefer internal host/port if available (for pgvector service)
            pghost = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST")
            pgport = os.getenv("PGPORT") or os.getenv("POSTGRES_PORT")
            pguser = os.getenv("PGUSER") or os.getenv("POSTGRES_USER") or "postgres"
            pgpassword = os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD") or ""
            pgdb = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB") or "railway"
            if pghost and pgport and pgpassword:
                db_url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdb}"
        if not db_url:
            # Try Railway internal PostgreSQL service first (pgvector)
            internal_url = os.getenv("DATABASE_INTERNAL_URL")
            primary_node = os.getenv("DATABASE_PRIMARY_NODE")
            if internal_url:
                db_url = internal_url
            elif primary_node:
                db_url = primary_node
            else:
                # Fallback to DATABASE_PUBLIC_URL (proxy)
                db_url = os.getenv("DATABASE_PUBLIC_URL")
        if db_url:
            # Add Railway-specific connection parameters for better stability
            if "railway.internal" in db_url and "?" not in db_url:
                db_url += "?sslmode=prefer&connect_timeout=30&application_name=ats_pgvector"
            elif "railway.internal" in db_url and "application_name" not in db_url:
                db_url += "&application_name=ats_pgvector"
            self.DATABASE_URL = db_url

        # Normalize to psycopg driver if needed
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


settings = Settings()  # type: ignore
