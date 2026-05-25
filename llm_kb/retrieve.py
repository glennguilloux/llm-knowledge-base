import os
import re
from pathlib import Path
from llm_kb.schema import KBEntry, parse_entry


def get_kb_path() -> Path:
    """Get the path to the knowledge base entries.
    
    Checks first in the package's bundled data directory,
    and falls back to current working directory.
    """
    pkg_data = Path(__file__).parent / "data"
    if pkg_data.exists():
        # verify if it actually has entry files (like anti-patterns directory, etc.)
        for path in pkg_data.iterdir():
            if path.is_symlink() or path.is_dir():
                return pkg_data
    return Path(".")


def load_entries(kb_path: Path | None = None) -> list[KBEntry]:
    """Load all knowledge base entries from the given path or default path."""
    if kb_path is None:
        kb_path = get_kb_path()
    
    entries = []
    skip_files = {"README.md", "schema.md", "CONTRIBUTING.md", "LLM_CODEBASE_KNOWLEDGE_BASE.md"}
    skip_parents = {"templates", ".github", "scripts", "__pycache__"}

    md_files = []
    for root, dirs, files in os.walk(str(kb_path), followlinks=True):
        for f in files:
            if f.endswith(".md"):
                md_file = Path(root) / f

                # Check for hidden directories or skip files
                if any(part.startswith(".") for part in md_file.parts):
                    continue
                if md_file.name in skip_files:
                    continue
                if any(p.name in skip_parents for p in md_file.parents):
                    continue

                md_files.append(md_file)

    for md_file in sorted(md_files):
        entry = parse_entry(md_file)
        if entry:
            entries.append(entry)

    # Deduplicate by ID (handles symlinked data directories)
    seen: dict[str, KBEntry] = {}
    for entry in entries:
        if entry.id not in seen:
            seen[entry.id] = entry
    entries = list(seen.values())

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
    lang_lower = language.lower()
    return [e for e in entries if e.language.lower() == lang_lower]


def search_by_keywords(entries: list[KBEntry], query: str) -> list[KBEntry]:
    """Search entries by keyword matching in title, tags, and retrieval_hint."""
    if not isinstance(query, str):
        raise TypeError(f"query must be a string, got {type(query).__name__}")
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
    kb_path: Path | None = None,
) -> list[KBEntry]:
    """Search the knowledge base with a natural language query."""
    if not isinstance(top_k, int):
        raise TypeError(f"top_k must be an int, got {type(top_k).__name__}")
    if top_k < 0:
        raise ValueError(f"top_k must be non-negative, got {top_k}")

    if kb_path is None:
        kb_path = get_kb_path()

    entries = load_entries(kb_path)

    if language:
        entries = search_by_language(entries, language)

    results = search_by_keywords(entries, query)
    return results[:top_k]
