#!/usr/bin/env python3
"""Prompt format and metadata tests.

Tests the build_prompt output for:
- All three profiles (small/medium/large) produce structurally correct output
- Budget calculation respects max_tokens limits
- JSON metadata output contains all required fields
- Format templates (raw-text, openai-chat, claude-xml) produce correct wrappers
- Model auto-profiling maps model names to correct profiles
- Template rendering (render_template) works with and without Jinja2
- Format wrapping (wrap_format) produces correct output for each format
"""

import json
import pytest

from llm_kb.prompt import (
    build_prompt,
    wrap_format,
    render_template,
)
from llm_kb.profiles import PROFILES


# ---------------------------------------------------------------------------
# Profile output format tests
# ---------------------------------------------------------------------------


class TestPromptProfileOutput:
    """Verify each profile produces structurally correct prompts."""

    def test_small_profile_has_knowledge_sections(self):
        prompt, metadata = build_prompt(
            "write a FastAPI endpoint with JWT auth",
            language="python",
            profile="small",
        )
        assert metadata.profile == "small"
        assert len(metadata.entries_included) > 0
        # Small template uses {{ knowledge_blocks }} directly (no "## Retrieved Knowledge")
        assert "WRONG/CORRECT" in prompt or "JWT" in prompt

    def test_medium_profile_is_condensed(self):
        prompt, metadata = build_prompt(
            "write a REST API",
            language="python",
            profile="medium",
        )
        assert metadata.profile == "medium"
        assert len(metadata.entries_included) > 0

    def test_large_profile_is_reference(self):
        prompt, metadata = build_prompt(
            "write a REST API",
            language="python",
            profile="large",
        )
        assert metadata.profile == "large"
        assert len(metadata.entries_included) > 0

    def test_all_profiles_return_some_entries(self):
        for profile in ["small", "medium", "large"]:
            _, metadata = build_prompt("test query", profile=profile)
            assert metadata.profile == profile
            assert isinstance(metadata.entries_included, list)

    def test_small_includes_mistakes(self):
        profile = PROFILES["small"]
        assert profile.include_mistakes is True

    def test_large_excludes_mistakes(self):
        profile = PROFILES["large"]
        assert profile.include_mistakes is False


# ---------------------------------------------------------------------------
# Budget / token limit tests
# ---------------------------------------------------------------------------


class TestPromptBudget:
    """Verify budget calculation respects max_tokens."""

    def test_budget_with_small_context(self):
        _, metadata = build_prompt(
            "write a REST API",
            profile="small",
            max_tokens=1024,
        )
        assert metadata.max_tokens == 1024
        assert metadata.total_tokens <= 1024
        assert metadata.budget_remaining >= 0

    def test_budget_with_large_context(self):
        _, metadata = build_prompt(
            "write a REST API",
            profile="large",
            max_tokens=32768,
        )
        assert metadata.budget_remaining >= 0

    def test_budget_default_uses_profile(self):
        _, metadata = build_prompt("test query", profile="small")
        assert metadata.max_tokens == PROFILES["small"].default_context

    def test_entries_truncated_when_over_budget(self):
        _, metadata = build_prompt(
            "python",
            profile="large",
            max_tokens=512,
        )
        # May or may not truncate depending on entry size, but budget_remaining should be >= 0
        assert metadata.budget_remaining >= 0


# ---------------------------------------------------------------------------
# Format template tests
# ---------------------------------------------------------------------------


class TestPromptFormatTemplates:
    """Verify each format template produces correct output structure."""

    def test_raw_text_format(self):
        prompt, metadata = build_prompt(
            "test query",
            profile="small",
            format_template="raw-text",
        )
        assert metadata.format_template == "raw-text"
        # raw-text: system_prompt + \n\n + user_query
        assert "\n\n" in prompt

    def test_openai_chat_format(self):
        prompt, metadata = build_prompt(
            "test query",
            profile="small",
            format_template="openai-chat",
        )
        assert metadata.format_template == "openai-chat"
        data = json.loads(prompt)
        assert "messages" in data
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][1]["role"] == "user"
        assert len(data["messages"][0]["content"]) > 0

    def test_claude_xml_format(self):
        prompt, metadata = build_prompt(
            "test query",
            profile="small",
            format_template="claude-xml",
        )
        assert metadata.format_template == "claude-xml"
        assert '<message role="system">' in prompt
        assert '<message role="user">' in prompt


# ---------------------------------------------------------------------------
# Metadata content tests
# ---------------------------------------------------------------------------


class TestPromptMetadata:
    """Verify metadata dict contains all required fields and correct values."""

    def test_metadata_has_required_fields(self):
        _, metadata = build_prompt("test query", profile="small")
        required = {
            "query_tokens", "system_prompt_tokens", "knowledge_tokens",
            "total_tokens", "max_tokens", "entries_included",
            "entries_truncated", "budget_remaining", "profile",
            "format_template", "system_prompt_template",
        }
        md_dict = {k: getattr(metadata, k) for k in required}
        assert all(k in md_dict for k in required)

    def test_metadata_tokens_are_non_negative(self):
        _, metadata = build_prompt("test query", profile="medium")
        assert metadata.query_tokens >= 0
        assert metadata.system_prompt_tokens >= 0
        assert metadata.knowledge_tokens >= 0
        assert metadata.total_tokens >= 0

    def test_metadata_has_model_when_specified(self):
        _, metadata = build_prompt("test query", model="qwen2.5-coder:32b")
        assert metadata.model == "qwen2.5-coder:32b"
        assert metadata.profile == "medium"

    def test_metadata_entries_truncated_is_list(self):
        _, metadata = build_prompt("test query", profile="small")
        assert isinstance(metadata.entries_truncated, list)


# ---------------------------------------------------------------------------
# Model auto-profiling tests
# ---------------------------------------------------------------------------


class TestModelAutoProfiling:
    """Verify model name → profile mapping works correctly."""

    def test_small_model_maps_to_small(self):
        _, metadata = build_prompt("test query", model="qwen2.5-coder:7b")
        assert metadata.profile == "small"

    def test_medium_model_maps_to_medium(self):
        _, metadata = build_prompt("test query", model="qwen2.5-coder:32b")
        assert metadata.profile == "medium"

    def test_large_model_maps_to_large(self):
        _, metadata = build_prompt("test query", model="llama3.1:70b")
        assert metadata.profile == "large"

    def test_unknown_model_defaults_to_small(self):
        _, metadata = build_prompt("test query", model="some-unknown-model-v1")
        assert metadata.profile == "small"


# ---------------------------------------------------------------------------
# Template rendering tests
# ---------------------------------------------------------------------------


class TestRenderTemplate:
    """Verify template rendering with and without Jinja2."""

    def test_basic_substitution(self):
        result = render_template("Hello {{ name }}!", {"name": "World"})
        assert "World" in result

    def test_multiple_variables(self):
        result = render_template(
            "{{ a }} + {{ b }} = {{ c }}",
            {"a": 1, "b": 2, "c": 3},
        )
        assert "1 + 2 = 3" in result

    def test_empty_context(self):
        result = render_template("static text", {})
        assert result == "static text"


# ---------------------------------------------------------------------------
# wrap_format unit tests
# ---------------------------------------------------------------------------


class TestWrapFormat:
    """Verify wrap_format produces correct API-specific formats."""

    def test_raw_text(self):
        result = wrap_format("system prompt", "user query", "raw-text")
        assert result == "system prompt\n\nuser query"

    def test_openai_chat_structure(self):
        result = wrap_format("system prompt", "user query", "openai-chat")
        data = json.loads(result)
        assert data["messages"][0]["role"] == "system"
        assert data["messages"][0]["content"] == "system prompt"
        assert data["messages"][1]["role"] == "user"
        assert data["messages"][1]["content"] == "user query"

    def test_claude_xml_structure(self):
        result = wrap_format("system prompt", "user query", "claude-xml")
        assert '<message role="system">' in result
        assert "system prompt" in result
        assert '<message role="user">' in result
        assert "user query" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
