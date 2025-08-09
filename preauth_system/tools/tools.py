"""
RAG Tool Functions for Agent Integration
=======================================

Tool functions for KB search and evidence retrieval that integrate with LangGraph agents.
Provides structured outputs, citation formatting, and cost-aware caching.

This module provides functionality to:
- Tool functions for KB search and evidence retrieval
- Citation formatting for agent responses  
- Cost tracking and token budgets for LLM calls
- Caching layer for repeated retrievals
- Integration with existing agent workflow
"""

import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import logging
import os
from loguru import logger

from preauth_system.rag.retrieve import create_retriever, RetrievalResponse


@dataclass
class ToolResponse:
    """Standardized tool response format for agent consumption."""

    success: bool
    data: Any
    error: Optional[str] = None
    processing_time_ms: float = 0
    cached: bool = False
    cost_info: Dict[str, Any] = None

    def __post_init__(self):
        if self.cost_info is None:
            self.cost_info = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


# Lightweight JSONL tracer for RAG tools
class _RagToolsTracer:
    def __init__(self) -> None:
        traces_dir = Path("output") / "traces"
        traces_dir.mkdir(parents=True, exist_ok=True)
        day = datetime.utcnow().strftime("%Y%m%d")
        self.path = traces_dir / f"rag_tools_{day}.jsonl"

    def write(self, event: str, **payload: Any) -> None:
        record = {
            "ts": datetime.utcnow().isoformat(),
            "event": event,
            **payload,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


_tools_tracer = _RagToolsTracer()
# Optional: include content previews in trace. Set RAG_TOOLS_LOG_CONTENT to an int (chars)
try:
    RAG_TRACE_CONTENT_MAX = int(os.getenv("RAG_TOOLS_LOG_CONTENT", "0"))
except Exception:
    RAG_TRACE_CONTENT_MAX = 0


class RAGToolCache:
    """
    Simple in-memory cache for RAG retrieval results to reduce costs.

    Implements aggressive caching to meet <$0.10/case cost target.
    """

    def __init__(self, ttl_minutes: int = 60, max_size: int = 1000):
        """
        Initialize cache with TTL and size limits.

        Args:
            ttl_minutes: Time-to-live for cached entries in minutes
            max_size: Maximum number of entries to cache
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_minutes = ttl_minutes
        self.max_size = max_size

    def _get_cache_key(self, query: str, **kwargs) -> str:
        """Generate cache key from query and parameters."""
        key_data = {"query": query.lower().strip(), **kwargs}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def get(self, query: str, **kwargs) -> Optional[Any]:
        """Get cached result if available and not expired."""
        cache_key = self._get_cache_key(query, **kwargs)

        if cache_key in self.cache:
            entry = self.cache[cache_key]

            # Check if entry has expired
            cached_time = datetime.fromisoformat(entry["timestamp"])
            if datetime.now() - cached_time < timedelta(minutes=self.ttl_minutes):
                logging.debug(f"Cache hit for query: {query[:50]}...")
                return entry["data"]
            else:
                # Remove expired entry
                del self.cache[cache_key]

        return None

    def set(self, query: str, data: Any, **kwargs) -> None:
        """Cache result with current timestamp."""
        cache_key = self._get_cache_key(query, **kwargs)

        # Implement simple LRU by removing oldest entries when at max size
        if len(self.cache) >= self.max_size:
            oldest_key = min(
                self.cache.keys(), key=lambda k: self.cache[k]["timestamp"]
            )
            del self.cache[oldest_key]

        self.cache[cache_key] = {"data": data, "timestamp": datetime.now().isoformat()}

        logging.debug(f"Cached result for query: {query[:50]}...")

    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()
        logging.info("RAG cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "entries": len(self.cache),
            "max_size": self.max_size,
            "ttl_minutes": self.ttl_minutes,
        }


class RAGTools:
    """
    RAG tool functions for LangGraph agent integration.

    Provides standardized tool functions with caching, cost tracking,
    and structured outputs for agent consumption.
    """

    def __init__(
        self,
        kb_directory: Union[str, Path],
        index_path: Optional[Union[str, Path]] = None,
        enable_cache: bool = True,
        cache_ttl_minutes: int = 60,
    ):
        """
        Initialize RAG tools with retriever and caching.

        Args:
            kb_directory: Path to knowledge base directory
            index_path: Optional path to search index
            enable_cache: Whether to enable result caching
            cache_ttl_minutes: Cache TTL in minutes
        """
        self.retriever = create_retriever(kb_directory, index_path)
        self.cache = (
            RAGToolCache(ttl_minutes=cache_ttl_minutes) if enable_cache else None
        )

        # Cost tracking
        self.total_retrievals = 0
        self.cache_hits = 0

        logging.info(
            f"✅ RAG Tools initialized with {len(self.retriever.kb_loader.snippets)} snippets"
        )

    def search_knowledge_base(
        self,
        query: str,
        top_k: int = 5,
        policy_filter: Optional[List[str]] = None,
        min_score: float = 0.1,
    ) -> ToolResponse:
        """
        Search knowledge base for relevant evidence.

        This is the primary tool function for agent knowledge retrieval.

        Args:
            query: Search query describing the clinical question
            top_k: Maximum number of results to return (1-10)
            policy_filter: Filter by policy types (diabetes_tech, osteoarthritis, parkinson_dbs)
            min_score: Minimum relevance score threshold (0.0-1.0)

        Returns:
            ToolResponse with formatted search results and citations
        """
        start_time = time.time()
        self.total_retrievals += 1

        try:
            # Check cache first
            cached_result = None
            if self.cache:
                cache_params = {
                    "top_k": top_k,
                    "policy_filter": policy_filter,
                    "min_score": min_score,
                }
                cached_result = self.cache.get(query, **cache_params)

                if cached_result:
                    self.cache_hits += 1
                    processing_time = (time.time() - start_time) * 1000
                    # Trace cached retrieval
                    try:
                        ids = [
                            e.get("snippet_id")
                            for e in cached_result.get("evidence", [])
                        ]
                        _tools_tracer.write(
                            "rag_search",
                            cached=True,
                            query=query,
                            top_k=top_k,
                            policy_filter=policy_filter,
                            results_returned=len(cached_result.get("evidence", [])),
                            snippet_ids=ids,
                            processing_time_ms=processing_time,
                        )
                    except Exception:
                        pass

                    return ToolResponse(
                        success=True,
                        data=cached_result,
                        processing_time_ms=processing_time,
                        cached=True,
                        cost_info={"cache_hit": True, "retrieval_avoided": True},
                    )

            # Perform retrieval
            response = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                policy_filter=policy_filter,
                min_score=min_score,
                expand_query=True,
            )

            # Format for agent consumption
            formatted_data = self._format_retrieval_response(response)

            # Cache result
            if self.cache:
                cache_params = {
                    "top_k": top_k,
                    "policy_filter": policy_filter,
                    "min_score": min_score,
                }
                self.cache.set(query, formatted_data, **cache_params)

            processing_time = (time.time() - start_time) * 1000

            # Trace retrieval summary (IDs and titles only)
            try:
                ids = [e.get("snippet_id") for e in formatted_data.get("evidence", [])]
                titles = [e.get("title") for e in formatted_data.get("evidence", [])]
                payload = {
                    "event": "rag_search",
                    "cached": False,
                    "query": query,
                    "top_k": top_k,
                    "policy_filter": policy_filter,
                    "results_returned": formatted_data.get("results_returned", 0),
                    "snippet_ids": ids,
                    "titles_preview": titles[:5],
                    "processing_time_ms": processing_time,
                }
                if RAG_TRACE_CONTENT_MAX > 0:
                    previews = []
                    for ev in formatted_data.get("evidence", [])[:5]:
                        previews.append(
                            {
                                "snippet_id": ev.get("snippet_id"),
                                "title": ev.get("title"),
                                "content_preview": (ev.get("content") or "")[
                                    :RAG_TRACE_CONTENT_MAX
                                ],
                            }
                        )
                    payload["evidence_preview"] = previews
                _tools_tracer.write(**payload)
            except Exception:
                pass

            return ToolResponse(
                success=True,
                data=formatted_data,
                processing_time_ms=processing_time,
                cached=False,
                cost_info={
                    "query_expansion_terms": len(response.query_expansion),
                    "total_snippets_searched": len(self.retriever.kb_loader.snippets),
                },
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logging.error(f"Knowledge base search failed: {e}")
            try:
                _tools_tracer.write(
                    "rag_search_error",
                    query=query,
                    top_k=top_k,
                    policy_filter=policy_filter,
                    error=str(e),
                    processing_time_ms=processing_time,
                )
            except Exception:
                pass

            return ToolResponse(
                success=False,
                data=None,
                error=str(e),
                processing_time_ms=processing_time,
                cost_info={"error": True},
            )

    def get_policy_overview(self, policy_type: str) -> ToolResponse:
        """
        Get overview of specific policy type with key sections.

        Args:
            policy_type: Policy type (diabetes_tech, osteoarthritis, parkinson_dbs)

        Returns:
            ToolResponse with policy overview and key sections
        """
        start_time = time.time()

        try:
            # Validate policy type
            valid_policies = ["diabetes_tech", "osteoarthritis", "parkinson_dbs"]
            if policy_type not in valid_policies:
                return ToolResponse(
                    success=False,
                    data=None,
                    error=f"Invalid policy type. Must be one of: {valid_policies}",
                )

            # Check cache
            cached_result = None
            if self.cache:
                cached_result = self.cache.get(f"policy_overview_{policy_type}")

                if cached_result:
                    self.cache_hits += 1
                    processing_time = (time.time() - start_time) * 1000
                    try:
                        _tools_tracer.write(
                            "rag_policy_overview",
                            cached=True,
                            policy_type=policy_type,
                            total_sections=cached_result.get("total_sections"),
                            processing_time_ms=processing_time,
                        )
                    except Exception:
                        pass

                    return ToolResponse(
                        success=True,
                        data=cached_result,
                        processing_time_ms=processing_time,
                        cached=True,
                    )

            # Get policy overview
            response = self.retriever.search_by_policy_type(
                policy_type=policy_type,
                query=None,  # Get all sections
                top_k=20,
            )

            # Organize by sections
            sections = {}
            for result in response.results:
                section = result.section
                if section not in sections:
                    sections[section] = []
                sections[section].append(
                    {
                        "title": result.title,
                        "snippet_id": result.snippet_id,
                        "subsection": result.subsection,
                        "content_preview": result.content[:200] + "..."
                        if len(result.content) > 200
                        else result.content,
                    }
                )

            formatted_data = {
                "policy_type": policy_type,
                "policy_name": self.retriever.kb_loader.policy_types.get(
                    policy_type, {}
                ).get("name", policy_type),
                "total_sections": len(sections),
                "sections": sections,
                "last_updated": datetime.now().isoformat(),
            }

            # Cache result
            if self.cache:
                self.cache.set(f"policy_overview_{policy_type}", formatted_data)

            processing_time = (time.time() - start_time) * 1000
            try:
                _tools_tracer.write(
                    "rag_policy_overview",
                    cached=False,
                    policy_type=policy_type,
                    total_sections=formatted_data["total_sections"],
                    processing_time_ms=processing_time,
                )
            except Exception:
                pass

            return ToolResponse(
                success=True,
                data=formatted_data,
                processing_time_ms=processing_time,
                cached=False,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logging.error(f"Policy overview failed: {e}")
            try:
                _tools_tracer.write(
                    "rag_policy_overview_error",
                    policy_type=policy_type,
                    error=str(e),
                    processing_time_ms=processing_time,
                )
            except Exception:
                pass

            return ToolResponse(
                success=False,
                data=None,
                error=str(e),
                processing_time_ms=processing_time,
            )

    def get_related_evidence(self, snippet_id: str, top_k: int = 3) -> ToolResponse:
        """
        Get evidence related to a specific knowledge snippet.

        Args:
            snippet_id: ID of reference knowledge snippet
            top_k: Number of related snippets to return

        Returns:
            ToolResponse with related evidence
        """
        start_time = time.time()

        try:
            # Check cache
            cached_result = None
            if self.cache:
                cached_result = self.cache.get(f"related_{snippet_id}_{top_k}")

                if cached_result:
                    self.cache_hits += 1
                    processing_time = (time.time() - start_time) * 1000
                    try:
                        ids = [
                            e.get("snippet_id")
                            for e in cached_result.get("related_evidence", [])
                        ]
                        _tools_tracer.write(
                            "rag_related_evidence",
                            cached=True,
                            reference_snippet_id=snippet_id,
                            results_returned=len(ids),
                            snippet_ids=ids,
                            processing_time_ms=processing_time,
                        )
                    except Exception:
                        pass

                    return ToolResponse(
                        success=True,
                        data=cached_result,
                        processing_time_ms=processing_time,
                        cached=True,
                    )

            # Get related snippets
            related_results = self.retriever.get_related_snippets(
                snippet_id=snippet_id, top_k=top_k
            )

            if not related_results:
                return ToolResponse(
                    success=False,
                    data=None,
                    error=f"No related evidence found for snippet_id: {snippet_id}",
                )

            # Format results
            formatted_data = {
                "reference_snippet_id": snippet_id,
                "related_evidence": [],
            }

            for result in related_results:
                formatted_data["related_evidence"].append(
                    {
                        "snippet_id": result.snippet_id,
                        "title": result.title,
                        "policy_type": result.policy_type,
                        "section": result.section,
                        "relevance_score": result.score,
                        "content": result.content,
                        "citation": result.get_citation_text(),
                    }
                )

            # Cache result
            if self.cache:
                self.cache.set(f"related_{snippet_id}_{top_k}", formatted_data)

            processing_time = (time.time() - start_time) * 1000
            try:
                ids = [
                    e.get("snippet_id")
                    for e in formatted_data.get("related_evidence", [])
                ]
                payload = {
                    "event": "rag_related_evidence",
                    "cached": False,
                    "reference_snippet_id": snippet_id,
                    "results_returned": len(ids),
                    "snippet_ids": ids,
                    "processing_time_ms": processing_time,
                }
                if RAG_TRACE_CONTENT_MAX > 0:
                    previews = []
                    for ev in formatted_data.get("related_evidence", [])[:5]:
                        previews.append(
                            {
                                "snippet_id": ev.get("snippet_id"),
                                "title": ev.get("title"),
                                "content_preview": (ev.get("content") or "")[
                                    :RAG_TRACE_CONTENT_MAX
                                ],
                            }
                        )
                    payload["evidence_preview"] = previews
                _tools_tracer.write(**payload)
            except Exception:
                pass

            return ToolResponse(
                success=True,
                data=formatted_data,
                processing_time_ms=processing_time,
                cached=False,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logging.error(f"Related evidence search failed: {e}")

            return ToolResponse(
                success=False,
                data=None,
                error=str(e),
                processing_time_ms=processing_time,
            )

    def validate_citation(self, snippet_id: str) -> ToolResponse:
        """
        Validate and get full citation information for a knowledge snippet.

        Args:
            snippet_id: ID of knowledge snippet to validate

        Returns:
            ToolResponse with full citation details
        """
        start_time = time.time()

        try:
            snippet = self.retriever.get_snippet_by_id(snippet_id)

            if not snippet:
                return ToolResponse(
                    success=False, data=None, error=f"Snippet not found: {snippet_id}"
                )

            citation_data = {
                "snippet_id": snippet.id,
                "title": snippet.title,
                "policy_type": snippet.policy_type,
                "section": snippet.section,
                "subsection": snippet.subsection,
                "source_file": snippet.source_file,
                "citations": snippet.citations,
                "metadata": snippet.metadata,
                "formatted_citation": f"**{snippet.title}** ({snippet.policy_type}) - Section: {snippet.section}",
                "full_content": snippet.content,
            }

            processing_time = (time.time() - start_time) * 1000
            try:
                payload = {
                    "event": "rag_validate_citation",
                    "snippet_id": snippet_id,
                    "title": snippet.title,
                    "policy_type": snippet.policy_type,
                    "section": snippet.section,
                    "processing_time_ms": processing_time,
                }
                if RAG_TRACE_CONTENT_MAX > 0:
                    payload["content_preview"] = (snippet.content or "")[
                        :RAG_TRACE_CONTENT_MAX
                    ]
                _tools_tracer.write(**payload)
            except Exception:
                pass

            return ToolResponse(
                success=True,
                data=citation_data,
                processing_time_ms=processing_time,
                cached=False,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logging.error(f"Citation validation failed: {e}")

            return ToolResponse(
                success=False,
                data=None,
                error=str(e),
                processing_time_ms=processing_time,
            )

    def _format_retrieval_response(
        self, response: "RetrievalResponse"
    ) -> Dict[str, Any]:
        """Format retrieval response for agent consumption."""
        if not response.results:
            return {
                "query": response.query,
                "found_evidence": False,
                "message": f"No relevant evidence found for: '{response.query}'",
                "suggestions": [
                    "Try rephrasing your query with different medical terminology",
                    "Check if you're searching for the correct policy type",
                    "Consider broader search terms",
                ],
            }

        formatted_results: List[Dict[str, Any]] = []
        for result in response.results:
            formatted_results.append(
                {
                    "snippet_id": result.snippet_id,
                    "title": result.title,
                    "policy_type": result.policy_type,
                    "section": result.section,
                    "subsection": result.subsection,
                    "relevance_score": round(result.score, 3),
                    "content": result.content,
                    "citations": result.citations,
                    "formatted_citation": result.get_citation_text(),
                    "source_file": Path(result.source_file).name,
                }
            )

        return {
            "query": response.query,
            "found_evidence": True,
            "total_results": response.total_results,
            "results_returned": len(response.results),
            "query_expansions": response.query_expansion,
            "evidence": formatted_results,
            "formatted_summary": response.get_formatted_results(include_content=False),
            "processing_time_ms": response.processing_time_ms,
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for cost tracking."""
        cache_hit_rate = (
            (self.cache_hits / self.total_retrievals * 100)
            if self.total_retrievals > 0
            else 0
        )
        stats = {
            "total_retrievals": self.total_retrievals,
            "cache_hits": self.cache_hits,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "knowledge_base_size": len(self.retriever.kb_loader.snippets),
            "has_search_index": self.retriever.kb_loader.index is not None,
        }
        if self.cache:
            stats["cache_stats"] = self.cache.get_stats()
        return stats


# Global RAG tools instance for agent integration
_rag_tools_instance = None


def get_rag_tools(kb_directory: Optional[Union[str, Path]] = None) -> RAGTools:
    """
    Get global RAG tools instance for agent integration.

    Args:
        kb_directory: Path to knowledge base directory (for initialization)

    Returns:
        Global RAGTools instance
    """
    global _rag_tools_instance

    if _rag_tools_instance is None:
        if kb_directory is None:
            # Prefer package KB under preauth_system/rag/kb with sensible fallbacks
            candidate_paths = [
                Path(__file__).parent.parent / "rag" / "kb",  # preauth_system/rag/kb
                Path.cwd() / "preauth_system" / "rag" / "kb",  # CWD absolute
                Path(__file__).parent.parent.parent / "kb",  # repo_root/kb
                Path.cwd() / "kb",  # CWD/kb
            ]
            for p in candidate_paths:
                if p.exists():
                    kb_directory = p
                    break
            if kb_directory is None:
                searched = [str(p) for p in candidate_paths]
                raise FileNotFoundError(
                    "Knowledge base not found. Place KB under one of: "
                    + ", ".join(searched)
                )

        _rag_tools_instance = RAGTools(kb_directory)
        logging.info(f"✅ Global RAG tools instance created (KB: {kb_directory})")

    return _rag_tools_instance


# Agent tool function definitions (for LangGraph integration)
def search_healthcare_policies(
    query: str, top_k: int = 5, policy_filter: Optional[str] = None
) -> str:
    """
    Search healthcare policy knowledge base for relevant evidence.

    Use this tool to find specific policy requirements, coverage criteria,
    or clinical guidelines relevant to a pre-authorization request.

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
        rag_tools = get_rag_tools()
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

    Use this tool to understand the structure and key requirements
    of a specific policy before searching for detailed criteria.

    Args:
        policy_type: Policy type - "diabetes_tech", "osteoarthritis", or "parkinson_dbs"

    Returns:
        JSON string with policy overview and section structure
    """
    logger.info(f"[tool.enter] get_policy_information policy_type={policy_type}")
    try:
        rag_tools = get_rag_tools()
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

    Use this tool to verify evidence sources and get complete
    citation details for recommendations.

    Args:
        snippet_id: ID of the evidence snippet to validate

    Returns:
        JSON string with full citation and source information
    """
    logger.info(f"[tool.enter] validate_evidence_citation snippet_id={snippet_id}")
    try:
        rag_tools = get_rag_tools()
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
        kb_path = Path(__file__).parent.parent.parent / "kb"

    try:
        # Create RAG tools
        rag_tools = RAGTools(kb_path)

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
        stats = rag_tools.get_usage_stats()
        print(f"\n📊 Usage Statistics:")
        print(f"   Total retrievals: {stats['total_retrievals']}")
        print(f"   Cache hit rate: {stats['cache_hit_rate_percent']}%")
        print(f"   Knowledge base size: {stats['knowledge_base_size']} snippets")

    except Exception as e:
        logging.error(f"❌ Failed to test RAG tools: {e}")
        sys.exit(1)
