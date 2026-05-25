"""Quality audit regression tests.

Ensures the quality auditor catches critical issues and prevents future
PRs from adding low-quality entries.

These tests run the quality_auditor.py checks in-process so they integrate
with pytest without needing subprocess calls.
"""

import re
from pathlib import Path

import pytest

from retrieval import load_entries


# ---------------------------------------------------------------------------
# Helpers (shared with quality_auditor.py logic)
# ---------------------------------------------------------------------------

SKIP_FILES = {
    "README.md", "schema.md", "CONTRIBUTING.md", "RELEASE_CHECKLIST.md",
    "LLM_CODEBASE_KNOWLEDGE_BASE.md", "CHANGELOG.md", "LICENSE",
}
SKIP_PARENTS = {
    "templates", ".github", "docs", "architecture", "scripts",
    "benchmark_prompts", "prompts", "build", "__pycache__", "node_modules",
}


def get_entry_files() -> list[Path]:
    """Get all knowledge base entry markdown files."""
    kb_path = Path(".")
    files = []
    for md_file in sorted(kb_path.rglob("*.md")):
        if any(part.startswith(".") for part in md_file.parts):
            continue
        if md_file.name in SKIP_FILES:
            continue
        if any(p.name in SKIP_PARENTS for p in md_file.parents):
            continue
        files.append(md_file)
    return files


def extract_section(content: str, heading: str) -> str:
    """Extract the text of a section by heading name.

    Skips headings that appear inside fenced code blocks.
    """
    lines = content.split("\n")
    in_section = False
    in_code_block = False
    result_lines = []

    for line in lines:
        if re.match(r"^```\w*\s*$", line):
            in_code_block = not in_code_block
        if in_section:
            if not in_code_block and re.match(r"^##\s+\S", line):
                break
            result_lines.append(line)
        elif not in_code_block and line.strip() == heading:
            in_section = True

    return "\n".join(result_lines)


def count_wrong_correct_pairs(content: str) -> int:
    """Count WRONG/CORRECT pairs in Common Mistakes AND Standard Pattern."""
    cm_text = extract_section(content, "## Common Mistakes")
    sp_text = extract_section(content, "## Standard Pattern")
    combined = cm_text + "\n" + sp_text
    wrong_count = len(re.findall(r"(?:#|//|--|<!--)\s*WRONG", combined))
    correct_count = len(re.findall(r"(?:#|//|--|<!--)\s*CORRECT", combined))
    return min(wrong_count, correct_count)


def count_gotchas(content: str) -> int:
    """Count gotcha bullet points."""
    g_text = extract_section(content, "## Gotchas")
    if not g_text:
        return 0
    return len(re.findall(r"^-\s+\S", g_text, re.MULTILINE))


def get_related_links(content: str) -> list[str]:
    """Extract Related link targets."""
    r_text = extract_section(content, "## Related")
    if not r_text:
        return []
    md_links = re.findall(r"\[.*?\]\((.+?\.md)\)", r_text)
    plain_links = re.findall(r"^-\s+(.+\.md)\s*$", r_text, re.MULTILINE)
    seen = set()
    result = []
    for link in md_links + plain_links:
        if link not in seen:
            seen.add(link)
            result.append(link)
    return result


def count_code_blocks_in_pattern(content: str) -> int:
    """Count fenced code blocks in Standard Pattern (or Common Mistakes for anti-patterns)."""
    sp_text = extract_section(content, "## Standard Pattern")
    sp_blocks = len(re.findall(r"```\w*\n", sp_text)) if sp_text else 0
    if sp_blocks == 0:
        cm_text = extract_section(content, "## Common Mistakes")
        return len(re.findall(r"```\w*\n", cm_text)) if cm_text else 0
    return sp_blocks


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def all_files():
    return get_entry_files()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestQualityAuditPairs:
    """Every entry must have >= 3 WRONG/CORRECT pairs."""

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_has_three_pairs(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        # Prose-format entries (anti-patterns, project-conventions) use bullet
        # descriptions instead of code WRONG/CORRECT pairs
        is_prose = (
            "anti-pattern" in filepath.parts[0]
            or "antipattern" in filepath.name
            or filepath.parts[0] == "project-conventions"
        )
        pairs = count_wrong_correct_pairs(content)
        if pairs == 0 and is_prose:
            cm_text = extract_section(content, "## Common Mistakes")
            bullets = len(re.findall(r"^-\s+\S", cm_text, re.MULTILINE))
            assert bullets >= 3, (
                f"{filepath}: prose entry needs >= 3 Common Mistakes items, "
                f"found {bullets} bullets"
            )
            return
        assert pairs >= 3, f"{filepath}: only {pairs} WRONG/CORRECT pairs (need >= 3)"


class TestQualityAuditGotchas:
    """Every entry must have >= 3 Gotchas."""

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_has_three_gotchas(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        count = count_gotchas(content)
        assert count >= 3, f"{filepath}: only {count} gotchas (need >= 3)"


class TestQualityAuditLinks:
    """Every entry must have >= 2 valid Related links."""

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_has_two_related_links(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        links = get_related_links(content)
        assert len(links) >= 2, f"{filepath}: only {len(links)} Related links (need >= 2)"

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_related_links_resolve(self, filepath):
        """Every Related link must point to an existing file."""
        content = filepath.read_text(encoding="utf-8")
        links = get_related_links(content)
        broken = []
        for link in links:
            link_clean = link.split("#")[0]
            target = Path(link_clean)
            if not target.exists():
                # Try relative to entry directory
                entry_dir = filepath.parent
                if not (entry_dir / target).exists():
                    broken.append(link)
        assert not broken, f"{filepath}: broken Related links: {broken}"


class TestQualityAuditCodeBlocks:
    """Every entry must have code blocks in Standard Pattern or Common Mistakes."""

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_has_code_blocks(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        count = count_code_blocks_in_pattern(content)
        assert count >= 1, f"{filepath}: no code blocks found"


class TestQualityAuditConfidence:
    """Entries with confidence 'high' must have >= 3 pairs AND >= 3 gotchas."""

    @pytest.mark.parametrize("filepath", get_entry_files(), ids=lambda p: str(p))
    def test_confidence_not_overstated(self, filepath):
        content = filepath.read_text(encoding="utf-8")
        # Parse frontmatter
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return
        import yaml
        try:
            meta = yaml.safe_load(match.group(1))
        except Exception:
            return
        if not isinstance(meta, dict):
            return
        if meta.get("confidence") != "high":
            return

        pairs = count_wrong_correct_pairs(content)
        gotchas = count_gotchas(content)

        # Allow anti-patterns with prose Common Mistakes to keep high confidence
        is_antipattern = "anti-pattern" in filepath.parts[0] or "antipattern" in filepath.name
        if is_antipattern and pairs == 0:
            cm_text = extract_section(content, "## Common Mistakes")
            bullets = len(re.findall(r"^-\s+\S", cm_text, re.MULTILINE))
            if bullets >= 6 and gotchas >= 3:
                return  # Acceptable for anti-pattern entries

        assert pairs >= 3, (
            f"{filepath}: confidence 'high' but only {pairs} pairs — "
            f"downgrade to 'medium' or add more WRONG/CORRECT pairs"
        )
        assert gotchas >= 3, (
            f"{filepath}: confidence 'high' but only {gotchas} gotchas — "
            f"downgrade to 'medium' or add more gotchas"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
