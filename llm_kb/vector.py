"""Vector search integration using ChromaDB and sentence-transformers.

Provides vector similarity search as an optional enhancement over keyword-only
retrieval. Falls back gracefully when vector dependencies are not installed.

Usage:
    from llm_kb.vector import vector_search, build_index, is_vector_available

    if is_vector_available():
        results = vector_search("JWT authentication", top_k=5)
"""

import os
import logging
from pathlib import Path
from functools import lru_cache
from typing import TYPE_CHECKING

from llm_kb.retrieve import get_kb_path, load_entries

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COLLECTION_NAME = "knowledge_base"
_MODEL_NAME = os.environ.get("LLM_KB_EMBED_MODEL", "BAAI/bge-small-en-v1.5")

# ChromaDB directory: configurable via env var, with reasonable defaults
_chroma_env = os.environ.get("LLM_KB_CHROMA_DIR")
if _chroma_env:
    CHROMA_DIR = _chroma_env
else:
    pkg_data = Path(__file__).parent / "data"
    if pkg_data.exists() and any(pkg_data.iterdir()):
        CHROMA_DIR = str(Path.home() / ".cache" / "llm-kb" / "chroma_db")
    else:
        CHROMA_DIR = "./chroma_db"

# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

_VECTOR_DEPS_AVAILABLE: bool | None = None


def is_vector_available() -> bool:
    """Check if vector search dependencies (chromadb, sentence-transformers) are installed.

    Returns True only if both are importable.
    """
    global _VECTOR_DEPS_AVAILABLE
    if _VECTOR_DEPS_AVAILABLE is not None:
        return _VECTOR_DEPS_AVAILABLE

    try:
        import chromadb  # noqa: F401
        import sentence_transformers  # noqa: F401
        _VECTOR_DEPS_AVAILABLE = True
    except ImportError:
        _VECTOR_DEPS_AVAILABLE = False

    return _VECTOR_DEPS_AVAILABLE


# ---------------------------------------------------------------------------
# Lazy singleton initialisers
# ---------------------------------------------------------------------------

_embedding_model = None
_chroma_client = None
_chroma_collection = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(_MODEL_NAME)
    return _embedding_model


def _get_chroma_collection():
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        _chroma_collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _chroma_collection


def _reset_singletons():
    global _embedding_model, _chroma_client, _chroma_collection, _VECTOR_DEPS_AVAILABLE
    _embedding_model = None
    _chroma_client = None
    _chroma_collection = None
    _VECTOR_DEPS_AVAILABLE = None


# ---------------------------------------------------------------------------
# Index building
# ---------------------------------------------------------------------------

def _build_text_for_embedding(title: str, retrieval_hint: str, tags: list[str],
                                language: str, category: str) -> str:
    parts = [
        title,
        retrieval_hint,
        " ".join(tags),
        language,
        category,
    ]
    return " ".join(filter(None, parts))


def build_index(kb_path: Path | None = None) -> int:
    """Build or rebuild the ChromaDB index from all knowledge base entries.

    Args:
        kb_path: Path to knowledge base root (default: auto-detect)

    Returns:
        Number of entries indexed.

    Raises:
        ImportError: If chromadb or sentence-transformers are not installed.
    """
    if not is_vector_available():
        raise ImportError(
            "Vector search dependencies not installed. "
            "Run: pip install llm-knowledge-base[vector]"
        )

    entries = load_entries(kb_path or get_kb_path())
    if not entries:
        logger.warning("No entries found to index.")
        return 0

    model = _get_embedding_model()
    collection = _get_chroma_collection()

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    embeddings: list[list[float]] = []

    for entry in entries:
        text = _build_text_for_embedding(
            title=entry.title,
            retrieval_hint=entry.retrieval_hint,
            tags=entry.tags,
            language=entry.language,
            category=entry.category,
        )
        embedding = model.encode(text).tolist()

        ids.append(entry.id)
        documents.append(entry.content[:1000])
        metadatas.append({
            "title": entry.title,
            "language": entry.language,
            "category": entry.category,
            "filepath": str(entry.filepath),
            "id": entry.id,
            "tags": ",".join(entry.tags),
        })
        embeddings.append(embedding)

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    return len(ids)


def index_exists() -> bool:
    """Check if a ChromaDB index exists on disk."""
    index_path = Path(CHROMA_DIR)
    if not index_path.exists():
        return False
    sqlite_file = index_path / "chroma.sqlite3"
    if sqlite_file.exists():
        return True
    return any(index_path.iterdir()) if index_path.is_dir() else False


# ---------------------------------------------------------------------------
# Vector search
# ---------------------------------------------------------------------------

def vector_search(
    query: str,
    language: str | None = None,
    top_k: int = 5,
    include_content: bool = False,
) -> list[dict]:
    """Search knowledge base using vector similarity.

    Args:
        query: Natural language query
        language: Optional language filter
        top_k: Maximum results to return
        include_content: Include full content in results

    Returns:
        List of dicts with keys: id, title, language, category, tags,
        score, and optionally content

    Raises:
        ImportError: If vector dependencies not installed.
        RuntimeError: If no index exists (run `llm-kb index` first).
    """
    if not is_vector_available():
        raise ImportError(
            "Vector search dependencies not installed. "
            "Run: pip install llm-knowledge-base[vector]"
        )

    if not index_exists():
        raise RuntimeError(
            "No vector index found. Run: llm-kb index"
        )

    model = _get_embedding_model()
    collection = _get_chroma_collection()

    query_embedding = model.encode(query).tolist()

    where_filter = {}
    if language:
        where_filter = {"language": language}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter if where_filter else None,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for i in range(len(results["ids"][0])):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        vector_sim = 1.0 - distance

        item = {
            "id": results["ids"][0][i],
            "title": metadata.get("title", ""),
            "language": metadata.get("language", ""),
            "category": metadata.get("category", ""),
            "tags": metadata.get("tags", "").split(",") if metadata.get("tags") else [],
            "score": max(0, min(1, vector_sim)),
        }
        if include_content:
            item["content"] = results["documents"][0][i] if results["documents"] else ""
        output.append(item)

    return output


# ---------------------------------------------------------------------------
# Content builder for embedding (for build_index convenience)
# ---------------------------------------------------------------------------

def build_text_for_entry(title: str, retrieval_hint: str, tags: list[str],
                         language: str, category: str) -> str:
    return _build_text_for_embedding(title, retrieval_hint, tags, language, category)
