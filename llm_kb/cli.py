"""CLI utility for LLM Knowledge Base."""

import argparse
import sys
import json
import subprocess
from pathlib import Path

from llm_kb import retrieve, build_prompt, get_stats
from llm_kb.retrieve import get_kb_path, load_entries
from llm_kb.schema import validate_entry_with_warnings
from llm_kb.scorecard import get_scorecard_data, print_dashboard
from llm_kb.profiles import get_profile, list_models, describe_profile, ModelProfile


def cmd_search(args):
    """Handle 'search' command."""
    # Handle shorthand --json
    out_format = "json" if args.json else args.format

    results = retrieve(query=args.query, language=args.lang, top_k=args.top)

    if out_format == "json":
        print(json.dumps(results, indent=2))
        return

    if out_format == "markdown":
        for i, res in enumerate(results, 1):
            print(f"## {i}. {res['title']}")
            print(f"- **Language**: {res['language']}")
            print(f"- **Category**: {res['category']}")
            print(f"- **Tags**: {', '.join(res['tags'])}")
            print(f"\n{res['content']}\n")
            print("---")
        return

    # default text
    if not results:
        print("No matching entries found.")
        sys.exit(0)

    print(f"Found {len(results)} matching entries:\n")
    for i, res in enumerate(results, 1):
        print(f"[{i}] {res['title']}")
        print(f"    Language: {res['language']} | Category: {res['category']}")
        print(f"    Tags: {', '.join(res['tags'])}")
        print()


def cmd_prompt(args):
    """Handle 'prompt' command."""
    out_format = "json" if args.json else args.format

    # We can also call the full build_prompt to get metadata if json is requested
    if out_format == "json":
        from llm_kb.prompt import build_prompt as _build_prompt_full
        prompt_str, metadata = _build_prompt_full(
            query=args.query,
            language=args.lang,
            max_tokens=args.max_tokens,
            model=args.model,
            profile=args.profile,
        )
        data = {
            "prompt": prompt_str,
            "metadata": {
                "query_tokens": metadata.query_tokens,
                "system_prompt_tokens": metadata.system_prompt_tokens,
                "knowledge_tokens": metadata.knowledge_tokens,
                "total_tokens": metadata.total_tokens,
                "max_tokens": metadata.max_tokens,
                "entries_included": metadata.entries_included,
                "entries_truncated": metadata.entries_truncated,
                "budget_remaining": metadata.budget_remaining,
                "profile": metadata.profile,
                "model": metadata.model,
            }
        }
        print(json.dumps(data, indent=2))
        return

    # default or markdown (just plain prompt)
    prompt_str = build_prompt(
        query=args.query,
        language=args.lang,
        max_tokens=args.max_tokens,
        model=args.model,
        profile=args.profile,
    )
    print(prompt_str)


def cmd_stats(args):
    """Handle 'stats' command."""
    out_format = "json" if args.json else args.format
    stats = get_stats()

    if out_format == "json":
        print(json.dumps(stats, indent=2))
        return

    # text/markdown formatting
    print("========================================")
    print("LLM Knowledge Base Statistics")
    print("========================================")
    print(f"Total entries:  {stats['total_entries']}")
    print(f"Quality Score:  {stats['quality_score']}/100")
    print(f"Languages ({len(stats['languages'])}): {', '.join(stats['languages'])}")
    print(f"Categories ({len(stats['categories'])}): {', '.join(stats['categories'])}")
    print("========================================")


def cmd_validate(args):
    """Handle 'validate' command."""
    import os
    out_format = "json" if args.json else args.format
    kb_path = get_kb_path()

    passed = 0
    failed = 0
    total = 0
    errors_map = {}
    warnings_map = {}

    skip_files = {"README.md", "schema.md", "CONTRIBUTING.md", "LLM_CODEBASE_KNOWLEDGE_BASE.md"}

    md_files = []
    for root, dirs, files in os.walk(str(kb_path), followlinks=True):
        for f in files:
            if f.endswith(".md"):
                md_file = Path(root) / f
                if any(part.startswith(".") for part in md_file.parts):
                    continue
                if md_file.name in skip_files:
                    continue
                if md_file.parent.name in ("templates", ".github"):
                    continue
                md_files.append(md_file)

    for md_file in sorted(md_files):
        total += 1
        errors, warnings = validate_entry_with_warnings(md_file)
        rel_path = str(md_file.relative_to(kb_path) if kb_path != Path(".") else md_file)

        if errors:
            failed += 1
            errors_map[rel_path] = errors
        else:
            passed += 1

        if warnings:
            warnings_map[rel_path] = warnings

    if out_format == "json":
        result = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors_map,
            "warnings": warnings_map
        }
        print(json.dumps(result, indent=2))
        sys.exit(1 if failed > 0 else 0)

    # Text output
    for path, errors in errors_map.items():
        print(f"FAIL {path}")
        for err in errors:
            print(f"     - {err}")
    for path, warnings in warnings_map.items():
        for warn in warnings:
            print(f"WARN {path}: {warn}")

    print(f"\n{'='*40}")
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    
    sys.exit(1 if failed > 0 else 0)


def cmd_scorecard(args):
    """Handle 'scorecard' command."""
    # Runs the quality scorecard
    data = get_scorecard_data()
    print_dashboard(data, verbose=args.verbose)


def cmd_benchmark(args):
    """Handle 'benchmark' command (export mode)."""
    # Simply invoke scripts/codegen_benchmark.py with --export-prompts
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "codegen_benchmark.py"
    if not script_path.exists():
        script_path = Path("scripts/codegen_benchmark.py")

    if not script_path.exists():
        print("Error: Could not locate scripts/codegen_benchmark.py", file=sys.stderr)
        sys.exit(1)

    print("Running codegen benchmark (export mode)...")
    cmd = [sys.executable, str(script_path), "--export-prompts"]
    # Pass profile if specified
    if args.profile:
        cmd.extend(["--profile", args.profile])
    res = subprocess.run(cmd)
    sys.exit(res.returncode)


def cmd_profile(args):
    """Handle 'profile' command."""
    if args.list:
        # List all known models
        models = list_models()
        print(f"\nKnown models ({len(models)}):\n")
        print(f"{'Model':<35} {'Profile':<10} {'Size':<12} {'Context':<8} {'Entries':<8} {'Mode'}")
        print("-" * 90)
        for m in models:
            print(f"{m['model']:<35} {m['profile']:<10} {m['params_range']:<12} {m['context']:<8} {m['max_entries']:<8} {m['entry_mode']}")
        print()
        return

    # Show profile for a specific model or default
    model_name = args.model
    size_hint = args.profile_hint

    model_profile = get_profile(model_name=model_name, size_hint=size_hint)
    desc = describe_profile(model_profile)

    print()
    if model_name:
        print(f"Model: {model_name}")
    print(desc)
    print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLM Knowledge Base CLI — Retrieval-ready coding patterns."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to run")

    # Global options for all subparsers
    for sub in [subparsers]:
        pass

    # 1. search query
    p_search = subparsers.add_parser("search", help="Search for knowledge entries")
    p_search.add_argument("query", help="Query string")
    p_search.add_argument("--lang", help="Filter by language")
    p_search.add_argument("--top", type=int, default=3, help="Number of results to return")
    p_search.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Output format")
    p_search.add_argument("--json", action="store_true", help="Format output as JSON")
    p_search.set_defaults(func=cmd_search)

    # 2. prompt query
    p_prompt = subparsers.add_parser("prompt", help="Build system prompt with knowledge injection")
    p_prompt.add_argument("query", help="Query/task describing what code to write")
    p_prompt.add_argument("--lang", help="Target programming language")
    p_prompt.add_argument("--max-tokens", type=int, default=None, help="Model context window (default: profile-based)")
    p_prompt.add_argument("--model", help="Model name for auto-profiling (e.g., qwen2.5-coder:32b)")
    p_prompt.add_argument("--profile", choices=["small", "medium", "large"], help="Explicit model size profile")
    p_prompt.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Output format")
    p_prompt.add_argument("--json", action="store_true", help="Format output as JSON with metadata")
    p_prompt.set_defaults(func=cmd_prompt)

    # 3. stats
    p_stats = subparsers.add_parser("stats", help="Show knowledge base statistics")
    p_stats.add_argument("--format", choices=["text", "json", "markdown"], default="text", help="Output format")
    p_stats.add_argument("--json", action="store_true", help="Format output as JSON")
    p_stats.set_defaults(func=cmd_stats)

    # 4. validate
    p_validate = subparsers.add_parser("validate", help="Validate all knowledge base entries")
    p_validate.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_validate.add_argument("--json", action="store_true", help="Format output as JSON")
    p_validate.set_defaults(func=cmd_validate)

    # 5. scorecard
    p_card = subparsers.add_parser("scorecard", help="Show quality scorecard details")
    p_card.add_argument("--verbose", "-v", action="store_true", help="Detailed metrics printing")
    p_card.set_defaults(func=cmd_scorecard)

    # 6. benchmark
    p_bench = subparsers.add_parser("benchmark", help="Export benchmark prompts to benchmark_prompts/ (for manual review)")
    p_bench.add_argument("--profile", choices=["small", "medium", "large"], help="Export prompts for a specific profile only (default: all three)")
    p_bench.set_defaults(func=cmd_benchmark)

    # 7. profile
    p_profile = subparsers.add_parser("profile", help="Show model profile information")
    p_profile.add_argument("--model", help="Model name to check profile for (e.g., qwen2.5-coder:32b)")
    p_profile.add_argument("--profile", dest="profile_hint", choices=["small", "medium", "large"], help="Profile to inspect")
    p_profile.add_argument("--list", "-l", action="store_true", help="List all known models and their profiles")
    p_profile.set_defaults(func=cmd_profile)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
