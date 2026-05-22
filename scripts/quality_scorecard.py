#!/usr/bin/env python3
"""Quality Scorecard for the Knowledge Base.

Scores the entire knowledge base on multiple quality dimensions
and outputs a dashboard.

Usage:
    python scripts/quality_scorecard.py
    python scripts/quality_scorecard.py --verbose
"""

import argparse
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from retrieval import load_entries, parse_entry, KBEntry


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def score_coverage(entries: list[KBEntry]) -> tuple[int, list[str]]:
    """What % of common coding tasks have at least one entry?

    Checks against a predefined list of essential topics.
    """
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

    # Map entries to topic coverage
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
    # Score: 1 entry/cat=30, 3/cat=70, 5+/cat=100
    score = min(100, int(avg / 5 * 100))
    return score, dict(cats.most_common(20))


def score_cross_references(entries: list[KBEntry]) -> tuple[int, list[str]]:
    """What % of entries have valid Related links?"""
    valid = 0
    broken = []
    kb_root = Path(".")

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
            # Try from kb root
            if not (kb_root / link).exists():
                # Try relative to entry's directory
                entry_dir = entry.filepath.parent
                if not (entry_dir / link).exists():
                    entry_valid = False
                    broken.append(f"{entry.id}: broken link {link}")

        if entry_valid:
            valid += 1

    pct = int(valid / len(entries) * 100) if entries else 0
    return pct, broken[:20]  # Limit reported broken links


def score_freshness(entries: list[KBEntry]) -> tuple[int, list[str]]:
    """How many entries have last_verified within 6 months?"""
    fresh = 0
    stale = []
    cutoff = datetime.now() - timedelta(days=180)

    for entry in entries:
        content = entry.content
        # Extract last_verified from frontmatter
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
    missing = []

    for entry in entries:
        if "anti-pattern" in entry.id or "antipattern" in entry.id:
            anti_pattern_langs.add(entry.language)

    covered = languages & anti_pattern_langs
    missing = sorted(languages - anti_pattern_langs)
    pct = int(len(covered) / len(languages) * 100) if languages else 0
    return pct, missing


def score_retrieval_test_coverage(entries: list[KBEntry]) -> tuple[int, list[str]]:
    """What % of entries are referenced by retrieval test queries?"""
    # Load test cases from comprehensive test file
    test_file = Path(__file__).parent.parent / "test_retrieval_comprehensive.py"
    if not test_file.exists():
        return 0, ["test_retrieval_comprehensive.py not found"]

    content = test_file.read_text()
    # Extract expected IDs from test cases
    expected_ids = set()
    for match in re.finditer(r'\["([^"]+)"', content):
        expected_ids.add(match.group(1))
    # Also match lists like ["id1", "id2"]
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


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def print_dashboard(scores: dict, verbose: bool = False):
    """Print the quality scorecard dashboard."""
    print("\n" + "=" * 60)
    print("KNOWLEDGE BASE QUALITY SCORECARD")
    print("=" * 60)

    metrics = [
        ("Coverage", scores["coverage"]["score"]),
        ("Depth", scores["depth"]["score"]),
        ("Cross-references", scores["cross_references"]["score"]),
        ("Freshness", scores["freshness"]["score"]),
        ("Anti-pattern coverage", scores["anti_patterns"]["score"]),
        ("Retrieval test coverage", scores["retrieval_coverage"]["score"]),
    ]

    overall = sum(m[1] for m in metrics) / len(metrics)

    print(f"┌{'─'*30}┬{'─'*8}┐")
    print(f"│{'Metric':<30}│{'Score':>6}  │")
    print(f"├{'─'*30}┼{'─'*8}┤")
    for name, score in metrics:
        indicator = "█" * (score // 10) + "░" * (10 - score // 10)
        print(f"│ {name:<29}│ {score:>4}/100│")
    print(f"├{'─'*30}┼{'─'*8}┤")
    print(f"│ {'OVERALL':<29}│ {overall:>4.0f}/100│")
    print(f"└{'─'*30}┴{'─'*8}┘")

    if verbose:
        print(f"\n{'─'*60}")
        print("COVERAGE GAPS:")
        for gap in scores["coverage"]["gaps"][:15]:
            print(f"  - {gap}")

        print(f"\nDEPTH BY CATEGORY:")
        for cat, count in sorted(scores["depth"]["details"].items(), key=lambda x: -x[1])[:15]:
            print(f"  {cat}: {count} entries")

        if scores["cross_references"]["broken"]:
            print(f"\nBROKEN CROSS-REFERENCES ({len(scores['cross_references']['broken'])}):")
            for b in scores["cross_references"]["broken"][:10]:
                print(f"  - {b}")

        if scores["freshness"]["stale"]:
            print(f"\nSTALE ENTRIES ({len(scores['freshness']['stale'])}):")
            for s in scores["freshness"]["stale"][:10]:
                print(f"  - {s}")

        if scores["anti_patterns"]["missing"]:
            print(f"\nMISSING ANTI-PATTERNS:")
            for m in scores["anti_patterns"]["missing"]:
                print(f"  - {m}")

        if scores["retrieval_coverage"]["uncovered"]:
            print(f"\nUNCOVERED BY RETRIEVAL TESTS ({len(scores['retrieval_coverage']['uncovered'])}):")
            for u in scores["retrieval_coverage"]["uncovered"][:15]:
                print(f"  - {u}")

    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Knowledge Base Quality Scorecard")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show detailed breakdown")
    parser.add_argument("--kb-path", type=str, default=".",
                        help="Path to knowledge base root")

    args = parser.parse_args()
    kb_path = Path(args.kb_path)

    print("Loading entries...")
    entries = load_entries(kb_path)
    print(f"Loaded {len(entries)} entries")

    print("Scoring coverage...")
    cov_score, cov_gaps = score_coverage(entries)

    print("Scoring depth...")
    depth_score, depth_details = score_depth(entries)

    print("Scoring cross-references...")
    xref_score, xref_broken = score_cross_references(entries)

    print("Scoring freshness...")
    fresh_score, fresh_stale = score_freshness(entries)

    print("Scoring anti-pattern coverage...")
    ap_score, ap_missing = score_anti_pattern_coverage(entries)

    print("Scoring retrieval test coverage...")
    rt_score, rt_uncovered = score_retrieval_test_coverage(entries)

    scores = {
        "coverage": {"score": cov_score, "gaps": cov_gaps},
        "depth": {"score": depth_score, "details": depth_details},
        "cross_references": {"score": xref_score, "broken": xref_broken},
        "freshness": {"score": fresh_score, "stale": fresh_stale},
        "anti_patterns": {"score": ap_score, "missing": ap_missing},
        "retrieval_coverage": {"score": rt_score, "uncovered": rt_uncovered},
    }

    print_dashboard(scores, verbose=args.verbose)


if __name__ == "__main__":
    main()
