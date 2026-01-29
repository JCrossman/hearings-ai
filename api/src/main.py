"""Hearings AI API - Hearing Document Search and Understanding.

This API provides semantic search, evidence retrieval, and document understanding
for hearing documents.
"""

import uuid
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.auth import build_search_filter, get_current_user, can_access_document
from src.config import settings
from src.models import (
    DocumentUnderstandingRequest,
    DocumentUnderstandingResponse,
    ErrorResponse,
    EvidenceRetrievalRequest,
    EvidenceRetrievalResponse,
    IngestionRequest,
    IngestionResponse,
    ProceedingOverview,
    SearchRequest,
    SearchResponse,
    UserClaims,
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    logger.info("Starting Hearings AI API", environment=settings.environment)
    # TODO: Initialize Azure clients here
    yield
    logger.info("Shutting down Hearings AI API")


app = FastAPI(
    title="Hearings AI API",
    description="Semantic search and document understanding for hearing preparation",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Middleware ===


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests for tracing."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")
async def extract_swa_auth(request: Request, call_next):
    """Extract user info from Azure Static Web Apps authentication headers.
    
    Static Web Apps injects authentication info via X-MS-CLIENT-PRINCIPAL header.
    https://learn.microsoft.com/azure/static-web-apps/user-information
    """
    import json
    import base64
    
    # Extract client principal header
    client_principal_header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
    
    if client_principal_header:
        try:
            # Decode base64 header
            client_principal_json = base64.b64decode(client_principal_header).decode("utf-8")
            client_principal = json.loads(client_principal_json)
            
            # Extract user claims
            user_id = client_principal.get("userId", "")
            user_details = client_principal.get("userDetails", "")
            claims = client_principal.get("claims", [])
            
            # Find email in claims
            email = user_details
            for claim in claims:
                if claim.get("typ") in ["emails", "email", "preferred_username"]:
                    email = claim.get("val", email)
                    break
            
            # Create UserClaims and attach to request state
            request.state.user_claims = UserClaims(
                oid=user_id,
                name=user_details,
                email=email,
                roles=["Staff"],  # Default role, can be customized based on claims
                party_affiliation=None,
                ba_code=None,
            )
        except Exception as e:
            logger.warning("Failed to parse Static Web Apps auth header", error=str(e))
    
    response = await call_next(request)
    return response


# === Exception Handlers ===


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error response."""
    detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=detail.get("code", f"HTTP_{exc.status_code}"),
            message=detail.get("message", str(exc.detail)),
            details=detail.get("details"),
        ).model_dump(),
    )


# === Health Check ===


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


# === Search Endpoints ===


@app.post("/api/search", response_model=SearchResponse)
async def search_documents_endpoint(
    request: SearchRequest,
    user_claims: Annotated[UserClaims, Depends(get_current_user)],
):
    """Semantic search across hearing documents with role-based filtering.

    Supports hybrid search (vector + keyword) with faceting by document type,
    parties, and regulatory citations. Results are filtered based on user's
    confidentiality access level.
    """
    from src.search.service import search_documents
    
    log = logger.bind(
        user_oid=user_claims.oid,
        query_length=len(request.query),
        proceeding_id=request.proceeding_id,
    )
    log.info("Search request received")

    # Build security filter - ALWAYS applied
    security_filter = build_search_filter(user_claims)

    # Execute search (synchronous function)
    response = search_documents(request, user_claims, security_filter)

    log.info("Search completed", result_count=response.total_count)

    return response


# === Evidence Retrieval Endpoints ===


@app.post("/api/evidence/retrieve", response_model=EvidenceRetrievalResponse)
async def retrieve_evidence(
    request: EvidenceRetrievalRequest,
    user_claims: Annotated[UserClaims, Depends(get_current_user)],
):
    """Retrieve evidence chunk with surrounding context.

    Returns the target chunk plus context_window chunks before and after,
    preserving paragraph numbers for proper citation.
    """
    log = logger.bind(
        user_oid=user_claims.oid,
        document_id=request.document_id,
        chunk_id=request.chunk_id,
    )
    log.info("Evidence retrieval request")

    # TODO: Implement evidence retrieval
    # 1. Fetch document metadata from Cosmos DB
    # 2. Check access with can_access_document()
    # 3. Retrieve chunks from search index
    # 4. Return with proper citation formatting

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"code": "NOT_IMPLEMENTED", "message": "Evidence retrieval not yet implemented"},
    )


# === Document Understanding Endpoints ===


@app.post("/api/documents/understand", response_model=DocumentUnderstandingResponse)
async def understand_document(
    request: DocumentUnderstandingRequest,
    user_claims: Annotated[UserClaims, Depends(get_current_user)],
):
    """Analyze document for summary, entities, key points, and regulatory citations.

    Uses Azure OpenAI to extract structured information from hearing documents.
    """
    log = logger.bind(
        user_oid=user_claims.oid,
        document_id=request.document_id,
        operations=request.operations,
    )
    log.info("Document understanding request")

    # TODO: Implement document understanding
    # 1. Fetch document from storage
    # 2. Check access
    # 3. Run requested operations with Azure OpenAI
    # 4. Extract entities (legal sections, well IDs, etc.)

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"code": "NOT_IMPLEMENTED", "message": "Document understanding not yet implemented"},
    )


# === Ingestion Endpoints ===


@app.post("/api/documents/ingest", response_model=IngestionResponse)
async def ingest_document(
    file: UploadFile,
    metadata: IngestionRequest,
    user_claims: Annotated[UserClaims, Depends(get_current_user)],
):
    """Upload and process a new hearing document.

    Requires Staff or Hearing_Panel role. Document is processed asynchronously:
    1. Stored in blob storage
    2. Text extracted with Document Intelligence
    3. Chunked and embedded
    4. Indexed in Azure AI Search
    """
    if "Staff" not in user_claims.roles and "Hearing_Panel" not in user_claims.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTH_002", "message": "Document ingestion requires Staff or Hearing_Panel role"},
        )

    log = logger.bind(
        user_oid=user_claims.oid,
        proceeding_id=metadata.proceeding_id,
        document_type=metadata.document_type,
        filename=file.filename,
    )
    log.info("Document ingestion request")

    # TODO: Implement ingestion pipeline
    # 1. Upload to blob storage
    # 2. Create metadata record in Cosmos DB
    # 3. Queue for async processing

    document_id = str(uuid.uuid4())
    return IngestionResponse(
        document_id=document_id,
        status="pending",
        estimated_completion_minutes=5,
    )


# === Proceeding Endpoints ===


@app.get("/api/proceedings/{proceeding_id}", response_model=ProceedingOverview)
async def get_proceeding(
    proceeding_id: str,
    user_claims: Annotated[UserClaims, Depends(get_current_user)],
):
    """Get proceeding overview with all associated documents.

    Returns proceeding metadata, parties, timeline, and documents grouped by type.
    Document lists are filtered based on user's access level.
    """
    log = logger.bind(user_oid=user_claims.oid, proceeding_id=proceeding_id)
    log.info("Proceeding overview request")

    # TODO: Implement proceeding retrieval
    # 1. Fetch proceeding from Cosmos DB
    # 2. Query all documents for this proceeding
    # 3. Filter by user access
    # 4. Group by document type

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={"code": "NOT_IMPLEMENTED", "message": "Proceeding overview not yet implemented"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
