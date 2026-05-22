"""End-to-end smoke test suite — tests real user journeys.

These tests exercise the system EXACTLY as a real user would:
- From imports and Python API usage
- From CLI subprocess invocations
- With model profiles and profile-aware prompting
"""

import subprocess
import sys
from pathlib import Path


class TestRealUserJourneys:
    """Test the exact flows a real user would follow."""

    def test_pip_install_and_import(self):
        """User does: pip install -e . && python -c 'from llm_kb import retrieve'"""
        from llm_kb import retrieve, build_prompt, get_stats
        stats = get_stats()
        assert stats["total_entries"] >= 270
        assert "python" in stats["languages"]

    def test_cli_search_returns_results(self):
        """User does: llm-kb search 'sha256'"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "search", "sha256"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "sha256" in result.stdout.lower() or "SHA" in result.stdout

    def test_cli_search_with_language_filter(self):
        """User does: llm-kb search 'JWT' --lang python --top 2"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "search", "JWT", "--lang", "python", "--top", "2"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        # Should show at most 2 entries
        entry_count = sum(1 for line in lines if line.startswith("["))
        assert entry_count <= 2

    def test_cli_prompt_small_model(self):
        """User does: llm-kb prompt 'hash a file' --profile small --lang python"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "prompt", "hash a file", "--profile", "small", "--lang", "python"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        combined = result.stdout.lower()
        assert "hashlib" in combined or "sha256" in combined or "hash" in combined
        # Small model prompt should include exhaustive instructions
        assert "exactly" in combined or "all imports" in combined

    def test_cli_prompt_medium_model(self):
        """User does: llm-kb prompt 'hash a file' --model qwen2.5-coder:32b --lang python"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "prompt", "hash a file",
             "--model", "qwen2.5-coder:32b", "--lang", "python"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        combined = result.stdout.lower()
        assert "hashlib" in combined or "sha256" in combined or "hash" in combined
        # Medium prompt should not include "When to Use" section (model knows this)
        assert "When to Use" not in result.stdout
        # Medium prompt should include condensed format
        assert "condensed" in combined

    def test_cli_stats(self):
        """User does: llm-kb stats"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "stats"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Total entries" in result.stdout
        # Verify a number is shown (entry count may vary)
        import re
        match = re.search(r'Total entries:\s+(\d+)', result.stdout)
        assert match is not None, f"Could not find 'Total entries: N' in: {result.stdout[:200]}"
        entry_count = int(match.group(1))
        assert entry_count >= 270

    def test_cli_profile_list(self):
        """User does: llm-kb profile --list"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "profile", "--list"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "qwen2.5-coder:32b" in result.stdout
        assert "medium" in result.stdout

    def test_cli_scorecard(self):
        """User does: llm-kb scorecard"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "scorecard"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "OVERALL" in result.stdout
        assert "92" in result.stdout

    def test_python_api_retrieve(self):
        """Developer uses Python API in their code"""
        from llm_kb import retrieve
        results = retrieve("FastAPI JWT authentication", language="python")
        assert len(results) > 0
        assert any(
            "jwt" in r.get("id", "").lower() or "auth" in r.get("id", "").lower()
            for r in results
        )

    def test_python_api_build_prompt_model_aware(self):
        """Developer builds a prompt for their specific model"""
        from llm_kb import build_prompt
        prompt_small = build_prompt("write a REST API", profile="small")
        prompt_medium = build_prompt("write a REST API", profile="medium")
        # Medium prompt should be different from small
        assert len(prompt_small) != len(prompt_medium)
        # Both should have relevant content
        assert "REST" in prompt_small or "api" in prompt_small.lower()
        assert "REST" in prompt_medium or "api" in prompt_medium.lower()

    def test_python_api_get_profile(self):
        """Developer looks up their model's profile"""
        from llm_kb import get_profile, list_models
        profile = get_profile(model="qwen2.5-coder:32b")
        assert profile.name == "medium"
        models = list_models()
        assert len(models) >= 20

    def test_cli_prompt_pipes_correctly(self):
        """User does: llm-kb prompt 'hash' which should produce substantial output"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "prompt", "hash"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert len(result.stdout) > 100  # Non-trivial output

    def test_cli_validate(self):
        """User does: llm-kb validate"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "validate"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Passed" in result.stdout

    def test_cli_search_json_output(self):
        """User does: llm-kb search 'hash' --json"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "search", "hash", "--json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_cli_prompt_json_output(self):
        """User does: llm-kb prompt 'hash' --json"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "prompt", "hash", "--json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert "prompt" in data
        assert "metadata" in data
        assert data["metadata"]["profile"] in ("small", "medium", "large")

    def test_cli_profile_model_lookup(self):
        """User does: llm-kb profile --model qwen2.5-coder:7b"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "profile", "--model", "qwen2.5-coder:7b"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "small" in result.stdout.lower()

    def test_cli_profile_model_32b(self):
        """User does: llm-kb profile --model qwen2.5-coder:32b"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "profile", "--model", "qwen2.5-coder:32b"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "medium" in result.stdout.lower()

    def test_cli_benchmark_help(self):
        """User does: llm-kb benchmark --help (should work even without LLM)"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "benchmark", "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "benchmark" in result.stdout.lower() or "export" in result.stdout.lower()

    def test_cli_search_markdown_format(self):
        """User does: llm-kb search 'hash' --format markdown"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "search", "hash", "--format", "markdown"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "## " in result.stdout  # Markdown headings

    def test_cli_stats_json(self):
        """User does: llm-kb stats --json"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "stats", "--json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert "total_entries" in data
        assert "languages" in data
        assert "quality_score" in data

    def test_cli_scorecard_verbose(self):
        """User does: llm-kb scorecard --verbose"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "scorecard", "--verbose"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "SCORECARD" in result.stdout

    def test_cli_validate_json(self):
        """User does: llm-kb validate --json"""
        result = subprocess.run(
            [sys.executable, "-m", "llm_kb", "validate", "--json"],
            capture_output=True, text=True,
        )
        # validate --json may exit with 1 if there are warnings (but no errors)
        assert result.returncode in (0, 1)
        import json
        data = json.loads(result.stdout)
        assert "total" in data
        assert "passed" in data


class TestProfileEdgeCases:
    """Test profile-related edge cases."""

    def test_get_profile_default(self):
        """Unknown model defaults to small"""
        from llm_kb import get_profile
        p = get_profile(model="nonexistent-model:1b")
        assert p.name == "small"

    def test_get_profile_explicit_hint(self):
        """Explicit size_hint overrides"""
        from llm_kb import get_profile
        p = get_profile(size_hint="large")
        assert p.name == "large"

    def test_get_profile_no_args(self):
        """No args defaults to small"""
        from llm_kb import get_profile
        p = get_profile()
        assert p.name == "small"

    def test_get_profile_all_known_models(self):
        """All known models resolve correctly"""
        from llm_kb import get_profile, MODEL_MAP
        for model_name in MODEL_MAP:
            p = get_profile(model=model_name)
            expected = MODEL_MAP[model_name]
            assert p.name == expected, f"{model_name} should resolve to {expected}, got {p.name}"

    def test_list_models_returns_all(self):
        """list_models returns all mapped models"""
        from llm_kb import list_models, MODEL_MAP
        models = list_models()
        assert len(models) == len(MODEL_MAP)
        model_names = {m["model"] for m in models}
        assert model_names == set(MODEL_MAP.keys())
