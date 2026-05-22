#!/usr/bin/env python3
"""Grep-based retrieval for the knowledge base."""

import re
import sys
from pathlib import Path
from dataclasses import dataclass, field

import yaml


@dataclass
class KBEntry:
    """Parsed knowledge base entry."""
    filepath: Path
    id: str
    title: str
    language: str
    category: str
    tags: list[str] = field(default_factory=list)
    retrieval_hint: str = ""
    confidence: str = "draft"
    content: str = ""


def parse_entry(filepath: Path) -> KBEntry | None:
    """Parse a knowledge base entry from a markdown file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None

    if not isinstance(meta, dict):
        return None

    return KBEntry(
        filepath=filepath,
        id=meta.get("id", ""),
        title=meta.get("title", ""),
        language=meta.get("language", ""),
        category=meta.get("category", ""),
        tags=meta.get("tags", []),
        retrieval_hint=meta.get("retrieval_hint", ""),
        confidence=meta.get("confidence", "draft"),
        content=content,
    )


def load_entries(kb_path: Path = Path(".")) -> list[KBEntry]:
    """Load all knowledge base entries."""
    entries = []
    skip_files = {"README.md", "schema.md", "CONTRIBUTING.md", "LLM_CODEBASE_KNOWLEDGE_BASE.md"}

    for md_file in sorted(kb_path.rglob("*.md")):
        if any(part.startswith(".") for part in md_file.parts):
            continue
        if md_file.name in skip_files:
            continue
        if md_file.parent.name in ("templates", ".github"):
            continue

        entry = parse_entry(md_file)
        if entry:
            entries.append(entry)

    return entries


def search_by_tags(entries: list[KBEntry], query_tags: list[str]) -> list[KBEntry]:
    """Search entries by matching tags."""
    query_set = set(t.lower() for t in query_tags)
    results = []
    for entry in entries:
        entry_tags = set(t.lower() for t in entry.tags)
        if query_set & entry_tags:
            results.append(entry)
    return results


def search_by_language(entries: list[KBEntry], language: str) -> list[KBEntry]:
    """Filter entries by language."""
    return [e for e in entries if e.language == language]


def search_by_keywords(entries: list[KBEntry], query: str) -> list[KBEntry]:
    """Search entries by keyword matching in title, tags, and retrieval_hint."""
    query_lower = query.lower()
    query_words = set(re.findall(r"\w+", query_lower))

    scored: list[tuple[float, KBEntry]] = []
    for entry in entries:
        score = 0.0

        # Title match (highest weight)
        title_lower = entry.title.lower()
        for word in query_words:
            if word in title_lower:
                score += 3.0

        # Tag match
        for tag in entry.tags:
            if any(word in tag.lower() for word in query_words):
                score += 2.0

        # Retrieval hint match
        hint_lower = entry.retrieval_hint.lower()
        for word in query_words:
            if word in hint_lower:
                score += 1.5

        # Content keyword match (lower weight)
        content_lower = entry.content.lower()
        for word in query_words:
            if word in content_lower:
                score += 0.5

        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored]


def search(
    query: str,
    language: str | None = None,
    top_k: int = 5,
    kb_path: Path = Path("."),
) -> list[KBEntry]:
    """Search the knowledge base with a natural language query."""
    entries = load_entries(kb_path)

    if language:
        entries = search_by_language(entries, language)

    results = search_by_keywords(entries, query)
    return results[:top_k]


def main() -> None:
    """CLI interface for knowledge base search."""
    if len(sys.argv) < 2:
        print("Usage: python retrieval.py <query> [--lang LANGUAGE] [--top N]")
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
    for i, entry in enumerate(results, 1):
        print(f"{i}. {entry.title}")
        print(f"   File: {entry.filepath}")
        print(f"   Language: {entry.language} | Category: {entry.category}")
        print(f"   Tags: {', '.join(entry.tags)}")
        print()


if __name__ == "__main__":
    main()
