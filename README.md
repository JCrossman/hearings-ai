# Hearings AI

Semantic search, evidence retrieval, and document understanding for hearing preparation.

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Azure CLI
- Azure subscription with OpenAI access

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

- **Azure AI Search** - Hybrid vector + keyword search
- **Azure OpenAI** - GPT-4o for understanding, text-embedding-3-large for vectors
- **Cosmos DB** - Document metadata and proceedings
- **Blob Storage** - PDF document storage
- **Entra ID** - Authentication and RBAC

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

## Security

All document access is filtered by confidentiality level:
- **Public** - Everyone
- **Protected A** - Staff, Panel, own-party
- **Confidential** - Panel only (requires s.49 order)

See `api/src/auth/__init__.py` for implementation.

## License

Internal use only
