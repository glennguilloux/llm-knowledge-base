"""Quality scorecard metrics for LLM Knowledge Base."""

import re
from datetime import datetime, timedelta
from pathlib import Path
from llm_kb.schema import KBEntry
from llm_kb.retrieve import load_entries, parse_entry, get_kb_path


def score_coverage(entries: list[KBEntry]) -> tuple[int, list[str]]:
    """What % of common coding tasks have at least one entry?"""
    essential_topics = {
        # Python
        "python-http-client", "python-http-server", "python-json",
        "python-file-io", "python-regex", "python-logging",
        "python-testing", "python-orm", "python-caching",
        "python-auth", "python-async", "python-cli",
        "python-env-config", "python-error-handling",
        # Java
        "java-collections", "java-streams", "java-exception",
        "java-concurrency", "java-testing", "java-dependency-injection",
        "java-rest-api", "java-orm", "java-security",
        # TypeScript
        "ts-async", "ts-error-handling", "ts-react", "ts-nextjs",
        "ts-express", "ts-testing", "ts-state", "ts-validation",
        # Go
        "go-goroutines", "go-channels", "go-error-handling",
        "go-http", "go-testing", "go-orm",
        # Rust
        "rust-ownership", "rust-error-handling", "rust-web",
        "rust-testing", "rust-serde",
        # Cross-cutting
        "docker", "kubernetes", "ci-cd", "database-postgres",
        "database-mongodb", "redis", "security", "api-design",
        "monitoring", "caching",
    }

    all_text = {e.id: f"{e.title} {' '.join(e.tags)} {e.retrieval_hint}".lower() for e in entries}
    covered = set()

    topic_keywords = {
        "python-http-client": ["requests", "httpx", "urllib"],
        "python-http-server": ["fastapi", "flask", "django", "uvicorn"],
        "python-json": ["json", "serialize"],
        "python-file-io": ["file", "pathlib", "read", "write"],
        "python-regex": ["regex", "re.compile", "pattern"],
        "python-logging": ["logging", "logger"],
        "python-testing": ["pytest", "unittest", "test"],
        "python-orm": ["sqlalchemy", "orm", "model"],
        "python-caching": ["redis", "cache"],
        "python-auth": ["jwt", "auth", "oauth"],
        "python-async": ["async", "await", "asyncio"],
        "python-cli": ["argparse", "click", "typer", "cli"],
        "python-env-config": ["dotenv", "env", "config"],
        "python-error-handling": ["error", "exception", "try", "except"],
        "java-collections": ["hashmap", "arraylist", "collections"],
        "java-streams": ["stream", "filter", "map", "collect"],
        "java-exception": ["exception", "try", "catch"],
        "java-concurrency": ["concurrent", "executor", "thread"],
        "java-testing": ["junit", "mockito", "test"],
        "java-dependency-injection": ["spring", "inject", "bean"],
        "java-rest-api": ["controller", "rest", "api"],
        "java-orm": ["jpa", "hibernate", "repository"],
        "java-security": ["security", "jwt", "oauth"],
        "ts-async": ["async", "await", "promise"],
        "ts-error-handling": ["error", "result", "catch"],
        "ts-react": ["react", "hooks", "component"],
        "ts-nextjs": ["next", "app router", "server component"],
        "ts-express": ["express", "middleware"],
        "ts-testing": ["vitest", "playwright", "jest"],
        "ts-state": ["zustand", "tanstack", "redux", "state"],
        "ts-validation": ["zod", "validation", "schema"],
        "go-goroutines": ["goroutine", "go func"],
        "go-channels": ["channel", "chan"],
        "go-error-handling": ["error", "wrap"],
        "go-http": ["http", "handler", "server"],
        "go-testing": ["test", "benchmark"],
        "go-orm": ["gorm", "sqlx", "database"],
        "rust-ownership": ["ownership", "borrow", "lifetime"],
        "rust-error-handling": ["result", "error", "anyhow", "thiserror"],
        "rust-web": ["axum", "actix", "web"],
        "rust-testing": ["test", "assert"],
        "rust-serde": ["serde", "serialize", "deserialize"],
        "docker": ["docker", "dockerfile", "compose"],
        "kubernetes": ["kubernetes", "k8s", "pod", "helm"],
        "ci-cd": ["github actions", "ci", "cd", "pipeline"],
        "database-postgres": ["postgres", "postgresql"],
        "database-mongodb": ["mongodb", "mongo"],
        "redis": ["redis"],
        "security": ["security", "xss", "csrf", "owasp"],
        "api-design": ["api design", "rest", "versioning"],
        "monitoring": ["observability", "metrics", "tracing"],
        "caching": ["cache", "cdn", "redis"],
    }

    for topic, keywords in topic_keywords.items():
        for eid, text in all_text.items():
            if any(kw in text for kw in keywords):
                covered.add(topic)
                break

    pct = int(len(covered) / len(essential_topics) * 100)
    gaps = sorted(essential_topics - covered)
    return pct, gaps


def score_depth(entries: list[KBEntry]) -> tuple[int, dict]:
    """Average entries per category."""
    from collections import Counter
    cats = Counter(f"{e.language}/{e.category}" for e in entries)
    avg = sum(cats.values()) / len(cats) if cats else 0
    score = min(100, int(avg / 5 * 100))
    return score, dict(cats.most_common(20))


def score_cross_references(entries: list[KBEntry]) -> tuple[int, list[str]]:
    """What % of entries have valid Related links?"""
    valid = 0
    broken = []
    # Make sure we use the resolved kb directory
    kb_root = get_kb_path()

    for entry in entries:
        content = entry.content
        r_match = re.search(r"## Related\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
        if not r_match:
            broken.append(f"{entry.id}: no Related section")
            continue

        links = re.findall(r"^-\s+(.+\.md)", r_match.group(1), re.MULTILINE)
        if not links:
            broken.append(f"{entry.id}: no .md links in Related")
            continue

        entry_valid = True
        for link in links:
            if not (kb_root / link).exists():
                entry_dir = entry.filepath.parent
                if not (entry_dir / link).exists():
                    entry_valid = False
                    broken.append(f"{entry.id}: broken link {link}")

        if entry_valid:
            valid += 1

    pct = int(valid / len(entries) * 100) if entries else 0
    return pct, broken[:20]


def score_freshness(entries: list[KBEntry]) -> tuple[int, list[str]]:
    """How many entries have last_verified within 6 months?"""
    fresh = 0
    stale = []
    cutoff = datetime.now() - timedelta(days=180)

    for entry in entries:
        content = entry.content
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            stale.append(f"{entry.id}: no frontmatter")
            continue

        import yaml
        try:
            meta = yaml.safe_load(match.group(1))
        except Exception:
            stale.append(f"{entry.id}: invalid YAML")
            continue

        lv = meta.get("last_verified", "")
        if not lv:
            stale.append(f"{entry.id}: no last_verified")
            continue

        try:
            verified_date = datetime.strptime(str(lv), "%Y-%m-%d")
            if verified_date >= cutoff:
                fresh += 1
            else:
                stale.append(f"{entry.id}: verified {lv}")
        except ValueError:
            stale.append(f"{entry.id}: invalid date format")

    pct = int(fresh / len(entries) * 100) if entries else 0
    return pct, stale[:20]


def score_anti_pattern_coverage(entries: list[KBEntry]) -> tuple[int, list[str]]:
    """How many language categories have anti-pattern entries?"""
    languages = {e.language for e in entries if e.language not in ("multi", "yaml", "shell", "hcl")}
    anti_pattern_langs = set()

    for entry in entries:
        if "anti-pattern" in entry.id or "antipattern" in entry.id:
            anti_pattern_langs.add(entry.language)

    covered = languages & anti_pattern_langs
    missing = sorted(languages - anti_pattern_langs)
    pct = int(len(covered) / len(languages) * 100) if languages else 0
    return pct, missing


def score_retrieval_test_coverage(entries: list[KBEntry]) -> tuple[int, list[str]]:
    """What % of entries are referenced by retrieval test queries?"""
    # Find test_retrieval_comprehensive.py relative to the directory of this file
    this_dir = Path(__file__).resolve().parent
    test_file = this_dir.parent / "test_retrieval_comprehensive.py"
    if not test_file.exists():
        # backup: look in current working directory
        test_file = Path("test_retrieval_comprehensive.py")
        if not test_file.exists():
            return 0, ["test_retrieval_comprehensive.py not found"]

    try:
        content = test_file.read_text(encoding="utf-8")
    except Exception as e:
        return 0, [f"Failed to read test file: {e}"]

    expected_ids = set()
    for match in re.finditer(r'\["([^"]+)"', content):
        expected_ids.add(match.group(1))
    for match in re.finditer(r'\["([^"]+)",\s*"([^"]+)"', content):
        expected_ids.add(match.group(1))
        expected_ids.add(match.group(2))
    for match in re.finditer(r'\["([^"]+)",\s*"([^"]+)",\s*"([^"]+)"', content):
        expected_ids.add(match.group(1))
        expected_ids.add(match.group(2))
        expected_ids.add(match.group(3))

    all_ids = {e.id for e in entries}
    covered = all_ids & expected_ids
    uncovered = sorted(all_ids - expected_ids)

    pct = int(len(covered) / len(all_ids) * 100) if all_ids else 0
    return pct, uncovered[:30]


def get_scorecard_data(kb_path: Path | None = None) -> dict:
    """Run all scorecard scoring functions and return the dict of results."""
    entries = load_entries(kb_path)
    
    cov_score, cov_gaps = score_coverage(entries)
    depth_score, depth_details = score_depth(entries)
    xref_score, xref_broken = score_cross_references(entries)
    fresh_score, fresh_stale = score_freshness(entries)
    ap_score, ap_missing = score_anti_pattern_coverage(entries)
    rt_score, rt_uncovered = score_retrieval_test_coverage(entries)

    metrics = {
        "coverage": cov_score,
        "depth": depth_score,
        "cross_references": xref_score,
        "freshness": fresh_score,
        "anti_patterns": ap_score,
        "retrieval_coverage": rt_score,
    }
    
    overall = sum(metrics.values()) / len(metrics)

    return {
        "metrics": metrics,
        "overall": int(round(overall)),
        "coverage_gaps": cov_gaps,
        "depth_details": depth_details,
        "xref_broken": xref_broken,
        "fresh_stale": fresh_stale,
        "ap_missing": ap_missing,
        "rt_uncovered": rt_uncovered,
        "total_entries": len(entries),
    }


def print_dashboard(data: dict, verbose: bool = False):
    """Print the quality scorecard dashboard."""
    print("\n" + "=" * 60)
    print("KNOWLEDGE BASE QUALITY SCORECARD")
    print("=" * 60)

    order = [
        ("Coverage", "coverage"),
        ("Depth", "depth"),
        ("Cross-references", "cross_references"),
        ("Freshness", "freshness"),
        ("Anti-pattern coverage", "anti_patterns"),
        ("Retrieval test coverage", "retrieval_coverage"),
    ]

    # Use ASCII-safe characters for Windows compatibility
    print(f"+{'-'*30}+{'-'*8}+")
    print(f"|{'Metric':<30}|{'Score':>6}  |")
    print(f"+{'-'*30}+{'-'*8}+")
    for display_name, key in order:
        score = data["metrics"][key]
        print(f"| {display_name:<29}| {score:>4}/100|")
    print(f"+{'-'*30}+{'-'*8}+")
    print(f"| {'OVERALL':<29}| {data['overall']:>4}/100|")
    print(f"+{'-'*30}+{'-'*8}+")

    if verbose:
        print(f"\n{'─'*60}")
        print("COVERAGE GAPS:")
        for gap in data["coverage_gaps"][:15]:
            print(f"  - {gap}")

        print(f"\nDEPTH BY CATEGORY:")
        for cat, count in sorted(data["depth_details"].items(), key=lambda x: -x[1])[:15]:
            print(f"  {cat}: {count} entries")

        if data["xref_broken"]:
            print(f"\nBROKEN CROSS-REFERENCES ({len(data['xref_broken'])}):")
            for b in data["xref_broken"][:10]:
                print(f"  - {b}")

        if data["fresh_stale"]:
            print(f"\nSTALE ENTRIES ({len(data['fresh_stale'])}):")
            for s in data["fresh_stale"][:10]:
                print(f"  - {s}")

        if data["ap_missing"]:
            print(f"\nMISSING ANTI-PATTERNS:")
            for m in data["ap_missing"]:
                print(f"  - {m}")

        if data["rt_uncovered"]:
            print(f"\nUNCOVERED BY RETRIEVAL TESTS ({len(data['rt_uncovered'])}):")
            for u in data["rt_uncovered"][:15]:
                print(f"  - {u}")

    print(f"\n{'='*60}")
