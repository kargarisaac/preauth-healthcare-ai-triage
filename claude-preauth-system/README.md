# Claude Pre-Authorization Analysis System

AI-powered healthcare decision support system for UAE insurance pre-authorization analysis using specialized Claude Code agents.

## Quick Start

```bash
# Install dependencies (from project root)
uv add claude-code-sdk loguru

# Run analysis
cd claude-preauth-system
./preauth_analyze.sh <xml_request> <patient_folder>
```

## Example Usage

```bash
# Analyze patient folder 10's latest request
./preauth_analyze.sh \
  ../data/synthetic_dataset/10/abudhabi_b7c8d9e0-1f2a-3b4c-5d6e-7f8g9h0i1j2k_20250820_req12_shafafiya.xml \
  ../data/synthetic_dataset/10/

# View results
ls ../analysis_results/analysis_*/
```

## System Components

- **orchestrator.py** - Python orchestrator coordinating 5 medical agents
- **preauth_analyze.sh** - User-friendly bash wrapper with validation
- **Medical Agents** - Located in `../.claude/agents/preauth/`
- **Results** - Saved to `../analysis_results/analysis_TIMESTAMP/`

## Output Files

Each analysis generates:
- `comprehensive_final_report.md` - Executive summary and recommendations
- `{agent-name}_analysis.md` - Individual specialist reports (5 files)
- `{agent-name}_debug.log` - Detailed processing logs (5 files)
- `analysis_metadata.json` - Processing statistics and timing

## Complete Documentation

See [`../docs/claude_preauth_system.md`](../docs/claude_preauth_system.md) for:
- System architecture and workflow
- Agent specializations and capabilities
- UAE healthcare compliance features
- Installation and configuration guide
- Troubleshooting and maintenance