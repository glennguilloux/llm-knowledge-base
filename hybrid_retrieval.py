#!/usr/bin/env python3
"""Hybrid retrieval combining vector search with keyword matching."""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field

import yaml
import chromadb
from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "knowledge_base"
CHROMA_DIR = "./chroma_db"


@dataclass
class SearchResult:
    """Search result with score breakdown."""
    id: str
    title: str
    filepath: str
    language: str
    category: str
    tags: list[str]
    vector_score: float = 0.0
    keyword_score: float = 0.0
    total_score: float = 0.0
    content: str = ""


def keyword_score(query: str, metadata: dict) -> float:
    """Calculate keyword relevance score."""
    query_words = set(re.findall(r"\w+", query.lower()))
    score = 0.0

    # Title match
    title = metadata.get("title", "").lower()
    for word in query_words:
        if word in title:
            score += 3.0

    # Tag match
    tags = metadata.get("tags", "").lower().split(",")
    for tag in tags:
        if any(word in tag for word in query_words):
            score += 2.0

    # Category match
    category = metadata.get("category", "").lower()
    for word in query_words:
        if word in category:
            score += 1.0

    return score


def search(
    query: str,
    language: str | None = None,
    top_k: int = 5,
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4,
) -> list[SearchResult]:
    """Hybrid search combining vector similarity and keyword matching."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=COLLECTION_NAME)

    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode(query).tolist()

    # Build where filter
    where_filter = {}
    if language:
        where_filter = {"language": language}

    # Vector search (get more candidates for re-ranking)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k * 3, 50),
        where=where_filter if where_filter else None,
        include=["documents", "metadatas", "distances"],
    )

    # Combine vector and keyword scores
    search_results = []
    for i in range(len(results["ids"][0])):
        entry_id = results["ids"][0][i]
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        document = results["documents"][0][i]

        # ChromaDB returns distances (lower = better), convert to similarity
        vector_sim = 1.0 - distance

        # Keyword score
        kw_score = keyword_score(query, metadata)

        # Normalize scores
        norm_vector = max(0, min(1, vector_sim))
        norm_keyword = max(0, min(1, kw_score / 10.0))

        total = (vector_weight * norm_vector) + (keyword_weight * norm_keyword)

        search_results.append(SearchResult(
            id=entry_id,
            title=metadata.get("title", ""),
            filepath=metadata.get("filepath", ""),
            language=metadata.get("language", ""),
            category=metadata.get("category", ""),
            tags=metadata.get("tags", "").split(","),
            vector_score=norm_vector,
            keyword_score=norm_keyword,
            total_score=total,
            content=document,
        ))

    # Sort by total score
    search_results.sort(key=lambda x: x.total_score, reverse=True)
    return search_results[:top_k]


def main() -> None:
    """CLI interface for hybrid search."""
    if len(sys.argv) < 2:
        print("Usage: python hybrid_retrieval.py <query> [--lang LANGUAGE] [--top N]")
        sys.exit(1)

    query = sys.argv[1]
    language = None
    top_k = 5

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--lang" and i + 1 < len(args):
            language = args[i + 1]
            i += 2
        elif args[i] == "--top" and i + 1 < len(args):
            top_k = int(args[i + 1])
            i += 2
        else:
            i += 1

    results = search(query, language=language, top_k=top_k)

    if not results:
        print("No matching entries found.")
        sys.exit(1)

    print(f"Found {len(results)} result(s):\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   File: {result.filepath}")
        print(f"   Language: {result.language} | Category: {result.category}")
        print(f"   Score: {result.total_score:.3f} (vector: {result.vector_score:.3f}, keyword: {result.keyword_score:.3f})")
        print()


if __name__ == "__main__":
    main()
