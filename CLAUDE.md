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
- Never use try/except block for imports. if a necessary library is not installed, it should fail.

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
- **System Architecture**: `docs/system_design.md`
- **FHIR Implementation**: `docs/FHIR_GUIDE.md`

## File Organization Guidelines
- Always keep the documents related to one part or topic in one single file in @docs/