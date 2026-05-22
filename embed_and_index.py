#!/usr/bin/env python3
"""Embed knowledge base entries and store in ChromaDB."""

import re
import sys
from pathlib import Path

import yaml
import chromadb
from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "knowledge_base"
CHROMA_DIR = "./chroma_db"


def extract_frontmatter(filepath: Path) -> dict | None:
    """Extract YAML frontmatter from a markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def extract_content(filepath: Path) -> str:
    """Extract the main content (after frontmatter) from a markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return ""

    match = re.match(r"^---\n.*?\n---\n?", content, re.DOTALL)
    if match:
        return content[match.end():]
    return content


def collect_entries(kb_path: Path) -> list[dict]:
    """Collect all knowledge base entries."""
    entries = []
    skip_files = {"README.md", "schema.md", "CONTRIBUTING.md", "LLM_CODEBASE_KNOWLEDGE_BASE.md"}

    for md_file in sorted(kb_path.rglob("*.md")):
        if md_file.name in skip_files:
            continue
        if md_file.parent.name in ("templates", ".github"):
            continue

        meta = extract_frontmatter(md_file)
        if not meta or not meta.get("id"):
            continue

        content = extract_content(md_file)
        entries.append({
            "id": meta["id"],
            "filepath": str(md_file),
            "title": meta.get("title", ""),
            "language": meta.get("language", ""),
            "category": meta.get("category", ""),
            "tags": meta.get("tags", []),
            "retrieval_hint": meta.get("retrieval_hint", ""),
            "confidence": meta.get("confidence", "draft"),
            "content": content,
        })

    return entries


def build_text_for_embedding(entry: dict) -> str:
    """Build text to embed from entry metadata and content."""
    parts = [
        entry["title"],
        entry.get("retrieval_hint", ""),
        " ".join(entry.get("tags", [])),
        entry.get("language", ""),
        entry.get("category", ""),
    ]
    return " ".join(filter(None, parts))


def main() -> None:
    """Embed all entries and store in ChromaDB."""
    kb_path = Path(".")
    entries = collect_entries(kb_path)

    if not entries:
        print("No entries found.")
        sys.exit(1)

    print(f"Found {len(entries)} entries. Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Prepare data
    ids = []
    documents = []
    metadatas = []
    embeddings = []

    print("Generating embeddings...")
    for entry in entries:
        text = build_text_for_embedding(entry)
        embedding = model.encode(text).tolist()

        ids.append(entry["id"])
        documents.append(entry["content"][:1000])  # Store truncated content
        metadatas.append({
            "title": entry["title"],
            "language": entry["language"],
            "category": entry["category"],
            "filepath": entry["filepath"],
            "confidence": entry["confidence"],
            "tags": ",".join(entry.get("tags", [])),
        })
        embeddings.append(embedding)

    # Upsert to ChromaDB
    print(f"Storing {len(ids)} embeddings in ChromaDB...")
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print(f"Done! Indexed {len(ids)} entries in {CHROMA_DIR}")
    print(f"Collection: {COLLECTION_NAME}")


if __name__ == "__main__":
    main()
