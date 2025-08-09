# Nazmito

AI-powered pre-authorization platform for UAE healthcare insurance that processes XML and CSV healthcare data into FHIR-compliant canonical JSON.

## Quick Start

### Setup
```bash
# Create and activate a virtual environment (optional)
uv venv .venv && source .venv/bin/activate

# Install dependencies
uv sync
```

### Running the System

**API Server:**
```bash
uv run python api/run_server.py
```
→ API docs: http://localhost:8000/api/docs

**Professional Dashboard:**
```bash
cd ui-react && uv run npm install && uv run npm run dev
```

**Demo Cases:**
```bash
uv run python -m tests.manual.run_single_agent --agent clinical-analyzer --xml data/dataset_2/synthetic_dataset/UAE_XML/Patient_007_eclaim.xml
```

### MCP Tools
- Start MCP server (for agents):
```bash
uv run python -m preauth_system.tools.mcp_server
```
- Quick tool check (direct):
```bash
uv run python tests/manual/run_mcp_tools.py
```

## Recommended way to run scripts in a package
- Prefer module-style execution so Python sets the package context correctly:
```bash
uv run python -m tests.manual.run_single_agent --agent clinical-analyzer --xml path/to.xml
```
- If you must run scripts by path, ensure the project is importable:
  - Option A (recommended): run with `-m` as above
  - Option B: install the package in editable mode (see below)

## Editable install (optional)
If you want to run scripts by path (not via `-m`) and import `preauth_system` anywhere, install the repo in editable mode. Setuptools needs explicit package discovery to avoid the “Multiple top-level packages discovered” error.

1) Update `pyproject.toml` package discovery (already configured):
```toml
[tool.setuptools]
packages = [
  "preauth_system",
  "data_ingestion",
  "api",
]
```

2) Install in editable mode once per environment:
```bash
uv pip install -e .
```
After that, `uv run python tests/manual/run_single_agent.py ...` will work because `preauth_system` is importable as an installed package.

## Architecture

### Core Components
- **API Layer** (`api/main.py`): FastAPI backend with endpoints
- **Orchestrator** (`preauth_system/orchestrator.py`): Main workflow coordinator
- **Policy Engine** (`preauth_system/policy/`): YAML-based rules engine
- **RAG System** (`preauth_system/rag/`): Knowledge retrieval with BM25S
- **Agent Tools** (`preauth_system/tools/`): MCP tools for Claude Code agents

### LangGraph Workflow
- **5 Specialized Agents**: Clinical analyzer, medication specialist, risk assessor, decision maker, compliance auditor
- **3-Phase Process**: Clinical analysis → Risk assessment → Decision & compliance

## Development

### Code Quality
```bash
uv run ruff check . --fix       # Lint
uv run black .                  # Format
uv run pytest                   # Test
```

### Key Endpoints
- `POST /api/process/eclaim` - Process eClaimLink XML files
- `GET /api/health` - Health check

---

Built with FastAPI, LangGraph, and Claude Code agents following CLAUDE.md principles.