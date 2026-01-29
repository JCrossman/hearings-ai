"""Search service for Hearings AI.

Implements hybrid search (vector + keyword) across hearing documents
with role-based filtering and citation formatting.
"""

import re
from typing import Any, Optional

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from src.clients import get_openai_client, get_search_client
from src.config import settings
from src.models import (
    FacetValue,
    SearchFilters,
    SearchRequest,
    SearchResponse,
    SearchResult,
    UserClaims,
)


def format_citation_ref(
    proceeding_id: str,
    document_type: str,
    page_number: int,
    paragraph_number: Optional[str],
    abaer_citation: Optional[str] = None,
) -> str:
    """Format a citation reference.
    
    Format: "Proceeding {ID}, {DocType}, p.{PageNum}, ¶{ParagraphNum}"
    Or for decisions: "2024-ABAER-001, p.47, ¶156"
    """
    if abaer_citation:
        citation = abaer_citation
    else:
        doc_type_display = {
            "decision": "Decision",
            "transcript": "Transcript",
            "evidence": "Exhibit",
            "procedural": "Procedural Order",
            "notice": "Notice",
        }.get(document_type, document_type.title())
        citation = f"Proceeding {proceeding_id}, {doc_type_display}"
    
    citation += f", p.{page_number}"
    
    if paragraph_number:
        citation += f", ¶{paragraph_number}"
    
    return citation


def highlight_snippet(content: str, max_length: int = 300) -> str:
    """Create a snippet from content, preserving important context."""
    # Try to find a good starting point (beginning of sentence or paragraph)
    content = content.strip()
    
    if len(content) <= max_length:
        return content
    
    # Try to end at a sentence boundary
    truncated = content[:max_length]
    last_period = truncated.rfind(". ")
    
    if last_period > max_length // 2:
        return truncated[:last_period + 1]
    
    # Fall back to word boundary
    last_space = truncated.rfind(" ")
    if last_space > 0:
        return truncated[:last_space] + "..."
    
    return truncated + "..."


def generate_embedding(text: str) -> list:
    """Generate embedding vector for a query using Azure OpenAI."""
    client = get_openai_client()
    response = client.embeddings.create(
        input=text,
        model=settings.azure_openai_deployment_embedding,
    )
    return response.data[0].embedding


def search_documents(
    request: SearchRequest,
    user_claims: UserClaims,
    security_filter: Optional[str],
) -> SearchResponse:
    """Execute hybrid search against Azure AI Search.
    
    Combines:
    - Vector similarity search for semantic matching
    - Keyword search for exact terms (citations, names)
    - Faceting for structured filtering
    - Role-based security filtering
    """
    search_client = get_search_client()
    
    # Build combined filter
    filters = []
    
    # Security filter (ALWAYS applied)
    if security_filter:
        filters.append(security_filter)
    
    # User-specified filters
    if request.filters:
        if request.filters.document_types:
            type_filter = " or ".join(
                f"documentType eq '{dt.value}'" 
                for dt in request.filters.document_types
            )
            filters.append(f"({type_filter})")
        
        if request.filters.parties:
            # Search for any of the specified parties
            party_filters = " or ".join(
                f"parties/any(p: p eq '{party}')"
                for party in request.filters.parties
            )
            filters.append(f"({party_filters})")
        
        if request.filters.regulatory_citations:
            # Search for any of the specified citations
            citation_filters = " or ".join(
                f"regulatoryCitations/any(c: search.ismatch('{cite}', 'c'))"
                for cite in request.filters.regulatory_citations
            )
            filters.append(f"({citation_filters})")
    
    # Proceeding filter
    if request.proceeding_id:
        filters.append(f"proceedingId eq '{request.proceeding_id}'")
    
    final_filter = " and ".join(filters) if filters else None
    
    # Generate embedding for vector search
    query_vector = generate_embedding(request.query)
    
    # Build vector query
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=50,
        fields="contentVector",
    )
    
    # Execute search based on mode
    search_kwargs: dict[str, Any] = {
        "search_text": request.query if request.search_mode in ("hybrid", "keyword") else None,
        "vector_queries": [vector_query] if request.search_mode in ("hybrid", "vector") else None,
        "filter": final_filter,
        "top": request.top,
        "select": [
            "id", "documentId", "proceedingId", "documentType", "abaerCitation",
            "content", "pageNumber", "paragraphNumber", "sectionTitle",
            "confidentialityLevel", "parties", "regulatoryCitations", "title",
        ],
        "facets": [
            "documentType,count:10",
            "proceedingId,count:20",
            "parties,count:20",
            "regulatoryCitations,count:20",
        ],
        "query_type": "semantic" if request.search_mode == "hybrid" else "simple",
        "semantic_configuration_name": "semantic-config" if request.search_mode == "hybrid" else None,
    }
    
    # Remove None values
    search_kwargs = {k: v for k, v in search_kwargs.items() if v is not None}
    
    results = search_client.search(**search_kwargs)
    
    # Process results
    search_results = []
    for result in results:
        # Format citation
        citation_ref = format_citation_ref(
            proceeding_id=result.get("proceedingId", "unknown"),
            document_type=result.get("documentType", "unknown"),
            page_number=result.get("pageNumber", 1),
            paragraph_number=result.get("paragraphNumber"),
            abaer_citation=result.get("abaerCitation"),
        )
        
        # Derive title from content or citation if not set
        raw_title = result.get("title")
        if not raw_title or raw_title in ("Untitled", "Unknown Document", None):
            # Try to extract from content - look for project/company name patterns
            content = result.get("content", "")
            abaer = result.get("abaerCitation", "")
            
            # Known document titles based on ABAER citation
            known_titles = {
                "2021-ABAER-010": "Benga Mining - Grassy Mountain Coal Project Decision",
                "2024-ABAER-007": "Decision Report",
                "2023-ABAER-012": "Decision Report",
            }
            
            if abaer and abaer in known_titles:
                raw_title = known_titles[abaer]
            elif "Grassy Mountain" in content or "Benga Mining" in content:
                raw_title = "Benga Mining - Grassy Mountain Coal Project"
            elif abaer:
                raw_title = f"Decision {abaer}"
            else:
                raw_title = f"Document - {result.get('documentType', 'Unknown')}"
        
        search_results.append(SearchResult(
            document_id=result.get("documentId", result["id"]),
            title=raw_title,
            abaer_citation=result.get("abaerCitation"),
            snippet=highlight_snippet(result.get("content", "")),
            relevance_score=result.get("@search.score", 0.0),
            page_number=result.get("pageNumber", 1),
            paragraph_number=result.get("paragraphNumber"),
            citation_ref=citation_ref,
            regulatory_citations=result.get("regulatoryCitations", []),
        ))
    
    # Process facets
    facets = {}
    if hasattr(results, "get_facets"):
        raw_facets = results.get_facets()
        if raw_facets:
            for facet_name, facet_values in raw_facets.items():
                facets[facet_name] = [
                    FacetValue(value=str(fv["value"]), count=fv["count"])
                    for fv in facet_values
                ]
    
    # Get total count
    total_count = len(search_results)  # Simplified; real impl would use @odata.count
    
    return SearchResponse(
        results=search_results,
        total_count=total_count,
        facets=facets,
    )
