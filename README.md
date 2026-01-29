# Hearings AI

> **Status:** ✅ Deployed and running in production  
> **Live URL:** https://lemon-river-0cd056d0f.4.azurestaticapps.net  
> **API:** https://hearingsai-api.lemonground-4dbaf9d3.canadacentral.azurecontainerapps.io

Semantic search and document understanding application for hearing preparation. Built with Python FastAPI, React TypeScript, and Azure AI services.

## 🎯 What's Implemented

### ✅ Completed Features
- **Authentication & Authorization**: Role-based access control (Staff, Hearing Panel, Intervener, Public)
- **Semantic Search**: Hybrid vector + keyword search across hearing documents
- **Document Security**: Confidentiality filtering (Public, Protected A, Confidential)
- **Search Service**: Full-text and vector similarity search with citation formatting
- **Web Interface**: React TypeScript frontend with role switching for demo
- **Azure Infrastructure**: Deployed to production with Container Apps, Static Web Apps, AI Search
- **API Documentation**: OpenAPI/Swagger at `/docs`

### 🚧 Planned Features (Not Yet Implemented)
- Evidence retrieval with context windows
- Document understanding (summarization, entity extraction)
- Document ingestion pipeline
- Proceeding overview pages
- Azure Cosmos DB integration (infrastructure ready, not connected)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Azure CLI
- Azure subscription with OpenAI and AI Search

### 1. Clone and Setup
```bash
# Install API dependencies
cd api
pip install -e ".[dev]"

# Install web dependencies
cd ../web
npm install
```

### 2. Deploy Infrastructure
```bash
cd infra

# Create resource group
az group create -n rg-hearingsai-dev -l canadacentral

# Deploy (update parameters first)
az deployment group create \
  -g rg-hearingsai-dev \
  -f main.bicep \
  -p environment=dev tenantId=<your-tenant> clientId=<your-app-id>
```

### 3. Get Test Data
```bash
cd scripts

# Download real public documents
python download-public-docs.py

# Or generate synthetic documents
python generate-synthetic-docs.py
```

### 4. Run Locally
```bash
# Copy .env.example to .env and fill in values from deployment outputs

# Start API
cd api
uvicorn src.main:app --reload

# Start web (separate terminal)
cd web
npm run dev
```

## Project Structure

```
hearings-ai/
├── COPILOT.md          # GitHub Copilot spec (READ THIS FIRST)
├── api/                # Python FastAPI backend
├── web/                # React frontend
├── infra/              # Bicep infrastructure as code
├── scripts/            # Data and utility scripts
└── test-data/          # Sample documents and metadata
```

## Key Files for Copilot

1. **COPILOT.md** - Complete specification including:
   - Terminology and document taxonomy
   - API contracts
   - Data models
   - Security/RBAC rules
   - Coding standards

2. **test-data/metadata/sample-proceedings.json** - Sample data structure

3. **api/src/models.py** - Pydantic models

## Architecture

### Deployed Infrastructure
- **Azure Container Apps** - FastAPI backend (Python 3.11)
- **Azure Static Web Apps** - React frontend (TypeScript + Vite)
- **Azure AI Search** - Hybrid vector + keyword search (Basic tier)
- **Azure OpenAI** - GPT-4o and text-embedding-3-large (East US)
- **Azure Container Registry** - Docker image storage
- **Azure Cosmos DB** - Infrastructure deployed, not yet integrated
- **Azure Blob Storage** - Infrastructure deployed, not yet integrated

### Technology Stack

**Backend:**
- FastAPI 0.128.0 with async support
- Pydantic 2.x for data validation
- Azure SDK for Python (azure-identity, azure-search-documents, openai)
- Structlog for structured logging
- Uvicorn ASGI server

**Frontend:**
- React 18 with TypeScript
- TanStack Query for data fetching
- Tailwind CSS for styling
- Vite for build tooling
- Lucide React for icons

**Infrastructure:**
- Bicep for IaC
- Managed identities for service authentication
- Role-based access control (RBAC)
- Canada Central region (data residency)

## Terminology

| Use This | Not This |
|----------|----------|
| Proceeding | Case |
| Intervener | Plaintiff |
| Hearing commissioner | Judge |
| Statement of concern | Complaint |
| ABAER decision | Ruling |

## Test Data Sources

### Real Public Documents (static.aer.ca)
- Decisions: `2024-ABAER-001.pdf`, `2021-ABAER-010.pdf` (Grassy Mountain)
- Transcripts: `proceeding-432-vol-4.pdf`
- Procedural: `proceeding-397-scheduling.pdf`

### Synthetic Documents
Run `scripts/generate-synthetic-docs.py` to create realistic test documents.

## Security & Access Control

### Role-Based Access
| Role | Public Docs | Protected A | Confidential |
|------|-------------|-------------|--------------|
| **Hearing Panel** | ✓ | ✓ | ✓ |
| **Staff** | ✓ | ✓ | ✗ |
| **Intervener** | ✓ | Own party only | ✗ |
| **Public** | ✓ | ✗ | ✗ |

### Security Features
- ✅ Entra ID authentication (production-ready, demo mode available)
- ✅ Server-side security filtering on all queries
- ✅ Managed identities for Azure service authentication
- ✅ No secrets in code or configuration
- ✅ Structured audit logging with correlation IDs
- ✅ TLS 1.3 for all connections

Implementation: See `api/src/auth/__init__.py`

## Development

### Running Tests
```bash
# API tests
cd api
pytest tests/ -v --cov=src

# Frontend tests  
cd web
npm run test
```

### Demo Mode
The application supports demo mode with X-Demo-Role header:
- `Staff` - Staff access
- `Hearing_Panel` - Full access
- `Intervener` - Intervener access  
- `Public` - Public access only

Set via environment variable or HTTP header for local development.

## Deployment

### Current Deployment
- **Environment**: Production (dev)
- **Resource Group**: rg-hearingsai-dev
- **Region**: Canada Central
- **API Version**: v4 (latest)
- **Deployed**: 2026-01-29

### Deploy Updates
```bash
# Build and push API
cd api
az acr build --registry hearingsaiacr --image hearingsai-api:v5 .

# Update Container App
az containerapp update -n hearingsai-api -g rg-hearingsai-dev \
  --image hearingsaiacr.azurecr.io/hearingsai-api:v5

# Deploy Web
cd web
npm run build
swa deploy --env production
```

## API Endpoints

### Implemented
- `GET /health` - Health check
- `POST /api/search` - Semantic search with role-based filtering

### Planned (501 Not Implemented)
- `POST /api/evidence/retrieve` - Evidence with context
- `POST /api/documents/understand` - Document analysis
- `POST /api/documents/ingest` - Upload documents
- `GET /api/proceedings/{id}` - Proceeding overview

Full API docs: https://hearingsai-api.lemonground-4dbaf9d3.canadacentral.azurecontainerapps.io/docs

## Project Status

**Phase 1: Foundation** ✅ Complete
- Infrastructure provisioned
- Authentication & authorization
- Search service implemented
- Web interface deployed

**Phase 2: Core Features** 🚧 In Progress
- Document ingestion pipeline
- Evidence retrieval with context
- Document understanding (AI analysis)

**Phase 3: Enhancement** 📋 Planned
- Proceeding overview pages
- Advanced search filters
- Document viewer
- User preferences

## Contributing

1. Clone the repository
2. Create a feature branch
3. Make changes following coding standards in COPILOT.md
4. Test locally
5. Submit pull request

## License

Internal use only
