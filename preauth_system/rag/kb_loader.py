"""
Knowledge Base Loader for Pre-Authorization System
================================================

Loads local guideline/policy snippets for RAG retrieval system.
Supports markdown and JSONL formats with citation tracking and provenance.

This module provides functionality to:
- Load knowledge snippets from local files (MD, JSONL)
- Create BM25S search index for retrieval
- Maintain citation links and source provenance
- Support the 3 MVP policies with structured metadata
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# External dependencies for search indexing
try:
    import bm25s
    import Stemmer  # PyStemmer for better stemming

    HAS_BM25S = True
except ImportError:
    HAS_BM25S = False
    logging.error(
        "bm25s or PyStemmer not available. Install with: pip install bm25s PyStemmer"
    )
    raise ImportError("bm25s or PyStemmer not available")

try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords

    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False
    logging.warning("NLTK not available. Install with: pip install nltk")


@dataclass
class KnowledgeSnippet:
    """Individual knowledge snippet with metadata."""

    id: str
    title: str
    content: str
    source_file: str
    policy_type: str  # 'diabetes_tech', 'osteoarthritis', 'parkinson_dbs'
    section: str
    subsection: Optional[str] = None
    citations: List[str] = None
    metadata: Dict[str, Any] = None
    created_at: str = None

    def __post_init__(self):
        if self.citations is None:
            self.citations = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeSnippet":
        """Create from dictionary."""
        return cls(**data)


class KnowledgeBaseLoader:
    """
    Loads and indexes local healthcare policy knowledge base.

    Features:
    - Multi-format support (Markdown, JSONL)
    - BM25S indexing for semantic retrieval
    - Citation tracking and provenance
    - Structured metadata for UAE healthcare policies
    """

    def __init__(self, kb_directory: Union[str, Path]):
        """
        Initialize knowledge base loader.

        Args:
            kb_directory: Path to knowledge base directory
        """
        self.kb_directory = Path(kb_directory)
        self.snippets: List[KnowledgeSnippet] = []
        self.index = None
        self.stemmer = None
        self.stop_words = set()

        # Initialize text processing
        self._initialize_text_processing()

        # Policy type mappings
        self.policy_types = {
            "diabetes_tech": {
                "name": "Diabetes Technology Guidelines",
                "description": "CGM/pump coverage criteria with citations",
            },
            "osteoarthritis": {
                "name": "Osteoarthritis Management",
                "description": "Conservative therapy requirements, intervention criteria",
            },
            "parkinson_dbs": {
                "name": "Parkinson's DBS",
                "description": "Medical optimization thresholds, evaluation protocols",
            },
        }

    def _initialize_text_processing(self):
        """Initialize text processing components."""
        if HAS_BM25S:
            try:
                self.stemmer = Stemmer.Stemmer("english")
                logging.info("✅ Stemmer initialized")
            except Exception as e:
                logging.warning(f"Stemmer initialization failed: {e}")

        if HAS_NLTK:
            try:
                # Download required NLTK data if not present
                import nltk

                nltk.download("punkt", quiet=True)
                nltk.download("stopwords", quiet=True)
                self.stop_words = set(stopwords.words("english"))
                logging.info("✅ NLTK components initialized")
            except Exception as e:
                logging.warning(f"NLTK initialization failed: {e}")

        # Fallback stop words
        if not self.stop_words:
            self.stop_words = {
                "a",
                "an",
                "and",
                "are",
                "as",
                "at",
                "be",
                "by",
                "for",
                "from",
                "has",
                "he",
                "in",
                "is",
                "it",
                "its",
                "of",
                "on",
                "that",
                "the",
                "to",
                "was",
                "will",
                "with",
            }

    def load_knowledge_base(self, force_reload: bool = False) -> List[KnowledgeSnippet]:
        """
        Load all knowledge snippets from the knowledge base directory.

        Args:
            force_reload: Force reload even if already loaded

        Returns:
            List of loaded knowledge snippets

        Raises:
            FileNotFoundError: If knowledge base directory doesn't exist
        """
        if self.snippets and not force_reload:
            logging.info(
                f"✅ Using cached knowledge base: {len(self.snippets)} snippets"
            )
            return self.snippets

        if not self.kb_directory.exists():
            raise FileNotFoundError(
                f"Knowledge base directory not found: {self.kb_directory}"
            )

        self.snippets = []

        # Load markdown files
        md_files = list(self.kb_directory.rglob("*.md"))
        for md_file in md_files:
            try:
                snippets = self._load_markdown_file(md_file)
                self.snippets.extend(snippets)
                logging.info(f"✅ Loaded {len(snippets)} snippets from {md_file.name}")
            except Exception as e:
                logging.error(f"❌ Failed to load {md_file}: {e}")

        # Load JSONL files
        jsonl_files = list(self.kb_directory.rglob("*.jsonl"))
        for jsonl_file in jsonl_files:
            try:
                snippets = self._load_jsonl_file(jsonl_file)
                self.snippets.extend(snippets)
                logging.info(
                    f"✅ Loaded {len(snippets)} snippets from {jsonl_file.name}"
                )
            except Exception as e:
                logging.error(f"❌ Failed to load {jsonl_file}: {e}")

        logging.info(f"✅ Total knowledge base loaded: {len(self.snippets)} snippets")
        return self.snippets

    def _load_markdown_file(self, file_path: Path) -> List[KnowledgeSnippet]:
        """
        Load knowledge snippets from markdown file.

        Expected format:
        - Headers (##, ###) define sections
        - Each section becomes a snippet
        - YAML frontmatter for metadata

        Args:
            file_path: Path to markdown file

        Returns:
            List of knowledge snippets
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        snippets = []
        lines = content.split("\n")

        # Parse frontmatter if present
        metadata = {}
        policy_type = self._infer_policy_type(file_path)

        if lines and lines[0].strip() == "---":
            frontmatter_end = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    frontmatter_end = i + 1
                    break

            if frontmatter_end > 0:
                try:
                    import yaml

                    frontmatter_content = "\n".join(lines[1 : frontmatter_end - 1])
                    metadata = yaml.safe_load(frontmatter_content) or {}
                    lines = lines[frontmatter_end:]
                except ImportError:
                    logging.warning("PyYAML not available for frontmatter parsing")
                except Exception as e:
                    logging.warning(f"Failed to parse frontmatter: {e}")

        # Parse sections
        current_section = None
        current_subsection = None
        current_content = []

        for line in lines:
            line = line.strip()

            if line.startswith("## "):
                # Save previous section
                if current_section and current_content:
                    snippet = self._create_snippet(
                        file_path,
                        policy_type,
                        current_section,
                        current_subsection,
                        "\n".join(current_content),
                        metadata,
                    )
                    snippets.append(snippet)

                # Start new section
                current_section = line[3:].strip()
                current_subsection = None
                current_content = []

            elif line.startswith("### "):
                # Save previous subsection
                if current_section and current_content:
                    snippet = self._create_snippet(
                        file_path,
                        policy_type,
                        current_section,
                        current_subsection,
                        "\n".join(current_content),
                        metadata,
                    )
                    snippets.append(snippet)

                # Start new subsection
                current_subsection = line[4:].strip()
                current_content = []

            elif line and current_section:
                current_content.append(line)

        # Save final section
        if current_section and current_content:
            snippet = self._create_snippet(
                file_path,
                policy_type,
                current_section,
                current_subsection,
                "\n".join(current_content),
                metadata,
            )
            snippets.append(snippet)

        return snippets

    def _load_jsonl_file(self, file_path: Path) -> List[KnowledgeSnippet]:
        """
        Load knowledge snippets from JSONL file.

        Each line should be a JSON object representing a KnowledgeSnippet.

        Args:
            file_path: Path to JSONL file

        Returns:
            List of knowledge snippets
        """
        snippets = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # Ensure required fields
                    if "source_file" not in data:
                        data["source_file"] = str(file_path)

                    snippet = KnowledgeSnippet.from_dict(data)
                    snippets.append(snippet)

                except json.JSONDecodeError as e:
                    logging.error(f"❌ Invalid JSON at {file_path}:{line_num}: {e}")
                except Exception as e:
                    logging.error(
                        f"❌ Failed to create snippet from {file_path}:{line_num}: {e}"
                    )

        return snippets

    def _create_snippet(
        self,
        file_path: Path,
        policy_type: str,
        section: str,
        subsection: Optional[str],
        content: str,
        metadata: Dict[str, Any],
    ) -> KnowledgeSnippet:
        """Create a knowledge snippet with proper ID and metadata."""

        # Generate unique ID
        id_content = f"{file_path.name}:{section}:{subsection or ''}"
        snippet_id = hashlib.md5(id_content.encode()).hexdigest()[:12]

        # Create title
        title = f"{section}"
        if subsection:
            title += f" - {subsection}"

        # Extract citations from content (look for [1], [2] patterns)
        import re

        citations = re.findall(r"\[(\d+)\]", content)

        return KnowledgeSnippet(
            id=snippet_id,
            title=title,
            content=content,
            source_file=str(file_path),
            policy_type=policy_type,
            section=section,
            subsection=subsection,
            citations=citations,
            metadata=metadata,
        )

    def _infer_policy_type(self, file_path: Path) -> str:
        """Infer policy type from file path or name."""
        path_str = str(file_path).lower()

        if "diabetes" in path_str or "cgm" in path_str or "pump" in path_str:
            return "diabetes_tech"
        elif "osteoarthritis" in path_str or "arthritis" in path_str:
            return "osteoarthritis"
        elif "parkinson" in path_str or "dbs" in path_str:
            return "parkinson_dbs"

        # Default to general if cannot infer
        return "general"

    def create_search_index(self) -> bool:
        """
        Create BM25S search index from loaded snippets.

        Returns:
            True if index created successfully, False otherwise
        """
        if not HAS_BM25S:
            logging.error("❌ BM25S not available. Cannot create search index.")
            return False

        if not self.snippets:
            logging.warning("⚠️ No snippets loaded. Load knowledge base first.")
            return False

        try:
            # Prepare documents for indexing
            documents = []
            for snippet in self.snippets:
                # Combine title and content for better retrieval
                doc_text = f"{snippet.title}. {snippet.content}"
                documents.append(doc_text)

            # Tokenize documents
            tokenized_docs = []
            for doc in documents:
                tokens = self._tokenize_text(doc)
                tokenized_docs.append(tokens)

            # Create and fit BM25S index
            self.index = bm25s.BM25()
            self.index.index(tokenized_docs)

            logging.info(f"✅ Search index created for {len(self.snippets)} snippets")
            return True

        except Exception as e:
            logging.error(f"❌ Failed to create search index: {e}")
            return False

    def _tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text with stemming and stop word removal.

        Args:
            text: Input text to tokenize

        Returns:
            List of processed tokens
        """
        # Basic tokenization
        if HAS_NLTK:
            try:
                tokens = word_tokenize(text.lower())
            except Exception:
                tokens = text.lower().split()
        else:
            tokens = text.lower().split()

        # Remove punctuation and short tokens
        tokens = [token for token in tokens if token.isalnum() and len(token) > 2]

        # Remove stop words
        tokens = [token for token in tokens if token not in self.stop_words]

        # Apply stemming
        if self.stemmer:
            try:
                tokens = self.stemmer.stemWords(tokens)
            except Exception as e:
                logging.warning(f"Stemming failed: {e}")

        return tokens

    def save_index(self, index_path: Union[str, Path]) -> bool:
        """
        Save the search index to disk.

        Args:
            index_path: Path to save index

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.index:
            logging.error("❌ No index to save. Create index first.")
            return False

        try:
            index_path = Path(index_path)
            index_path.parent.mkdir(parents=True, exist_ok=True)

            # Save BM25S index
            self.index.save(str(index_path))

            # Save snippets metadata
            metadata_path = index_path.parent / f"{index_path.stem}_metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump([snippet.to_dict() for snippet in self.snippets], f, indent=2)

            logging.info(f"✅ Index saved to {index_path}")
            logging.info(f"✅ Metadata saved to {metadata_path}")
            return True

        except Exception as e:
            logging.error(f"❌ Failed to save index: {e}")
            return False

    def load_index(self, index_path: Union[str, Path]) -> bool:
        """
        Load a previously saved search index.

        Args:
            index_path: Path to saved index

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            index_path = Path(index_path)

            if not HAS_BM25S:
                logging.error("❌ BM25S not available. Cannot load search index.")
                return False

            # Load BM25S index
            self.index = bm25s.BM25.load(str(index_path))

            # Load snippets metadata
            metadata_path = index_path.parent / f"{index_path.stem}_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    snippets_data = json.load(f)
                    self.snippets = [
                        KnowledgeSnippet.from_dict(data) for data in snippets_data
                    ]

            logging.info(f"✅ Index loaded from {index_path}")
            logging.info(f"✅ Loaded {len(self.snippets)} snippets")
            return True

        except Exception as e:
            logging.error(f"❌ Failed to load index: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        if not self.snippets:
            return {"total_snippets": 0}

        stats = {
            "total_snippets": len(self.snippets),
            "policy_types": {},
            "sections": {},
            "has_index": self.index is not None,
        }

        for snippet in self.snippets:
            # Policy type stats
            policy_type = snippet.policy_type
            if policy_type not in stats["policy_types"]:
                stats["policy_types"][policy_type] = 0
            stats["policy_types"][policy_type] += 1

            # Section stats
            section = snippet.section
            if section not in stats["sections"]:
                stats["sections"][section] = 0
            stats["sections"][section] += 1

        return stats


def create_knowledge_base(
    kb_directory: Union[str, Path], index_path: Optional[Union[str, Path]] = None
) -> KnowledgeBaseLoader:
    """
    Convenience function to create and initialize a knowledge base.

    Args:
        kb_directory: Path to knowledge base directory
        index_path: Optional path to save/load search index

    Returns:
        Initialized KnowledgeBaseLoader
    """
    loader = KnowledgeBaseLoader(kb_directory)

    # Load knowledge base
    snippets = loader.load_knowledge_base()
    logging.info(f"✅ Loaded knowledge base with {len(snippets)} snippets")

    # Create search index
    if loader.create_search_index():
        logging.info("✅ Search index created successfully")

        # Save index if path provided
        if index_path:
            loader.save_index(index_path)

    return loader


if __name__ == "__main__":
    # Example usage
    import sys
    from pathlib import Path

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Get knowledge base path from command line or use default
    if len(sys.argv) > 1:
        kb_path = Path(sys.argv[1])
    else:
        kb_path = Path(__file__).parent.parent.parent / "kb"

    try:
        # Create knowledge base
        kb_loader = create_knowledge_base(
            kb_directory=kb_path, index_path=kb_path / "index" / "kb_index"
        )

        # Print statistics
        stats = kb_loader.get_stats()
        print(f"\n📊 Knowledge Base Statistics:")
        print(f"Total snippets: {stats['total_snippets']}")
        print(f"Has search index: {stats['has_index']}")
        print(f"\nPolicy types:")
        for policy_type, count in stats["policy_types"].items():
            print(f"  - {policy_type}: {count} snippets")

        print(f"\nTop sections:")
        sections = sorted(stats["sections"].items(), key=lambda x: x[1], reverse=True)
        for section, count in sections[:5]:
            print(f"  - {section}: {count} snippets")

    except Exception as e:
        logging.error(f"❌ Failed to create knowledge base: {e}")
        sys.exit(1)
