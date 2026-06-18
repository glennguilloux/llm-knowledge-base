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
from llm_kb.condenser import condense_entry


def cmd_search(args):
    """Handle 'search' command."""
    out_format = "json" if args.json else args.format

    model_profile = None
    if args.model or args.profile:
        model_profile = get_profile(model_name=args.model, size_hint=args.profile)

    top_k = args.top
    if model_profile and top_k == 3:
        top_k = model_profile.max_entries

    include_anti = getattr(args, "include_anti_patterns", False)

    if args.use_vector:
        results = retrieve(query=args.query, language=args.lang, top_k=top_k, use_vector=True, include_anti_patterns=include_anti)
    else:
        results = retrieve(query=args.query, language=args.lang, top_k=top_k, include_anti_patterns=include_anti)

    if model_profile and results:
        condensed = []
        for entry_dict in results:
            from llm_kb.schema import KBEntry
            dummy = KBEntry(
                filepath=Path(entry_dict.get("source", "")),
                id=entry_dict.get("id", ""),
                title=entry_dict.get("title", ""),
                language=entry_dict.get("language", ""),
                category=entry_dict.get("category", ""),
                tags=entry_dict.get("tags", []),
                retrieval_hint=entry_dict.get("retrieval_hint", ""),
                content=entry_dict.get("content", ""),
            )
            condensed_content = condense_entry(entry_dict["content"], model_profile)
            entry_dict["content"] = condensed_content
            entry_dict["_profile"] = model_profile.name
            condensed.append(entry_dict)
        results = condensed

    if out_format == "json":
        output = []
        for res in results:
            item = {
                "id": res["id"],
                "title": res["title"],
                "language": res["language"],
                "category": res["category"],
                "tags": res["tags"],
            }
            if model_profile:
                item["entry_mode"] = model_profile.entry_mode
            output.append(item)
        print(json.dumps(output, indent=2))
        return

    if out_format == "markdown":
        for i, res in enumerate(results, 1):
            print(f"## {i}. {res['title']}")
            print(f"- **Language**: {res['language']}")
            print(f"- **Category**: {res['category']}")
            print(f"- **Tags**: {', '.join(res['tags'])}")
            if model_profile:
                print(f"- **Mode**: {model_profile.entry_mode}")
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
        if model_profile:
            print(f"    Mode: {model_profile.entry_mode} ({model_profile.name} profile)")
        print()


def cmd_prompt(args):
    """Handle 'prompt' command."""
    out_format = "json" if args.json else args.format

    from llm_kb.prompt import build_prompt as _build_prompt_full

    prompt_kwargs = {
        "query": args.query,
        "language": args.lang,
        "max_tokens": args.max_tokens,
        "model": args.model,
        "profile": args.profile,
        "format_template": getattr(args, "format_template", "raw-text"),
        "include_anti_patterns": getattr(args, "include_anti_patterns", False),
    }
    if args.system_prompt:
        prompt_kwargs["system_prompt"] = args.system_prompt

    prompt_str, metadata = _build_prompt_full(**prompt_kwargs)

    if out_format == "json":
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
                "format_template": metadata.format_template,
                "system_prompt_template": metadata.system_prompt_template,
            }
        }
        print(json.dumps(data, indent=2))
        return

    # default or markdown (just plain prompt)
    print(prompt_str)


def cmd_ask(args):
    """Handle 'ask' command — retrieve, build prompt, and call an LLM."""
    from llm_kb.prompt import build_prompt as _build_prompt_full
    from llm_kb.model_client import ask as _model_ask

    # Step 1: Build prompt with knowledge injection
    prompt_str, metadata = _build_prompt_full(
        query=args.query,
        language=args.lang,
        max_tokens=args.max_tokens,
        model=args.model or args.llm_model,
        profile=args.profile,
        include_anti_patterns=getattr(args, "include_anti_patterns", False),
    )

    # Print metadata to stderr if verbose
    if args.verbose:
        print(f"[llm-kb] Profile: {metadata.profile}", file=sys.stderr)
        print(f"[llm-kb] Model: {args.model or args.llm_model or 'auto'}", file=sys.stderr)
        print(f"[llm-kb] Entries: {metadata.entries_included}", file=sys.stderr)
        print(f"[llm-kb] Total tokens: {metadata.total_tokens}", file=sys.stderr)
        print(file=sys.stderr)

    # Step 2: Call LLM
    provider = args.provider or "ollama"
    ask_kwargs = {"provider": provider}

    if provider == "ollama":
        ask_kwargs["model"] = args.llm_model or "qwen2.5-coder:7b"
        if args.host:
            ask_kwargs["host"] = args.host
    elif provider == "openai":
        ask_kwargs["model"] = args.llm_model or "gpt-4o-mini"
        if args.api_key:
            ask_kwargs["api_key"] = args.api_key
        if args.host:
            ask_kwargs["base_url"] = args.host
    elif provider == "custom":
        ask_kwargs["model"] = args.llm_model or ""
        if args.api_key:
            ask_kwargs["api_key"] = args.api_key
        if args.endpoint:
            ask_kwargs["endpoint"] = args.endpoint

    try:
        response = _model_ask(prompt_str, **ask_kwargs)
        print(response)
    except (ConnectionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


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


def _run_freshness_check(args):
    script = Path(__file__).resolve().parent.parent / "scripts" / "auto_freshness.py"
    if not script.exists():
        print("Error: scripts/auto_freshness.py not found", file=sys.stderr)
        sys.exit(1)

    cmd = [sys.executable, str(script), "--json-only"]
    if args.fix_dates:
        cmd.append("--fix-dates")
    if args.skip_link_check:
        cmd.append("--skip-link-check")
    if args.skip_version_check:
        cmd.append("--skip-version-check")

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)


def cmd_validate(args):
    """Handle 'validate' command."""
    import os
    out_format = "json" if args.json else args.format

    if args.stale:
        _run_freshness_check(args)
        return

    kb_path = get_kb_path()

    skip_files = {"README.md", "schema.md", "CONTRIBUTING.md"}

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

    total = 0
    passed = 0
    failed = 0
    errors_map: dict[str, list[str]] = {}
    warnings_map: dict[str, list[str]] = {}

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


def cmd_index(args):
    """Handle 'index' command — build/rebuild ChromaDB vector index."""
    from llm_kb.vector import build_index, is_vector_available

    if not is_vector_available():
        print("Vector search dependencies not installed.", file=sys.stderr)
        print("Install: pip install llm-knowledge-base[vector]", file=sys.stderr)
        sys.exit(1)

    print("Building vector index from knowledge base entries...")
    count = build_index()
    print(f"Done. Indexed {count} entries.")
    print("Use 'llm-kb search --use-vector' for hybrid search.")


def cmd_gaps(args):
    """Handle 'gaps' command — run gap detection analysis."""
    import sys as _sys
    from pathlib import Path as _Path

    _scripts_dir = str(_Path(__file__).resolve().parent.parent / "scripts")
    if _scripts_dir not in _sys.path:
        _sys.path.insert(0, _scripts_dir)

    from gap_detector import run_gap_detection as _run_gaps
    from crawl_references import run_crawl as _run_crawl

    gap_count = _run_gaps(
        kb_path=".",
        language=args.language,
        output=args.output,
        skip_trends=args.skip_trends,
        skip_simulation=args.skip_simulation,
    )

    if args.include_references:
        print("\n---\nChecking reference repositories for uncovered patterns...\n")
        ref_count = _run_crawl(
            kb_path=".",
            output_dir="references/candidate_entries",
            dry_run=args.dry_run,
        )
        if ref_count:
            print(f"\n{ref_count} uncovered patterns found in reference repos.")
            print(f"Review candidates in references/candidate_entries/")
        else:
            print("\nAll patterns from reference repos are covered.")

    if args.format == "json":
        import json
        print(json.dumps({"gaps_found": gap_count}))
        return

    print(f"\nDone. {gap_count} gaps identified.")


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
    p_search.add_argument("--model", help="Model name for auto-profiling (e.g., qwen2.5-coder:32b)")
    p_search.add_argument("--profile", choices=["small", "medium", "large"], help="Explicit model size profile for condensing output")
    p_search.add_argument("--use-vector", action="store_true", help="Enable hybrid vector+keyword search (requires: pip install llm-knowledge-base[vector])")
    p_search.add_argument("--include-anti-patterns", action="store_true", help="Include anti-pattern entries in results (by default only one is shown)")
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
    p_prompt.add_argument("--system-prompt", help="Custom system prompt template (overrides profile default)")
    p_prompt.add_argument("--format-template", choices=["raw-text", "openai-chat", "claude-xml"], default="raw-text", help="Output format for the prompt")
    p_prompt.add_argument("--include-anti-patterns", action="store_true", help="Include anti-pattern entries in results (by default only one is shown)")
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
    p_validate.add_argument("--stale", action="store_true", help="Run freshness check (stale entries, deprecated patterns, broken links)")
    p_validate.add_argument("--fix-dates", action="store_true", help="With --stale: update last_verified dates for clean entries")
    p_validate.add_argument("--skip-link-check", action="store_true", help="With --stale: skip link checking (faster)")
    p_validate.add_argument("--skip-version-check", action="store_true", help="With --stale: skip version checking (avoids network calls)")
    p_validate.set_defaults(func=cmd_validate)

    # 5. scorecard
    p_card = subparsers.add_parser("scorecard", help="Show quality scorecard details")
    p_card.add_argument("--verbose", "-v", action="store_true", help="Detailed metrics printing")
    p_card.set_defaults(func=cmd_scorecard)

    # 6. benchmark
    p_bench = subparsers.add_parser("benchmark", help="Export benchmark prompts to benchmark_prompts/ (for manual review)")
    p_bench.add_argument("--profile", choices=["small", "medium", "large"], help="Export prompts for a specific profile only (default: all three)")
    p_bench.set_defaults(func=cmd_benchmark)

    # 7. index
    p_index = subparsers.add_parser("index", help="Build/rebuild ChromaDB vector index for hybrid search")
    p_index.set_defaults(func=cmd_index)

    # 8. profile
    p_profile = subparsers.add_parser("profile", help="Show model profile information")
    p_profile.add_argument("--model", help="Model name to check profile for (e.g., qwen2.5-coder:32b)")
    p_profile.add_argument("--profile", dest="profile_hint", choices=["small", "medium", "large"], help="Profile to inspect")
    p_profile.add_argument("--list", "-l", action="store_true", help="List all known models and their profiles")
    p_profile.set_defaults(func=cmd_profile)

    # 9. gaps
    p_gaps = subparsers.add_parser("gaps", help="Run gap detection analysis")
    p_gaps.add_argument("--language", "-l", help="Focus on a specific language (python, java, etc.)")
    p_gaps.add_argument("--output", default="scripts/gap_report.md", help="Output report file path")
    p_gaps.add_argument("--skip-trends", action="store_true", help="Skip trend analysis (network calls)")
    p_gaps.add_argument("--skip-simulation", action="store_true", help="Skip query simulation")
    p_gaps.add_argument("--include-references", "-r", action="store_true", help="Also check reference repos for uncovered patterns")
    p_gaps.add_argument("--dry-run", action="store_true", help="For --include-references: show what would be generated without writing")
    p_gaps.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_gaps.set_defaults(func=cmd_gaps)

    # 10. ask
    p_ask = subparsers.add_parser("ask", help="Ask an LLM with knowledge from the knowledge base")
    p_ask.add_argument("query", help="What to ask (coding question)")
    p_ask.add_argument("--lang", help="Target programming language")
    p_ask.add_argument("--model", help="Model name for auto-profiling (e.g., qwen2.5-coder:32b)")
    p_ask.add_argument("--profile", choices=["small", "medium", "large"], help="Explicit model size profile")
    p_ask.add_argument("--max-tokens", type=int, default=None, help="Model context window (default: profile-based)")
    p_ask.add_argument("--llm-model", help="LLM model to call (default: from config or qwen2.5-coder:7b)")
    p_ask.add_argument("--provider", choices=["ollama", "openai", "custom"], help="LLM provider (default: ollama)")
    p_ask.add_argument("--host", help="Ollama host or OpenAI base URL override")
    p_ask.add_argument("--endpoint", help="Custom LLM endpoint URL (for provider=custom)")
    p_ask.add_argument("--api-key", help="API key (for provider=openai or custom)")
    p_ask.add_argument("--include-anti-patterns", action="store_true", help="Include anti-pattern entries in results (by default only one is shown)")
    p_ask.add_argument("--verbose", "-v", action="store_true", help="Print metadata to stderr before response")
    p_ask.set_defaults(func=cmd_ask)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
