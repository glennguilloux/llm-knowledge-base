"""Prompt building and formatting with retrieved knowledge context.

Supports model-aware prompting: different model sizes get different amounts
and formats of knowledge based on their capabilities.
"""

import re
from pathlib import Path
from dataclasses import dataclass
from llm_kb.schema import KBEntry
from llm_kb.retrieve import search
from llm_kb.profiles import ModelProfile, get_profile, describe_profile
from llm_kb.condenser import condense_entry, estimate_tokens, _trim_to_tokens


# ---------------------------------------------------------------------------
# System prompt templates (fallback if profile-specific ones not loaded)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are a coding assistant with access to verified knowledge base entries.

## Retrieved Knowledge

{knowledge_blocks}

## Instructions

- Use the knowledge above to write correct, production-quality code
- Follow the patterns shown in the knowledge entries
- Avoid the common mistakes listed in the entries
- If the knowledge doesn't cover the request, say so and use your general knowledge
"""

SYSTEM_PROMPT_MEDIUM = """You are a coding assistant with access to curated knowledge base entries covering
library-specific patterns, version-sensitive APIs, and integration examples.
Use the knowledge entries as authoritative reference for:
- Library-specific syntax (SQLAlchemy 2.0, Pydantic v2, Spring Boot 3)
- Common mistakes and gotchas for the target framework
- Integration patterns between systems

You already know standard library APIs and general programming patterns.
Focus on applying the LIBRARY-SPECIFIC patterns from the knowledge entries.
If the knowledge contradicts your training, trust the knowledge — it's version-verified.

## Retrieved Knowledge

{knowledge_blocks}
"""

SYSTEM_PROMPT_LARGE = """Reference cards attached. These contain library-specific patterns, version notes,
and non-obvious gotchas. Apply them where relevant.

{knowledge_blocks}
"""

SYSTEM_PROMPT_SMALL = """You are a coding assistant with access to verified knowledge base entries.
RULES:
1. Follow the patterns in the knowledge entries EXACTLY
2. If no knowledge entry matches, say "No reference found" and mark code as # UNCERTAIN
3. Never invent API methods not shown in the entries
4. Include ALL imports shown in the patterns
5. Use the error handling patterns shown — never write bare try/except

## Retrieved Knowledge

{knowledge_blocks}
"""

# Map profile name to system prompt template
PROFILE_PROMPTS = {
    "small": SYSTEM_PROMPT_SMALL,
    "medium": SYSTEM_PROMPT_MEDIUM,
    "large": SYSTEM_PROMPT_LARGE,
}


# ---------------------------------------------------------------------------
# Block templates
# ---------------------------------------------------------------------------

KNOWLEDGE_BLOCK_TEMPLATE = """### {title}
**Language:** {language} | **Category:** {category}
**Source:** {filepath}

{content}
"""

CONDENSED_BLOCK_TEMPLATE = """### {title} (condensed)
**Language:** {language} | **Category:** {category}

{condensed_content}
"""

REFERENCE_BLOCK_TEMPLATE = """### {title}
**Language:** {language} | **Category:** {category}

{content}
"""


# ---------------------------------------------------------------------------
# Prompt metadata
# ---------------------------------------------------------------------------

@dataclass
class PromptMetadata:
    """Metadata about the assembled prompt."""
    query_tokens: int
    system_prompt_tokens: int
    knowledge_tokens: int
    total_tokens: int
    max_tokens: int
    entries_included: list[str]
    entries_truncated: list[str]
    budget_remaining: int
    profile: str = "small"
    model: str = ""


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------

def build_knowledge_block(entry: KBEntry) -> str:
    """Format a single knowledge entry as a full prompt block."""
    return KNOWLEDGE_BLOCK_TEMPLATE.format(
        title=entry.title,
        language=entry.language,
        category=entry.category,
        filepath=entry.filepath,
        content=entry.content,
    )


def build_condensed_block(entry: KBEntry, profile: ModelProfile) -> str:
    """Build a condensed knowledge block based on model profile."""
    condensed_content = condense_entry(entry.content, profile)
    if profile.entry_mode == "reference":
        return REFERENCE_BLOCK_TEMPLATE.format(
            title=entry.title,
            language=entry.language,
            category=entry.category,
            content=condensed_content,
        )
    elif profile.entry_mode == "condensed":
        return CONDENSED_BLOCK_TEMPLATE.format(
            title=entry.title,
            language=entry.language,
            category=entry.category,
            condensed_content=condensed_content,
        )
    else:
        return build_knowledge_block(entry)


def _detect_language(query: str) -> str | None:
    """Detect programming language from query text."""
    q = query.lower()
    lang_keywords = {
        "python": ["python", "fastapi", "flask", "django", "pytest", "sqlalchemy", "pydantic"],
        "java": ["java", "spring", "jpa", "junit", "maven", "gradle"],
        "typescript": ["typescript", "react", "next.js", "nextjs", "vue", "angular", "express"],
        "go": ["golang", " go ", "goroutine", "chi"],
        "rust": ["rust", "axum", "tokio", "cargo"],
        "csharp": ["c#", "csharp", ".net", "asp.net", "entity framework"],
        "bash": ["bash", "shell", "sh "],
    }
    for lang, keywords in lang_keywords.items():
        if any(kw in q for kw in keywords):
            return lang
    return None


def _boost_entries(entries: list[KBEntry], query: str) -> list[KBEntry]:
    """Re-rank entries with language-aware boosting."""
    detected_lang = _detect_language(query)
    if not detected_lang:
        return entries

    boosted = []
    anti_patterns = []

    for entry in entries:
        score_boost = 0
        if entry.language == detected_lang:
            score_boost = 10
        if "anti-pattern" in entry.id or "antipattern" in entry.id:
            if entry.language == detected_lang or entry.language == "multi":
                anti_patterns.append(entry)
                continue
        boosted.append((score_boost, entry))

    boosted.sort(key=lambda x: -x[0])
    result = [e for _, e in boosted]

    if anti_patterns:
        result = anti_patterns[:1] + result

    return result


# ---------------------------------------------------------------------------
# _load_profile_prompt
# ---------------------------------------------------------------------------

def _load_profile_prompt(profile: ModelProfile) -> str:
    """Load the appropriate system prompt template for a profile.

    Tries to read from llm_kb/prompts/<name>.md first, falls back to
    the in-code templates.
    """
    prompt_path = Path(__file__).parent / "prompts" / f"{profile.name}.md"
    if prompt_path.exists():
        try:
            content = prompt_path.read_text(encoding="utf-8").strip()
            # Ensure the template has {knowledge_blocks} placeholder
            if "{knowledge_blocks}" not in content:
                content += "\n\n{knowledge_blocks}"
            return content
        except Exception:
            pass

    # Fall back to in-code templates
    return PROFILE_PROMPTS.get(profile.name, SYSTEM_PROMPT_TEMPLATE)


# ---------------------------------------------------------------------------
# Main build_prompt function
# ---------------------------------------------------------------------------

def build_prompt(
    query: str,
    language: str | None = None,
    top_k: int | None = None,
    kb_path: Path | None = None,
    max_tokens: int | None = None,
    system_prompt: str | None = None,
    model: str | None = None,
    profile: str | None = None,
) -> tuple[str, PromptMetadata]:
    """Build a complete prompt with retrieved knowledge, optimized for model size.

    Args:
        query: User's coding question
        language: Filter results to this language (auto-detected if None)
        top_k: Number of entries to retrieve (uses profile default if None)
        kb_path: Path to knowledge base root
        max_tokens: Maximum context window size (uses profile default if None)
        system_prompt: Custom system prompt (uses profile-appropriate default if None)
        model: Model name (e.g., "qwen2.5-coder:32b") for auto-profiling
        profile: Explicit profile ("small", "medium", "large")

    Returns:
        Tuple of (assembled_prompt, metadata)

    Examples:
        # 7B model — full entries, max 3
        build_prompt("write a REST API", model="qwen2.5-coder:7b")

        # 32B model — condensed entries, max 5
        build_prompt("write a REST API", model="qwen2.5-coder:32b")

        # Explicit profile
        build_prompt("write a REST API", profile="medium")
    """
    # Resolve profile
    model_profile = get_profile(model_name=model, size_hint=profile)

    # Apply profile defaults
    if max_tokens is None:
        max_tokens = model_profile.default_context
    if top_k is None:
        top_k = model_profile.max_entries

    # Auto-detect language
    if language is None:
        language = _detect_language(query)

    # Search with appropriate top_k
    results = search(query, language=language, top_k=top_k, kb_path=kb_path)

    # Apply language-aware boosting
    results = _boost_entries(results, query)

    # Select system prompt template
    if system_prompt is None:
        sys_template = _load_profile_prompt(model_profile)
    else:
        sys_template = system_prompt

    system_tokens = estimate_tokens(sys_template)
    query_tokens = estimate_tokens(query) if query else 0

    # Calculate budget
    if max_tokens:
        response_reserve = max_tokens // 4
        available = max_tokens - system_tokens - query_tokens - response_reserve
    else:
        available = float("inf")

    # Build knowledge blocks within budget
    knowledge_blocks = []
    used_tokens = 0
    included = []
    truncated = []

    for entry in results:
        if model_profile.entry_mode == "full":
            # Full mode: use full entry, fall back to condensed if needed
            full_block = build_knowledge_block(entry)
            full_tokens = estimate_tokens(full_block)

            if used_tokens + full_tokens <= available:
                knowledge_blocks.append(full_block)
                used_tokens += full_tokens
                included.append(entry.id)
            else:
                # Try condensed version for full mode
                condensed_block = build_condensed_block(entry, model_profile)
                condensed_tokens = estimate_tokens(condensed_block)
                if used_tokens + condensed_tokens <= available:
                    knowledge_blocks.append(condensed_block)
                    used_tokens += condensed_tokens
                    included.append(f"{entry.id} (condensed)")
                    truncated.append(entry.id)
        else:
            # Condensed/reference mode: always use profile-optimized format
            block = build_condensed_block(entry, model_profile)
            block_tokens = estimate_tokens(block)

            if used_tokens + block_tokens <= available:
                knowledge_blocks.append(block)
                used_tokens += block_tokens
                included.append(entry.id)
            else:
                # Try to trim further using token-aware trimming
                remaining_tokens = available - used_tokens
                if remaining_tokens > 100:  # Only worth it for meaningful content
                    trimmed = _trim_to_tokens(block, remaining_tokens)
                    if estimate_tokens(trimmed) > 0:
                        knowledge_blocks.append(trimmed)
                        used_tokens += estimate_tokens(trimmed)
                        included.append(f"{entry.id} (trimmed)")
                        truncated.append(entry.id)

    # Handle no results
    separator = "\n---\n"
    if not knowledge_blocks:
        knowledge_text = "No relevant knowledge found. Use your general knowledge."
    elif truncated:
        knowledge_blocks.append(
            f"**Note:** {len(truncated)} entries truncated to fit context budget "
            f"(profile: {model_profile.name})."
        )
        knowledge_text = separator.join(knowledge_blocks)
    else:
        knowledge_text = separator.join(knowledge_blocks)

    # Check if template has knowledge_blocks placeholder
    if "{knowledge_blocks}" in sys_template:
        assembled = sys_template.format(knowledge_blocks=knowledge_text)
    else:
        assembled = sys_template + "\n\n" + knowledge_text

    metadata = PromptMetadata(
        query_tokens=query_tokens,
        system_prompt_tokens=system_tokens,
        knowledge_tokens=used_tokens,
        total_tokens=system_tokens + query_tokens + used_tokens,
        max_tokens=max_tokens or 0,
        entries_included=included,
        entries_truncated=truncated,
        budget_remaining=(available - used_tokens) if max_tokens else 0,
        profile=model_profile.name,
        model=model or "",
    )

    return assembled, metadata


def build_user_prompt(query: str, context: str = "") -> str:
    """Build the user-facing prompt."""
    parts = []
    if context:
        parts.append(f"Context: {context}")
    parts.append(query)
    return "\n\n".join(parts)


def format_metadata(metadata: PromptMetadata) -> str:
    """Format metadata as a human-readable report."""
    lines = []
    lines.append("=" * 50)
    lines.append("PROMPT BUDGET REPORT")
    lines.append("=" * 50)
    if metadata.model:
        lines.append(f"Model: {metadata.model}")
    lines.append(f"Profile: {metadata.profile}")
    lines.append(f"Query: {metadata.query_tokens} tokens")
    lines.append(f"System: {metadata.system_prompt_tokens} tokens")
    lines.append(f"Knowledge: {metadata.knowledge_tokens} tokens")
    lines.append(f"Total: {metadata.total_tokens} tokens")
    if metadata.max_tokens:
        lines.append(f"Max context: {metadata.max_tokens} tokens")
        lines.append(f"Remaining: {metadata.budget_remaining} tokens")
    lines.append(f"\nEntries included ({len(metadata.entries_included)}):")
    for eid in metadata.entries_included:
        lines.append(f"  + {eid}")
    if metadata.entries_truncated:
        lines.append(f"\nEntries truncated ({len(metadata.entries_truncated)}):")
        for eid in metadata.entries_truncated:
            lines.append(f"  ~ {eid}")
    lines.append("=" * 50)
    return "\n".join(lines)
