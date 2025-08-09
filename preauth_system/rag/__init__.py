"""
RAG (Retrieval-Augmented Generation) System for Pre-Authorization
================================================================

This module provides knowledge retrieval and evidence integration for the
Nazmito pre-authorization system, enabling agents to access structured
healthcare policy information with proper citations.

Components:
- kb_loader: Knowledge base loading and indexing
- retrieve: BM25S-based semantic retrieval
- tools: Agent tool functions for LangGraph integration

Usage:
    from preauth_system.rag import get_rag_tools, search_healthcare_policies
    
    # Get RAG tools instance
    rag_tools = get_rag_tools()
    
    # Use as agent tool
    result = search_healthcare_policies("diabetes CGM coverage criteria")
"""

from pathlib import Path
from typing import Optional, Union

# Import main components
from .kb_loader import (
    KnowledgeBaseLoader,
    KnowledgeSnippet, 
    create_knowledge_base
)

from .retrieve import (
    RAGRetriever,
    RetrievalResponse,
    RetrievalResult,
    HealthcareQueryExpander,
    create_retriever
)

# Tools are now in preauth_system.tools package

# Version information
__version__ = "1.0.0"
__author__ = "Nazmito AI Team"

# Default knowledge base path
DEFAULT_KB_PATH = Path(__file__).parent.parent.parent / "kb"

# Public API
__all__ = [
    # Core classes
    "KnowledgeBaseLoader",
    "KnowledgeSnippet",
    "RAGRetriever", 
    "RetrievalResponse",
    "RetrievalResult",
    
    # Factory functions
    "create_knowledge_base",
    "create_retriever",
    
    # Utility classes
    "HealthcareQueryExpander",
    
    # Constants
    "DEFAULT_KB_PATH"
]


def initialize_rag_system(kb_directory: Optional[Union[str, Path]] = None,
                         force_rebuild: bool = False) -> "RAGRetriever":
    """
    Initialize the RAG system with knowledge base loading and indexing.
    
    Args:
        kb_directory: Path to knowledge base directory (defaults to DEFAULT_KB_PATH)
        force_rebuild: Force rebuild of search index even if exists
        
    Returns:
        Initialized RAGRetriever instance ready for retrieval
        
    Example:
        >>> retriever = initialize_rag_system()
        >>> result = retriever.retrieve("insulin pump criteria")
        >>> print(f"Found {result.total_results} results")
    """
    if kb_directory is None:
        kb_directory = DEFAULT_KB_PATH
    
    # Create retriever with knowledge base
    retriever = create_retriever(
        kb_directory=kb_directory,
        index_path=Path(kb_directory) / "index" / "kb_index" if force_rebuild else None
    )
    
    return retriever


def get_system_info() -> dict:
    """
    Get information about the RAG system configuration and status.
    
    Returns:
        Dictionary with system information and statistics
    """
    try:
        retriever = initialize_rag_system()
        kb_stats = retriever.kb_loader.get_stats()
        
        return {
            "version": __version__,
            "knowledge_base": {
                "path": str(DEFAULT_KB_PATH),
                "total_snippets": kb_stats.get("total_snippets", 0),
                "policy_types": list(kb_stats.get("policy_types", {}).keys()),
                "has_index": kb_stats.get("has_index", False)
            },
            "supported_policies": [
                "diabetes_tech",
                "osteoarthritis", 
                "parkinson_dbs"
            ]
        }
    except Exception as e:
        return {
            "version": __version__,
            "status": "not_initialized",
            "error": str(e),
            "default_kb_path": str(DEFAULT_KB_PATH)
        }


# Initialize system information
SYSTEM_INFO = get_system_info()