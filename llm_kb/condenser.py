"""
Condense knowledge entries based on model profile.

Full entry (for 7B):    ~1500 tokens, all sections, verbose examples
Condensed entry (27B):  ~800 tokens, key pattern + gotchas + mistakes
Reference entry (70B):  ~400 tokens, pattern signature + gotchas only
"""

import re
from llm_kb.profiles import ModelProfile


def condense_entry(entry_content: str, profile: ModelProfile) -> str:
    """Transform a full knowledge entry into a profile-appropriate format.

    For "full" mode (7-14B):
        Keep: all sections, minimal trimming
        Return content mostly as-is, trimmed to max_entry_tokens

    For "condensed" mode (27B-32B):
        Keep: Title, Standard Pattern (trimmed), Common Mistakes, Gotchas
        If include_when_to_use: add When to Use
        If include_real_world: add Real-World Example (trimmed)
        Trim code examples to essentials (remove redundant comments, blank lines)
        Keep WRONG/CORRECT pairs but shorten descriptions

    For "reference" mode (70B+):
        Keep: Title, Standard Pattern (code only, no prose), Gotchas
        Drop: Everything else
        Extract just the function/class signatures and key patterns
        Format as compact reference card
    """
    mode = profile.entry_mode

    # Extract sections
    sections = _extract_sections(entry_content)

    if mode == "full":
        return _condense_full(entry_content, sections, profile)
    elif mode == "condensed":
        return _condense_medium(entry_content, sections, profile)
    elif mode == "reference":
        return _condense_reference(entry_content, sections, profile)
    else:
        # Fallback: return as-is trimmed to budget
        return _trim_to_tokens(entry_content, profile.max_entry_tokens)


def _extract_sections(content: str) -> dict[str, str]:
    """Extract all markdown sections from an entry.

    Returns dict of section_name -> section_content (including heading).
    """
    sections: dict[str, str] = {}

    # Extract title (first # heading)
    title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
    if title_match:
        sections["title"] = title_match.group(0)

    # Extract YAML frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        sections["frontmatter"] = fm_match.group(0)

    # Split into sections by ## headings
    # Find all ## headings and their content
    section_pattern = re.compile(r"(^## .+?$)\n(.*?)(?=\n^## |\Z)", re.MULTILINE | re.DOTALL)
    for match in section_pattern.finditer(content):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        section_name = heading.lstrip("#").strip().lower()
        # Normalize section name
        section_name = section_name.replace(" ", "_").replace("-", "_")
        sections[section_name] = heading + "\n" + body

    return sections


def _condense_full(content: str, sections: dict[str, str], profile: ModelProfile) -> str:
    """Full mode: keep everything, just trim to token budget if needed."""
    # Build the entry with all sections
    parts = []

    if "frontmatter" in sections:
        parts.append(sections["frontmatter"])
    if "title" in sections:
        parts.append(sections["title"])

    # Include sections in order
    section_order = [
        ("when_to_use", profile.include_when_to_use),
        ("standard_pattern", True),  # Always include
        ("common_mistakes", profile.include_mistakes),
        ("gotchas", profile.include_gotchas),
        ("real_world_example", profile.include_real_world),
    ]

    for key, include in section_order:
        if include and key in sections:
            content_block = sections[key]
            # Trim code blocks within the section
            content_block = _trim_code_blocks(content_block)
            parts.append(content_block)

    # Add Related section if present
    if "related" in sections:
        parts.append(_trim_section(sections["related"], 150))

    result = "\n\n".join(parts)
    return _trim_to_tokens(result, profile.max_entry_tokens)


def _condense_medium(content: str, sections: dict[str, str], profile: ModelProfile) -> str:
    """Condensed mode for 27B-32B: key pattern + gotchas + mistakes, trimmed."""
    parts = []

    if "title" in sections:
        parts.append(sections["title"])

    # Standard Pattern — keep but trim aggressively
    if "standard_pattern" in sections:
        sp = sections["standard_pattern"]
        # Trim code blocks: remove blank lines, keep only essential comments
        sp = _trim_code_blocks(sp, max_lines_per_block=30)
        parts.append(sp)

    # When to Use — only if profile says so (default False for medium)
    if profile.include_when_to_use and "when_to_use" in sections:
        wtu = _trim_section(sections["when_to_use"], 100)
        parts.append(wtu)

    # Common Mistakes — keep WRONG/CORRECT pairs, shorten descriptions
    if profile.include_mistakes and "common_mistakes" in sections:
        cm = sections["common_mistakes"]
        cm = _trim_code_blocks(cm, max_lines_per_block=20)
        cm = _shorten_mistake_descriptions(cm)
        parts.append(cm)

    # Gotchas — always keep for medium models (this is where 27B fails)
    if profile.include_gotchas and "gotchas" in sections:
        gotchas = sections["gotchas"]
        gotchas = _trim_section(gotchas, 500)
        parts.append(gotchas)

    # Real-World Example — if profile says so
    if profile.include_real_world and "real_world_example" in sections:
        rwe = sections["real_world_example"]
        rwe = _trim_code_blocks(rwe, max_lines_per_block=25)
        parts.append(rwe)

    result = "\n\n".join(parts)
    return _trim_to_tokens(result, profile.max_entry_tokens)


def _condense_reference(content: str, sections: dict[str, str], profile: ModelProfile) -> str:
    """Reference mode for 70B+: pattern signature + gotchas only, very compact."""
    parts = []

    if "title" in sections:
        parts.append(sections["title"])

    # Standard Pattern — extract ONLY code blocks and key signatures
    if "standard_pattern" in sections:
        sp = sections["standard_pattern"]
        # Extract code blocks only
        code_blocks = re.findall(r"```.*?```", sp, re.DOTALL)
        sp_text = re.sub(r"```.*?```", "", sp, flags=re.DOTALL)
        # Extract only the first sentence of each paragraph
        sp_text = re.sub(r"(?<=[.!?])\s+.*?(?=[.!?])", "", sp_text)
        # Keep only first 200 chars of prose
        sp_text = sp_text[:200].strip()
        parts.append("## Standard Pattern\n" + sp_text + "\n\n" + "\n".join(code_blocks[:3]))

    # Gotchas — compact bullet points
    if profile.include_gotchas and "gotchas" in sections:
        gotchas = sections["gotchas"]
        # Extract bullet points only
        bullets = re.findall(r"^- .+$", gotchas, re.MULTILINE)
        if bullets:
            parts.append("## Gotchas\n" + "\n".join(bullets[:8]))
        else:
            parts.append(_trim_section(gotchas, 200))

    result = "\n\n".join(parts)
    return _trim_to_tokens(result, profile.max_entry_tokens)


def _trim_code_blocks(text: str, max_lines_per_block: int = 30) -> str:
    """Trim code blocks to reduce verbosity.

    - Remove blank lines within code blocks
    - Remove comments that are purely explanatory (keep TODO/FIXME/IMPORTANT)
    - Limit code blocks to max_lines_per_block lines
    """
    def trim_block(match: re.Match) -> str:
        full_block = match.group(0)
        lang_tag = match.group(1) if match.lastindex and match.group(1) else ""

        # Get content between backticks
        if lang_tag:
            content = full_block[len("```" + lang_tag):-len("```")]
            content = content.lstrip("\n")
        else:
            content = full_block[3:-3].lstrip("\n")

        lines = content.split("\n")

        # Remove blank lines
        lines = [l for l in lines if l.strip() != ""]

        # Remove explanatory comments (keep TODO, FIXME, NOTE, IMPORTANT, WRONG, CORRECT)
        filtered = []
        for line in lines:
            stripped = line.strip()
            # Keep non-comment lines
            if not stripped.startswith("#") and not stripped.startswith("//"):
                filtered.append(line)
                continue
            # Keep important comments (includes WRONG/CORRECT for mistake sections)
            lower = stripped.lower()
            if any(kw in lower for kw in ["todo", "fixme", "note:", "important", "warning", "hack", "wrong", "correct"]):
                filtered.append(line)
                continue
            # Drop other comments

        # Limit lines
        if len(filtered) > max_lines_per_block:
            filtered = filtered[:max_lines_per_block]
            filtered.append(f"# ... ({len(lines) - max_lines_per_block} more lines omitted)")

        result = "\n".join(filtered)
        lang_part = lang_tag if lang_tag else ""
        return f"```{lang_part}\n{result}\n```"

    return re.sub(r"```(\w*)\n.*?\n?```", trim_block, text, flags=re.DOTALL)


def _shorten_mistake_descriptions(text: str) -> str:
    """Shorten WRONG/CORRECT descriptions in Common Mistakes section."""
    # Keep code blocks (both fenced and indented), reduce the prose between them
    lines = text.split("\n")
    result_lines = []
    in_fenced_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fenced_block = not in_fenced_block
            result_lines.append(line)
            continue
        if in_fenced_block:
            # Inside fenced code block, keep everything
            result_lines.append(line)
            continue
        # Outside code block — check for indented code (4+ spaces)
        if line.startswith("    ") or line.startswith("\t"):
            result_lines.append(line)
            continue
        # Keep headings and bullet points
        if stripped.startswith("#"):
            result_lines.append(line)
        elif stripped.startswith("-") or stripped.startswith("*"):
            result_lines.append(line)
        elif len(stripped) > 0 and len(stripped) < 200:
            result_lines.append(line)

    return "\n".join(result_lines)


def _trim_section(section_content: str, max_chars: int) -> str:
    """Trim a section to a maximum character count while preserving structure."""
    if len(section_content) <= max_chars:
        return section_content

    # Keep heading
    lines = section_content.split("\n")
    result = [lines[0]]  # Keep the heading
    remaining = max_chars - len(lines[0])

    for line in lines[1:]:
        if remaining <= 0:
            break
        if len(line) + 1 <= remaining:
            result.append(line)
            remaining -= len(line) + 1
        else:
            # Add truncated version of the line
            result.append(line[:remaining] + "...")
            break

    return "\n".join(result)


def _trim_to_tokens(text: str, max_tokens: int) -> str:
    """Trim text to fit within a token budget (~4 chars per token)."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text

    # Try to break at a section boundary
    truncated = text[:max_chars]
    # Find last ## heading
    last_section = truncated.rfind("\n## ")
    if last_section > 0:
        return truncated[:last_section].strip()

    return truncated


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token for English/code)."""
    return len(text) // 4
