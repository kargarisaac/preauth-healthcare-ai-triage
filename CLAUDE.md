# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nazmito is an intelligent AI-powered pre-authorization platform for UAE healthcare insurance. It transforms manual pre-authorization processes into opportunities for cost savings, quality improvement, and enhanced patient outcomes by applying AI and clinical rules to enrich authorization decisions.

## Commands and Development

### Package Management
- **Package Manager**: `uv` (ultra-fast Python package manager)
- **Install dependencies**: `uv pip install -r pyproject.toml`
- **Add new package**: `uv pip install <package_name>`
- **Create virtual environment**: `uv venv .venv && source .venv/bin/activate`

### Code Quality
- **Format code**: `black . --skip-string-normalization`
- **Lint code**: `ruff check . --fix`
- **Run pre-commit hooks**: `pre-commit run --all-files`

### Running the Application
- **Run main script**: `python main.py`
- **Run XML validation**: `python data_pipelines/eclaim_link.py`

### Website Development
- **View website locally**:
  - Open directly: `open website/nazmito-website.html`
  - Or start server: `python3 -m http.server 8000` in website directory
- **New UI version**: Located in `new-ui/` folder with modern design

## Architecture Overview

### Core Components

1. **Data Ingestion Pipeline** (`data_pipelines/`)
   - `eclaim_link.py`: Handles XML normalization for UAE healthcare formats (eClaimLink/Shafafiya)
   - Supports two XML formats: 2019/11 PriorAuthorizationRequest and 2011 Prior.Authorization
   - Validates against XSD schemas and normalizes to unified structure

2. **XML Schemas** (`schemas/`)
   - `CommonTypes_20191113.xsd`: Common types for UAE healthcare data
   - `PriorAuthorization.xsd`: Prior authorization request schema

3. **Website** (`website/` and `new-ui/`)
   - Marketing website and investor pitch materials
   - Two versions: original in `website/`, modern redesign in `new-ui/`

### Architecture Overview (See docs/ARCHITECTURE.md)

The system implements a modern medallion architecture with AI-powered processing:
- **Bronze Layer**: Raw ingested data with immutable storage and SHA-256 hashing
- **Silver Layer**: Cleaned, source-shaped data with basic validation
- **Gold Layer**: FHIR-compliant canonical schema with UAE extensions
- **AI Layer**: Vector embeddings, knowledge graphs (KuzuDB), and LLM agents (LangGraph)

Key pipeline stages:
1. Multi-format ingestion (XML/CSV/PDF/OCR)
2. Data quality scoring and validation
3. FHIR canonical mapping with UAE extensions
4. AI enrichment with clinical context
5. Event streaming via Kafka
6. Explainable decision support

**Detailed Technical Design**: See `/docs/ARCHITECTURE.md` for complete system architecture

## Key UAE Healthcare Standards

- **eClaimLink** (Dubai Health Authority): XML-based claims and authorization system
- **Shafafiya** (Abu Dhabi Department of Health): Healthcare data exchange platform
- **ICD-10-AM**: Australian modification of ICD-10 used in UAE
- **CPT**: Current Procedural Terminology codes

## Development Guidelines

### When working with XML data
- Always validate against the appropriate XSD schema before processing
- Use the `normalize_prior_authorization()` function for consistent data structure
- Check both 2019/11 and 2011 format compatibility

### When building new features
- Follow the sprint-based architecture in `docs/todo_list.md` (28-day MVP timeline)
- Reference complete technical design in `docs/ARCHITECTURE.md`
- Use FHIR implementation guide in `docs/FHIR_GUIDE.md` for clinical data handling
- Maintain compatibility with UAE healthcare standards (eClaimLink, Shafafiya)
- Ensure PDPL (Personal Data Protection Law) compliance for UAE

### API and Integration Points
- REST API implemented with FastAPI (`/ingest`, `/claim/{id}`, `/search`, `/chat`)
- Kafka event streaming for real-time data flow
- FHIR-compliant canonical schema with UAE extensions
- WebSocket support for conversational AI interfaces
- Server-sent events for real-time dashboard updates

## Testing Strategy
- Create tests in `tests/` directory (currently not present but planned)
- Use pytest for unit and integration tests
- Validate all XML processing against sample files in `samples/`

## Security and Compliance Considerations
- UAE PDPL compliance required
- ADHICS (Abu Dhabi Healthcare Information and Cyber Security) standards
- ISO 27001 certification planned
- All data must be encrypted at rest (AES-256) and in transit (TLS 1.2+)
