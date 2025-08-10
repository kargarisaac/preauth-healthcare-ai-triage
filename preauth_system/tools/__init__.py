"""
Tools package for preauth system agent integration.
Simplified to provide RAG tools that either inline small KB files or use OpenAI File Search for large ones.
"""

from .tools import (
    RAGTools,
    get_rag_tools,
)

__all__ = [
    "RAGTools",
    "get_rag_tools",
]
