from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env", override=False)
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
TRACE_DIR = DATA_DIR / "traces"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TRACE_DIR.mkdir(parents=True, exist_ok=True)


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Plataforma Monda")
    app_version: str = os.getenv("APP_VERSION", "2.0.0-entrega2")
    environment: str = os.getenv("APP_ENV", "local")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'monda.db'}")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "30"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    secret_key: str = os.getenv("MONDA_SECRET_KEY", "monda-local-change-me-2026-use-32-bytes-minimum")
    access_minutes: int = int(os.getenv("ACCESS_MINUTES", "30"))
    refresh_days: int = int(os.getenv("REFRESH_DAYS", "7"))
    cookie_secure: bool = _bool("COOKIE_SECURE", False)
    demo_mode: bool = _bool("MONDA_DEMO", True)
    allow_test_password_fallback: bool = _bool("MONDA_ALLOW_PBKDF2_FOR_TESTS", False)

    rag_mode: str = os.getenv("RAG_MODE", "auto").lower()
    rag_allow_fallback: bool = _bool("RAG_ALLOW_FALLBACK", True)
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    rag_similarity_threshold: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.35"))
    rag_minimum_score_margin: float = float(os.getenv("RAG_MINIMUM_SCORE_MARGIN", "0.0"))
    rag_candidate_multiplier: int = int(os.getenv("RAG_CANDIDATE_MULTIPLIER", "4"))

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    # Gemini must remain disabled until the institution explicitly authorizes
    # sending course material and learner questions to the external provider.
    gemini_external_processing_authorized: bool = _bool("GEMINI_EXTERNAL_PROCESSING_AUTHORIZED", False)
    gemini_llm_model: str = os.getenv("GEMINI_LLM_MODEL", "gemini-3-flash-preview")
    gemini_llm_fallback_models: list[str] = field(default_factory=lambda: [
        model.strip()
        for model in os.getenv("GEMINI_LLM_FALLBACK_MODELS", "gemini-3.8-flash,gemini-3.6-flash").split(",")
        if model.strip()
    ])
    gemini_embedding_model: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
    gemini_base_url: str = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")

    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_llm_model: str = os.getenv("OLLAMA_LLM_MODEL", "llama3")
    ollama_embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

    storage_mode: str = os.getenv("STORAGE_MODE", "local").lower()
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")

    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "")

    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
    login_max_failures: int = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
    login_lock_minutes: int = int(os.getenv("LOGIN_LOCK_MINUTES", "15"))


settings = Settings()
