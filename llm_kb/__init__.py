"""LLM Knowledge Base — Retrieval-ready code patterns for small LLMs.

Now supports model-aware prompting: automatically optimizes knowledge delivery
for 7B, 27B, and 70B+ models via profiles.
"""

from llm_kb.retrieve import search, load_entries
from llm_kb.prompt import build_prompt as _build_prompt_full
from llm_kb.scorecard import get_scorecard_data
from llm_kb.profiles import list_models, describe_profile, ModelProfile, PROFILES, MODEL_MAP
from llm_kb.profiles import get_profile as _get_profile

__version__ = "2.0.0"


def get_profile(model: str | None = None, size_hint: str | None = None) -> ModelProfile:
    """Get the appropriate model profile for a given model or size hint.

    Args:
        model: Model name (e.g., "qwen2.5-coder:32b")
        size_hint: One of "small", "medium", "large"

    Returns:
        ModelProfile for the given model or hint.

    Example:
        >>> profile = get_profile(model="qwen2.5-coder:32b")
        >>> print(profile.name)
        'medium'
    """
    return _get_profile(model_name=model, size_hint=size_hint)


def retrieve(query: str, language: str | None = None, top_k: int = 3) -> list[dict]:
    """Retrieve relevant knowledge entries.

    Args:
        query: Natural language query (e.g., "how to hash a file in Python")
        language: Filter by language (python, java, typescript, go, rust, csharp, bash)
        top_k: Number of entries to return

    Returns:
        List of dicts with keys: id, title, language, category, content, tags

    Example:
        >>> results = retrieve("FastAPI JWT authentication")
        >>> print(results[0]["title"])
        'JWT Authentication with FastAPI'
    """
    entries = search(query, language=language, top_k=top_k)
    return [
        {
            "id": entry.id,
            "title": entry.title,
            "language": entry.language,
            "category": entry.category,
            "content": entry.content,
            "tags": entry.tags,
        }
        for entry in entries
    ]


def build_prompt(
    query: str,
    language: str | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
    profile: str | None = None,
) -> str:
    """Build a complete system prompt with retrieved knowledge, optimized for model size.

    Automatically retrieves relevant entries, condenses them for the model's needs,
    and formats into a ready-to-use system prompt.

    Args:
        query: What the user wants to code
        language: Target language
        max_tokens: Model's context window size (uses profile default if None)
        model: Model name for auto-profiling (e.g., "qwen2.5-coder:32b")
        profile: Explicit profile: "small", "medium", or "large"

    Returns:
        Complete system prompt string with knowledge injected

    Example:
        >>> # 7B model — full entries, max 3
        >>> prompt = build_prompt("write a REST API", model="qwen2.5-coder:7b")
        >>>
        >>> # 32B model — condensed entries, max 5
        >>> prompt = build_prompt("write a REST API", model="qwen2.5-coder:32b")
    """
    prompt_str, _ = _build_prompt_full(
        query, language=language, max_tokens=max_tokens, model=model, profile=profile
    )
    return prompt_str


def get_stats() -> dict:
    """Get knowledge base statistics.

    Returns:
        Dict with: total_entries, languages, categories, quality_score

    Example:
        >>> stats = get_stats()
        >>> print(f"{stats['total_entries']} entries across {len(stats['languages'])} languages")
    """
    entries = load_entries()
    languages = set(e.language for e in entries if e.language)
    categories = set(e.category for e in entries if e.category)

    scorecard_data = get_scorecard_data()
    quality_score = scorecard_data["overall"]

    return {
        "total_entries": len(entries),
        "languages": sorted(list(languages)),
        "categories": sorted(list(categories)),
        "quality_score": quality_score,
    }
