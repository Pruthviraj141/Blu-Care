from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # API Prefix
    api_v1_prefix: str = "/api/v1"

    # Groq API Credentials
    groq_api_key: str = "mock_groq_key"
    groq_api_key_secondary: str | None = None
    groq_model: str = "qwen/qwen3.6-27b"

    # LangSmith Observability Tracing
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "symptom-triage-agent"
    langchain_endpoint: str = "https://api.smith.langchain.com"

    # Langfuse Observability Tracing
    langfuse_enabled: bool = False
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "https://us.cloud.langfuse.com"

    # Qdrant Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "medical_triage_kb"

    # Redis Database / Checkpointer
    redis_url: str = "redis://localhost:6379/0"

    # Redis Semantic Cache Configuration
    redis_cache_enabled: bool = False
    redis_cache_ttl_seconds: int = 21600
    redis_cache_distance_threshold: float = 0.08
    corpus_version: str = "curated_kb_v1.0"
    synthesis_prompt_version: str = "v1.0.0"

    # Embeddings Configuration
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    bge_query_instruction: str = "Represent this sentence for searching relevant passages: "

    # Cross-Encoder Reranker
    reranker_model_name: str = "BAAI/bge-reranker-base"

    # Retrieval Pipeline Tuning
    score_threshold: float = 0.55
    fetch_k: int = 20
    mmr_k: int = 10
    mmr_lambda: float = 0.5
    final_k: int = 5

    # App Behavior & Limits
    app_env: str = "development"
    max_intake_turns: int = 7
    confidence_threshold: float = 0.75
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:8000",
    ]
    rate_limit_per_minute: int = 60

    # Clerk Authentication
    clerk_issuer_url: str | None = "https://clerk.accepted.catfish-84.clerk.accounts.dev"
    clerk_jwks_url: str | None = None
    clerk_audience: str | None = None
    allow_dev_auth: bool = False

    # Database Configuration (PostgreSQL / Supabase / SQLite fallback)
    database_url: str | None = None
    supabase_url: str | None = None
    supabase_key: str | None = None
    supabase_db_url: str | None = None

    # Safety Engine
    safety_ruleset_version: str = "1.0.0-provisional"

    # Hospital Discovery Scraper Configuration
    scraper_enabled: bool = True
    scraper_headless: bool = True
    scraper_timeout_seconds: int = 20
    scraper_default_radius_meters: int = 5000
    scraper_max_radius_meters: int = 20000
    scraper_max_results: int = 25
    scraper_cache_ttl_seconds: int = 900
    scraper_user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
    # Legacy alias attributes kept for backward-compatibility
    overpass_enabled: bool = False
    overpass_endpoint: str = ""
    overpass_backup_endpoints: list[str] = []
    overpass_timeout_seconds: int = 35
    overpass_default_radius_meters: int = 5000
    overpass_max_radius_meters: int = 20000
    overpass_max_results: int = 20
    overpass_cache_ttl_seconds: int = 600
    overpass_user_agent: str = "BluCarePlus/1.0"


settings = Settings()
