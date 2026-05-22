#!/usr/bin/env python3
"""
Detect gaps in knowledge base coverage.

Strategies:
  1. TREND ANALYSIS: Check trending topics on GitHub/PyPI/HN and flag uncovered ones.
  2. INTERNAL GAP ANALYSIS:
     - For each language, list categories with < 3 entries
     - Check for orphan entries (no Related links pointing to them)
     - Check if every language has anti-pattern coverage
     - Check if web framework entries have corresponding testing entries
  3. USER QUERY SIMULATION:
     - Generate realistic coding queries per language
     - Run retrieval for each
     - Flag queries where top result has confidence < 0.5 (no good match)

Output:
  - Gap report: scripts/gap_report.md
  - Priority-ranked list of missing entries
  - For each gap: suggested title, language, category, why it matters

Usage:
  python scripts/gap_detector.py
  python scripts/gap_detector.py --output my_gap_report.md
  python scripts/gap_detector.py --language python  # Focus on one language
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
import ssl
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Ideal minimum entries per language-category combination
MIN_ENTRIES_PER_CATEGORY = 3

# Known categories that every language should ideally cover
IDEAL_CATEGORIES = [
    "stdlib", "web", "db", "testing", "data", "patterns",
    "crypto", "devops", "concurrency", "security",
]

# Anti-patterns coverage: which languages SHOULD have anti-pattern entries
ANTI_PATTERN_TARGETS = [
    "python", "java", "typescript", "go", "rust", "csharp", "bash", "sql",
]

# Web framework → testing framework mapping
WEB_TESTING_PAIRS = {
    "python": {"web": ("pytest", "testing"), "fastapi": ("pytest", "testing")},
    "java": {"spring": ("junit", "testing"), "spring-boot": ("junit", "testing")},
    "typescript": {"react": ("vitest", "testing"), "next": ("playwright", "testing"), "express": ("jest", "testing")},
    "go": {"chi": ("testing", "testing"), "gin": ("testing", "testing")},
    "rust": {"axum": ("tokio::test", "testing"), "actix": ("actix-test", "testing")},
    "csharp": {"asp.net": ("xunit", "testing"), "minimal-api": ("xunit", "testing")},
}

# Simulated user queries per language (realistic coding questions)
SIMULATED_QUERIES: dict[str, list[str]] = {
    "python": [
        "How to read and write CSV files efficiently",
        "FastAPI dependency injection with database sessions",
        "Asyncio background tasks with proper error handling",
        "Pydantic model validation with custom validators",
        "SQLAlchemy 2.0 async session with PostgreSQL",
        "How to implement rate limiting in Flask",
        "Python multiprocessing pool with shared state",
        "Decorator for retrying failed API calls with backoff",
        "Context manager for timing code blocks",
        "How to use Python's struct module for binary data",
        "WebSocket server with asyncio",
        "How to profile Python code with cProfile",
        "Type guard narrowing with isinstance",
        "Using functools.lru_cache for expensive computations",
        "How to mock external APIs in pytest",
        "Dataclass with field validation",
        "How to use Pathlib for cross-platform file operations",
        "Python packaging with pyproject.toml",
        "How to handle circular imports",
        "Using Protocol classes for structural subtyping",
    ],
    "java": [
        "Spring Boot JPA repository with custom queries",
        "How to use Java CompletableFuture for async operations",
        "JUnit 5 parameterized tests with method source",
        "Mockito mock static methods in tests",
        "Java Stream grouping by with downstream collectors",
        "How to implement a thread-safe singleton",
        "Java records vs Lombok for DTOs",
        "How to handle exceptions in functional interfaces",
        "Using Optional to avoid null checks",
        "Spring Boot custom annotation for validation",
        "How to use Testcontainers for integration tests",
        "Java HttpClient with connection pooling",
        "How to serialize records to JSON with Jackson",
        "Using Sealed classes for pattern matching",
        "Spring Boot graceful shutdown configuration",
        "How to implement a Builder pattern with validation",
        "Java time API for date arithmetic",
        "How to use virtual threads in Java 21",
        "Spring Security OAuth2 resource server",
        "How to batch insert with JPA",
    ],
    "typescript": [
        "React useEffect cleanup with AbortController",
        "Next.js server actions with form validation using Zod",
        "TypeScript discriminated unions for API responses",
        "Express middleware for request logging",
        "Prisma with PostgreSQL and row-level security",
        "Zustand state management with persist middleware",
        "TanStack React Query with optimistic updates",
        "How to type a generic fetch wrapper",
        "Playwright end-to-end test with page objects",
        "Next.js middleware for route protection",
        "TypeScript module augmentation for third-party libs",
        "How to use the satisfies operator",
        "Custom React hook for debounced search",
        "TypeScript template literal types",
        "How to handle WebSocket reconnection",
        "Zod schema with refinement and transform",
        "React context with useReducer pattern",
        "How to use TypeScript const assertions",
        "SWR vs React Query for data fetching",
        "How to structure a monorepo with Turborepo",
    ],
    "go": [
        "Go HTTP server with middleware chaining",
        "How to use Go generics for type-safe collections",
        "Go context propagation in microservices",
        "GORM vs sqlx for database access",
        "How to implement graceful shutdown in Go",
        "Go testing with table-driven tests and subtests",
        "How to use errgroup for concurrent error handling",
        "Go channels: buffered vs unbuffered patterns",
        "How to implement a rate limiter in Go",
        "Go embed directive for static files",
        "How to profile Go applications with pprof",
        "Go struct tags for JSON and validation",
        "How to use sync.Pool for object reuse",
        "Go gRPC server with interceptors",
        "How to handle panics in goroutines",
        "Go functional options pattern",
        "How to use Go's net/http/httptest",
        "Go workspace mode for multi-module projects",
        "How to implement circuit breaker in Go",
        "Go slog structured logging best practices",
    ],
    "rust": [
        "Rust error handling with thiserror and anyhow",
        "How to use Rust async/await with tokio",
        "Axum middleware for authentication",
        "Rust builder pattern with typestate",
        "How to serialize with serde custom formats",
        "Rust enum with associated data matching",
        "How to use Rust's borrow checker effectively",
        "Rust Rayon for parallel iterators",
        "How to implement the Display trait",
        "Rust SQLx with compile-time checked queries",
        "How to use miette for error reporting",
        "Rust tower middleware stack",
        "How to handle async closures",
        "Rust cfg conditional compilation",
        "How to use tracing for structured logging",
        "Rust once_cell vs LazyLock",
        "How to implement Iterator trait for custom types",
        "Rust type state pattern for state machines",
        "How to use include_str! and include_bytes!",
        "Rust cargo workspace organization",
    ],
    "csharp": [
        "ASP.NET Core minimal API with dependency injection",
        "C# LINQ with grouping and aggregation",
        "Entity Framework Core migrations in production",
        "C# async/await with CancellationToken",
        "How to use C# records for immutable DTOs",
        "xUnit integration tests with WebApplicationFactory",
        "C# pattern matching with switch expressions",
        "How to implement MediatR pipeline behaviors",
        "C# IOptions pattern for configuration",
        "Background services with IHostedService",
        "How to use FluentValidation with ASP.NET",
        "C# source generators for code generation",
        "How to implement the Result pattern",
        "C# Polly for retry and circuit breaker",
        "How to use Channels for producer-consumer",
        "C# primary constructors in classes",
        "How to use Serilog for structured logging",
        "C# nullable reference types migration",
        "How to implement rate limiting middleware",
        "C# System.Text.Json custom converters",
    ],
    "bash": [
        "How to write a robust Bash script with error handling",
        "Bash associative arrays for configuration",
        "How to use trap for signal handling",
        "Bash parallel execution with xargs",
        "How to create a progress bar in Bash",
        "Bash here documents for templating",
        "How to handle JSON in Bash with jq",
        "Bash getopts for command-line parsing",
        "How to lock a file with flock",
        "Bash process substitution patterns",
    ],
    "sql": [
        "PostgreSQL window functions for ranking",
        "How to optimize slow queries with EXPLAIN",
        "SQL recursive CTE for tree traversal",
        "PostgreSQL full-text search with tsvector",
        "How to use JSON functions in PostgreSQL",
        "SQL indexing strategies for read-heavy workloads",
        "How to handle database migrations safely",
        "PostgreSQL row-level security policies",
        "SQL MATERIALIZED VIEW vs regular VIEW",
        "How to use transactions with savepoints",
    ],
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def find_entry_files(kb_path: Path) -> list[Path]:
    """Find all knowledge base entry markdown files."""
    skip_files = {"README.md", "schema.md", "CONTRIBUTING.md", "LLM_CODEBASE_KNOWLEDGE_BASE.md"}
    files = []
    for md_file in sorted(kb_path.rglob("*.md")):
        if md_file.name in skip_files:
            continue
        if md_file.parent.name in ("templates", ".github"):
            continue
        if any(part.startswith(".") for part in md_file.parts):
            continue
        files.append(md_file)
    return files


def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter."""
    content = filepath.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    try:
        import yaml
        meta = yaml.safe_load(match.group(1))
        return meta if isinstance(meta, dict) else {}
    except Exception:
        return {}


def load_entries_data(kb_path: Path) -> list[dict]:
    """Load all entries with metadata."""
    entries = []
    for fp in find_entry_files(kb_path):
        meta = parse_frontmatter(fp)
        content = fp.read_text(encoding="utf-8")
        entries.append({
            "filepath": str(fp.relative_to(kb_path)),
            "id": meta.get("id", fp.stem),
            "title": meta.get("title", ""),
            "language": meta.get("language", ""),
            "category": meta.get("category", ""),
            "tags": meta.get("tags", []),
            "confidence": meta.get("confidence", "draft"),
            "content": content,
            # Extract related links
            "related": re.findall(
                r"## Related\s*\n(.*?)(?=\n## |\Z)",
                content, re.DOTALL
            ),
        })
    return entries


# ---------------------------------------------------------------------------
# Strategy 1: Trend Analysis
# ---------------------------------------------------------------------------

def check_trending_topics(entries: list[dict], timeout: int = 10) -> list[dict]:
    """Query GitHub trending and check for uncovered topics."""
    gaps = []

    # Try GitHub trending (no API key needed for basic access)
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            "https://api.github.com/search/repositories?q=stars:>1000+pushed:>2024-01-01&sort=stars&per_page=10",
            headers={"User-Agent": "llm-kb-gap/1.0", "Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            trending_topics = set()
            for repo in data.get("items", []):
                desc = (repo.get("description") or "").lower()
                name = repo.get("name", "").lower()
                language = (repo.get("language") or "").lower()
                for topic in repo.get("topics", []):
                    trending_topics.add(topic.lower())
                trending_topics.add(name)
                # Extract keywords from description
                for word in re.findall(r"\w+", desc):
                    if len(word) > 4:
                        trending_topics.add(word.lower())

            # Check which trending topics we cover
            all_entry_text = " ".join(
                f"{e['title']} {' '.join(e.get('tags', []))} {e.get('content', '')[:500]}"
                for e in entries
            ).lower()

            uncovered = []
            for topic in sorted(trending_topics):
                if topic not in all_entry_text and len(topic) > 4:
                    uncovered.append(topic)

            for topic in uncovered[:10]:
                gaps.append({
                    "topic": topic,
                    "language": "multi",
                    "category": "patterns",
                    "priority": "medium",
                    "source": "github_trending",
                    "suggested_title": f"{topic.title()} Patterns and Best Practices",
                    "why_it_matters": f"Trending on GitHub but no knowledge base coverage",
                })

    except Exception as e:
        print(f"  (GitHub trending check skipped: {e})", file=sys.stderr)

    return gaps


# ---------------------------------------------------------------------------
# Strategy 2: Internal Gap Analysis
# ---------------------------------------------------------------------------

def check_stackoverflow(entries: list[dict], target_language: str | None = None, timeout: int = 10) -> list[dict]:
    """Check Stack Overflow top questions for uncovered topics.

    Uses the public Stack Exchange API (no key required for moderate use).
    Language tags are mapped to Stack Overflow tags.
    """
    gaps = []

    # Map our language names to SO tags
    SO_TAGS = {
        "python": "python",
        "java": "java",
        "typescript": "typescript",
        "go": "go",
        "rust": "rust",
        "csharp": "c%23",  # c#
        "bash": "bash",
        "sql": "sql",
    }

    languages_to_check = [target_language] if target_language else list(SO_TAGS.keys())

    all_entry_text = " ".join(
        f"{e['title']} {' '.join(e.get('tags', []))}"
        for e in entries
    ).lower()

    for lang in languages_to_check:
        if lang not in SO_TAGS:
            continue

        so_tag = SO_TAGS[lang]
        try:
            ctx = ssl.create_default_context()
            url = (
                f"https://api.stackexchange.com/2.3/questions"
                f"?order=desc&sort=votes&tagged={so_tag}"
                f"&site=stackoverflow&pagesize=25&filter=withbody"
            )
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "llm-kb-gap/1.0"},
            )
            # Stack Exchange API requires gzip encoding
            req.add_header("Accept-Encoding", "gzip")
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                import gzip
                raw = resp.read()
                data = json.loads(gzip.decompress(raw).decode())

            questions = data.get("items", [])
            flagged = 0

            for q in questions[:25]:
                title_lower = q.get("title", "").lower()
                tags = [t.lower() for t in q.get("tags", [])]

                # Check if any entry covers this topic
                # Simple keyword overlap check
                title_words = set(re.findall(r"\w+", title_lower))
                title_words.discard(lang.lower())
                # Remove common stop words
                stop_words = {"how", "to", "in", "a", "the", "is", "it", "of", "and", "or", "for", "with", "using", "do", "i", "can", "does", "what", "why", "when"}
                significant_words = {w for w in title_words if len(w) > 3 and w not in stop_words}

                if not significant_words:
                    continue

                # Check if at least 2 significant words appear in our entries
                match_count = sum(1 for w in significant_words if w in all_entry_text)

                if match_count < 2:
                    flagged += 1
                    gaps.append({
                        "language": lang,
                        "query": q.get("title", ""),
                        "priority": "medium" if flagged <= 10 else "low",
                        "source": "stackoverflow",
                        "suggested_title": f"[{lang.title()}] {q.get('title', '')[:80]}",
                        "why_it_matters": f"Top-voted SO question with no matching KB entry (score: {q.get('score', 0)}, views: {q.get('view_count', 0)})",
                    })

                if flagged >= 15:
                    break  # Don't over-report per language

        except Exception as e:
            print(f"  (Stack Overflow check for {lang} skipped: {e})", file=sys.stderr)

    return gaps


def analyze_internal_gaps(entries: list[dict], target_language: str | None = None) -> list[dict]:
    """Find internal coverage gaps.

    Checks:
      1. Categories with < MIN_ENTRIES_PER_CATEGORY entries per language
      2. Anti-pattern coverage per language
      3. Web framework → testing entry pairing
      4. Orphan entries with no incoming Related links
    """
    gaps: list[dict] = []

    # Build lookup structures
    lang_cat_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    lang_entries: dict[str, list[dict]] = defaultdict(list)
    entry_ids = {e["id"] for e in entries}
    referenced: set[str] = set()

    for entry in entries:
        lang = entry["language"]
        cat = entry["category"]
        lang_cat_counts[lang][cat] += 1
        lang_entries[lang].append(entry)

    languages = set(lang_entries.keys())
    if target_language:
        languages = {target_language} & languages

    # Check 1: Categories with < MIN_ENTRIES_PER_CATEGORY entries
    for lang in sorted(languages):
        if lang in ("multi", "yaml", "docker", "javascript", "shell"):
            continue

        for cat in IDEAL_CATEGORIES:
            count = lang_cat_counts[lang].get(cat, 0)
            if count < MIN_ENTRIES_PER_CATEGORY:
                gaps.append({
                    "language": lang,
                    "category": cat,
                    "current_count": count,
                    "target_count": MIN_ENTRIES_PER_CATEGORY,
                    "priority": "high" if count == 0 else "medium",
                    "source": "thin_category",
                    "suggested_title": f"[{lang.title()}] Additional {cat.title()} patterns (currently {count})",
                    "why_it_matters": f"Only {count} entries in {lang}/{cat}. Minimum recommended: {MIN_ENTRIES_PER_CATEGORY}.",
                })

    # Check 2: Anti-pattern coverage per language
    for lang in ANTI_PATTERN_TARGETS:
        if target_language and lang != target_language:
            continue
        has_anti = any(
            "anti-pattern" in e["id"].lower() or "antipattern" in e["id"].lower()
            for e in lang_entries[lang]
        )
        if not has_anti:
            gaps.append({
                "language": lang,
                "category": "anti-patterns",
                "priority": "high",
                "source": "missing_anti_patterns",
                "suggested_title": f"Common {lang.title()} Anti-Patterns and How to Avoid Them",
                "why_it_matters": f"No anti-pattern entry for {lang.title()}. Every major language needs anti-pattern coverage.",
            })

    # Check 3: Web → testing pairing
    for lang, framework_pairs in WEB_TESTING_PAIRS.items():
        if target_language and lang != target_language:
            continue
        lang_content = " ".join(e["content"].lower() for e in lang_entries[lang])
        for fw, (test_fw, test_cat) in framework_pairs.items():
            has_fw = fw in lang_content or fw.replace("-", "") in lang_content
            has_test = test_fw in lang_content
            if has_fw and not has_test:
                gaps.append({
                    "language": lang,
                    "category": test_cat,
                    "priority": "medium",
                    "source": "web_testing_pair",
                    "suggested_title": f"Testing {fw.title()} applications with {test_fw}",
                    "why_it_matters": f"{fw.title()} is referenced but no corresponding testing entry found.",
                })

    # Check 4: Orphan detection (entries with no incoming Related links)
    for entry in entries:
        content = entry["content"]
        # Find Related section links
        related_section = re.search(
            r"## Related\s*\n(.*?)(?=\n## |\Z)",
            content, re.DOTALL
        )
        if related_section:
            links = re.findall(r"-\s+(.+\.md)", related_section.group(1))
            for link in links:
                # Try to match the link to an entry ID
                link_stem = Path(link).stem
                for eid in entry_ids:
                    if eid.endswith(link_stem):
                        referenced.add(eid)

    orphans = []
    for entry in entries:
        if entry["id"] not in referenced:
            # Check if it's the only entry in its category for that language
            lang = entry["language"]
            cat = entry["category"]
            cat_count = lang_cat_counts[lang].get(cat, 0)
            if cat_count <= 2:  # Only flag if category is thin
                orphans.append(entry["id"])

    if orphans:
        gaps.append({
            "language": "multi",
            "category": "cross-refs",
            "priority": "low",
            "source": "orphan_entries",
            "suggested_title": f"Add cross-references to orphan entries: {', '.join(orphans[:5])}",
            "why_it_matters": f"{len(orphans)} entries have no incoming Related links. Consider adding cross-references.",
        })

    return gaps


# ---------------------------------------------------------------------------
# Strategy 3: User Query Simulation
# ---------------------------------------------------------------------------

def simulate_queries(
    entries: list[dict],
    kb_path: Path,
    target_language: str | None = None,
) -> list[dict]:
    """Simulate retrieval for realistic queries and flag poor results."""
    gaps = []

    # Add KB path to sys.path for retrieval
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        from llm_kb.retrieve import search, load_entries
        kb_entries = load_entries(kb_path)
    except ImportError:
        # Fallback: manual keyword search
        return _simulate_queries_local(entries, target_language)

    languages_to_check = [target_language] if target_language else list(SIMULATED_QUERIES.keys())

    for lang in languages_to_check:
        if lang not in SIMULATED_QUERIES:
            continue
        queries = SIMULATED_QUERIES[lang]

        for query in queries:
            try:
                results = search(query, language=lang, top_k=1, kb_path=kb_path)
                if not results:
                    gaps.append({
                        "language": lang,
                        "query": query,
                        "priority": "high",
                        "source": "query_simulation",
                        "suggested_title": f"[{lang.title()}] Entry covering: {query[:60]}...",
                        "why_it_matters": f"No results returned for query: '{query[:80]}...'",
                    })
                else:
                    top = results[0]
                    if top.confidence == "draft" or (hasattr(top, "confidence") and top.confidence not in ("high", "medium")):
                        gaps.append({
                            "language": lang,
                            "query": query,
                            "priority": "medium",
                            "source": "query_simulation",
                            "suggested_title": f"[{lang.title()}] Improve entry for: {query[:60]}...",
                            "why_it_matters": f"Top result is draft/low confidence for: '{query[:80]}...'",
                        })
            except Exception:
                pass  # Skip failed queries

    return gaps


def _simulate_queries_local(entries: list[dict], target_language: str | None = None) -> list[dict]:
    """Local query simulation without the retrieval module (fallback)."""
    gaps = []
    languages_to_check = [target_language] if target_language else list(SIMULATED_QUERIES.keys())

    for lang in languages_to_check:
        if lang not in SIMULATED_QUERIES:
            continue
        lang_entries = [e for e in entries if e["language"] == lang]
        queries = SIMULATED_QUERIES[lang]

        for query in queries:
            query_words = set(re.findall(r"\w+", query.lower()))
            # Score each entry
            best_score = 0
            best_entry = None

            for entry in lang_entries:
                score = 0
                text = (entry["title"] + " " + " ".join(entry.get("tags", []))).lower()
                for word in query_words:
                    if len(word) > 3 and word in text:
                        score += 2
                if entry.get("confidence") == "high":
                    score += 1
                if score > best_score:
                    best_score = score
                    best_entry = entry

            if best_score == 0 or best_entry is None:
                gaps.append({
                    "language": lang,
                    "query": query,
                    "priority": "high",
                    "source": "query_simulation",
                    "suggested_title": f"[{lang.title()}] Entry covering: {query[:60]}...",
                    "why_it_matters": f"No matching entry for common query: '{query[:80]}...'",
                })

    return gaps


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_markdown_report(
    all_gaps: list[dict],
    entries: list[dict],
    elapsed: float,
) -> str:
    """Generate a markdown gap report."""
    lines = []
    lines.append("# Knowledge Base Gap Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Entries Analyzed:** {len(entries)}  ")
    lines.append(f"**Gaps Found:** {len(all_gaps)}  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary
    by_priority = defaultdict(int)
    by_source = defaultdict(int)
    by_language = defaultdict(int)

    for gap in all_gaps:
        by_priority[gap.get("priority", "low")] += 1
        by_source[gap.get("source", "unknown")] += 1
        by_language[gap.get("language", "multi")] += 1

    lines.append("## Summary")
    lines.append("")
    lines.append("| Priority | Count |")
    lines.append("|----------|-------|")
    for p in ("high", "medium", "low"):
        lines.append(f"| {p} | {by_priority.get(p, 0)} |")
    lines.append("")
    lines.append("| Source | Count |")
    lines.append("|--------|-------|")
    for s, c in sorted(by_source.items()):
        lines.append(f"| {s} | {c} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Priority-ranked gaps
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_gaps = sorted(all_gaps, key=lambda g: priority_order.get(g.get("priority", "low"), 99))

    lines.append("## Priority-Ranked Gaps")
    lines.append("")

    for i, gap in enumerate(sorted_gaps, 1):
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(gap.get("priority", "low"), "⚪")
        lines.append(f"### {i}. {priority_emoji} [{gap.get('priority', 'N/A').upper()}] {gap.get('suggested_title', 'Untitled')}")
        lines.append("")
        lines.append(f"- **Language:** {gap.get('language', 'N/A')}")
        lines.append(f"- **Category:** {gap.get('category', 'N/A')}")
        lines.append(f"- **Source:** {gap.get('source', 'unknown')}")
        if gap.get("current_count") is not None:
            lines.append(f"- **Current entries:** {gap['current_count']}/{gap.get('target_count', '?')}")
        if gap.get("query"):
            lines.append(f"- **Example query:** \"{gap['query'][:120]}\"")
        lines.append(f"- **Why it matters:** {gap.get('why_it_matters', 'N/A')}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Report generated in {elapsed:.1f}s by `scripts/gap_detector.py`*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect gaps in knowledge base coverage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--output", type=str, default="scripts/gap_report.md",
                        help="Output report file path (default: scripts/gap_report.md)")
    parser.add_argument("--kb-path", type=str, default=".",
                        help="Path to knowledge base root")
    parser.add_argument("--language", type=str, default=None,
                        help="Focus on a specific language (python, java, etc.)")
    parser.add_argument("--skip-trends", action="store_true",
                        help="Skip trend analysis (network calls)")
    parser.add_argument("--skip-simulation", action="store_true",
                        help="Skip query simulation")

    args = parser.parse_args()
    kb_path = Path(args.kb_path)

    if not kb_path.exists():
        print(f"Error: Path '{kb_path}' does not exist", file=sys.stderr)
        return 1

    start_time = datetime.now()

    print("Loading entries...")
    entries = load_entries_data(kb_path)
    print(f"Loaded {len(entries)} entries")

    all_gaps: list[dict] = []

    # Strategy 1: Trend analysis
    if not args.skip_trends:
        print("Checking trending topics...")
        all_gaps.extend(check_trending_topics(entries))

    # Strategy 1b: Stack Overflow analysis
    if not args.skip_trends:
        print("Checking Stack Overflow top questions...")
        all_gaps.extend(check_stackoverflow(entries, target_language=args.language))

    # Strategy 2: Internal gap analysis
    print("Analyzing internal coverage gaps...")
    all_gaps.extend(analyze_internal_gaps(entries, target_language=args.language))

    # Strategy 3: Query simulation
    if not args.skip_simulation:
        print("Simulating user queries...")
        all_gaps.extend(simulate_queries(entries, kb_path, target_language=args.language))

    elapsed = (datetime.now() - start_time).total_seconds()

    # Generate report
    report = generate_markdown_report(all_gaps, entries, elapsed)
    output_path = Path(args.output)
    output_path.write_text(report, encoding="utf-8")
    print(f"\nGap report saved to: {output_path}")
    print(f"Found {len(all_gaps)} gaps in {elapsed:.1f}s")

    # Quick console summary
    high = sum(1 for g in all_gaps if g.get("priority") == "high")
    medium = sum(1 for g in all_gaps if g.get("priority") == "medium")
    low = sum(1 for g in all_gaps if g.get("priority") == "low")

    if high:
        print(f"  🔴 {high} high-priority gaps")
    if medium:
        print(f"  🟡 {medium} medium-priority gaps")
    if low:
        print(f"  🔵 {low} low-priority gaps")

    return 0


if __name__ == "__main__":
    sys.exit(main())
