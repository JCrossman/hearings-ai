"""Configuration settings for Hearings AI API."""

from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_api_version: str = "2024-06-01"
    azure_openai_deployment_chat: str = "gpt-4o"
    azure_openai_deployment_embedding: str = "text-embedding-3-large"

    # Azure AI Search
    azure_search_endpoint: str
    azure_search_index: str = "hearings-index"

    # Cosmos DB
    cosmos_endpoint: str
    cosmos_database: str = "hearings"
    cosmos_container: str = "documents"

    # Blob Storage (optional for demo)
    storage_account_url: Optional[str] = None
    storage_container: str = "hearing-documents"

    # Auth (optional - uses managed identity if not set)
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173", "*"]

    # Chunking
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 128


settings = Settings()  # type: ignore[call-arg]
