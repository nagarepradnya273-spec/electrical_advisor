import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Indian Electrical Advisor & E-Commerce Platform API"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./electrical_platform.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    # Both localhost and 127.0.0.1 are included by default since browsers
    # treat them as different origins even though they're the same machine.
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

    # Optional: when set, the Advisor uses Claude to understand free-text
    # problem descriptions. When empty, it falls back to keyword matching -
    # the app works fully without this key.
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    # Optional: when set, the RAG knowledge base (app/services/embedding_service.py)
    # uses Voyage AI for real embeddings. When empty, it falls back to a local,
    # dependency-free embedding - knowledge ingestion and search still work
    # fully without this key, same philosophy as ANTHROPIC_API_KEY above.
    VOYAGE_API_KEY: str = os.getenv("VOYAGE_API_KEY", "")


settings = Settings()
