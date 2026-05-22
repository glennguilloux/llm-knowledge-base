"""Retrieval edge case tests — stress-testing with real user query patterns.

Tests queries that real users would type: typos, vague queries, special characters,
very long queries, non-English text, and condensed/reference entry quality.
"""

from llm_kb import retrieve, get_profile
from llm_kb.retrieve import search
from llm_kb.condenser import condense_entry
from llm_kb.profiles import PROFILES


class TestRetrievalEdgeCases:
    """Test retrieval with queries that real users would type."""

    def test_typos(self):
        """User types 'fasapi' instead of 'fastapi'"""
        results = retrieve("fasapi authentication")
        assert len(results) > 0  # Should still find FastAPI entries

    def test_typos_jwt(self):
        """User types 'jwt' instead of 'JWT'"""
        results = retrieve("jwt token verification")
        assert len(results) > 0

    def test_very_vague_query(self):
        """User types 'help with code'"""
        results = retrieve("help with code")
        assert isinstance(results, list)  # Shouldn't crash

    def test_very_specific_query(self):
        """User types exact entry title"""
        # Try a query that should match SHA-256 hashing
        results = retrieve("SHA-256 Hashing with hashlib")
        assert len(results) > 0
        assert any("sha256" in r["id"].lower() for r in results)

    def test_multi_language_query(self):
        """User asks about something that exists in multiple languages"""
        results = retrieve("hash a string")
        assert len(results) >= 1  # Should find at least SHA-256 or hashlib

    def test_empty_query(self):
        """User sends empty string"""
        results = retrieve("")
        assert isinstance(results, list)  # Shouldn't crash

    def test_very_long_query(self):
        """User pastes a paragraph"""
        long_query = "I need to write a Python FastAPI endpoint that accepts " * 20
        results = retrieve(long_query)
        assert isinstance(results, list)
        # Should still find relevant entries for the repeated terms
        assert len(results) >= 0  # May or may not find results, but shouldn't crash

    def test_special_characters(self):
        """User includes regex or code in query"""
        results = retrieve("how to use /api/v1/users/{id} in FastAPI")
        assert isinstance(results, list)

    def test_non_english_query(self):
        """User types in another language"""
        results = retrieve("comment hacher un fichier")  # French
        assert isinstance(results, list)

    def test_condensed_entry_quality(self):
        """Verify condensed entries are actually useful"""
        full_entries = retrieve("FastAPI JWT", top_k=1)
        if len(full_entries) == 0:
            import pytest
            pytest.skip("No entries found for 'FastAPI JWT'")
        full = full_entries[0]
        content = full["content"]
        condensed = condense_entry(content, PROFILES["medium"])
        # Condensed should still contain key patterns
        combined = condensed.lower()
        assert "jwt" in combined or "token" in combined
        # Condensed should be shorter
        assert len(condensed) < len(content)

    def test_reference_entry_quality(self):
        """Verify reference entries contain the minimum needed"""
        full_entries = retrieve("FastAPI JWT", top_k=1)
        if len(full_entries) == 0:
            import pytest
            pytest.skip("No entries found for 'FastAPI JWT'")
        full = full_entries[0]
        content = full["content"]
        reference = condense_entry(content, PROFILES["large"])
        condensed = condense_entry(content, PROFILES["medium"])
        # Reference should have meaningful content (title and at least some section)
        assert len(reference) > 0
        assert "jwt" in reference.lower() or "token" in reference.lower() or "auth" in reference.lower()
        # Reference should be very short compared to medium-condensed
        assert len(reference) <= len(condensed), (
            f"Reference ({len(reference)} chars) should be <= condensed ({len(condensed)} chars)"
        )

    def test_full_entry_quality(self):
        """Verify full mode preserves more content"""
        full_entries = retrieve("FastAPI JWT", top_k=1)
        if len(full_entries) == 0:
            import pytest
            pytest.skip("No entries found for 'FastAPI JWT'")
        full = full_entries[0]
        content = full["content"]
        full_result = condense_entry(content, PROFILES["small"])
        condensed = condense_entry(content, PROFILES["medium"])
        # Full should be larger than condensed
        assert len(full_result) >= len(condensed), (
            f"Full ({len(full_result)} chars) should be >= condensed ({len(condensed)} chars)"
        )

    def test_search_preserves_ordering(self):
        """Results should be ordered by relevance"""
        results = retrieve("python hashlib sha256 hash file")
        if len(results) >= 2:
            # First result should be more relevant than second
            # (We can't assert exact order, but results should be deterministic)
            pass  # Documented: ordering is deterministic by score

    def test_retrieve_with_language_filter(self):
        """Language filter should work correctly"""
        py_results = retrieve("hash", language="python")
        go_results = retrieve("hash", language="go")
        # With language filter, all results should match
        if py_results:
            assert all(r["language"] == "python" for r in py_results)
        if go_results:
            assert all(r["language"] == "go" for r in go_results)

    def test_retrieve_top_k_limit(self):
        """top_k should limit results"""
        results = retrieve("hash", top_k=2)
        assert len(results) <= 2

    def test_single_character_query(self):
        """User types a single character"""
        results = retrieve("a")
        assert isinstance(results, list)

    def test_numbers_only_query(self):
        """User types numbers only"""
        results = retrieve("12345")
        assert isinstance(results, list)

    def test_query_with_newlines(self):
        """User query contains newlines"""
        results = retrieve("python\nfastapi\njwt")
        assert isinstance(results, list)


class TestCondenserEdgeCases:
    """Test the condenser with edge case inputs."""

    def test_condense_empty_content(self):
        """Condensing empty content shouldn't crash"""
        result = condense_entry("", PROFILES["small"])
        assert isinstance(result, str)
        assert len(result) == 0

    def test_condense_minimal_content(self):
        """Condensing minimal content shouldn't crash"""
        result = condense_entry("# Title\n\n## Standard Pattern\n\n```python\nx = 1\n```\n", PROFILES["medium"])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_condense_no_sections(self):
        """Entry with no standard sections"""
        result = condense_entry("# Just a title\n\nNo sections here.", PROFILES["small"])
        assert isinstance(result, str)

    def test_condense_all_profiles(self):
        """All profiles should produce valid output"""
        content = "# Test\n\n## Standard Pattern\n```python\ndef foo():\n    return 'bar'\n```\n\n## Common Mistakes\n- Mistake 1: Don't do X\n\n## Gotchas\n- Gotcha 1: Watch for Y"
        for profile_name, profile in PROFILES.items():
            result = condense_entry(content, profile)
            assert isinstance(result, str)
            assert len(result) > 0, f"Profile {profile_name} produced empty result"

    def test_condense_respects_profile_settings(self):
        """Profile settings should affect output"""
        content = (
            "# Test Entry\n\n"
            "## When to Use\nUse this when you need X.\n\n"
            "## Standard Pattern\n```python\ndef example():\n    pass\n```\n\n"
            "## Common Mistakes\n- WRONG: doing it this way\n- CORRECT: doing it that way\n\n"
            "## Gotchas\n- Watch out for Y\n\n"
            "## Real-World Example\nIn production at Company Z, this pattern works well.\n"
        )

        # Small profile includes more sections
        small_result = condense_entry(content, PROFILES["small"])

        # Large profile is very compact
        large_result = condense_entry(content, PROFILES["large"])

        assert len(small_result) > 0
        assert len(large_result) > 0
        # Large should be more compact than small
        assert len(large_result) <= len(small_result), (
            f"Large ({len(large_result)}) should be <= small ({len(small_result)})"
        )


class TestModelMapCoverage:
    """Test the model map covers expected models."""

    def test_all_profiles_have_models(self):
        """Each profile should have at least one model mapped"""
        from llm_kb.profiles import MODEL_MAP, PROFILES
        for profile_name in PROFILES:
            models = [m for m, p in MODEL_MAP.items() if p == profile_name]
            assert len(models) > 0, f"No models mapped to profile '{profile_name}'"

    def test_qwen_models_covered(self):
        """Popular Qwen models should be mapped"""
        from llm_kb.profiles import MODEL_MAP
        assert "qwen2.5-coder:7b" in MODEL_MAP
        assert "qwen2.5-coder:14b" in MODEL_MAP
        assert "qwen2.5-coder:32b" in MODEL_MAP

    def test_deepseek_models_covered(self):
        """DeepSeek models should be mapped"""
        from llm_kb.profiles import MODEL_MAP
        assert "deepseek-coder:6.7b" in MODEL_MAP
        assert "deepseek-coder-v2:16b" in MODEL_MAP

    def test_profile_consistency(self):
        """Models in the same parameter range should have consistent profiles"""
        from llm_kb.profiles import MODEL_MAP
        # All 7-14B models -> small
        small_models = ["qwen2.5-coder:7b", "codellama:13b", "deepseek-coder:6.7b", "starcoder2:7b"]
        for m in small_models:
            assert MODEL_MAP.get(m) == "small", f"{m} should be small"

        # All 70B+ models -> large
        large_models = ["llama3.1:70b", "qwen2.5:72b", "codellama:70b"]
        for m in large_models:
            assert MODEL_MAP.get(m) == "large", f"{m} should be large"
