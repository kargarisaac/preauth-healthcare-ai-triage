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

### Running Applications
- **FastAPI backend**: `python api/run_server.py`
- **Professional dashboard**: `cd ui && python3 -m http.server 8080` → http://localhost:8080/dashboard/dashboard.html
- **API docs**: http://localhost:8000/api/docs

## Architecture

### Data Processors
- **XMLProcessor** (`pipelines/xml_processor.py`): Handles eClaimLink (Dubai) and Shafafiya (Abu Dhabi) formats
- **CSVProcessor** (`pipelines/csv_processor.py`): Processes healthcare CSV with intelligent column detection and FHIR resource mapping

### Usage
See `docs/xml_processing.md` and `docs/csv_processing.md` for usage examples.

### Output Structure
Both processors return FHIR Bundle with:
- `resourceType: "Bundle"`
- Essential mapped fields (authorization_id, sender, receiver)
- FHIR resources (Claims, ServiceRequests, Observations, MedicationStatements, Conditions, Procedures)
- Complete original data preserved in `raw_data` field
- Processing metadata

### FastAPI Backend (`api/main.py`)
Key endpoints:
- `POST /api/process/eclaim` - Process eClaimLink XML files
- `POST /api/process/shafafiya` - Process Shafafiya XML files
- `POST /api/process/csv` - Process healthcare CSV files
- `GET /api/health` - Health check

### UI Structure
- `ui/landing/` - Marketing website
- `ui/dashboard/` - Professional processing interface with drag-drop upload
- `ui/assets/` - Shared brand assets

## Key UAE Healthcare Standards
- **eClaimLink** (Dubai Health Authority): XML-based claims system
- **Shafafiya** (Abu Dhabi Department of Health): Healthcare data exchange
- **ICD-10-AM**: Australian modification of ICD-10 used in UAE
- **CPT**: Current Procedural Terminology codes

## Development Guidelines

### When building new features
- Follow the processor pattern (XMLProcessor/CSVProcessor style)
- Maintain Bundle structure for consistent output
- Preserve all original data in `raw_data` field
- Map core fields only, avoid over-engineering
- Use `if __name__ == '__main__':` sections for standalone testing

### Error Handling
- Graceful handling with default values
- Comprehensive logging with loguru
- Complete error context for troubleshooting

### Logging and Debugging
- Never create any debug or log result of test anywhere outside of the @logs folder

## Documentation References
- **System Architecture**: `docs/ARCHITECTURE.md`
- **FHIR Implementation**: `docs/FHIR_GUIDE.md`
- **XML Processing**: `docs/xml_processing.md`
- **CSV Processing**: `docs/csv_processing.md`
- **Format Comparison**: `docs/format_comparison.md`
- **Field Mappings**: `docs/field_mappings.md`

## File Organization Guidelines
- Always keep the documents related to one part or topic in one single file in @docs/