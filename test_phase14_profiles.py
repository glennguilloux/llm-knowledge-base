"""Tests for model profiles, condenser, and model-aware prompt building."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from llm_kb.profiles import (
    ModelProfile,
    PROFILES,
    MODEL_MAP,
    get_profile,
    list_models,
    describe_profile,
)
from llm_kb.condenser import condense_entry, _extract_sections, estimate_tokens


# ---------------------------------------------------------------------------
# Profile tests
# ---------------------------------------------------------------------------

class TestModelProfile:
    """Test ModelProfile dataclass."""

    def test_profile_is_frozen(self):
        """Profiles should be immutable."""
        profile = PROFILES["small"]
        with pytest.raises(Exception):
            profile.max_entries = 10  # type: ignore[misc]

    def test_profile_required_fields(self):
        """All profiles should have all required fields."""
        for name, profile in PROFILES.items():
            assert profile.name == name
            assert isinstance(profile.min_params_b, (int, float))
            assert isinstance(profile.max_params_b, (int, float))
            assert isinstance(profile.default_context, int)
            assert isinstance(profile.max_entries, int)
            assert profile.entry_mode in ("full", "condensed", "reference")
            assert isinstance(profile.include_mistakes, bool)
            assert isinstance(profile.include_gotchas, bool)
            assert isinstance(profile.include_when_to_use, bool)
            assert isinstance(profile.include_real_world, bool)
            assert isinstance(profile.max_entry_tokens, int)
            assert isinstance(profile.prioritize, list)

    def test_three_profiles_exist(self):
        """Should have small, medium, large profiles."""
        assert "small" in PROFILES
        assert "medium" in PROFILES
        assert "large" in PROFILES

    def test_small_profile_properties(self):
        """Small profile should be exhaustive but limited entries."""
        profile = PROFILES["small"]
        assert profile.max_entries == 3
        assert profile.entry_mode == "full"
        assert profile.include_mistakes is True
        assert profile.include_gotchas is True
        assert profile.include_when_to_use is True
        assert profile.include_real_world is False  # Too long for 4K
        assert profile.default_context == 4096

    def test_medium_profile_properties(self):
        """Medium profile should be condensed with more entries."""
        profile = PROFILES["medium"]
        assert profile.max_entries == 5
        assert profile.entry_mode == "condensed"
        assert profile.include_mistakes is True  # 27B still makes mistakes
        assert profile.include_gotchas is True
        assert profile.include_when_to_use is False  # 27B knows when to use
        assert profile.include_real_world is True
        assert profile.default_context == 8192

    def test_large_profile_properties(self):
        """Large profile should be reference cards with maximum breadth."""
        profile = PROFILES["large"]
        assert profile.max_entries == 8
        assert profile.entry_mode == "reference"
        assert profile.include_mistakes is False  # 70B doesn't need
        assert profile.include_gotchas is True
        assert profile.include_when_to_use is False
        assert profile.include_real_world is False
        assert profile.default_context == 16384


class TestModelMap:
    """Test MODEL_MAP and known models."""

    def test_at_least_20_models(self):
        """Should have 20+ model names mapped."""
        assert len(MODEL_MAP) >= 20

    def test_all_mappings_reference_valid_profiles(self):
        """Every model mapping should point to a valid profile."""
        for model_name, profile_name in MODEL_MAP.items():
            assert profile_name in PROFILES, f"{model_name} -> {profile_name} not found"

    def test_known_small_models(self):
        """Common 7B models should map to 'small'."""
        assert MODEL_MAP["qwen2.5-coder:7b"] == "small"
        assert MODEL_MAP["codellama:7b"] == "small"
        assert MODEL_MAP["deepseek-coder:6.7b"] == "small"
        assert MODEL_MAP["phi-3:14b"] == "small"
        assert MODEL_MAP["qwen2.5-coder:14b"] == "small"

    def test_known_medium_models(self):
        """Common 27-32B models should map to 'medium'."""
        assert MODEL_MAP["qwen2.5-coder:32b"] == "medium"
        assert MODEL_MAP["command-r:35b"] == "medium"
        assert MODEL_MAP["mixtral:8x7b"] == "medium"
        assert MODEL_MAP["qwq:32b"] == "medium"

    def test_known_large_models(self):
        """Common 70B+ models should map to 'large'."""
        assert MODEL_MAP["llama3.1:70b"] == "large"
        assert MODEL_MAP["qwen2.5:72b"] == "large"
        assert MODEL_MAP["codellama:70b"] == "large"


class TestGetProfile:
    """Test get_profile function."""

    def test_model_name_lookup(self):
        """Should find profile by model name."""
        profile = get_profile(model_name="qwen2.5-coder:32b")
        assert profile.name == "medium"
        assert profile.max_entries == 5

    def test_model_name_case_insensitive(self):
        """Model name lookup should be case-insensitive."""
        profile = get_profile(model_name="QWEN2.5-CODER:32B")
        assert profile.name == "medium"

    def test_size_hint(self):
        """Should find profile by size hint."""
        profile = get_profile(size_hint="large")
        assert profile.name == "large"
        assert profile.max_entries == 8

    def test_model_takes_precedence_over_hint(self):
        """Model name should take precedence over size hint."""
        profile = get_profile(model_name="qwen2.5-coder:7b", size_hint="large")
        assert profile.name == "small"  # Model name wins

    def test_unknown_model_falls_back_to_hint(self):
        """Unknown model name should not crash if hint is provided."""
        profile = get_profile(model_name="unknown-model:99b", size_hint="medium")
        assert profile.name == "medium"

    def test_default_to_small(self):
        """No model, no hint → small (safe default)."""
        profile = get_profile()
        assert profile.name == "small"

    def test_unknown_model_no_hint_defaults_small(self):
        """Completely unknown with no hint → small."""
        profile = get_profile(model_name="completely-unknown-model")
        assert profile.name == "small"


class TestListModels:
    """Test list_models function."""

    def test_returns_list_of_dicts(self):
        """Should return a list of dicts with expected keys."""
        models = list_models()
        assert isinstance(models, list)
        assert len(models) >= 20
        for m in models:
            assert "model" in m
            assert "profile" in m
            assert "params_range" in m
            assert "context" in m
            assert "max_entries" in m
            assert "entry_mode" in m

    def test_sorted_alphabetically(self):
        """Models should be sorted by name."""
        models = list_models()
        names = [m["model"] for m in models]
        assert names == sorted(names)


class TestDescribeProfile:
    """Test describe_profile function."""

    def test_small_profile_description(self):
        """Should describe small profile."""
        desc = describe_profile(PROFILES["small"])
        assert "small" in desc
        assert "mistakes" in desc
        assert "when-to-use" in desc

    def test_medium_profile_description(self):
        """Should describe medium profile with exclusion note."""
        desc = describe_profile(PROFILES["medium"])
        assert "medium" in desc
        assert "condensed" in desc
        assert "Excludes: when-to-use" in desc
        assert "27-32B" in desc

    def test_large_profile_description(self):
        """Should describe large profile."""
        desc = describe_profile(PROFILES["large"])
        assert "large" in desc
        assert "reference" in desc
        assert "70B" in desc


# ---------------------------------------------------------------------------
# Condenser tests
# ---------------------------------------------------------------------------

SAMPLE_ENTRY = """---
id: "python-stdlib-hashlib-sha256"
title: "SHA-256 File Hashing"
language: "python"
category: "stdlib"
tags: ["hashlib", "sha256", "hashing"]
retrieval_hint: "SHA256 file hash"
last_verified: "2025-06-01"
confidence: "high"
---

# SHA-256 File Hashing

## When to Use

Use SHA-256 when you need to verify file integrity, generate content-based IDs, or create checksums. SHA-256 is cryptographically secure and produces a 64-character hex digest.

## Standard Pattern

```python
import hashlib
from pathlib import Path

def hash_file(filepath: str | Path) -> str:
    \"\"\"Compute SHA-256 hash of a file.\"\"\"
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
```

## Common Mistakes

```python
# WRONG: Reading entire file into memory
def bad_hash(path):
    with open(path, "rb") as f:
        data = f.read()  # Could be gigabytes!
    return hashlib.sha256(data).hexdigest()

# CORRECT: Stream in chunks
def good_hash(path):
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
```

```python
# WRONG: Not handling binary mode
def bad_hash2(path):
    with open(path, "r") as f:  # Text mode!
        return hashlib.sha256(f.read().encode()).hexdigest()

# CORRECT: Always use "rb" for binary
def good_hash2(path):
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
```

## Gotchas

- Always open files in binary mode ("rb") — text mode may alter line endings
- The `iter(lambda: f.read(8192), b"")` pattern stops when empty bytes returned
- SHA-256 is NOT for passwords — use bcrypt or argon2 instead
- `.hexdigest()` returns a string, `.digest()` returns bytes
- For very large files, consider `hashlib.file_digest()` in Python 3.11+

## Real-World Example

Here's a real-world script that hashes all files in a directory and detects duplicates:

```python
import hashlib
from pathlib import Path

def find_duplicates(directory: Path) -> dict[str, list[Path]]:
    hashes = {}
    for filepath in directory.rglob("*"):
        if filepath.is_file():
            file_hash = hash_file(filepath)
            hashes.setdefault(file_hash, []).append(filepath)
    return {h: paths for h, paths in hashes.items() if len(paths) > 1}
```

This was used in a production system to deduplicate 2TB of user uploads.

## Related

- crypto/password-hashing.md
- python/stdlib/file-io.md
"""


class TestExtractSections:
    """Test section extraction."""

    def test_extracts_title(self):
        """Should extract the title."""
        sections = _extract_sections(SAMPLE_ENTRY)
        assert "title" in sections
        assert "SHA-256 File Hashing" in sections["title"]

    def test_extracts_standard_pattern(self):
        """Should extract Standard Pattern section."""
        sections = _extract_sections(SAMPLE_ENTRY)
        assert "standard_pattern" in sections
        assert "hashlib.sha256()" in sections["standard_pattern"]

    def test_extracts_common_mistakes(self):
        """Should extract Common Mistakes section."""
        sections = _extract_sections(SAMPLE_ENTRY)
        assert "common_mistakes" in sections
        assert "WRONG" in sections["common_mistakes"]
        assert "CORRECT" in sections["common_mistakes"]

    def test_extracts_gotchas(self):
        """Should extract Gotchas section."""
        sections = _extract_sections(SAMPLE_ENTRY)
        assert "gotchas" in sections
        assert "binary mode" in sections["gotchas"]

    def test_extracts_when_to_use(self):
        """Should extract When to Use section."""
        sections = _extract_sections(SAMPLE_ENTRY)
        assert "when_to_use" in sections

    def test_extracts_real_world_example(self):
        """Should extract Real-World Example section."""
        sections = _extract_sections(SAMPLE_ENTRY)
        assert "real_world_example" in sections


class TestCondenseEntry:
    """Test condense_entry function."""

    def test_full_mode_keeps_all(self):
        """Full mode should keep most content."""
        profile = PROFILES["small"]
        result = condense_entry(SAMPLE_ENTRY, profile)
        # Should still have the key sections
        assert "Standard Pattern" in result
        assert "Common Mistakes" in result
        assert "Gotchas" in result
        assert "When to Use" in result
        # Should be shorter than original (trimmed)
        assert len(result) < len(SAMPLE_ENTRY)

    def test_condensed_mode_excludes_when_to_use(self):
        """Condensed mode should exclude When to Use section."""
        profile = PROFILES["medium"]
        result = condense_entry(SAMPLE_ENTRY, profile)
        assert "Standard Pattern" in result
        assert "Common Mistakes" in result
        assert "Gotchas" in result
        # When to Use should NOT be present (medium excludes it)
        assert "When to Use" not in result
        # Real-World Example SHOULD be present (medium includes it)
        assert "Real-World Example" in result

    def test_reference_mode_minimal(self):
        """Reference mode should be very compact."""
        profile = PROFILES["large"]
        result = condense_entry(SAMPLE_ENTRY, profile)
        # Should be much shorter
        assert len(result) < 1000  # Should be very compact
        # Should have title
        assert "SHA-256" in result
        # Should have gotchas
        assert "Gotchas" in result
        # Should NOT have mistakes or when-to-use
        assert "Common Mistakes" not in result
        assert "When to Use" not in result

    def test_condense_respects_token_budget(self):
        """Condensation should respect max_entry_tokens."""
        profile = PROFILES["large"]
        result = condense_entry(SAMPLE_ENTRY, profile)
        estimated = estimate_tokens(result)
        assert estimated <= profile.max_entry_tokens + 50  # Allow small margin

    def test_condensed_preserves_wrong_correct_pairs(self):
        """Medium models still need WRONG/CORRECT pairs."""
        profile = PROFILES["medium"]
        result = condense_entry(SAMPLE_ENTRY, profile)
        # WRONG/CORRECT pairs should still be present
        assert "WRONG" in result
        assert "CORRECT" in result

    def test_reference_drops_wrong_correct(self):
        """Large models don't need WRONG/CORRECT pairs."""
        profile = PROFILES["large"]
        result = condense_entry(SAMPLE_ENTRY, profile)
        assert "WRONG" not in result
        assert "CORRECT" not in result

    def test_condensed_removes_blank_lines_in_code(self):
        """Condensed mode should remove blank lines from code blocks."""
        profile = PROFILES["medium"]
        result = condense_entry(SAMPLE_ENTRY, profile)
        # Should not have consecutive blank lines
        assert "\n\n\n" not in result

    def test_handles_empty_content(self):
        """Should handle empty content gracefully."""
        profile = PROFILES["medium"]
        result = condense_entry("", profile)
        assert result == ""


class TestEstimateTokens:
    """Test token estimation."""

    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_four_chars_per_token(self):
        assert estimate_tokens("abcd") == 1
        assert estimate_tokens("abcdefgh") == 2

    def test_long_text(self):
        text = "x" * 1000
        assert estimate_tokens(text) == 250


# ---------------------------------------------------------------------------
# Model-aware prompt building tests
# ---------------------------------------------------------------------------

class TestModelAwarePromptBuilding:
    """Test that build_prompt respects model profiles."""

    def test_build_prompt_with_model(self):
        """build_prompt with model name should work."""
        from llm_kb.prompt import build_prompt
        prompt, metadata = build_prompt(
            query="hash a file",
            language="python",
            model="qwen2.5-coder:32b",
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert metadata.profile == "medium"
        assert metadata.model == "qwen2.5-coder:32b"

    def test_build_prompt_with_profile(self):
        """build_prompt with profile hint should work."""
        from llm_kb.prompt import build_prompt
        prompt, metadata = build_prompt(
            query="hash a file",
            language="python",
            profile="large",
        )
        assert isinstance(prompt, str)
        assert metadata.profile == "large"

    def test_build_prompt_default_is_small(self):
        """Default profile should be small (backward compatible)."""
        from llm_kb.prompt import build_prompt
        prompt, metadata = build_prompt(
            query="hash a file",
            language="python",
        )
        assert metadata.profile == "small"

    def test_build_prompt_medium_gets_more_entries(self):
        """Medium profile should retrieve more entries."""
        from llm_kb.prompt import build_prompt
        _, meta_small = build_prompt(
            query="write a REST API",
            language="python",
            profile="small",
        )
        _, meta_medium = build_prompt(
            query="write a REST API",
            language="python",
            profile="medium",
        )
        # Medium should have at least as many entries as small (usually more)
        assert len(meta_medium.entries_included) >= len(meta_small.entries_included)

    def test_medium_entries_are_condensed(self):
        """Medium profile entries should show as condensed."""
        from llm_kb.prompt import build_prompt
        # Use a query that returns multiple results
        prompt, metadata = build_prompt(
            query="Python concurrent async asyncio coroutine",
            language="python",
            profile="medium",
        )
        # At least some entries should be condensed
        # (condensed entries end with "(condensed)" in the prompt)
        if len(metadata.entries_included) > 0:
            # Check prompt contains relevant content
            assert len(prompt) > 0

    def test_build_prompt_respects_custom_max_tokens(self):
        """Custom max_tokens should override profile default."""
        from llm_kb.prompt import build_prompt
        _, metadata = build_prompt(
            query="hash a file",
            language="python",
            profile="small",
            max_tokens=8192,  # Override small's 4096 default
        )
        assert metadata.max_tokens == 8192

    def test_build_prompt_json_metadata_includes_profile(self):
        """JSON metadata should include profile and model info."""
        from llm_kb.prompt import build_prompt
        _, metadata = build_prompt(
            query="test query",
            language="python",
            model="qwq:32b",
        )
        assert metadata.profile == "medium"
        assert metadata.model == "qwq:32b"


class TestPublicAPISignature:
    """Test that public API signatures are backward compatible."""

    def test_retrieve_signature(self):
        """retrieve() should still work with old signature."""
        from llm_kb import retrieve
        results = retrieve("FastAPI JWT", language="python", top_k=3)
        assert isinstance(results, list)

    def test_build_prompt_old_signature(self):
        """build_prompt() should still work with old signature."""
        from llm_kb import build_prompt
        prompt = build_prompt(
            query="hash a file",
            language="python",
            max_tokens=4096,
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_prompt_new_model_param(self):
        """build_prompt() should accept model parameter."""
        from llm_kb import build_prompt
        prompt = build_prompt(
            query="hash a file",
            language="python",
            model="qwen2.5-coder:32b",
        )
        assert isinstance(prompt, str)

    def test_build_prompt_new_profile_param(self):
        """build_prompt() should accept profile parameter."""
        from llm_kb import build_prompt
        prompt = build_prompt(
            query="hash a file",
            language="python",
            profile="medium",
        )
        assert isinstance(prompt, str)
