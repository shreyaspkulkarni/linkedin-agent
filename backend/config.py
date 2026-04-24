from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Claude
    anthropic_api_key: str = ""

    # LinkedIn OAuth
    linkedin_client_id: str
    linkedin_client_secret: str
    linkedin_redirect_uri: str = "http://localhost:8000/auth/callback"

    # OpenAI (embeddings — Phase 2)
    openai_api_key: str = ""

    # Tavily (search — Phase 3)
    tavily_api_key: str = ""

    # PostgreSQL
    database_url: str = "postgresql://linkedin_agent:password@localhost:5432/linkedin_agent"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "linkedin-agent"

    # App
    secret_key: str = "change-this-to-a-random-secret-key"
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


settings = Settings()
