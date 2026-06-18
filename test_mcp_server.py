#!/usr/bin/env python3
"""MCP server integration tests.

Tests all MCP tool functions directly (without a running MCP client):
- search_knowledge: basic search, language filter, top_k, edge cases
- build_code_prompt: prompt building with different profiles and formats
- list_languages: returns all covered languages
- get_entry: valid entry lookup, nonexistent entry
- get_model_profile: known model, size hint, unknown model fallback
- list_supported_models: returns all known models
"""

import pytest

from llm_kb.mcp_server import (
    search_knowledge,
    build_code_prompt,
    list_languages,
    get_entry,
    get_model_profile,
    list_supported_models,
)


class TestSearchKnowledge:
    def test_basic_search(self):
        results = search_knowledge("SHA-256 file hashing in Python")
        assert len(results) > 0
        ids = [r["id"] for r in results]
        assert any("sha256" in i or "hashlib" in i for i in ids)

    def test_search_with_language_filter(self):
        results = search_knowledge("hashing", language="python")
        assert len(results) > 0
        assert all(r["language"] == "python" for r in results)

    def test_search_top_k(self):
        results = search_knowledge("testing", top_k=2)
        assert len(results) <= 2

    def test_empty_query_returns_empty(self):
        results = search_knowledge("")
        assert len(results) == 0

    def test_unknown_language_returns_empty(self):
        results = search_knowledge("testing", language="completely-fake-language-xyz")
        assert len(results) == 0


class TestBuildCodePrompt:
    def test_basic_prompt(self):
        result = build_code_prompt("write a REST API with JWT auth", language="python")
        assert isinstance(result, str)
        assert len(result) > 0
        assert "knowledge" in result.lower() or "pattern" in result.lower()

    def test_prompt_with_model_profiling(self):
        result = build_code_prompt("write a REST API", model="qwen2.5-coder:7b")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_prompt_with_max_tokens_limit(self):
        """Small token budget should still produce a valid prompt."""
        result = build_code_prompt("write a function", max_tokens=1024)
        assert isinstance(result, str)
        assert len(result) > 0


class TestListLanguages:
    def test_list_languages_returns_strings(self):
        langs = list_languages()
        assert isinstance(langs, list)
        assert len(langs) > 0
        assert all(isinstance(lang, str) for lang in langs)

    def test_python_is_covered(self):
        langs = list_languages()
        assert "python" in langs


class TestGetEntry:
    def test_get_existing_entry(self):
        entry = get_entry("python-stdlib-hashlib-sha256")
        assert entry is not None
        assert entry["id"] == "python-stdlib-hashlib-sha256"
        assert "title" in entry and "content" in entry
        assert "tags" in entry

    def test_get_nonexistent_entry_returns_none(self):
        entry = get_entry("this-entry-id-should-not-exist-xyz")
        assert entry is None

    def test_get_entry_has_required_fields(self):
        entry = get_entry("python-stdlib-hashlib-sha256")
        required = {"id", "title", "language", "category", "tags", "content"}
        assert required.issubset(entry.keys())


class TestGetModelProfile:
    def test_known_small_model(self):
        profile = get_model_profile(model_name="qwen2.5-coder:7b")
        assert profile["name"] == "small"
        assert profile["max_entries"] == 3

    def test_known_medium_model(self):
        profile = get_model_profile(model_name="qwen2.5-coder:32b")
        assert profile["name"] == "medium"
        assert profile["max_entries"] >= 3

    def test_by_size_hint_large(self):
        profile = get_model_profile(size_hint="large")
        assert profile["name"] == "large"

    def test_by_size_hint_small(self):
        profile = get_model_profile(size_hint="small")
        assert profile["name"] == "small"

    def test_unknown_model_defaults_to_small(self):
        profile = get_model_profile(model_name="some-unknown-model-xyz")
        assert profile["name"] == "small"

    def test_all_profiles_have_required_keys(self):
        required = {"name", "params_range", "default_context", "max_entries",
                     "entry_mode", "max_entry_tokens", "includes", "excludes"}
        for size in ["small", "medium", "large"]:
            profile = get_model_profile(size_hint=size)
            assert required.issubset(profile.keys()), f"{size} missing keys"


class TestListSupportedModels:
    def test_returns_list(self):
        models = list_supported_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_entries_have_required_fields(self):
        models = list_supported_models()
        required = {"model", "profile", "params_range", "context", "max_entries", "entry_mode"}
        for m in models:
            assert required.issubset(m.keys()), f"{m['model']} missing keys"

    def test_known_model_present(self):
        models = list_supported_models()
        model_names = [m["model"] for m in models]
        assert "qwen2.5-coder:7b" in model_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
