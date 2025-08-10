from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from loguru import logger

from preauth_system.tools.tools import get_rag_tools
from preauth_system.utils import get_config

# OpenAI Agents SDK tool decorator
try:
    from agents.tool import function_tool as tool_function  # type: ignore
except Exception as e:  # pragma: no cover
    logger.warning(f"Agents tool decorator not available: {e}")

    def tool_function(fn):  # type: ignore
        return fn


# Load shared config once
_CFG = get_config()


def _resolve_kb_path() -> Path:
    rag_cfg = _CFG.get("rag", {}) if isinstance(_CFG, dict) else {}
    kb_dirs: List[str] = rag_cfg.get("kb_dirs", []) or []
    for p in [Path(x) for x in kb_dirs]:
        if p.exists():
            return p
    # Fallback to default kb folder inside repo if config missing
    return Path("preauth_system/rag/kb")


def _get_tools_singleton():
    kb_path = _resolve_kb_path()
    return get_rag_tools(kb_path)


@tool_function
def search_healthcare_policies(
    query: str, top_k: int = 5, policy_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Search healthcare policy knowledge base for relevant evidence.

    - query: user query string
    - top_k: number of results to return (1-10)
    - policy_filter: optional list of policy tags ["diabetes_tech"|"osteoarthritis"|"parkinson_dbs"]
    """
    tools = _get_tools_singleton()
    resp = tools.search_knowledge_base(
        query=query, top_k=top_k, policy_filter=policy_filter
    )
    return resp.to_dict()


@tool_function
def get_policy_information(policy_type: str) -> Dict[str, Any]:
    """Get comprehensive overview of a specific healthcare policy.

    - policy_type: one of ["diabetes_tech"|"osteoarthritis"|"parkinson_dbs"]
    """
    tools = _get_tools_singleton()
    resp = tools.get_policy_overview(policy_type)
    return resp.to_dict()


@tool_function
def validate_evidence_citation(snippet_id: str) -> Dict[str, Any]:
    """Validate and get detailed citation information for evidence snippet.

    - snippet_id: knowledge base snippet identifier
    """
    tools = _get_tools_singleton()
    resp = tools.validate_citation(snippet_id)
    return resp.to_dict()


def get_openai_tools(tool_names: List[str]) -> List[Any]:
    registry: Dict[str, Any] = {
        "search_healthcare_policies": search_healthcare_policies,
        "get_policy_information": get_policy_information,
        "validate_evidence_citation": validate_evidence_citation,
    }
    selected = []
    for n in tool_names:
        if n in registry:
            selected.append(registry[n])
        else:
            logger.warning(f"Requested unknown tool: {n}")
    return selected
