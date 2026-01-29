"""Shared Pydantic models for Hearings AI API.

Uses terminology throughout:
- "proceeding" not "case"
- "intervener" not "plaintiff"  
- "ABAER citation" not "ruling"
"""

from datetime import date, datetime
from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field


# === Enums (Document Taxonomy) ===


class DocumentType(str, Enum):
    """Document type taxonomy."""

    DECISION = "decision"  # Final hearing decisions (ABAER citations)
    TRANSCRIPT = "transcript"  # Daily hearing transcripts
    PROCEDURAL = "procedural"  # Scheduling orders, confidentiality rulings
    EVIDENCE = "evidence"  # Expert reports, submissions, exhibits
    NOTICE = "notice"  # Hearing notices, participation decisions
    IR = "information_request"  # Information requests and responses


class ConfidentialityLevel(str, Enum):
    """Confidentiality levels per Rules of Practice s. 49."""

    PUBLIC = "public"  # Default - accessible to all
    PROTECTED_A = "protected_a"  # Standard government sensitivity
    CONFIDENTIAL = "confidential"  # S.49 confidentiality order granted


class PartyRole(str, Enum):
    """Party roles in proceedings."""

    APPLICANT = "applicant"
    INTERVENER = "intervener"
    STAFF = "staff"


class ProcessingStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


# === Party Models ===


class Party(BaseModel):
    """A party to a proceeding."""

    name: str
    role: PartyRole
    ba_code: Optional[str] = None  # Licensee BA code if applicable


# === Regulatory Citation Models ===


class RegulatoryCitation(BaseModel):
    """A reference to legislation or directive."""

    type: Annotated[str, Field(pattern=r"^(legislation|directive|manual)$")]
    reference: str  # e.g., "REDA s. 34", "Directive 056 s. 2.1"
    context: Optional[str] = None  # How it's used in the document


class ExtractedCitation(RegulatoryCitation):
    """A regulatory citation extracted with paragraph references."""

    paragraphs: list[str] = []  # e.g., ["[45]", "[67]"]


# === Document Models ===


class HearingDates(BaseModel):
    """Hearing date range."""

    start: date
    end: Optional[date] = None


class DocumentMetadata(BaseModel):
    """Full document metadata stored in Cosmos DB."""

    id: str
    proceeding_id: str
    application_numbers: list[str] = []
    regulatory_appeal_number: Optional[str] = None
    document_type: DocumentType
    abaer_citation: Optional[str] = None  # e.g., "2024-ABAER-001"
    title: str
    parties: list[Party] = []
    confidentiality_level: ConfidentialityLevel = ConfidentialityLevel.PUBLIC
    regulatory_citations: list[RegulatoryCitation] = []
    hearing_dates: Optional[HearingDates] = None
    decision_date: Optional[date] = None
    uploaded_at: datetime
    source_url: Optional[str] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    page_count: Optional[int] = None
    volume_number: Optional[int] = None  # For transcripts


class DocumentSummary(BaseModel):
    """Lightweight document reference for listings."""

    id: str
    title: str
    document_type: DocumentType
    abaer_citation: Optional[str] = None
    page_count: Optional[int] = None


# === Search Models ===


class SearchFilters(BaseModel):
    """Filters for search queries."""

    document_types: Optional[List[DocumentType]] = None
    parties: Optional[List[str]] = None
    regulatory_citations: Optional[List[str]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class SearchRequest(BaseModel):
    """Search request payload."""

    query: str = Field(..., min_length=3, max_length=1000)
    proceeding_id: Optional[str] = None
    filters: Optional[SearchFilters] = None
    top: int = Field(default=10, ge=1, le=50)
    search_mode: Annotated[str, Field(pattern=r"^(hybrid|vector|keyword)$")] = "hybrid"


class SearchResult(BaseModel):
    """A single search result with citation."""

    document_id: str
    title: str
    abaer_citation: Optional[str] = None
    snippet: str
    relevance_score: float
    page_number: int
    paragraph_number: Optional[str] = None  # e.g., "[156]"
    citation_ref: str  # Full citation: "Proceeding 449, Exhibit 12.01, p.47, ¶156"
    parties: list[str] = []
    regulatory_citations: list[str] = []


class FacetValue(BaseModel):
    """A facet value with count."""

    value: str
    count: int


class SearchResponse(BaseModel):
    """Search response with results and facets."""

    results: list[SearchResult]
    total_count: int
    facets: dict[str, list[FacetValue]] = {}


# === Evidence Retrieval Models ===


class EvidenceChunk(BaseModel):
    """A chunk of evidence content."""

    chunk_id: int
    paragraph_number: Optional[str] = None
    content: str
    is_target: bool = False


class EvidenceRetrievalRequest(BaseModel):
    """Request to retrieve evidence with context."""

    document_id: str
    chunk_id: int
    context_window: int = Field(default=2, ge=0, le=5)


class EvidenceRetrievalResponse(BaseModel):
    """Evidence chunks with surrounding context."""

    document: DocumentSummary
    proceeding_id: str
    citation_ref: str
    chunks: list[EvidenceChunk]
    page_range: str
    source_url: Optional[str] = None


# === Document Understanding Models ===


class DocumentUnderstandingRequest(BaseModel):
    """Request for document analysis."""

    document_id: str
    operations: list[Annotated[str, Field(pattern=r"^(summarize|extractEntities|extractKeyPoints|extractRegulatoryCitations)$")]]


class ExtractedEntities(BaseModel):
    """Entities extracted from a document."""

    locations: list[str] = []  # Townships, regions, landmarks
    organizations: list[str] = []
    well_identifiers: list[str] = []  # MW-3, etc.
    dates: list[str] = []
    regulations: list[str] = []


class DocumentUnderstandingResponse(BaseModel):
    """Document analysis results."""

    summary: Optional[str] = None
    entities: Optional[ExtractedEntities] = None
    key_points: Optional[List[str]] = None
    regulatory_citations: Optional[List[ExtractedCitation]] = None


# === Proceeding Models ===


class ProceedingDocuments(BaseModel):
    """Documents grouped by type for a proceeding."""

    decisions: list[DocumentSummary] = []
    transcripts: list[DocumentSummary] = []
    evidence: list[DocumentSummary] = []
    procedural: list[DocumentSummary] = []
    notices: list[DocumentSummary] = []


class TimelineEvent(BaseModel):
    """A proceeding timeline event."""

    date: date
    event: str


class ProceedingOverview(BaseModel):
    """Full proceeding overview."""

    proceeding_id: str
    title: str
    status: Annotated[str, Field(pattern=r"^(active|closed|adjourned)$")]
    applicant: Optional[Party] = None
    interveners: list[Party] = []
    hearing_dates: Optional[HearingDates] = None
    documents: ProceedingDocuments
    timeline: list[TimelineEvent] = []


# === Auth Models ===


class UserClaims(BaseModel):
    """User claims extracted from Entra ID token."""

    oid: str  # User object ID
    name: str
    email: str
    roles: list[str] = []  # AER_Staff, Hearing_Panel, Intervener, Public
    party_affiliation: Optional[str] = None  # For interveners
    ba_code: Optional[str] = None  # For licensee users


# === Ingestion Models ===


class IngestionRequest(BaseModel):
    """Metadata for document ingestion."""

    proceeding_id: str
    document_type: DocumentType
    title: str
    confidentiality_level: ConfidentialityLevel = ConfidentialityLevel.PUBLIC
    parties: list[Party] = []
    abaer_citation: Optional[str] = None
    volume_number: Optional[int] = None


class IngestionResponse(BaseModel):
    """Response after initiating document ingestion."""

    document_id: str
    status: ProcessingStatus
    estimated_completion_minutes: int


# === Error Models ===


class ErrorResponse(BaseModel):
    """Standard error response."""

    code: str
    message: str
    details: Optional[dict] = None
