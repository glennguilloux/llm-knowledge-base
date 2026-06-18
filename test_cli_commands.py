#!/usr/bin/env python3
"""Smoke tests for CLI commands.

Tests the llm-kb CLI via subprocess invocation:
- `llm-kb index` — graceful fallback when vector deps missing
- `llm-kb search` — basic search, JSON output, no-results case
- `llm-kb stats` — text and JSON output
- `llm-kb profile` — list all models, profile for specific model
- `llm-kb validate` — basic validation smoke test

Each test invokes the CLI as a subprocess to verify actual command-line behavior.
"""

import json
import subprocess
import sys
import pytest

pytestmark = pytest.mark.smoke


CLI_CMD = [sys.executable, "-m", "llm_kb.cli"]


def run_cli(*args, expect_failure=False) -> subprocess.CompletedProcess:
    """Run llm-kb CLI with given args and return result."""
    result = subprocess.run(
        CLI_CMD + list(args),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if expect_failure:
        assert result.returncode != 0, (
            f"Expected failure but got exit code 0.\n"
            f"stdout: {result.stdout[:500]}\n"
            f"stderr: {result.stderr[:500]}"
        )
    else:
        assert result.returncode == 0, (
            f"CLI exited with code {result.returncode}.\n"
            f"stdout: {result.stdout[:500]}\n"
            f"stderr: {result.stderr[:500]}"
        )
    return result


# ---------------------------------------------------------------------------
# llm-kb index — smoke test
# ---------------------------------------------------------------------------


class TestCliIndex:
    """Verify `llm-kb index` handles missing vector deps gracefully."""

    def test_index_without_vector_deps_exits_gracefully(self):
        """llm-kb index should show a graceful error when vector deps absent."""
        result = run_cli("index", expect_failure=True)
        stderr_lower = result.stderr.lower()
        stdout_lower = result.stdout.lower()
        combined = stderr_lower + stdout_lower
        assert any(phrase in combined for phrase in [
            "not installed",
            "install",
            "vector",
        ]), f"No graceful fallback message. stderr: {result.stderr[:300]}"

    def test_index_help_shows_usage(self):
        """`llm-kb index --help` should show help text."""
        result = run_cli("index", "--help")
        assert "usage:" in result.stdout.lower()
        assert "index" in result.stdout.lower()


# ---------------------------------------------------------------------------
# llm-kb search — smoke test
# ---------------------------------------------------------------------------


class TestCliSearch:
    """Verify basic search command works."""

    def test_search_basic_text_output(self):
        """Basic text search should print results."""
        result = run_cli("search", "SHA-256 file hashing")
        assert "SHA" in result.stdout or "sha256" in result.stdout.lower()

    def test_search_json_output(self):
        """`llm-kb search --json` should produce valid JSON."""
        result = run_cli("search", "FastAPI", "--json")
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        if data:
            assert "id" in data[0]
            assert "title" in data[0]
            assert "language" in data[0]

    def test_search_no_results_shows_message(self):
        """Search for gibberish should show 'No matching entries'."""
        result = run_cli("search", "zxcvbnmlkjhgfdsa")
        assert "No matching entries" in result.stdout

    def test_search_with_language_filter(self):
        """`--lang python` should only show Python entries."""
        result = run_cli("search", "async", "--lang", "python")
        if "No matching entries" not in result.stdout:
            # Results should mention Python
            assert "python" in result.stdout.lower() or "Python" in result.stdout

    def test_search_markdown_format(self):
        """`--format markdown` should produce markdown output."""
        result = run_cli("search", "testing", "--format", "markdown")
        assert "##" in result.stdout  # markdown headings


# ---------------------------------------------------------------------------
# llm-kb stats — smoke test
# ---------------------------------------------------------------------------


class TestCliStats:
    """Verify stats command works."""

    def test_stats_text_output(self):
        result = run_cli("stats")
        assert "Total entries" in result.stdout
        assert "Quality Score" in result.stdout

    def test_stats_json_output(self):
        result = run_cli("stats", "--json")
        data = json.loads(result.stdout)
        assert "total_entries" in data
        assert "quality_score" in data
        assert "languages" in data
        assert "categories" in data
        assert isinstance(data["total_entries"], int)
        assert data["total_entries"] > 0


# ---------------------------------------------------------------------------
# llm-kb profile — smoke test
# ---------------------------------------------------------------------------


class TestCliProfile:
    """Verify profile command works."""

    def test_profile_list_shows_all_models(self):
        result = run_cli("profile", "--list")
        assert "Known models" in result.stdout
        assert "qwen2.5-coder:7b" in result.stdout

    def test_profile_for_small_model(self):
        result = run_cli("profile", "--model", "qwen2.5-coder:7b")
        assert "small" in result.stdout.lower()

    def test_profile_for_medium_model(self):
        result = run_cli("profile", "--model", "qwen2.5-coder:32b")
        assert "medium" in result.stdout.lower() or "Medium" in result.stdout


# ---------------------------------------------------------------------------
# llm-kb prompt — smoke test
# ---------------------------------------------------------------------------


class TestCliPrompt:
    """Verify prompt command works."""

    def test_prompt_basic_output(self):
        result = run_cli("prompt", "write a REST API", "--lang", "python")
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_prompt_json_output(self):
        result = run_cli("prompt", "test query", "--json")
        data = json.loads(result.stdout)
        assert "prompt" in data
        assert "metadata" in data
        md = data["metadata"]
        assert "total_tokens" in md
        assert "entries_included" in md
        assert "profile" in md


# ---------------------------------------------------------------------------
# llm-kb validate — smoke test
# ---------------------------------------------------------------------------


class TestCliValidate:
    """Verify validate command runs (may find pre-existing issues)."""

    def test_validate_runs(self):
        """Just check the command runs and exits (0 or 1 both OK)."""
        result = subprocess.run(
            CLI_CMD + ["validate"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # Validate may find pre-existing errors, so any exit code is acceptable
        assert "Total" in result.stdout or "FAIL" in result.stdout or "WARN" in result.stdout
        assert "Failed" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
