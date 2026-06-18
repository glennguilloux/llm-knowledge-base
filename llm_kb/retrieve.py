import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Callable
from llm_kb.schema import KBEntry, parse_entry
from llm_kb.expand import expand_query


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
    skip_files = {"README.md", "schema.md", "CONTRIBUTING.md"}
    skip_parents = {"templates", ".github", "scripts", "__pycache__", "docs"}

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


def search_expanded(entries: list[KBEntry], query: str) -> list[tuple[float, KBEntry]]:
    """Search with query expansion: returns merged scored results from expanded queries.

    Runs keyword search for the original query and each expanded variant,
    then merges scores (an entry appearing in multiple expansions gets
    cumulative score).
    """
    queries = expand_query(query)
    merged: dict[str, tuple[float, KBEntry]] = {}
    for q in queries:
        q_lower = q.lower()
        q_words = set(re.findall(r"\w+", q_lower))
        for entry in entries:
            score = _score_entry(entry, q_lower, q_words)
            if score > 0:
                if entry.id not in merged:
                    merged[entry.id] = (score, entry)
                else:
                    existing_score, _ = merged[entry.id]
                    merged[entry.id] = (existing_score + score * 0.3, entry)

    scored = list(merged.values())
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def _score_entry(entry: KBEntry, query_lower: str, query_words: set[str]) -> float:
    """Score a single entry against a query. Returns cumulative score."""
    score = 0.0

    title_lower = entry.title.lower()
    for word in query_words:
        if word in title_lower:
            score += 3.0

    for tag in entry.tags:
        if any(word in tag.lower() for word in query_words):
            score += 2.0

    hint_lower = entry.retrieval_hint.lower()
    for word in query_words:
        if word in hint_lower:
            score += 1.5

    content_lower = entry.content.lower()
    for word in query_words:
        if word in content_lower:
            score += 0.5

    return score


# ---------------------------------------------------------------------------
# Cross-reference boosting
# ---------------------------------------------------------------------------


def _parse_related_ids(entry: KBEntry) -> set[str]:
    """Extract entry IDs from a knowledge entry's 'Related' section.

    Looks for the ## Related section and extracts Markdown links like
    [python-db-redis-rate-limiting](./python/db/redis/rate-limiting.md)
    or inline references like `python-db-redis-rate-limiting`.
    """
    related_section = _extract_section(entry.content, "## Related")
    if not related_section:
        return set()

    ids: set[str] = set()
    # Match markdown links: [id](path) or [id](./path)
    for match in re.finditer(r"\[([^\]]+)\]\([^)]+\)", related_section):
        link_text = match.group(1).strip()
        if link_text:
            ids.add(link_text)

    # Match bare IDs (word-word-word patterns that look like entry IDs)
    for match in re.finditer(r"[a-z]+[-][a-z]+[-][a-z0-9-]+", related_section):
        ids.add(match.group(0))

    return ids


def _extract_section(content: str, heading: str) -> str:
    """Extract a markdown section by heading name."""
    pattern = re.compile(rf"^{heading}\n(.*?)(?=\n## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return ""


def _build_reference_graph(entries: list[KBEntry]) -> dict[str, set[str]]:
    """Build a graph of 'entry_id -> set of related entry IDs'.

    Parses the ## Related section of every entry to find cross-references.
    """
    graph: dict[str, set[str]] = {}
    for entry in entries:
        related = _parse_related_ids(entry)
        if related:
            graph[entry.id] = related
    return graph


def score_cross_reference_boost(
    scored_results: list[tuple[float, KBEntry]],
    all_entries: list[KBEntry],
) -> list[tuple[float, KBEntry]]:
    """Boost entries that are well-referenced by other entries in the results.

    An entry that appears in the Related links of many other entries is
    likely a foundational pattern worth promoting.
    """
    if not scored_results:
        return scored_results

    reference_graph = _build_reference_graph(all_entries)

    reference_count: dict[str, int] = defaultdict(int)
    for entry_id, related_ids in reference_graph.items():
        for rid in related_ids:
            reference_count[rid] += 1

    boosted: list[tuple[float, KBEntry]] = []
    for score, entry in scored_results:
        boost = 0.0
        if entry.id in reference_count:
            # Each reference gives a small boost, capped at 3.0
            boost = min(reference_count[entry.id] * 0.5, 3.0)
        boosted.append((score + boost, entry))

    boosted.sort(key=lambda x: x[0], reverse=True)
    return boosted


# ---------------------------------------------------------------------------
# Results diversification
# ---------------------------------------------------------------------------


def diversify_results(
    scored_results: list[tuple[float, KBEntry]],
    top_k: int,
    diversity_penalty: float = 1.5,
) -> list[KBEntry]:
    """Diversify results by penalizing entries from the same category.

    Ensures cross-category diversity in the top-k results. When two entries
    share a category, the second one gets a penalty applied to its score.
    """
    if not scored_results:
        return []

    selected: list[KBEntry] = []
    seen_categories: set[str] = set()
    remaining = list(scored_results)

    while len(selected) < top_k and remaining:
        best_idx = 0
        best_score = float("-inf")

        for i, (score, entry) in enumerate(remaining):
            effective_score = score
            if entry.category in seen_categories:
                effective_score = score - diversity_penalty
            if effective_score > best_score:
                best_score = effective_score
                best_idx = i

        _, best_entry = remaining.pop(best_idx)
        selected.append(best_entry)
        seen_categories.add(best_entry.category)

    return selected[:top_k]


def search(
    query: str,
    language: str | None = None,
    top_k: int = 5,
    kb_path: Path | None = None,
    use_expansion: bool = True,
    use_boosting: bool = True,
    use_diversification: bool = True,
) -> list[KBEntry]:
    """Search the knowledge base with query expansion, boosting, and diversification.

    Args:
        query: Natural language query (e.g., "how to hash a file in Python")
        language: Filter by language (python, java, etc.)
        top_k: Number of entries to return
        kb_path: Custom knowledge base path
        use_expansion: Enable query expansion (abbreviations, synonyms)
        use_boosting: Enable cross-reference boosting
        use_diversification: Enable category diversification in results

    Returns:
        List of KBEntry objects ranked by relevance.
    """
    if not isinstance(top_k, int):
        raise TypeError(f"top_k must be an int, got {type(top_k).__name__}")
    if top_k < 0:
        raise ValueError(f"top_k must be non-negative, got {top_k}")

    if kb_path is None:
        kb_path = get_kb_path()

    all_entries = load_entries(kb_path)

    if language:
        all_entries = search_by_language(all_entries, language)

    if use_expansion:
        scored = search_expanded(all_entries, query)
    else:
        scored = [(0.0, e) for e in search_by_keywords(all_entries, query)]

    if use_boosting and scored:
        scored = score_cross_reference_boost(scored, all_entries)

    if use_diversification and scored:
        return diversify_results(scored, top_k)
    else:
        return [entry for _, entry in scored[:top_k]]


# ---------------------------------------------------------------------------
# Hybrid search (vector + keyword)
# ---------------------------------------------------------------------------


def hybrid_search(
    query: str,
    language: str | None = None,
    top_k: int = 5,
    kb_path: Path | None = None,
    vector_weight: float = 0.6,
    keyword_weight: float = 0.4,
) -> list[KBEntry]:
    """Hybrid search combining vector similarity with keyword scoring.

    Falls back to pure keyword search when:
    - chromadb / sentence-transformers not installed
    - No vector index exists

    Args:
        query: Search query
        language: Optional language filter
        top_k: Results to return
        kb_path: Custom knowledge base path
        vector_weight: Weight for vector similarity score (0-1)
        keyword_weight: Weight for keyword score (0-1)

    Returns:
        List of KBEntry objects ranked by hybrid score.
    """
    if kb_path is None:
        kb_path = get_kb_path()
    all_entries = load_entries(kb_path)

    if language:
        all_entries = search_by_language(all_entries, language)

    try:
        from llm_kb.vector import vector_search, is_vector_available, index_exists

        if not is_vector_available():
            return search(query, language=language, top_k=top_k, kb_path=kb_path,
                          use_expansion=True, use_boosting=True, use_diversification=False)

        if not index_exists():
            return search(query, language=language, top_k=top_k, kb_path=kb_path,
                          use_expansion=True, use_boosting=True, use_diversification=False)

        vector_results = vector_search(query, language=language, top_k=top_k * 3)

        entry_by_id: dict[str, KBEntry] = {e.id: e for e in all_entries}
        entry_scores: dict[str, float] = {}
        entry_objects: dict[str, KBEntry] = {}

        for vr in vector_results:
            eid = vr["id"]
            if eid in entry_by_id:
                entry_scores[eid] = vr["score"] * vector_weight
                entry_objects[eid] = entry_by_id[eid]

        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))
        for eid, entry in entry_objects.items():
            kw = _score_entry(entry, query_lower, query_words)
            norm_kw = min(kw / 15.0, 1.0)
            entry_scores[eid] += norm_kw * keyword_weight

        scored = [(entry_scores[eid], entry_objects[eid]) for eid in entry_scores]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Apply cross-reference boosting
        scored = score_cross_reference_boost(scored, all_entries)

        return [entry for _, entry in scored[:top_k]]

    except (ImportError, RuntimeError):
        return search(query, language=language, top_k=top_k, kb_path=kb_path,
                      use_expansion=True, use_boosting=True, use_diversification=True)
