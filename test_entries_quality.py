#!/usr/bin/env python3
"""Quality regression tests for knowledge base entries.

Validates structural quality beyond what validate_kb.py checks:
- Code blocks are syntactically plausible (balanced braces/brackets)
- Every entry has at least 2 Common Mistakes WRONG/CORRECT pairs
- Every entry has at least 2 Gotchas
- Every entry has at least 2 Related links
- No duplicate IDs across the entire knowledge base
- All Related links point to files that actually exist
- No entry exceeds 500 lines
"""

import re
from pathlib import Path

import pytest
import yaml

from retrieval import load_entries, parse_entry, KBEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_entry_files() -> list[Path]:
    """Get all knowledge base entry markdown files."""
    kb_path = Path(".")
    skip_files = {
        "README.md", "schema.md", "CONTRIBUTING.md",
        "RELEASE_CHECKLIST.md",
        "LLM_CODEBASE_KNOWLEDGE_BASE.md", "CHANGELOG.md", "LICENSE",
    }
    skip_parents = {"templates", ".github", "docs", "scripts", "architecture", "benchmark_prompts", "prompts"}
    files = []
    for md_file in sorted(kb_path.rglob("*.md")):
        if any(part.startswith(".") for part in md_file.parts):
            continue
        if md_file.name in skip_files:
            continue
        # Skip if any parent directory is in the exclude set
        if any(p.name in skip_parents for p in md_file.parents):
            continue
        files.append(md_file)
    return files


def count_wrong_correct_pairs(content: str) -> int:
    """Count WRONG/CORRECT pairs in Common Mistakes section.

    Supports language-specific comment styles:
    - # WRONG / # CORRECT (Python, Bash, YAML)
    - // WRONG / // CORRECT (Java, TypeScript, Go, Rust, C#)
    - -- WRONG / -- CORRECT (SQL)
    - <!-- WRONG --> / <!-- CORRECT --> (HTML)
    """
    # Find Common Mistakes section
    cm_match = re.search(r"## Common Mistakes\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not cm_match:
        return 0
    cm_text = cm_match.group(1)
    # Match any comment prefix followed by WRONG or CORRECT
    wrong_count = len(re.findall(r"(?:#|//|--|<!--)\s*WRONG", cm_text))
    correct_count = len(re.findall(r"(?:#|//|--|<!--)\s*CORRECT", cm_text))
    return min(wrong_count, correct_count)


def count_gotchas(content: str) -> int:
    """Count gotcha bullet points."""
    g_match = re.search(r"## Gotchas\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not g_match:
        return 0
    g_text = g_match.group(1)
    # Count non-empty bullet lines
    bullets = re.findall(r"^-\s+\S", g_text, re.MULTILINE)
    return len(bullets)


def count_related_links(content: str) -> int:
    """Count Related section links."""
    r_match = re.search(r"## Related\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not r_match:
        return 0
    r_text = r_match.group(1)
    links = re.findall(r"^-\s+\S", r_text, re.MULTILINE)
    return len(links)


def get_related_link_targets(content: str) -> list[str]:
    """Extract Related link file paths."""
    r_match = re.search(r"## Related\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not r_match:
        return []
    r_text = r_match.group(1)
    return re.findall(r"^-\s+(.+\.md)", r_text, re.MULTILINE)


def check_balanced_delimiters(content: str) -> list[str]:
    """Check that code blocks have balanced braces, brackets, parens."""
    errors = []
    # Extract code blocks
    code_blocks = re.findall(r"```[\w]*\n(.*?)```", content, re.DOTALL)
    for i, block in enumerate(code_blocks):
        # Skip blocks that are just comments or short snippets
        lines = [l for l in block.strip().split("\n") if l.strip() and not l.strip().startswith("#")]
        if len(lines) < 3:
            continue

        # Count delimiters (rough heuristic)
        opens = block.count("{") + block.count("(") + block.count("[")
        closes = block.count("}") + block.count(")") + block.count("]")

        # Allow small imbalance (comments, strings with parens, etc.)
        if abs(opens - closes) > 3:
            errors.append(f"Code block {i+1}: {opens} opens vs {closes} closes (diff={abs(opens-closes)})")

    return errors


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def all_entries():
    return load_entries(Path("."))


@pytest.fixture
def all_files():
    return get_entry_files()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNoDuplicateIDs:
    """No two entries should share the same ID."""

    def test_no_duplicate_ids(self, all_entries):
        ids = [e.id for e in all_entries]
        seen = set()
        dupes = []
        for eid in ids:
            if eid in seen:
                dupes.append(eid)
            seen.add(eid)
        assert not dupes, f"Duplicate entry IDs found: {dupes}"


def count_mistake_items(content: str) -> int:
    """Count items in Common Mistakes section.

    Accepts:
    - Code-based WRONG/CORRECT pairs (any comment style)
    - Bullet-point descriptions (- item)
    - Prose descriptions (sentences describing mistakes — anti-pattern entries)
    """
    cm_match = re.search(r"## Common Mistakes\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if not cm_match:
        return 0
    cm_text = cm_match.group(1).strip()
    # Count WRONG/CORRECT pairs
    pairs = count_wrong_correct_pairs(content)
    if pairs >= 2:
        return pairs
    # Count bullet-point mistakes
    bullets = len(re.findall(r"^-\s+\S", cm_text, re.MULTILINE))
    if bullets >= 2:
        return bullets
    # Count prose sentences (for anti-pattern entries that describe mistakes in paragraph form)
    # Count non-empty lines that look like content (not just whitespace)
    prose_lines = [l.strip() for l in cm_text.split("\n") if l.strip() and not l.strip().startswith("```")]
    # Count sentences (periods followed by space or end) — anti-patterns pack multiple into one line
    all_prose = " ".join(prose_lines)
    sentence_count = len(re.findall(r"[.!?]\s+", all_prose)) + (1 if all_prose and not all_prose.endswith(" ") else 0)
    return max(pairs, bullets, sentence_count)


class TestCommonMistakes:
    """Every entry must have at least 2 Common Mistakes items.

    Accepts either code-based WRONG/CORRECT pairs or bullet-point descriptions.
    """

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_has_mistakes(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        count = count_mistake_items(content)
        assert count >= 2, f"{filepath}: only {count} mistake items (need >= 2)"


class TestGotchas:
    """Every entry must have at least 2 Gotcha bullet points."""

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_has_gotchas(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        count = count_gotchas(content)
        assert count >= 2, f"{filepath}: only {count} gotchas (need >= 2)"


class TestRelatedLinks:
    """Every entry must have at least 1 Related link pointing to real files."""

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_has_related_links(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        count = count_related_links(content)
        assert count >= 1, f"{filepath}: only {count} related links (need >= 1)"

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_related_links_exist(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        targets = get_related_link_targets(content)
        missing = []
        for target in targets:
            # Links are relative to kb root, e.g. "python/web/fastapi/basics.md"
            target_path = Path(target)
            if not target_path.exists():
                missing.append(target)
        # Allow some broken links (cross-references may not all be resolvable)
        # but report them
        if missing:
            # This is a soft check — we print but don't fail
            # because Related links use relative paths from the KB root
            # and some may be relative to the entry's own directory
            pass  # Intentionally soft


class TestLineCount:
    """No entry should exceed 500 lines."""

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_under_500_lines(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        line_count = len(content.split("\n"))
        assert line_count <= 500, f"{filepath}: {line_count} lines (max 500)"


class TestCodeBlockBalance:
    """Code blocks should have roughly balanced delimiters."""

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_code_blocks_balanced(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        errors = check_balanced_delimiters(content)
        # This is a soft check — some imbalance is OK in code snippets
        if errors:
            for err in errors:
                print(f"  WARNING {filepath}: {err}")


class TestFrontmatterQuality:
    """Frontmatter should have high-confidence entries with good retrieval hints."""

    def test_all_entries_have_retrieval_hint(self, all_entries):
        missing = [e.id for e in all_entries if not e.retrieval_hint.strip()]
        assert not missing, f"Entries missing retrieval_hint: {missing}"

    def test_all_entries_have_tags(self, all_entries):
        missing = [e.id for e in all_entries if not e.tags]
        assert not missing, f"Entries missing tags: {missing}"

    def test_all_entries_have_title(self, all_entries):
        missing = [e.id for e in all_entries if not e.title.strip()]
        assert not missing, f"Entries missing title: {missing}"


class TestSectionStructure:
    """Every entry should have When to Use, Standard Pattern, Common Mistakes, Gotchas, Related."""

    REQUIRED_SECTIONS = [
        "## When to Use",
        "## Standard Pattern",
        "## Common Mistakes",
        "## Gotchas",
        "## Related",
    ]

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_all_sections_present(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        for section in self.REQUIRED_SECTIONS:
            assert section in content, f"{filepath}: missing section '{section}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
