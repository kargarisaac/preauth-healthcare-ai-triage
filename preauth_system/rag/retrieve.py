"""
RAG Retrieval System for Pre-Authorization
==========================================

BM25S-based semantic retrieval over local knowledge base.
Returns top-k sections with citations and evidence for agent tool calling.

This module provides functionality to:
- Perform semantic search over healthcare policy knowledge base
- Query expansion for medical terms and concepts
- Return structured results with citations and provenance
- Integration with LangGraph agent tool calling
"""

import logging
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from preauth_system.rag.kb_loader import KnowledgeBaseLoader, KnowledgeSnippet


@dataclass
class RetrievalResult:
    """Individual retrieval result with scoring and metadata."""

    snippet_id: str
    title: str
    content: str
    source_file: str
    policy_type: str
    section: str
    subsection: Optional[str]
    citations: List[str]
    score: float
    rank: int
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    def get_citation_text(self) -> str:
        """Get formatted citation text for this result."""
        citation = f"**{self.title}** ({self.policy_type})"
        if self.subsection:
            citation += f" - {self.subsection}"
        citation += f" [Source: {Path(self.source_file).name}]"
        return citation


@dataclass
class RetrievalResponse:
    """Complete retrieval response with results and metadata."""

    query: str
    results: List[RetrievalResult]
    total_results: int
    query_expansion: List[str]
    processing_time_ms: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "results": [result.to_dict() for result in self.results],
            "total_results": self.total_results,
            "query_expansion": self.query_expansion,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
        }

    def get_formatted_results(self, include_content: bool = True) -> str:
        """Get formatted results text for agent consumption."""
        if not self.results:
            return f"No relevant information found for query: '{self.query}'"

        formatted = f"**Retrieved Evidence for: '{self.query}'**\n\n"
        formatted += f"Found {len(self.results)} relevant sections:\n\n"

        for i, result in enumerate(self.results, 1):
            formatted += f"**{i}. {result.get_citation_text()}**\n"
            formatted += f"   Relevance Score: {result.score:.3f}\n"

            if include_content:
                # Truncate content if too long
                content = result.content
                if len(content) > 500:
                    content = content[:500] + "..."
                formatted += f"   Content: {content}\n"

            if result.citations:
                formatted += f"   Citations: {', '.join(result.citations)}\n"

            formatted += "\n"

        return formatted


class HealthcareQueryExpander:
    """
    Expands medical queries with synonyms and related terms.

    Focuses on UAE healthcare terminology and common medical concepts
    relevant to pre-authorization scenarios.
    """

    def __init__(self):
        """Initialize with medical terminology mappings."""
        self.medical_synonyms = {
            # Diabetes related terms
            "diabetes": ["diabetes mellitus", "dm", "diabetic", "glucose", "insulin"],
            "cgm": [
                "continuous glucose monitoring",
                "glucose monitor",
                "blood glucose",
            ],
            "pump": ["insulin pump", "insulin delivery", "insulin therapy"],
            "hba1c": ["hemoglobin a1c", "glycated hemoglobin", "glucose control"],
            # Orthopedic terms
            "osteoarthritis": ["oa", "arthritis", "joint degeneration", "cartilage"],
            "knee": ["patella", "tibia", "femur", "meniscus"],
            "hip": ["acetabulum", "femoral head", "pelvis"],
            "joint": ["articulation", "synovial", "cartilage"],
            # Neurological terms
            "parkinson": ["pd", "parkinsonian", "parkinsonism"],
            "dbs": ["deep brain stimulation", "brain stimulation", "neurostimulation"],
            "tremor": ["shaking", "oscillation", "movement disorder"],
            "bradykinesia": ["slow movement", "reduced movement"],
            # General medical terms
            "therapy": ["treatment", "intervention", "management"],
            "medication": ["drug", "pharmaceutical", "medicine"],
            "diagnosis": ["condition", "disease", "disorder"],
            "treatment": ["therapy", "intervention", "care"],
            "conservative": ["non-surgical", "non-invasive", "medical management"],
        }

        # Common medical abbreviations
        self.abbreviations = {
            "dm": "diabetes mellitus",
            "oa": "osteoarthritis",
            "pd": "parkinson disease",
            "dbs": "deep brain stimulation",
            "cgm": "continuous glucose monitoring",
            "bmi": "body mass index",
            "htn": "hypertension",
            "cad": "coronary artery disease",
        }

    def expand_query(self, query: str, max_expansions: int = 3) -> List[str]:
        """
        Expand query with medical synonyms and related terms.

        Args:
            query: Original search query
            max_expansions: Maximum number of expansion terms per concept

        Returns:
            List of expanded query terms
        """
        query_lower = query.lower()
        expansions = [query]  # Include original query

        # Expand abbreviations
        for abbrev, expansion in self.abbreviations.items():
            if abbrev in query_lower:
                expanded_query = query_lower.replace(abbrev, expansion)
                if expanded_query not in expansions:
                    expansions.append(expanded_query)

        # Expand synonyms
        words = query_lower.split()
        for word in words:
            if word in self.medical_synonyms:
                synonyms = self.medical_synonyms[word][:max_expansions]
                for synonym in synonyms:
                    # Replace word with synonym in query
                    expanded_query = query_lower.replace(word, synonym)
                    if expanded_query not in expansions:
                        expansions.append(expanded_query)

        return expansions[:5]  # Limit total expansions


class RAGRetriever:
    """
    BM25S-based retrieval system for healthcare policy knowledge base.

    Features:
    - Semantic search with BM25S ranking
    - Medical query expansion
    - Result filtering and ranking
    - Citation and provenance tracking
    - Integration with agent tool calling
    """

    def __init__(self, kb_loader: KnowledgeBaseLoader):
        """
        Initialize retriever with knowledge base loader.

        Args:
            kb_loader: Initialized KnowledgeBaseLoader with search index
        """
        self.kb_loader = kb_loader
        self.query_expander = HealthcareQueryExpander()

        if not kb_loader.index:
            logging.warning(
                "⚠️ No search index found. Create index first for optimal performance."
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.1,
        policy_filter: Optional[List[str]] = None,
        expand_query: bool = True,
    ) -> RetrievalResponse:
        """
        Retrieve relevant knowledge snippets for a query.

        Args:
            query: Search query
            top_k: Number of top results to return
            min_score: Minimum relevance score threshold
            policy_filter: Filter by policy types (e.g., ['diabetes_tech'])
            expand_query: Whether to apply query expansion

        Returns:
            RetrievalResponse with results and metadata
        """
        import time

        start_time = time.time()

        if not self.kb_loader.snippets:
            logging.warning("⚠️ No knowledge base loaded")
            return RetrievalResponse(
                query=query,
                results=[],
                total_results=0,
                query_expansion=[],
                processing_time_ms=0,
                metadata={"error": "No knowledge base loaded"},
            )

        # Query expansion
        expanded_queries = []
        if expand_query:
            expanded_queries = self.query_expander.expand_query(query)
        else:
            expanded_queries = [query]

        # Retrieve results for each expanded query
        all_results = []
        for exp_query in expanded_queries:
            results = self._search_knowledge_base(
                exp_query,
                top_k * 2,
                policy_filter,  # Get more results initially
            )
            all_results.extend(results)

        # Deduplicate and re-rank results
        seen_ids = set()
        unique_results = []
        for result in all_results:
            if result.snippet_id not in seen_ids:
                seen_ids.add(result.snippet_id)
                unique_results.append(result)

        # Sort by score and apply filters
        unique_results.sort(key=lambda x: x.score, reverse=True)
        filtered_results = [r for r in unique_results if r.score >= min_score]
        final_results = filtered_results[:top_k]

        # Update ranks
        for i, result in enumerate(final_results):
            result.rank = i + 1

        processing_time = (time.time() - start_time) * 1000

        return RetrievalResponse(
            query=query,
            results=final_results,
            total_results=len(filtered_results),
            query_expansion=expanded_queries[1:],  # Exclude original query
            processing_time_ms=processing_time,
            metadata={
                "policy_filter": policy_filter,
                "min_score": min_score,
                "query_expanded": expand_query,
            },
        )

    def _search_knowledge_base(
        self, query: str, top_k: int, policy_filter: Optional[List[str]] = None
    ) -> List[RetrievalResult]:
        """
        Search knowledge base using BM25S or fallback to simple text matching.

        Args:
            query: Search query
            top_k: Number of results to return
            policy_filter: Optional policy type filter

        Returns:
            List of retrieval results
        """
        if self.kb_loader.index:
            return self._search_with_bm25s(query, top_k, policy_filter)
        else:
            return self._search_with_text_matching(query, top_k, policy_filter)

    def _search_with_bm25s(
        self, query: str, top_k: int, policy_filter: Optional[List[str]] = None
    ) -> List[RetrievalResult]:
        """Search using BM25S index."""
        try:
            # Tokenize query
            query_tokens = self.kb_loader._tokenize_text(query)

            # If tokenization yields no tokens, fall back silently
            if not query_tokens:
                return self._search_with_text_matching(query, top_k, policy_filter)

            # BM25S expects a batch of queries (list of token lists)
            results, scores = self.kb_loader.index.retrieve([query_tokens], k=top_k)

            retrieval_results = []
            for i, (doc_idx, score) in enumerate(zip(results[0], scores[0])):
                if 0 <= doc_idx < len(self.kb_loader.snippets):
                    snippet = self.kb_loader.snippets[doc_idx]

                    # Apply policy filter
                    if policy_filter and snippet.policy_type not in policy_filter:
                        continue

                    result = RetrievalResult(
                        snippet_id=snippet.id,
                        title=snippet.title,
                        content=snippet.content,
                        source_file=snippet.source_file,
                        policy_type=snippet.policy_type,
                        section=snippet.section,
                        subsection=snippet.subsection,
                        citations=snippet.citations,
                        score=float(score),
                        rank=i + 1,
                        metadata=snippet.metadata,
                    )
                    retrieval_results.append(result)

            return retrieval_results

        except Exception as e:
            logging.debug(f"BM25S search failed, falling back to text matching: {e}")
            return self._search_with_text_matching(query, top_k, policy_filter)

    def _search_with_text_matching(
        self, query: str, top_k: int, policy_filter: Optional[List[str]] = None
    ) -> List[RetrievalResult]:
        """Fallback text-based search."""
        query_terms = query.lower().split()
        results = []

        for snippet in self.kb_loader.snippets:
            # Apply policy filter
            if policy_filter and snippet.policy_type not in policy_filter:
                continue

            # Simple text matching score
            content_lower = f"{snippet.title} {snippet.content}".lower()
            score = 0.0

            for term in query_terms:
                if term in content_lower:
                    score += content_lower.count(term)

            if score > 0:
                # Normalize score
                score = score / len(content_lower.split())

                result = RetrievalResult(
                    snippet_id=snippet.id,
                    title=snippet.title,
                    content=snippet.content,
                    source_file=snippet.source_file,
                    policy_type=snippet.policy_type,
                    section=snippet.section,
                    subsection=snippet.subsection,
                    citations=snippet.citations,
                    score=score,
                    rank=0,  # Will be set later
                    metadata=snippet.metadata,
                )
                results.append(result)

        # Sort by score and return top-k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def search_by_policy_type(
        self, policy_type: str, query: Optional[str] = None, top_k: int = 10
    ) -> RetrievalResponse:
        """
        Search within a specific policy type.

        Args:
            policy_type: Policy type to search within
            query: Optional search query within policy
            top_k: Number of results to return

        Returns:
            RetrievalResponse filtered to policy type
        """
        if query:
            return self.retrieve(query=query, top_k=top_k, policy_filter=[policy_type])
        else:
            # Return all snippets for this policy type
            policy_snippets = [
                s for s in self.kb_loader.snippets if s.policy_type == policy_type
            ]

            results = []
            for i, snippet in enumerate(policy_snippets[:top_k]):
                result = RetrievalResult(
                    snippet_id=snippet.id,
                    title=snippet.title,
                    content=snippet.content,
                    source_file=snippet.source_file,
                    policy_type=snippet.policy_type,
                    section=snippet.section,
                    subsection=snippet.subsection,
                    citations=snippet.citations,
                    score=1.0,  # Equal scores for non-query results
                    rank=i + 1,
                    metadata=snippet.metadata,
                )
                results.append(result)

            return RetrievalResponse(
                query=f"All {policy_type} policies",
                results=results,
                total_results=len(policy_snippets),
                query_expansion=[],
                processing_time_ms=0,
                metadata={"policy_type": policy_type},
            )

    def get_snippet_by_id(self, snippet_id: str) -> Optional[KnowledgeSnippet]:
        """Get a specific knowledge snippet by ID."""
        for snippet in self.kb_loader.snippets:
            if snippet.id == snippet_id:
                return snippet
        return None

    def get_related_snippets(
        self, snippet_id: str, top_k: int = 3
    ) -> List[RetrievalResult]:
        """
        Find related snippets based on section and policy type.

        Args:
            snippet_id: ID of reference snippet
            top_k: Number of related snippets to return

        Returns:
            List of related retrieval results
        """
        reference_snippet = self.get_snippet_by_id(snippet_id)
        if not reference_snippet:
            return []

        related_results = []

        for snippet in self.kb_loader.snippets:
            if snippet.id == snippet_id:
                continue  # Skip the reference snippet

            score = 0.0

            # Same policy type gets high score
            if snippet.policy_type == reference_snippet.policy_type:
                score += 0.5

            # Same section gets high score
            if snippet.section == reference_snippet.section:
                score += 0.3

            # Related subsections
            if (
                snippet.subsection
                and reference_snippet.subsection
                and snippet.subsection != reference_snippet.subsection
            ):
                score += 0.2

            if score > 0:
                result = RetrievalResult(
                    snippet_id=snippet.id,
                    title=snippet.title,
                    content=snippet.content,
                    source_file=snippet.source_file,
                    policy_type=snippet.policy_type,
                    section=snippet.section,
                    subsection=snippet.subsection,
                    citations=snippet.citations,
                    score=score,
                    rank=0,
                    metadata=snippet.metadata,
                )
                related_results.append(result)

        # Sort by score and return top-k
        related_results.sort(key=lambda x: x.score, reverse=True)
        for i, result in enumerate(related_results[:top_k]):
            result.rank = i + 1

        return related_results[:top_k]


def create_retriever(
    kb_directory: Union[str, Path], index_path: Optional[Union[str, Path]] = None
) -> RAGRetriever:
    """
    Convenience function to create and initialize a RAG retriever.

    Args:
        kb_directory: Path to knowledge base directory
        index_path: Optional path to load search index

    Returns:
        Initialized RAGRetriever
    """
    from preauth_system.rag.kb_loader import create_knowledge_base

    # Create or load knowledge base
    kb_loader = create_knowledge_base(kb_directory)

    # Load existing index if provided
    if index_path and Path(index_path).exists():
        kb_loader.load_index(index_path)

    # Create retriever
    retriever = RAGRetriever(kb_loader)
    logging.info(f"✅ RAG Retriever created with {len(kb_loader.snippets)} snippets")

    return retriever


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
        # Create retriever
        retriever = create_retriever(kb_path)

        # Test queries
        test_queries = [
            "diabetes continuous glucose monitoring criteria",
            "osteoarthritis conservative treatment requirements",
            "parkinson deep brain stimulation evaluation",
            "insulin pump coverage guidelines",
        ]

        print("\n🔍 Testing RAG Retrieval System:\n")

        for query in test_queries:
            print(f"Query: '{query}'")
            response = retriever.retrieve(query, top_k=3)

            if response.results:
                print(f"Found {len(response.results)} results:")
                for result in response.results:
                    print(f"  - {result.title} (score: {result.score:.3f})")
                    print(
                        f"    Policy: {result.policy_type}, Section: {result.section}"
                    )
            else:
                print("  No results found")

            print(f"  Processing time: {response.processing_time_ms:.1f}ms")
            print()

    except Exception as e:
        logging.error(f"❌ Failed to test retriever: {e}")
        sys.exit(1)
