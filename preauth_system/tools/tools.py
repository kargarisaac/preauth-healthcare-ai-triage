"""
RAG Tool Functions for Agent Integration
=======================================

Simplified RAG per requirements:
- Files with < threshold tokens: read entire file content inline
- Files with >= threshold tokens: use OpenAI File Search
- No BM25/NLTK or local vector search
"""

from __future__ import annotations

import os
import json
import time
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from preauth_system.utils import get_config

# OpenAI file-search for large files
try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

# Load config from shared utils
_CFG = get_config()


@dataclass
class ToolResponse:
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None
    cached: bool = False
    cost_info: Optional[Dict[str, Any]] = None


class RAGToolCache:
    def __init__(self, ttl_minutes: int = 60) -> None:
        self.ttl_seconds = ttl_minutes * 60
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}

    def _make_key(self, query: str, **params: Any) -> str:
        return json.dumps({"q": query, **params}, sort_keys=True)

    def get(self, query: str, **params: Any) -> Optional[Dict[str, Any]]:
        key = self._make_key(query, **params)
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl_seconds:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, query: str, value: Dict[str, Any], **params: Any) -> None:
        key = self._make_key(query, **params)
        self.cache[key] = value
        self.timestamps[key] = time.time()


# Tracing
class _RagToolsTracer:
    def __init__(self) -> None:
        traces_dir = Path(
            (_CFG.get("tracing", {}) or {}).get("dir", str(Path("output") / "traces"))
        ).resolve()
        traces_dir.mkdir(parents=True, exist_ok=True)
        day = datetime.utcnow().strftime("%Y%m%d")
        self.path = traces_dir / f"rag_tools_{day}.jsonl"

    def write(self, event: str, **payload: Any) -> None:
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {"ts": datetime.utcnow().isoformat(), "event": event, **payload}
                    )
                    + "\n"
                )
        except Exception:
            pass


_tools_tracer = _RagToolsTracer()


RAG_TRACE_CONTENT_MAX = 500


class RAGTools:
    def __init__(
        self,
        kb_directory: Path,
        index_path: Optional[Path] = None,
        enable_cache: bool = True,
        cache_ttl_minutes: int = 60,
    ):
        """
        Initialize simplified RAG tools with caching and token-aware behavior.
        """
        self.kb_directory = kb_directory

        cache_cfg = (
            ((_CFG.get("rag") or {}).get("cache")) if isinstance(_CFG, dict) else None
        ) or {}
        self.cache = (
            RAGToolCache(
                ttl_minutes=int(cache_cfg.get("ttl_minutes", cache_ttl_minutes))
            )
            if enable_cache
            else None
        )

        # Shared config lookups
        rag_cfg = (_CFG.get("rag") or {}) if isinstance(_CFG, dict) else {}
        self._large_file_token_threshold = int(
            rag_cfg.get("large_file_token_threshold", 10000)
        )
        self._openai_file_registry = Path(
            rag_cfg.get("openai_file_registry_path", "output/openai_files.json")
        ).resolve()
        self._kb_token_csv = Path(
            rag_cfg.get(
                "kb_token_csv_path", "preauth_system/rag/kb/kb_token_counts.csv"
            )
        ).resolve()
        self._max_large_files = int(rag_cfg.get("max_large_files", 3))

        # Internal registries
        self._kb_token_counts = self._load_kb_token_counts()
        self._openai_files = self._load_openai_file_registry()

    def _load_kb_token_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        try:
            if self._kb_token_csv.exists():
                import csv

                with open(self._kb_token_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        counts[row["file_path"]] = (
                            int(row["num_tokens"]) if row.get("num_tokens") else 0
                        )
            else:
                logging.warning(f"KB token CSV not found at: {self._kb_token_csv}")
        except Exception as e:  # pragma: no cover
            logging.warning(f"Failed to load KB token counts: {e}")
        return counts

    def _load_openai_file_registry(self) -> Dict[str, Any]:
        try:
            if self._openai_file_registry.exists():
                return json.loads(
                    self._openai_file_registry.read_text(encoding="utf-8")
                )
        except Exception:
            pass
        return {}

    def _save_openai_file_registry(self) -> None:
        self._openai_file_registry.parent.mkdir(parents=True, exist_ok=True)
        self._openai_file_registry.write_text(
            json.dumps(self._openai_files, indent=2), encoding="utf-8"
        )

    def _infer_policy_type(self, path: Path) -> Optional[str]:
        name = path.name.lower()
        if "diabetes" in name:
            return "diabetes_tech"
        if "osteo" in name:
            return "osteoarthritis"
        if "parkinson" in name:
            return "parkinson_dbs"
        return None

    def _list_kb_markdown_files(self) -> List[Path]:
        files: List[Path] = []
        if self.kb_directory.exists():
            for p in sorted(self.kb_directory.glob("**/*.md")):
                files.append(p)
        return files

    def _get_small_and_large_files(
        self, policy_filter: Optional[List[str]] = None
    ) -> Dict[str, List[Path]]:
        small: List[Path] = []
        large: List[Path] = []
        all_files = self._list_kb_markdown_files()
        for p in all_files:
            pt = self._infer_policy_type(p)
            if policy_filter and pt not in (policy_filter or []):
                continue
            tokens = self._kb_token_counts.get(str(p), 0)
            if tokens >= self._large_file_token_threshold:
                large.append(p)
            else:
                small.append(p)
        # limit large files for cost
        large = sorted(
            large,
            key=lambda x: self._kb_token_counts.get(str(x), 0),
            reverse=True,
        )[: self._max_large_files]
        return {"small": small, "large": large}

    def _ensure_openai_file_ids(self, file_paths: List[Path]) -> List[str]:
        if not file_paths:
            return []
        if OpenAI is None:
            logging.warning("OpenAI client not available; skipping file-search upload")
            return []
        client = OpenAI()
        file_ids: List[str] = []
        updated = False
        for p in file_paths:
            key = str(p)
            mtime = p.stat().st_mtime if p.exists() else 0
            rec = self._openai_files.get(key)
            if rec and rec.get("mtime") == mtime and rec.get("file_id"):
                file_ids.append(rec["file_id"])
                continue
            try:
                with open(p, "rb") as f:
                    uploaded = client.files.create(file=f, purpose="file_search")
                fid = getattr(uploaded, "id", None)
                if fid:
                    self._openai_files[key] = {"file_id": fid, "mtime": mtime}
                    file_ids.append(fid)
                    updated = True
                    _tools_tracer.write(
                        "openai_file_uploaded",
                        file=str(p),
                        file_id=fid,
                        size=os.path.getsize(p),
                    )
            except Exception as e:  # pragma: no cover
                logging.warning(f"Failed to upload file to OpenAI: {p} ({e})")
        if updated:
            self._save_openai_file_registry()
        return file_ids

    def _query_openai_file_search(
        self, query: str, file_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        if not file_ids or OpenAI is None:
            return None
        if self.cache:
            cached = self.cache.get(
                query, provider="openai_file_search", file_ids=file_ids
            )
            if cached:
                return cached
        try:
            from preauth_system.rag.openai_rag import query_large_file

            resp = query_large_file(query, file_ids=file_ids)
            data = {
                "provider": "openai_file_search",
                "text": resp.get("text") or "",
                "file_ids": file_ids,
            }
            if self.cache:
                self.cache.set(
                    query, data, provider="openai_file_search", file_ids=file_ids
                )
            return data
        except Exception as e:  # pragma: no cover
            logging.warning(f"OpenAI file search failed: {e}")
            return None

    def _read_text(self, p: Path) -> str:
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            try:
                return p.read_text(errors="ignore")
            except Exception:
                return ""

    def search_knowledge_base(
        self,
        query: str,
        top_k: int = 5,
        policy_filter: Optional[List[str]] = None,
    ) -> ToolResponse:
        start_time = time.time()

        try:
            cache_key_params = {
                "top_k": top_k,
                "policy_filter": policy_filter,
                "provider": "inline_and_file_search",
            }
            if self.cache:
                cached = self.cache.get(query, **cache_key_params)
                if cached:
                    return ToolResponse(
                        success=True,
                        data=cached,
                        processing_time_ms=(time.time() - start_time) * 1000,
                        cached=True,
                        cost_info={"cache_hit": True},
                    )

            fl = self._get_small_and_large_files(policy_filter)
            small_files = fl["small"]
            large_files = fl["large"]

            # Inline include: read entire small files
            evidence: List[Dict[str, Any]] = []
            for p in small_files:
                content = self._read_text(p)
                evidence.append(
                    {
                        "snippet_id": str(p),
                        "title": (p.stem.replace("_", " ") or "KB File"),
                        "policy_type": self._infer_policy_type(p),
                        "section": None,
                        "relevance_score": None,
                        "content": content,
                        "citation": f"{p.name}",
                    }
                )

            data: Dict[str, Any] = {
                "results_returned": len(evidence),
                "evidence": evidence if top_k <= 0 else evidence[: max(top_k, 1)],
            }

            # Augment with OpenAI file search for large files
            if large_files:
                file_ids = self._ensure_openai_file_ids(large_files)
                augmentation = self._query_openai_file_search(query, file_ids)
                if augmentation and augmentation.get("text"):
                    data["openai_file_search"] = augmentation

            if self.cache:
                self.cache.set(query, data, **cache_key_params)

            processing_time = (time.time() - start_time) * 1000
            try:
                _tools_tracer.write(
                    "rag_search",
                    provider="inline_and_file_search",
                    query=query,
                    top_k=top_k,
                    policy_filter=policy_filter,
                    results_returned=len(data.get("evidence", [])),
                    processing_time_ms=processing_time,
                )
            except Exception:
                pass

            return ToolResponse(
                success=True,
                data=data,
                processing_time_ms=processing_time,
                cached=False,
                cost_info={"openai_file_search_used": bool(large_files)},
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logging.error(f"RAG search failed: {e}")

            return ToolResponse(
                success=False,
                data=None,
                error=str(e),
                processing_time_ms=processing_time,
            )

    def get_policy_overview(self, policy_type: str) -> ToolResponse:
        """Return high-level policy information by parsing markdown headings."""
        start_time = time.time()
        try:
            files = [
                p
                for p in self._list_kb_markdown_files()
                if self._infer_policy_type(p) == policy_type
            ]
            sections: List[str] = []
            for p in files:
                text = self._read_text(p)
                for line in text.splitlines():
                    if line.lstrip().startswith("#"):
                        heading = line.lstrip("#").strip()
                        if heading:
                            sections.append(heading)
            # Deduplicate, keep order
            seen = set()
            ordered_sections = []
            for s in sections:
                if s not in seen:
                    seen.add(s)
                    ordered_sections.append(s)
            data = {
                "policy_type": policy_type,
                "total_sections": len(ordered_sections),
                "sections": ordered_sections,
            }
            return ToolResponse(
                success=True,
                data=data,
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ToolResponse(success=False, data=None, error=str(e))

    def validate_citation(self, snippet_id: str) -> ToolResponse:
        start_time = time.time()
        try:
            p = Path(snippet_id)
            if not p.exists():
                return ToolResponse(
                    success=False,
                    data=None,
                    error=f"Snippet {snippet_id} not found",
                    processing_time_ms=(time.time() - start_time) * 1000,
                )
            text = self._read_text(p)
            title = p.stem.replace("_", " ") or "KB File"
            citation_data = {
                "snippet_id": str(p),
                "title": title,
                "policy_type": self._infer_policy_type(p),
                "section": None,
                "citation": f"{p.name}",
                "full_content": text,
            }
            return ToolResponse(
                success=True,
                data=citation_data,
                processing_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ToolResponse(success=False, data=None, error=str(e))


def get_rag_tools(kb_directory: Path) -> "RAGTools":
    return RAGTools(kb_directory=kb_directory)


# Agent tool function definitions (for LangGraph integration)
def search_healthcare_policies(
    query: str, top_k: int = 5, policy_filter: Optional[str] = None
) -> str:
    """
    Search healthcare policy knowledge base (inline for small files; file search for large files).

    Args:
        query: Clinical question or search terms (e.g., "diabetes CGM coverage criteria")
        top_k: Maximum results to return (1-10, default 5)
        policy_filter: Filter by policy type - "diabetes_tech", "osteoarthritis", or "parkinson_dbs"

    Returns:
        JSON string with search results and formatted evidence
    """
    logger.info(
        f"[tool.enter] search_healthcare_policies query='{query[:120]}', top_k={top_k}, policy_filter={policy_filter}"
    )
    try:
        rag_tools = get_rag_tools(Path(__file__).parent.parent / "rag" / "kb")
    except Exception as e:
        logger.error(f"[tool.error] search_healthcare_policies missing KB: {e}")
        return json.dumps(
            {"success": False, "error": str(e), "missing_kb": True}, indent=2
        )

    # Convert policy_filter to list format if provided
    filter_list = [policy_filter] if policy_filter else None

    response = rag_tools.search_knowledge_base(
        query=query,
        top_k=min(max(top_k, 1), 10),  # Clamp to 1-10 range
        policy_filter=filter_list,
    )
    payload = response.to_dict()
    try:
        data = payload.get("data") or {}
        ids = [e.get("snippet_id") for e in (data.get("evidence") or [])]
        logger.info(
            f"[tool.exit] search_healthcare_policies success={payload.get('success')} returned={data.get('results_returned')} ids={ids[:5]}"
        )
    except Exception:
        logger.info(
            f"[tool.exit] search_healthcare_policies success={payload.get('success')} (summary unavailable)"
        )

    return json.dumps(payload, indent=2)


def get_policy_information(policy_type: str) -> str:
    """
    Get comprehensive overview of a specific healthcare policy.

    Args:
        policy_type: Policy type - "diabetes_tech", "osteoarthritis", or "parkinson_dbs"

    Returns:
        JSON string with policy overview and section structure
    """
    logger.info(f"[tool.enter] get_policy_information policy_type={policy_type}")
    try:
        rag_tools = get_rag_tools(Path(__file__).parent.parent / "rag" / "kb")
    except Exception as e:
        logger.error(f"[tool.error] get_policy_information missing KB: {e}")
        return json.dumps(
            {"success": False, "error": str(e), "missing_kb": True}, indent=2
        )

    response = rag_tools.get_policy_overview(policy_type)
    payload = response.to_dict()
    try:
        data = payload.get("data") or {}
        logger.info(
            f"[tool.exit] get_policy_information success={payload.get('success')} sections={data.get('total_sections')}"
        )
    except Exception:
        logger.info(
            f"[tool.exit] get_policy_information success={payload.get('success')} (summary unavailable)"
        )

    return json.dumps(payload, indent=2)


def validate_evidence_citation(snippet_id: str) -> str:
    """
    Validate and get detailed citation information for evidence.

    Args:
        snippet_id: expected to be a file path to a KB markdown file

    Returns:
        JSON string with full citation and source information
    """
    logger.info(f"[tool.enter] validate_evidence_citation snippet_id={snippet_id}")
    try:
        rag_tools = get_rag_tools(Path(__file__).parent.parent / "rag" / "kb")
    except Exception as e:
        logger.error(f"[tool.error] validate_evidence_citation missing KB: {e}")
        return json.dumps(
            {"success": False, "error": str(e), "missing_kb": True}, indent=2
        )

    response = rag_tools.validate_citation(snippet_id)
    payload = response.to_dict()
    try:
        data = payload.get("data") or {}
        logger.info(
            f"[tool.exit] validate_evidence_citation success={payload.get('success')} title={data.get('title')!r}"
        )
    except Exception:
        logger.info(
            f"[tool.exit] validate_evidence_citation success={payload.get('success')} (summary unavailable)"
        )

    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    # Example usage and testing
    import sys
    from pathlib import Path

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Get knowledge base path
    if len(sys.argv) > 1:
        kb_path = Path(sys.argv[1])
    else:
        kb_path = Path(__file__).parent.parent / "rag" / "kb"

    try:
        # Create RAG tools
        rag_tools = get_rag_tools(kb_path)

        # Test search functionality
        print("🔍 Testing RAG Tools:\n")

        # Test 1: Search for diabetes technology
        print("1. Testing diabetes technology search...")
        response = rag_tools.search_knowledge_base(
            "CGM continuous glucose monitoring coverage criteria",
            top_k=3,
            policy_filter=["diabetes_tech"],
        )
        print(f"   Success: {response.success}")
        if response.success:
            print(f"   Results: {response.data['results_returned']}")
            print(f"   Cache hit: {response.cached}")

        # Test 2: Get policy overview
        print("\n2. Testing policy overview...")
        response = rag_tools.get_policy_overview("osteoarthritis")
        print(f"   Success: {response.success}")
        if response.success:
            print(f"   Sections: {response.data['total_sections']}")

        # Test 3: Cache performance (same query)
        print("\n3. Testing cache performance...")
        response = rag_tools.search_knowledge_base(
            "CGM continuous glucose monitoring coverage criteria",
            top_k=3,
            policy_filter=["diabetes_tech"],
        )
        print(f"   Cache hit: {response.cached}")

        # Print usage stats
        # The original code had get_usage_stats(), but it's not defined in the new RAGTools class.
        # For now, we'll just print the relevant info.
        print(f"\n📊 Usage Statistics:")
        print(
            f"   Knowledge base size: {len(rag_tools._list_kb_markdown_files())} snippets"
        )

    except Exception as e:
        logging.error(f"❌ Failed to test RAG tools: {e}")
        sys.exit(1)
