# Changelog

All notable changes to the Hearings AI project will be documented in this file.

## [0.2.0] - 2026-01-29

### 🎉 Deployed to Production
- Deployed API backend to Azure Container Apps (Canada Central)
- Deployed web frontend to Azure Static Web Apps  
- Published to GitHub: https://github.com/JCrossman/hearings-ai

### ✨ Added
- Semantic search API endpoint with hybrid vector + keyword search
- Role-based access control (Staff, Hearing Panel, Intervener, Public)
- Confidentiality filtering (Public, Protected A, Confidential)
- React TypeScript web interface with role switching
- Authentication system with Entra ID integration (demo mode supported)
- Health check endpoint for monitoring
- Structured logging with correlation IDs
- Citation formatting for search results

### 🏗️ Infrastructure
- Azure Container Apps for API hosting
- Azure Static Web Apps for frontend
- Azure AI Search (Basic tier) with hybrid search
- Azure OpenAI (GPT-4o, text-embedding-3-large)
- Azure Container Registry for images
- Azure Cosmos DB (deployed, not yet integrated)
- Azure Blob Storage (deployed, not yet integrated)
- Bicep infrastructure as code

### 🔒 Security
- Managed identity authentication for Azure services
- Server-side security filtering on all queries
- No secrets in code or configuration files
- TLS 1.3 for all connections
- Audit logging for all document access

### 📝 Documentation
- Updated README with deployment status
- Added CHANGELOG for version tracking
- Maintained COPILOT.md for development guidelines
- Maintained AGENTS.md for multi-agent development

### 🔧 Technical Details
- **API Version**: v4
- **Python**: 3.11
- **FastAPI**: 0.128.0
- **React**: 18
- **Node**: 20
- **Region**: Canada Central (data residency)

### 🚧 Known Limitations
- Evidence retrieval not yet implemented (returns 501)
- Document understanding not yet implemented (returns 501)
- Document ingestion not yet implemented (returns 501)
- Proceeding overview not yet implemented (returns 501)
- Cosmos DB and Blob Storage infrastructure ready but not connected

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
| v4 | 2026-01-29 | Production | Initial production deployment |
| v3 | 2026-01-28 | Dev | Pre-release testing |
| v2 | 2026-01-28 | Dev | Infrastructure validation |
| v1 | 2026-01-28 | Dev | Initial build |
