#!/usr/bin/env python3
"""Build prompts with retrieved knowledge base context.

Features:
- Context window budgeting (max_tokens parameter)
- Entry summarization for tight budgets
- Language-aware filtering (boost relevant entries)
- Output with metadata (token counts, budget usage)
- Model-aware prompting: different model sizes get optimized knowledge delivery
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass

from retrieval import KBEntry, search, load_entries

# Try to import profiles and condenser, fall back gracefully
try:
    from llm_kb.profiles import ModelProfile, get_profile, describe_profile, PROFILES
    from llm_kb.condenser import condense_entry as _condense_entry
except ImportError:
    ModelProfile = None
    get_profile = None
    PROFILES = {}
    _condense_entry = None


SYSTEM_PROMPT_TEMPLATE = """You are a coding assistant with access to verified knowledge base entries.

## Retrieved Knowledge

{knowledge_blocks}

## Instructions

- Use the knowledge above to write correct, production-quality code
- Follow the patterns shown in the knowledge entries
- Avoid the common mistakes listed in the entries
- If the knowledge doesn't cover the request, say so and use your general knowledge
"""

# In-code fallback prompts in case the markdown files aren't available
_FALLBACK_SYSTEM_PROMPTS = {
    "small": """You are a coding assistant with access to verified knowledge base entries.
RULES:
1. Follow the patterns in the knowledge entries EXACTLY
2. If no knowledge entry matches, say "No reference found" and mark code as # UNCERTAIN
3. Never invent API methods not shown in the entries
4. Include ALL imports shown in the patterns
5. Use the error handling patterns shown — never write bare try/except

## Retrieved Knowledge

{knowledge_blocks}
""",
    "medium": """You are a coding assistant with access to curated knowledge base entries covering
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
""",
    "large": """Reference cards attached. These contain library-specific patterns, version notes,
and non-obvious gotchas. Apply them where relevant.

{knowledge_blocks}
""",
}


def _load_profile_system_prompt(profile_name: str) -> str:
    """Load the appropriate system prompt template for a profile.

    Tries to read from llm_kb/prompts/<name>.md first, falls back to
    the in-code fallback templates.
    """
    # Try to locate the markdown prompt files relative to this script
    try:
        prompt_path = Path(__file__).parent / "llm_kb" / "prompts" / f"{profile_name}.md"
        if prompt_path.exists():
            content = prompt_path.read_text(encoding="utf-8").strip()
            # Ensure the template has {knowledge_blocks} placeholder
            if "{knowledge_blocks}" not in content:
                content += "\n\n{knowledge_blocks}"
            return content
    except Exception:
        pass

    # Fall back to in-code templates
    return _FALLBACK_SYSTEM_PROMPTS.get(profile_name, SYSTEM_PROMPT_TEMPLATE)

KNOWLEDGE_BLOCK_TEMPLATE = """### {title}
**Language:** {language} | **Category:** {category}
**Source:** {filepath}

{content}
"""

CONDENSED_BLOCK_TEMPLATE = """### {title} (condensed)
**Language:** {language} | **Category:** {category}

{condensed_content}
"""


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token for English/code)."""
    return len(text) // 4


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


def build_knowledge_block(entry: KBEntry) -> str:
    """Format a single knowledge entry as a prompt block."""
    return KNOWLEDGE_BLOCK_TEMPLATE.format(
        title=entry.title,
        language=entry.language,
        category=entry.category,
        filepath=entry.filepath,
        content=entry.content,
    )


def build_condensed_block(entry: KBEntry) -> str:
    """Build a condensed version: Standard Pattern + Gotchas only."""
    content = entry.content

    parts = []
    title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
    if title_match:
        parts.append(f"# {title_match.group(1)}")

    sp_match = re.search(r"## Standard Pattern\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if sp_match:
        parts.append("## Standard Pattern\n" + sp_match.group(1).strip())

    g_match = re.search(r"## Gotchas\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if g_match:
        parts.append("## Gotchas\n" + g_match.group(1).strip())

    condensed = "\n\n".join(parts)

    return CONDENSED_BLOCK_TEMPLATE.format(
        title=entry.title,
        language=entry.language,
        category=entry.category,
        condensed_content=condensed,
    )


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
    """Re-rank entries with language-aware boosting.

    If the query mentions a language, boost entries from that language.
    Always include anti-pattern entries for the detected language.
    """
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

    # Sort: boosted entries first, then by original order
    boosted.sort(key=lambda x: -x[0])
    result = [e for _, e in boosted]

    # Insert anti-patterns near the top if detected language matches
    if anti_patterns:
        result = anti_patterns[:1] + result

    return result


def build_prompt(
    query: str,
    language: str | None = None,
    top_k: int = 3,
    kb_path: Path = Path("."),
    max_tokens: int | None = None,
    system_prompt: str | None = None,
    model: str | None = None,
    profile: str | None = None,
) -> tuple[str, PromptMetadata]:
    """Build a complete prompt with retrieved knowledge.

    Args:
        query: User's coding question
        language: Filter results to this language (auto-detected if None)
        top_k: Number of entries to retrieve (uses profile default if None)
        kb_path: Path to knowledge base root
        max_tokens: Maximum context window size (uses profile default if None)
        system_prompt: Custom system prompt (uses default if None)
        model: Model name for auto-profiling (e.g., "qwen2.5-coder:32b")
        profile: Explicit profile ("small", "medium", "large")

    Returns:
        Tuple of (assembled_prompt, metadata)
    """
    # Resolve profile if available
    model_profile = None
    if get_profile is not None:
        model_profile = get_profile(model_name=model, size_hint=profile)
        if top_k == 3 and model_profile.max_entries != 3:
            top_k = model_profile.max_entries
        if max_tokens is None:
            max_tokens = model_profile.default_context

    if language is None:
        language = _detect_language(query)

    results = search(query, language=language, top_k=top_k, kb_path=kb_path)

    # Apply language-aware boosting
    results = _boost_entries(results, query)

    # Select system prompt template based on profile
    if system_prompt is None and model_profile and model_profile.name:
        sys_template = _load_profile_system_prompt(model_profile.name)
    else:
        sys_template = system_prompt or SYSTEM_PROMPT_TEMPLATE
    system_tokens = estimate_tokens(sys_template)
    query_tokens = estimate_tokens(query)

    # Calculate budget
    if max_tokens:
        # Reserve space for system prompt, query, and response
        response_reserve = max_tokens // 4  # 25% for response
        available = max_tokens - system_tokens - query_tokens - response_reserve
    else:
        available = float("inf")

    # Build knowledge blocks within budget
    knowledge_blocks = []
    used_tokens = 0
    included = []
    truncated = []

    for entry in results:
        # Use profile-aware condensation if available and applicable
        if model_profile and model_profile.entry_mode != "full" and _condense_entry:
            condensed_content = _condense_entry(entry.content, model_profile)
            if model_profile.entry_mode == "reference":
                block = f"### {entry.title}\n**Language:** {entry.language} | **Category:** {entry.category}\n\n{condensed_content}"
            else:
                block = CONDENSED_BLOCK_TEMPLATE.format(
                    title=entry.title,
                    language=entry.language,
                    category=entry.category,
                    condensed_content=condensed_content,
                )
            block_tokens = estimate_tokens(block)

            if used_tokens + block_tokens <= available:
                knowledge_blocks.append(block)
                used_tokens += block_tokens
                included.append(entry.id)
            else:
                truncated.append(entry.id)
        else:
            full_block = build_knowledge_block(entry)
            full_tokens = estimate_tokens(full_block)

            if used_tokens + full_tokens <= available:
                knowledge_blocks.append(full_block)
                used_tokens += full_tokens
                included.append(entry.id)
            else:
                # Try condensed version
                condensed_block = build_condensed_block(entry)
                condensed_tokens = estimate_tokens(condensed_block)

                if used_tokens + condensed_tokens <= available:
                    knowledge_blocks.append(condensed_block)
                    used_tokens += condensed_tokens
                    included.append(f"{entry.id} (condensed)")
                    truncated.append(entry.id)
                # else: skip — doesn't fit even condensed

    # Handle no results
    if not knowledge_blocks:
        knowledge_text = "No relevant knowledge found. Use your general knowledge."
    else:
        separator = "\n---\n"
        if truncated:
            knowledge_blocks.append(
                f"**Note:** {len(truncated)} entries shown in condensed form "
                f"(Standard Pattern + Gotchas only) to fit context budget."
            )
        knowledge_text = separator.join(knowledge_blocks)

    assembled = sys_template.format(knowledge_blocks=knowledge_text)

    metadata = PromptMetadata(
        query_tokens=query_tokens,
        system_prompt_tokens=system_tokens,
        knowledge_tokens=used_tokens,
        total_tokens=system_tokens + query_tokens + used_tokens,
        max_tokens=max_tokens or 0,
        entries_included=included,
        entries_truncated=truncated,
        budget_remaining=(available - used_tokens) if max_tokens else 0,
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


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "FastAPI JWT authentication"

    # Show different budget scenarios
    print(f"Query: {query}\n")

    for max_tok in [None, 4096, 8192, 16384]:
        label = f"max_tokens={max_tok}" if max_tok else "no limit"
        prompt, meta = build_prompt(query, max_tokens=max_tok)
        print(f"--- {label} ---")
        print(format_metadata(meta))
        print()
