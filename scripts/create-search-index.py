#!/usr/bin/env python3
"""Create Azure AI Search index for Hearings AI.

Creates the search index schema with:
- Text content for full-text search
- Vector field for semantic search (3072 dimensions for text-embedding-3-large)
- Filterable/facetable fields for structured queries
- Semantic configuration for ranking
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)
from dotenv import load_dotenv

# Load environment
load_dotenv(Path(__file__).parent.parent / "api" / ".env")

SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX", "hearings-index")
OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-3-large")


def create_index_schema() -> SearchIndex:
    """Create the search index schema per COPILOT.md specification."""
    
    fields = [
        # Key field
        SearchField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        # Document reference
        SearchField(
            name="documentId",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
        ),
        # structured fields
        SearchField(
            name="proceedingId",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
            sortable=True,
        ),
        SearchField(
            name="documentType",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        SearchField(
            name="abaerCitation",
            type=SearchFieldDataType.String,
            filterable=True,
            searchable=True,
        ),
        # Chunk metadata
        SearchField(
            name="chunkId",
            type=SearchFieldDataType.Int32,
            sortable=True,
        ),
        SearchField(
            name="pageNumber",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True,
        ),
        SearchField(
            name="paragraphNumber",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SearchField(
            name="sectionTitle",
            type=SearchFieldDataType.String,
            searchable=True,
        ),
        # Content fields
        SearchField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True,
            analyzer_name="en.microsoft",
        ),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,
            vector_search_profile_name="hnsw-profile",
        ),
        # Access control
        SearchField(
            name="confidentialityLevel",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True,
        ),
        # Parties (for filtering by party name)
        SearchField(
            name="parties",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True,
        ),
        # Regulatory citations
        SearchField(
            name="regulatoryCitations",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True,
        ),
        # Document metadata
        SearchField(
            name="title",
            type=SearchFieldDataType.String,
            searchable=True,
        ),
        SearchField(
            name="sourceUrl",
            type=SearchFieldDataType.String,
        ),
    ]

    # Vector search configuration
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine",
                },
            ),
        ],
        profiles=[
            VectorSearchProfile(
                name="hnsw-profile",
                algorithm_configuration_name="hnsw",
                vectorizer_name="openai-vectorizer",
            ),
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="openai-vectorizer",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=OPENAI_ENDPOINT,
                    deployment_name=EMBEDDING_DEPLOYMENT,
                    model_name="text-embedding-3-large",
                ),
            ),
        ],
    )

    # Semantic search configuration
    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="sectionTitle"),
                    content_fields=[SemanticField(field_name="content")],
                    keywords_fields=[
                        SemanticField(field_name="regulatoryCitations"),
                        SemanticField(field_name="parties"),
                    ],
                ),
            ),
        ],
    )

    return SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )


def main():
    """Create or update the search index."""
    print("=" * 60)
    print("Hearings AI - Search Index Creator")
    print("=" * 60)
    print(f"\nEndpoint: {SEARCH_ENDPOINT}")
    print(f"Index name: {INDEX_NAME}")
    print(f"OpenAI endpoint: {OPENAI_ENDPOINT}")
    print(f"Embedding deployment: {EMBEDDING_DEPLOYMENT}")

    # Create client with managed identity
    credential = DefaultAzureCredential()
    client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)

    # Create index schema
    print("\nCreating index schema...")
    index = create_index_schema()

    # Create or update index
    try:
        result = client.create_or_update_index(index)
        print(f"✓ Index '{result.name}' created/updated successfully")
        print(f"  Fields: {len(result.fields)}")
        print(f"  Vector search: enabled")
        print(f"  Semantic search: enabled")
    except Exception as e:
        print(f"✗ Failed to create index: {e}")
        raise

    print("\n" + "=" * 60)
    print("Index ready for document ingestion")
    print("=" * 60)


if __name__ == "__main__":
    main()
