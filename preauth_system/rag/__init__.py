"""
RAG (Retrieval-Augmented Generation) System for Pre-Authorization
================================================================

Simplified RAG interface: tools consume markdown KB files directly (< threshold tokens)
or via OpenAI File Search (>= threshold tokens). No local BM25/NLTK indexing.

Usage:
    from preauth_system.tools import get_rag_tools
"""

from pathlib import Path

__version__ = "2.0.0"
__author__ = "Nazmito AI Team"

DEFAULT_KB_PATH = Path(__file__).parent / "kb"

__all__ = [
    "DEFAULT_KB_PATH",
    "__version__",
]
