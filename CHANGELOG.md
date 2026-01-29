# Changelog

All notable changes to the Hearings AI project will be documented in this file.

## [0.2.0] - 2026-01-29

### 🎉 Deployed to Production
- Deployed API backend to Azure Container Apps (Canada Central) - v7
- Deployed web frontend to Azure Static Web Apps  
- Published to GitHub: https://github.com/JCrossman/hearings-ai
- **Search index populated**: 5,693 chunks from 54 real PDF documents

### ✨ Added - Authentication & Security
- Azure Static Web Apps authentication (GitHub/Microsoft login)
- Email-based allowlist for access control (managed via environment variables)
- Frontend sends user email via `X-User-Email` header
- Backend validates against `ALLOWED_USERS` allowlist
- Documentation: `ALLOWLIST.md` for managing user access

### ✨ Added - Search & Indexing
- **Search index created**: `hearings-index` with 16 fields
- **Document ingestion**: 54 PDFs processed from `test-data/documents/`
- **Vector embeddings**: text-embedding-3-large (3072 dimensions)
- **Hybrid search**: Vector + keyword with semantic ranking
- **Chunking strategy**: 512 tokens with 128 token overlap
- **Faceting**: Document types, parties, regulatory citations

### ✨ Added - User Interface
- **Interactive Quick Filters**: Clickable filter badges with toggle behavior
- **Active filter styling**: Selected filters highlighted in teal
- **Real-time filtering**: Clicking filter triggers new search
- **Party display**: Party names shown in search results (when available)
- **Facet counts**: Each filter shows document count

### 🔧 Technical Improvements
- Cloud-based Docker builds via `az acr build` (avoids local network issues)
- Explicit Static Web Apps deployment to production environment
- Frontend build automation includes `staticwebapp.config.json`
- API returns party data in search results
- TypeScript interfaces updated for party field

### 🏗️ Infrastructure
- Azure Container Apps for API hosting
- Azure Static Web Apps for frontend with authentication
- Azure AI Search (Basic tier) with hybrid search
- Azure OpenAI (GPT-4o, text-embedding-3-large)
- Azure Container Registry for images
- Azure Cosmos DB (deployed, metadata storage failing - RBAC issue)
- Azure Blob Storage (deployed, not yet integrated)
- Bicep infrastructure as code

### 🔒 Security
- Managed identity authentication for Azure services
- Server-side security filtering on all queries
- No secrets in code or configuration files
- TLS 1.3 for all connections
- Audit logging for all document access
- Two-tier authentication: Static Web Apps + API allowlist

### 📝 Documentation
- Updated README with authentication setup
- Added ALLOWLIST.md for user management
- Updated CHANGELOG with all recent changes
- Maintained COPILOT.md for development guidelines
- Maintained AGENTS.md for multi-agent development

### 🔧 Technical Details
- **API Version**: v7
- **Python**: 3.11
- **FastAPI**: 0.128.0
- **React**: 18
- **Node**: 20
- **Region**: Canada Central (data residency)
- **Search Documents**: 54 PDFs (5,693 chunks)

### 🚧 Known Limitations
- Evidence retrieval not yet implemented (returns 501)
- Document understanding not yet implemented (returns 501)
- Party metadata not populated in indexed documents (field exists but empty)
- Cosmos DB metadata storage failing (RBAC permissions issue - doesn't affect search)
- Allowlist can be disabled by removing `ALLOWED_USERS` env var

---

## [0.1.0] - 2026-01-28

### Initial Setup
- Project scaffolding and structure
- API backend foundation with FastAPI
- React TypeScript frontend setup
- Azure infrastructure defined in Bicep
- Basic authentication and authorization framework
- Data models and API contracts defined
- Test data collection (80+ real ABAER documents)
- Development environment configuration

### Project Structure
- `/api` - Python FastAPI backend
- `/web` - React TypeScript frontend
- `/infra` - Azure Bicep IaC
- `/scripts` - Utility scripts for data processing
- `/test-data` - Sample documents and metadata

---

## Future Releases

### [0.3.0] - Planned
**Evidence Retrieval**
- Implement evidence retrieval with context windows
- Add paragraph-level citation tracking
- Support for surrounding context extraction

**Document Understanding**
- Summarization of hearing documents
- Entity extraction (parties, citations, dates)
- Key points identification
- Regulatory citation detection

### [0.4.0] - Planned
**Document Ingestion**
- File upload capability
- Azure Document Intelligence integration
- Text chunking and embedding pipeline
- Search index population
- Cosmos DB metadata storage

**Proceeding Overview**
- Proceeding detail pages
- Document timeline view
- Party and participant information
- Related documents grouping

### [0.5.0] - Planned
**Enhanced Search**
- Advanced search filters
- Date range filtering
- Party-specific searches
- Document type faceting
- Saved searches

**User Experience**
- Document viewer with highlighting
- Export search results
- Bookmarking capability
- User preferences

---

## Notes

### Versioning
This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes to API or major feature overhaul
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes and minor improvements

### Deployment History
| Version | Date | Environment | Notes |
|---------|------|-------------|-------|
| v7 | 2026-01-29 | Production | Added party field to search results |
| v6 | 2026-01-29 | Production | Added X-User-Email header support |
| v5 | 2026-01-29 | Production | Added email allowlist validation |
| v4 | 2026-01-29 | Production | Initial production deployment with authentication |
| v3 | 2026-01-28 | Dev | Pre-release testing |
| v2 | 2026-01-28 | Dev | Infrastructure validation |
| v1 | 2026-01-28 | Dev | Initial build |
