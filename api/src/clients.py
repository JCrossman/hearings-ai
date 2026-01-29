"""Azure service clients for Hearings AI API.

Initializes and provides access to Azure OpenAI, AI Search, Cosmos DB, and Blob Storage.
Uses managed identity authentication when running in Azure.
"""

from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from openai import AzureOpenAI

from src.config import settings


@lru_cache()
def get_credential() -> DefaultAzureCredential:
    """Get Azure credential (cached singleton)."""
    return DefaultAzureCredential()


@lru_cache()
def get_search_client() -> SearchClient:
    """Get Azure AI Search client for document operations."""
    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index,
        credential=get_credential(),
    )


@lru_cache()
def get_search_index_client() -> SearchIndexClient:
    """Get Azure AI Search client for index management."""
    return SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=get_credential(),
    )


@lru_cache()
def get_openai_client() -> AzureOpenAI:
    """Get Azure OpenAI client.
    
    Uses managed identity token for authentication.
    """
    credential = get_credential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        azure_ad_token=token.token,
    )
