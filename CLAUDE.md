# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nazmito is an AI-powered pre-authorization platform for UAE healthcare insurance that processes XML and CSV healthcare data into FHIR-compliant canonical JSON.

## Core Development Philosophy

- **Simplicity First**: Implement minimum viable code, avoid over-engineering
- **Direct Solutions**: Choose straightforward approaches, prefer composition over inheritance
- **Clear Code**: Use descriptive names, keep functions short (<50 lines), limit file size (<500 lines)
- **Temporary Files**: IF you create any temporary files which are not part of the feature or not supposed to be pushed to git, like .md, .py, .json, etc. then always put them in the `output/` folder with a <name_date_time> name, so i know they are temporary and not for the project to be pushed on git. if there is any file that needs to be kept, do not put it in the `output/` folder.
- **Package Importing**: Always import packages from root, and not local and relative importing
- Never use try/except block for importing a package. The required packages SHOULD be installed and if not,the system should fail.

## Sub-agent Usage Strategy

- **Maximize Parallelization**: When planning tasks, identify which steps can run in parallel vs sequential
- **Parallel Execution**: Use single message with multiple sub-agent calls for independent tasks
- **Sequential Dependencies**: Only run sub-agents sequentially when one depends on another's completion
- **Task Planning**: First identify available sub-agents, then plan which agent handles each step and execution order

## Commands

### Package Management
- **Package Manager**: `uv`
- **Install dependencies**: `uv pip install -e .`
- **Create virtual environment**: `uv venv .venv && source .venv/bin/activate`

### Code Quality
- **Format**: `black . --skip-string-normalization`
- **Lint**: `ruff check . --fix`
- **Tests**: `pytest` (structure: `/tests/unit/`, `/tests/integration/`)

### Running Applications & Demos
- **MVP Demo (CLI)**: `python -m preauth_system.demo` - Interactive demo with 3 test cases
- **FastAPI backend**: `python api/run_server.py` - Main API server
- **React Dashboard**: `cd ui-react && npm run dev` → http://localhost:5173
- **HTML Dashboard**: `cd ui && python3 -m http.server 8080` → http://localhost:8080/dashboard/dashboard.html
- **API docs**: http://localhost:8000/docs (auto-generated OpenAPI)

### MVP Processing Modes
- **Deterministic**: Policy rules only, no LLM calls, $0 cost
- **Hybrid**: Default mode, intelligent LLM routing, <$0.10 per case
- **Agentic**: Full LLM agent execution for complex cases

## Architecture

### MVP System Components (Implemented)
```
preauth_system/
├── orchestrator.py    # Main workflow orchestration
├── intake.py          # eClaimLink XML → Canonical mapping
├── summary.py         # Clinical data aggregation & FHIR integration
├── policy/            # Deterministic policy engine
│   ├── rules_engine.py
│   └── policies/      # YAML-based policy definitions
├── rag/              # Local knowledge base & retrieval
│   ├── kb_loader.py
│   ├── retrieve.py   # BM25 search with citations
│   └── tools.py      # Agent tools for KB queries
├── safety.py         # Drug interactions & risk assessment
├── decision.py       # Deterministic decision synthesis
├── compliance.py     # UAE PDPL & documentation auditing
├── dossier.py        # HTML report generation
└── demo.py           # Interactive CLI demonstration
```

### FastAPI Backend (`api/main.py`) - Production Ready
Core endpoints (all implemented):
- `POST /api/process/unified` - Multi-format processing (XML/CSV) with mode selection
- `GET /api/dossier/{analysis_id}` - Professional HTML/PDF dossier generation
- `GET /api/patients` - Synthetic patient data management
- `GET /api/dashboard/summary` - Real-time analytics and metrics
- `GET /api/health` - System health monitoring with detailed status
- `GET /api/docs` - Interactive OpenAPI documentation

### UI Architecture - Multi-Platform Implementation
- `ui-react/` - Production React dashboard (TypeScript, Tailwind, drag-drop processing)
- `ui/dashboard/` - HTML5 professional interface for simple deployment
- `ui/landing/` - Marketing website with investor pitch materials
- `ui/assets/` - Shared branding assets and clinical icons
- `demo/` - Professional investor demo materials and technical overviews

## UAE Healthcare Integration (Fully Compliant)
- **eClaimLink** (Dubai Health Authority): Complete XML parsing with validation
- **Shafafiya** (Abu Dhabi DOH): Native XML format support
- **ICD-10-AM**: UAE-specific diagnosis code mappings and validation
- **CPT/HCPCS**: Procedure code normalization with UAE extensions
- **PDPL Compliance**: UAE Personal Data Protection Law adherence
- **FHIR R4**: Complete UAE healthcare extensions implementation
- **Arabic Language**: Native RTL support for UI and reports

## Development Guidelines

### Production Development Patterns (Implemented)
- **Hybrid by Default**: Intelligent routing between deterministic rules and LLM agents
- **Cost Optimization**: 3-tier processing (Deterministic: $0, Hybrid: <$0.10, Agentic: <$0.25)
- **Agent Tools Architecture**: Tools-first approach with KB search, FHIR queries, safety checks
- **Policy as Code**: 3 production YAML policies with comprehensive criteria mapping
- **Evidence-Based Decisions**: Every decision includes clinical citations and policy references
- **Multi-Modal Processing**: Support for XML (eClaimLink/Shafafiya) and CSV clinical data
- **Caching Strategy**: Intelligent caching for patient summaries, policy evaluations, KB retrievals
- **Audit Trail**: Complete processing logs for regulatory compliance

### When building new features
- Follow the orchestrator pattern (preauth_system/orchestrator.py)
- Maintain consistent agent result structures
- Preserve all original data in `raw_data` field
- Use structured outputs via BAML schemas
- Add policy definitions to `preauth_system/policy/policies/`
- Include knowledge base content in `kb/` with proper citations

### Policy Engine Development (Production Implementation)
- **3 Clinical Pathways Implemented**: diabetes_technology.yaml, osteoarthritis_knee_intervention.yaml, parkinsons_dbs.yaml
- **Scoring System**: Percentage-based policy compliance (Patient_007: 100%, Patient_005: 20%, Patient_011: 18%)
- **Evidence Requirements**: Each criterion linked to clinical guidelines with specific citations
- **Tri-State Logic**: met/unmet/uncertain states with rationale for each criterion
- **Version Control**: Policy versioning with effective dates and change tracking
- **Testing Framework**: All policies validated against synthetic demo cases

### Multi-Agent System (LangGraph Implementation)
- **5 Specialized Agents**: clinical-analyzer, medication-specialist, risk-assessor, decision-maker, compliance-auditor
- **Tools-First Architecture**: Agents use tools (kb_search, fhir_query, safety_check) before LLM calls
- **BAML Integration**: Structured outputs with type safety and validation
- **Confidence Scoring**: Each agent provides confidence metrics (0-100%)
- **Token Optimization**: Efficient prompting with <$0.10 per case in hybrid mode
- **Intelligent Caching**: Patient summaries (1hr), policy evaluations (content-hash), KB retrievals (session-based)
- **Mode Selection**: Automatic routing based on case complexity and cost thresholds

### Error Handling
- Graceful degradation with fallback modes
- Comprehensive logging with structured data
- Performance monitoring and cost tracking
- Complete error context for troubleshooting

### Logging and Debugging
- Never create debug files outside of `logs/` folder
- Use structured JSON logging for production
- Track processing times and LLM token usage

## Production Documentation (Complete)
- **System Architecture**: `docs/system_design.md` - Complete technical implementation details
- **MVP Demo Guide**: `docs/mvp_demo_guide.md` - Step-by-step demonstration instructions
- **FHIR Implementation**: `docs/FHIR_GUIDE.md` - UAE healthcare data standards
- **Investor Materials**: `demo/` - Professional presentation materials and ROI analysis
- **API Documentation**: http://localhost:8000/docs - Interactive OpenAPI specification
- **Knowledge Base**: `kb/` - Clinical guidelines and policy documentation

## File Organization Guidelines
- Always keep the documents related to one part or topic in one single file in @docs/