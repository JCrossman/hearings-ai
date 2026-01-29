# COPILOT.md - Hearings AI POC

---

## Project Overview

**Name:** Hearings AI  
**Type:** Internal Tool (High Sensitivity & Complexity)  
**Purpose:** Accelerate hearing preparation through semantic search, evidence retrieval, and document understanding across structured and unstructured hearing data.

### Core Capabilities
1. **Semantic Search** - Natural language queries across hearing documents
2. **Evidence Retrieval** - Surface relevant evidence with citations and context
3. **Document Understanding** - Extract entities, summarize, and relate documents

### Success Criteria
- Reduce hearing preparation time by 50%+
- Maintain 100% compliance with confidentiality requirements
- Support role-based access aligned with existing security model

---

## Domain Context

### Terminology (Use These Terms)
| Correct Term | Not This |
|--------------|----------|
| Hearing commissioners | Judges |
| Interveners / Participants | Plaintiffs |
| Statements of concern | Complaints |
| Applications | Petitions |
| Directives | Regulations (for -issued) |
| Proceeding ID | Case number |
| ABAER decision | Ruling |

### Document Taxonomy
| Category | Document Types | ID Format |
|----------|---------------|-----------|
| **Decisions** | Final decisions, costs orders | `YYYY-ABAER-NNN` (e.g., 2024-ABAER-001) |
| **Transcripts** | Daily hearing records | `proceeding[ID]-vol-[#]-[date].pdf` |
| **Procedural** | Scheduling orders, confidentiality rulings | `[AppNum]_YYYYMMDD.pdf` |
| **Evidence** | Expert reports, submissions, IRs | Party-prefixed filing numbers |
| **Notices** | Hearing notices, participation decisions | Proceeding ID referenced |

### Key Identifiers
- **Proceeding ID**: 3-digit numeric (e.g., 449, 454)
- **Application Number**: 7-8 digits (e.g., 1943077, 32140532)
- **Regulatory Appeal Number**: 7 digits (e.g., 1927181)
- **BA Code**: Licensee identifier for party matching

### Regulatory References to Extract
**Legislation:**
- REDA (Responsible Energy Development Act)
- EPEA (Environmental Protection and Enhancement Act, RSA 2000, c E-12)
- OGCA (Oil and Gas Conservation Act)
- Pipeline Act, Water Act, Public Lands Act

**Commonly Cited Directives:**
- Directive 056: Energy Development Applications
- Directive 067: Licence Eligibility
- Directive 088: Licensee Life-Cycle Management
- Directive 031: REDA Energy Cost Claims
- Directive 071: Emergency Preparedness

### Confidentiality Levels
| Level | Description | Access |
|-------|-------------|--------|
| **Public** | Default for all hearing documents | All users |
| **Protected A** | Standard government sensitivity | Staff, Panel |
| **Confidential** | S.49 confidentiality order granted | Panel only |

Confidentiality triggers:
- Significant competitive harm
- Undue financial loss/gain
- Personal information (medical, income, banking)
- Experimental scheme data (5-year protection)

---

## Architecture

### Azure Services
```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│                    Azure Static Web Apps                        │
│              Style: Blue/Teal palette, clean UI             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      API Layer (Python)                         │
│                 Azure Container Apps                            │
└───────┬─────────────────┬─────────────────┬─────────────────────┘
        │                 │                 │
┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
│  Azure OpenAI │ │ Azure AI      │ │ Azure Cosmos  │
│  (GPT-4o)     │ │ Search        │ │ DB            │
│               │ │ (Vector +     │ │ (Metadata)    │
│  - Embeddings │ │  Hybrid)      │ │               │
│  - Chat       │ │               │ │               │
│  - Summarize  │ │               │ │               │
└───────────────┘ └───────────────┘ └───────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Azure Blob Storage                           │
│              (Source Documents - PDFs from static.aer.ca)       │
└─────────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Microsoft Entra ID                           │
│              (Authentication + RBAC)                            │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow
1. Documents ingested from Blob Storage (mirroring static.aer.ca structure)
2. Azure AI Document Intelligence extracts text/structure
3. Text chunked (512 tokens, 128 overlap) and embedded via Azure OpenAI
4. Chunks indexed in Azure AI Search (vector + keyword hybrid)
5. Structured metadata stored in Cosmos DB with taxonomy
6. User queries processed via RAG pattern
7. Results filtered by user's Entra ID roles/claims

---

## Data Model

### Document Metadata (Cosmos DB)
```json
{
  "id": "doc-uuid",
  "proceedingId": "449",
  "applicationNumbers": ["1943077"],
  "regulatoryAppealNumber": null,
  "documentType": "decision|transcript|procedural|evidence|notice",
  "abaerCitation": "2024-ABAER-001",
  "title": "Decision: Northback Holdings Corporation Applications",
  "parties": [
    { "name": "Northback Holdings Corporation", "role": "applicant", "baCode": "A1B2C3" },
    { "name": "Smith Family", "role": "intervener" }
  ],
  "confidentialityLevel": "public|protected_a|confidential",
  "regulatoryCitations": [
    { "type": "legislation", "reference": "REDA s. 34" },
    { "type": "directive", "reference": "Directive 056" }
  ],
  "hearingDates": { "start": "2024-03-01", "end": "2024-03-15" },
  "decisionDate": "2024-06-01",
  "uploadedAt": "ISO8601",
  "sourceUrl": "https://static.aer.ca/prd/documents/decisions/2024/2024-ABAER-001.pdf",
  "processingStatus": "pending|indexed|failed",
  "pageCount": 87,
  "volumeNumber": null
}
```

### Search Index Schema (Azure AI Search)
```json
{
  "name": "hearings-index",
  "fields": [
    { "name": "id", "type": "Edm.String", "key": true },
    { "name": "documentId", "type": "Edm.String", "filterable": true },
    { "name": "proceedingId", "type": "Edm.String", "filterable": true, "facetable": true },
    { "name": "documentType", "type": "Edm.String", "filterable": true, "facetable": true },
    { "name": "chunkId", "type": "Edm.Int32" },
    { "name": "content", "type": "Edm.String", "searchable": true, "analyzer": "en.microsoft" },
    { "name": "contentVector", "type": "Collection(Edm.Single)", "dimensions": 3072, "vectorSearchProfile": "hnsw-profile" },
    { "name": "confidentialityLevel", "type": "Edm.String", "filterable": true },
    { "name": "parties", "type": "Collection(Edm.String)", "filterable": true, "facetable": true },
    { "name": "pageNumber", "type": "Edm.Int32", "sortable": true },
    { "name": "paragraphNumber", "type": "Edm.String", "filterable": true },
    { "name": "sectionTitle", "type": "Edm.String", "searchable": true },
    { "name": "regulatoryCitations", "type": "Collection(Edm.String)", "filterable": true, "facetable": true },
    { "name": "abaerCitation", "type": "Edm.String", "filterable": true }
  ],
  "vectorSearch": {
    "algorithms": [{ "name": "hnsw", "kind": "hnsw", "hnswParameters": { "m": 4, "efConstruction": 400, "efSearch": 500 } }],
    "profiles": [{ "name": "hnsw-profile", "algorithm": "hnsw", "vectorizer": "openai-vectorizer" }],
    "vectorizers": [{ "name": "openai-vectorizer", "kind": "azureOpenAI", "azureOpenAIParameters": { "deploymentId": "text-embedding-3-large" } }]
  },
  "semantic": {
    "configurations": [{
      "name": "semantic-config",
      "prioritizedFields": {
        "titleField": { "fieldName": "sectionTitle" },
        "contentFields": [{ "fieldName": "content" }]
      }
    }]
  }
}
```

### Access Control Matrix
| Role | Public | Protected A | Confidential |
|------|--------|-------------|--------------|
| Hearing Panel | ✓ | ✓ | ✓ |
| Staff | ✓ | ✓ | ✗ |
| Intervener | ✓ | Own Party | ✗ |
| Public | ✓ | ✗ | ✗ |

---

## API Contracts

### POST /api/search
Semantic search with role-based filtering.

**Request:**
```json
{
  "query": "What evidence exists for groundwater contamination near the proposed well site?",
  "proceedingId": "449",
  "filters": {
    "documentTypes": ["evidence", "transcript"],
    "parties": ["Northback Holdings Corporation"],
    "regulatoryCitations": ["EPEA"]
  },
  "top": 10,
  "searchMode": "hybrid"
}
```

**Response:**
```json
{
  "results": [
    {
      "documentId": "doc-uuid",
      "title": "Environmental Assessment Report",
      "abaerCitation": null,
      "snippet": "...groundwater samples from monitoring well MW-3 showed elevated levels of benzene at 0.008 mg/L, exceeding the EPEA Tier 1 guideline of 0.005 mg/L...",
      "relevanceScore": 0.92,
      "pageNumber": 47,
      "paragraphNumber": "[156]",
      "citationRef": "Proceeding 449, Exhibit 12.01, p.47, ¶156",
      "regulatoryCitations": ["EPEA s. 2", "Directive 056 s. 2.1"]
    }
  ],
  "totalCount": 23,
  "facets": {
    "documentType": [{ "value": "evidence", "count": 15 }, { "value": "transcript", "count": 8 }],
    "parties": [{ "value": "Northback Holdings Corporation", "count": 12 }]
  }
}
```

### POST /api/evidence/retrieve
Retrieve full evidence context with surrounding chunks.

**Request:**
```json
{
  "documentId": "doc-uuid",
  "chunkId": 15,
  "contextWindow": 2
}
```

**Response:**
```json
{
  "document": {
    "title": "Environmental Assessment Report",
    "proceedingId": "449",
    "citationRef": "Proceeding 449, Exhibit 12.01"
  },
  "chunks": [
    { "chunkId": 13, "paragraphNumber": "[154]", "content": "..." },
    { "chunkId": 14, "paragraphNumber": "[155]", "content": "..." },
    { "chunkId": 15, "paragraphNumber": "[156]", "content": "...", "isTarget": true },
    { "chunkId": 16, "paragraphNumber": "[157]", "content": "..." },
    { "chunkId": 17, "paragraphNumber": "[158]", "content": "..." }
  ],
  "pageRange": "45-48",
  "sourceUrl": "https://static.aer.ca/..."
}
```

### POST /api/documents/understand
Document analysis and summarization.

**Request:**
```json
{
  "documentId": "doc-uuid",
  "operations": ["summarize", "extractEntities", "extractKeyPoints", "extractRegulatoryCitations"]
}
```

**Response:**
```json
{
  "summary": "This decision addresses Northback Holdings Corporation's applications for coal exploration programs in the Rocky Mountain region. The panel considered statements of concern from 12 interveners regarding potential impacts to groundwater and wildlife habitat...",
  "entities": {
    "locations": ["Township 45, Range 23, W5M", "Crowsnest Pass"],
    "organizations": ["Northback Holdings Corporation", "Alberta Environment and Parks"],
    "wellIdentifiers": ["MW-3", "MW-7"],
    "dates": ["2024-03-01", "2024-06-15"],
    "regulations": ["EPEA s. 2", "REDA s. 34", "Directive 056 s. 2.1"]
  },
  "keyPoints": [
    "Groundwater monitoring detected benzene at 0.008 mg/L, exceeding Tier 1 guidelines",
    "Applicant committed to enhanced monitoring program per Directive 071",
    "Panel imposed 23 conditions on approval",
    "Intervener cost claims of $45,000 awarded in part"
  ],
  "regulatoryCitations": [
    { "reference": "REDA s. 34", "context": "Panel authority to impose conditions", "paragraphs": ["[45]", "[67]"] },
    { "reference": "EPEA s. 2", "context": "Environmental protection mandate", "paragraphs": ["[89]", "[112]"] },
    { "reference": "Directive 056 s. 2.1", "context": "Application requirements", "paragraphs": ["[23]"] }
  ]
}
```

### POST /api/documents/ingest
Upload and process new documents.

**Request:** `multipart/form-data`
- `file`: Document file (PDF)
- `metadata`: JSON with proceedingId, documentType, confidentialityLevel, parties

**Response:**
```json
{
  "documentId": "doc-uuid",
  "status": "processing",
  "estimatedCompletionMinutes": 5
}
```

### GET /api/proceedings/{proceedingId}
Get proceeding overview with all associated documents.

**Response:**
```json
{
  "proceedingId": "449",
  "title": "Summit Coal Ltd. Applications",
  "status": "active",
  "applicant": { "name": "Summit Coal Ltd.", "baCode": "..." },
  "interveners": [{ "name": "...", "role": "landowner" }],
  "hearingDates": { "start": "2025-02-01", "end": null },
  "documents": {
    "decisions": [],
    "transcripts": [{ "id": "...", "title": "Volume 1 - February 1, 2025" }],
    "evidence": [{ "id": "...", "title": "Applicant Opening Statement" }],
    "procedural": [{ "id": "...", "title": "Scheduling Order" }]
  },
  "timeline": [
    { "date": "2024-11-15", "event": "Statement of Concern filed" },
    { "date": "2025-01-10", "event": "Notice of Hearing issued" }
  ]
}
```

---

## Security Requirements

### Authentication
- All requests require valid Entra ID bearer token
- Token must include custom claims: `roles`, `partyAffiliation`, `baCode`
- Session timeout: 60 minutes

### Authorization Rules
```python
def can_access_document(user_claims: UserClaims, document: Document) -> bool:
    level = document.confidentiality_level
    
    if level == "public":
        return True
    
    if level == "protected_a":
        if "AER_Staff" in user_claims.roles:
            return True
        if "Hearing_Panel" in user_claims.roles:
            return True
        # Interveners can see their own party's protected documents
        if user_claims.party_affiliation:
            party_names = [p.name for p in document.parties]
            if user_claims.party_affiliation in party_names:
                return True
        return False
    
    if level == "confidential":
        return "Hearing_Panel" in user_claims.roles
    
    return False
```

### Search Filter Injection
```python
def build_search_filter(user_claims: UserClaims) -> str | None:
    """Always append user-based security filter to search queries."""
    filters = []
    
    if "Hearing_Panel" not in user_claims.roles:
        filters.append("confidentialityLevel ne 'confidential'")
    
    if "AER_Staff" not in user_claims.roles:
        if user_claims.party_affiliation:
            party_filter = f"(confidentialityLevel eq 'public' or parties/any(p: p eq '{user_claims.party_affiliation}'))"
            filters.append(party_filter)
        else:
            filters.append("confidentialityLevel eq 'public'")
    
    return " and ".join(filters) if filters else None
```

### Data Protection
- All data encrypted at rest (Azure Storage Service Encryption)
- TLS 1.3 for all traffic
- No PII in logs; use correlation IDs only
- Audit log all document access: user OID, document ID, timestamp, action

---

## Coding Standards

### Python (Backend)
- Python 3.12+
- Use `pydantic` v2 for all request/response models
- Async functions for all I/O operations
- Type hints required on all function signatures
- Use `structlog` for structured JSON logging
- Follow terminology in all code comments and variable names

```python
# Example: Use terminology
async def search_proceeding_documents(
    query: SearchRequest,
    proceeding_id: str,  # Not "case_id"
    user_claims: UserClaims,
    search_client: SearchClient
) -> SearchResponse:
    """Search documents within a specific proceeding."""
    ...
```

### TypeScript (Frontend)
- React 18+ with TypeScript strict mode
- Use TanStack Query for server state
- Tailwind CSS with color palette
- Components in `src/components/`, hooks in `src/hooks/`

### Style Guide Compliance
```css
/* Brand Colors */
:root {
  --aer-blue: #003366;
  --aer-teal: #00818a;
  --aer-light-blue: #e6f2f5;
  --aer-text: #333333;
  --aer-background: #ffffff;
}
```

### Error Handling
```python
class HearingsAIError(Exception):
    def __init__(self, code: str, message: str, status: int = 500):
        self.code = code
        self.message = message
        self.status = status

# Standard error codes
# AUTH_001: Invalid or expired token
# AUTH_002: Insufficient permissions for confidentiality level
# SEARCH_001: Query parsing failed
# SEARCH_002: Proceeding not found
# DOC_001: Document not found
# DOC_002: Document processing failed
# DOC_003: Confidentiality restriction
```

---

## File Structure
```
hearings-ai/
├── COPILOT.md
├── README.md
├── .env.example
├── infra/
│   ├── main.bicep
│   ├── modules/
│   │   ├── ai-search.bicep
│   │   ├── openai.bicep
│   │   ├── cosmos.bicep
│   │   ├── storage.bicep
│   │   └── container-apps.bicep
│   └── parameters/
│       ├── dev.bicepparam
│       └── prod.bicepparam
├── api/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── src/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── middleware.py
│   │   │   └── claims.py
│   │   ├── search/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── models.py
│   │   ├── documents/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── ingestion.py
│   │   │   └── models.py
│   │   ├── evidence/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── models.py
│   │   └── proceedings/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       ├── service.py
│   │       └── models.py
│   └── tests/
│       ├── conftest.py
│       ├── test_search.py
│       ├── test_auth.py
│       └── test_documents.py
├── web/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ResultsList.tsx
│   │   │   ├── DocumentViewer.tsx
│   │   │   ├── EvidencePanel.tsx
│   │   │   ├── ProceedingTimeline.tsx
│   │   │   └── CitationCard.tsx
│   │   ├── hooks/
│   │   │   ├── useSearch.ts
│   │   │   ├── useDocument.ts
│   │   │   └── useProceeding.ts
│   │   └── types/
│   │       └── index.ts
│   └── tests/
├── scripts/
│   ├── seed-data.py
│   ├── download-public-docs.py
│   └── run-local.sh
└── test-data/
    ├── documents/
    │   ├── 2024-ABAER-001-sample.pdf
    │   └── proceeding-449-transcript-sample.pdf
    └── metadata/
        └── sample-proceedings.json
```

---

## Test Data Sources

### Real Public Documents (for POC testing)
Download these from static.aer.ca:

**Decisions:**
- `https://static.aer.ca/prd/documents/decisions/2024/2024-ABAER-001.pdf` (87 pages)
- `https://static.aer.ca/prd/documents/decisions/2024/2024-ABAER-004.pdf`
- `https://static.aer.ca/prd/documents/decisions/2021/2021ABAER010.pdf` (Grassy Mountain, 200+ pages)

**Transcripts:**
- `https://static.aer.ca/aer/documents/applications/hearings/proceeding411-vol-1-march-08-2022.pdf`
- `https://static.aer.ca/aer/documents/applications/hearings/Proceeding-432-Vol-4-March-11-2024.pdf`

**Procedural:**
- `https://static.aer.ca/prd/documents/decisions/Participatory_Procedural/1927181_20200715.pdf`

### Synthetic Test Scenarios
See `test-data/metadata/sample-proceedings.json` for synthetic proceeding data covering:
- Coal exploration applications (like Proceeding 449)
- Pipeline regulatory appeals
- SAGD facility applications
- Multi-party intervener scenarios

---

## POC Milestones

### Week 1-2: Foundation
- [ ] Provision Azure resources (Bicep)
- [ ] Implement auth middleware with Entra ID
- [ ] Create document ingestion pipeline with taxonomy
- [ ] Download and seed with real public documents
- [ ] Validate document parsing (paragraph numbers, citations)

### Week 3-4: Core Features
- [ ] Implement semantic search with hybrid ranking
- [ ] Build evidence retrieval with paragraph-level context
- [ ] Add document understanding (summarize, entities, regulatory citations)
- [ ] Integrate RBAC filters into all queries
- [ ] Add proceeding overview endpoint

### Week 5-6: Frontend & Polish
- [ ] Build React search interface with styling
- [ ] Implement document viewer with highlights
- [ ] Add evidence citation panel with proper citation format
- [ ] Proceeding timeline visualization
- [ ] User acceptance testing with staff

---

## Environment Variables
```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_CHAT=gpt-4o
AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-3-large
AZURE_OPENAI_API_VERSION=2024-06-01

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<resource>.search.windows.net
AZURE_SEARCH_INDEX=hearings-index

# Cosmos DB
COSMOS_ENDPOINT=https://<resource>.documents.azure.com:443/
COSMOS_DATABASE=hearings
COSMOS_CONTAINER=documents

# Blob Storage
STORAGE_ACCOUNT_URL=https://<resource>.blob.core.windows.net
STORAGE_CONTAINER=hearing-documents

# Auth
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<app-registration-client-id>
```

---

## Copilot Instructions

When generating code for this project:

1. **Use terminology** - Use "proceeding" not "case", "intervener" not "plaintiff", "ABAER citation" not "ruling reference".

2. **Always apply security filters** - Never return search results or documents without checking `can_access_document()` against user claims.

3. **Use async patterns** - All database, search, and OpenAI calls must be async.

4. **Include proper citations** - Every search result must include `citationRef` in format: `Proceeding {ID}, {DocType}, p.{PageNum}, ¶{ParagraphNum}`.

5. **Extract regulatory references** - Parse and index REDA, EPEA, OGCA sections and Directive references from all documents.

6. **Validate inputs** - Use Pydantic models for all API request/response validation.

7. **Log with correlation** - Every request gets a correlation ID; include it in all log entries.

8. **Chunk documents properly** - Use 512 token chunks with 128 token overlap. Preserve paragraph number boundaries where possible.

9. **Handle errors gracefully** - Return structured error responses with codes; never expose stack traces.

10. **Test with roles** - Unit tests must cover all four access roles (Panel, Staff, Intervener, Public).

11. **Follow style** - Use the color palette (blue #003366, teal #00818a) and professional tone in UI.

12. **Parse document structure** - Recognize numbered paragraphs [1], [2], etc. and standard section headings (Decision Summary, Introduction, Regulatory Framework, Evidence and Arguments, Orders).
