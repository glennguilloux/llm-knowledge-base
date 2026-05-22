#!/usr/bin/env python3
"""
Automated freshness check for knowledge base entries.

Strategies:
  1. VERSION CHECK: For entries that specify a library version, check
     PyPI/NPM/Maven for the latest version. Flag entries >2 major versions behind.
  2. PATTERN DEPRECATION: Search entries for known deprecated patterns
     across Python, Java, TypeScript, Go, Rust.
  3. LINK CHECK: Verify any URLs in entries still return 200.
  4. CONSISTENCY CHECK: Entries using the same library should reference
     compatible versions. No contradictory version claims.

Output:
  - Console report with color-coded status
  - JSON report: scripts/freshness_report.json
  - Exit code: 0 if all fresh, 1 if any entries need review

Usage:
  python scripts/auto_freshness.py
  python scripts/auto_freshness.py --fix-dates  # Update last_verified for clean entries
  python scripts/auto_freshness.py --json-only   # Only output JSON (for CI)
  python scripts/auto_freshness.py --report-dir ./reports  # Custom output dir
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Color helpers (ANSI)
# ---------------------------------------------------------------------------

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    DIM = "\033[2m"


def red(text: str) -> str: return f"{Colors.RED}{text}{Colors.RESET}"
def green(text: str) -> str: return f"{Colors.GREEN}{text}{Colors.RESET}"
def yellow(text: str) -> str: return f"{Colors.YELLOW}{text}{Colors.RESET}"
def cyan(text: str) -> str: return f"{Colors.CYAN}{text}{Colors.RESET}"
def bold(text: str) -> str: return f"{Colors.BOLD}{text}{Colors.RESET}"
def dim(text: str) -> str: return f"{Colors.DIM}{text}{Colors.RESET}"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Known deprecated patterns per language
DEPRECATED_PATTERNS: dict[str, list[dict]] = {
    "python": [
        {"pattern": r"import cgi\b", "reason": "cgi module deprecated in Python 3.11, removed in 3.13", "severity": "critical"},
        {"pattern": r"import urlparse\b", "reason": "urlparse removed; use urllib.parse instead", "severity": "critical"},
        {"pattern": r"urllib\.urlopen\(", "reason": "urllib.urlopen() is removed in Python 3; use urllib.request.urlopen()", "severity": "critical"},
        {"pattern": r"asyncio\.get_event_loop\(\)", "reason": "asyncio.get_event_loop() deprecated in 3.10; use asyncio.get_running_loop()", "severity": "warning"},
        {"pattern": r"from distutils", "reason": "distutils deprecated in 3.10, removed in 3.12", "severity": "critical"},
        {"pattern": r"import imp\b", "reason": "imp module deprecated in 3.4, removed in 3.12", "severity": "critical"},
        {"pattern": r"\.has_key\(", "reason": "dict.has_key() removed in Python 3; use 'in' operator", "severity": "critical"},
        {"pattern": r"except\s+\w+,\s+\w+:", "reason": "Old-style except syntax; use 'except X as e:'", "severity": "warning"},
        {"pattern": r"from collections import (?!.*(?:Counter|defaultdict|OrderedDict|deque|namedtuple|ChainMap)\b)\w+", "reason": "Check: many collections types moved to collections.abc in 3.3+", "severity": "info"},
    ],
    "java": [
        {"pattern": r"new Date\(\)", "reason": "java.util.Date is legacy; use java.time (Instant, LocalDate, ZonedDateTime)", "severity": "warning"},
        {"pattern": r"new Vector\b", "reason": "Vector is legacy; use ArrayList or Collections.synchronizedList()", "severity": "warning"},
        {"pattern": r"new Hashtable\b", "reason": "Hashtable is legacy; use HashMap or ConcurrentHashMap", "severity": "warning"},
        {"pattern": r"import javax\.xml\.bind\b", "reason": "javax.xml.bind removed in Java 11; use jakarta.xml.bind", "severity": "critical"},
        {"pattern": r"import javax\.activation\b", "reason": "javax.activation removed in Java 11; use jakarta.activation", "severity": "critical"},
        {"pattern": r"Thread\.stop\(\)", "reason": "Thread.stop() is deprecated and unsafe", "severity": "critical"},
        {"pattern": r"System\.runFinalizersOnExit\b", "reason": "System.runFinalizersOnExit is deprecated", "severity": "critical"},
        {"pattern": r"new Integer\((\d+)\)", "reason": "new Integer(n) is deprecated in Java 9; use Integer.valueOf(n)", "severity": "warning"},
    ],
    "typescript": [
        {"pattern": r"var \w+", "reason": "'var' is deprecated in favor of const/let", "severity": "info"},
        {"pattern": r"require\(['\"]", "reason": "require() is CommonJS; prefer ES module imports", "severity": "info"},
        {"pattern": r"from ['\"]moment['\"]", "reason": "Moment.js is legacy; consider date-fns or luxon", "severity": "warning"},
        {"pattern": r"new Promise\(.*resolve.*new Promise", "reason": "Nested Promise constructor antipattern (explicit promise construction)", "severity": "warning"},
    ],
    "go": [
        {"pattern": r"\"io/ioutil\"", "reason": "io/ioutil deprecated in Go 1.16; use io and os packages directly", "severity": "critical"},
        {"pattern": r"ioutil\.ReadAll\(", "reason": "ioutil.ReadAll deprecated; use io.ReadAll (Go 1.16+)", "severity": "critical"},
        {"pattern": r"ioutil\.ReadFile\(", "reason": "ioutil.ReadFile deprecated; use os.ReadFile (Go 1.16+)", "severity": "critical"},
        {"pattern": r"ioutil\.WriteFile\(", "reason": "ioutil.WriteFile deprecated; use os.WriteFile (Go 1.16+)", "severity": "critical"},
        {"pattern": r"ioutil\.ReadDir\(", "reason": "ioutil.ReadDir deprecated; use os.ReadDir (Go 1.16+)", "severity": "critical"},
        {"pattern": r"ioutil\.TempFile\(", "reason": "ioutil.TempFile deprecated; use os.CreateTemp (Go 1.16+)", "severity": "critical"},
        {"pattern": r"ioutil\.TempDir\(", "reason": "ioutil.TempDir deprecated; use os.MkdirTemp (Go 1.16+)", "severity": "critical"},
        {"pattern": r"ioutil\.NopCloser\(", "reason": "ioutil.NopCloser deprecated; use io.NopCloser (Go 1.16+)", "severity": "critical"},
        {"pattern": r"golang\.org/x/net/context", "reason": "Old context package; use 'context' stdlib (Go 1.7+)", "severity": "critical"},
    ],
    "rust": [
        {"pattern": r"try!\(", "reason": "try!() macro replaced by the ? operator (Rust 1.13+)", "severity": "critical"},
        {"pattern": r"extern crate (serde|serde_json|regex|rand|tokio)\b", "reason": "extern crate unnecessary in Rust 2018+; use 'use' directly", "severity": "info"},
        {"pattern": r"#!\[feature\(use_extern_macros\)\]", "reason": "use_extern_macros feature stabilized in Rust 1.30", "severity": "info"},
    ],
}

# Libraries whose latest versions we should check on PyPI
PYPI_PACKAGES_OF_INTEREST = [
    "fastapi", "flask", "django", "sqlalchemy", "pydantic",
    "httpx", "requests", "pytest", "celery", "pandas",
    "numpy", "alembic", "uvicorn", "starlette", "aiohttp",
    "redis", "psycopg2", "asyncpg", "boto3", "cryptography",
]

# Libraries whose latest versions we should check on npm
NPM_PACKAGES_OF_INTEREST = [
    "react", "next", "express", "typescript", "vue",
    "@angular/core", "prisma", "zod", "tailwindcss", "vitest",
    "playwright", "jest", "zustand", "@tanstack/react-query",
]

# Libraries whose latest versions we should check on Maven Central
MAVEN_PACKAGES_OF_INTEREST = [
    "org.springframework.boot:spring-boot-starter-web",
    "org.springframework.boot:spring-boot-starter-data-jpa",
    "org.junit.jupiter:junit-jupiter",
    "org.mockito:mockito-core",
    "com.google.guava:guava",
    "com.fasterxml.jackson.core:jackson-databind",
    "org.testcontainers:testcontainers",
    "org.hibernate.orm:hibernate-core",
]

# How many months before an entry is considered "stale"
STALE_MONTHS = 6

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def find_entry_files(kb_path: Path) -> list[Path]:
    """Find all knowledge base entry markdown files, excluding non-entries."""
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
    """Extract and parse YAML frontmatter from a markdown file."""
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


def get_entry_path_info(filepath: Path, kb_path: Path) -> dict:
    """Get entry ID and relative path."""
    meta = parse_frontmatter(filepath)
    return {
        "filepath": str(filepath.relative_to(kb_path) if kb_path != Path(".") else filepath),
        "id": meta.get("id", filepath.stem),
        "title": meta.get("title", ""),
        "language": meta.get("language", ""),
        "version": meta.get("version", ""),
        "last_verified": meta.get("last_verified", ""),
        "confidence": meta.get("confidence", "draft"),
        "content": filepath.read_text(encoding="utf-8"),
    }


# ---------------------------------------------------------------------------
# Strategy 1: Version Check
# ---------------------------------------------------------------------------

def _fetch_pypi_latest(package: str, timeout: int = 10) -> str | None:
    """Fetch latest version from PyPI JSON API."""
    try:
        ctx = ssl.create_default_context()
        url = f"https://pypi.org/pypi/{package}/json"
        req = urllib.request.Request(url, headers={"User-Agent": "llm-kb-freshness/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            return data.get("info", {}).get("version")
    except Exception:
        return None


def _fetch_npm_latest(package: str, timeout: int = 10) -> str | None:
    """Fetch latest version from npm registry."""
    try:
        ctx = ssl.create_default_context()
        # URL-encode scoped packages like @angular/core
        encoded = package.replace("/", "%2F")
        url = f"https://registry.npmjs.org/{encoded}/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "llm-kb-freshness/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            return data.get("version")
    except Exception:
        return None


def _fetch_maven_latest(group_id: str, artifact_id: str, timeout: int = 10) -> str | None:
    """Fetch latest version from Maven Central search API."""
    try:
        ctx = ssl.create_default_context()
        url = f"https://search.maven.org/solrsearch/select?q=g:{group_id}+AND+a:{artifact_id}&rows=1&wt=json"
        req = urllib.request.Request(url, headers={"User-Agent": "llm-kb-freshness/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            docs = data.get("response", {}).get("docs", [])
            if docs:
                return docs[0].get("latestVersion")
    except Exception:
        return None


def _version_behind(entry_version: str, latest: str) -> tuple[bool, int]:
    """Check if entry_version is more than 2 major versions behind latest."""
    try:
        ev_parts = [int(x) for x in re.findall(r"\d+", entry_version)]
        lv_parts = [int(x) for x in re.findall(r"\d+", latest)]
        if not ev_parts or not lv_parts:
            return False, 0
        diff = lv_parts[0] - ev_parts[0]
        return diff > 2, diff
    except Exception:
        return False, 0


def check_version_freshness(entries: list[dict]) -> list[dict]:
    """Check if entries referencing known libraries use up-to-date versions."""
    flags = []
    # Build version cache to avoid duplicate API calls
    version_cache: dict[str, str | None] = {}

    # Fetch latest versions
    for pkg in PYPI_PACKAGES_OF_INTEREST:
        version_cache[f"pypi:{pkg}"] = _fetch_pypi_latest(pkg)
    for pkg in NPM_PACKAGES_OF_INTEREST:
        version_cache[f"npm:{pkg}"] = _fetch_npm_latest(pkg)
    for pkg in MAVEN_PACKAGES_OF_INTEREST:
        parts = pkg.split(":")
        if len(parts) == 2:
            version_cache[f"maven:{pkg}"] = _fetch_maven_latest(parts[0], parts[1])

    # Check each entry for version references
    for entry in entries:
        content_lower = entry["content"].lower()
        entry_version = entry.get("version", "")

        for pkg in PYPI_PACKAGES_OF_INTEREST:
            if pkg in content_lower:
                latest = version_cache.get(f"pypi:{pkg}")
                if latest and entry_version:
                    behind, diff = _version_behind(entry_version, latest)
                    if behind:
                        flags.append({
                            "entry_id": entry["id"],
                            "type": "version_check",
                            "severity": "warning",
                            "reason": f"Entry references {pkg} version {entry_version}; latest is {latest} ({diff} major versions behind)",
                            "suggested_action": f"Update entry to cover {pkg} {latest}+ patterns",
                        })

        for pkg in NPM_PACKAGES_OF_INTEREST:
            if pkg.replace("@", "").replace("/", "") in content_lower.replace("@", "").replace("/", ""):
                latest = version_cache.get(f"npm:{pkg}")
                if latest and entry_version:
                    behind, diff = _version_behind(entry_version, latest)
                    if behind:
                        flags.append({
                            "entry_id": entry["id"],
                            "type": "version_check",
                            "severity": "warning",
                            "reason": f"Entry references {pkg} version {entry_version}; latest is {latest} ({diff} major versions behind)",
                            "suggested_action": f"Update entry to cover {pkg} {latest}+ patterns",
                        })

        for pkg in MAVEN_PACKAGES_OF_INTEREST:
            pkg_lower = pkg.split(":")[-1].lower()
            if pkg_lower in content_lower:
                latest = version_cache.get(f"maven:{pkg}")
                if latest and entry_version:
                    behind, diff = _version_behind(entry_version, latest)
                    if behind:
                        flags.append({
                            "entry_id": entry["id"],
                            "type": "version_check",
                            "severity": "warning",
                            "reason": f"Entry references {pkg} version {entry_version}; latest is {latest} ({diff} major versions behind)",
                            "suggested_action": f"Update entry to cover {pkg} {latest}+ patterns",
                        })

    return flags


# ---------------------------------------------------------------------------
# Strategy 2: Pattern Deprecation Detection
# ---------------------------------------------------------------------------

def check_deprecated_patterns(entries: list[dict]) -> list[dict]:
    """Search entries for known deprecated patterns."""
    flags = []

    for entry in entries:
        lang = entry.get("language", "").lower()
        if lang not in DEPRECATED_PATTERNS:
            continue

        for dep in DEPRECATED_PATTERNS[lang]:
            matches = list(re.finditer(dep["pattern"], entry["content"], re.MULTILINE))
            if matches:
                # Extract a snippet around the match
                for m in matches[:3]:  # Limit to 3 per pattern
                    start = max(0, m.start() - 20)
                    end = min(len(entry["content"]), m.end() + 40)
                    snippet = entry["content"][start:end].replace("\n", " ").strip()
                    flags.append({
                        "entry_id": entry["id"],
                        "type": "deprecation",
                        "severity": dep["severity"],
                        "reason": dep["reason"],
                        "snippet": f"...{snippet}...",
                        "suggested_action": f"Replace deprecated pattern: {dep['reason']}",
                    })

    return flags


# ---------------------------------------------------------------------------
# Strategy 3: Link Check
# ---------------------------------------------------------------------------

def check_links(entries: list[dict], timeout: int = 5) -> list[dict]:
    """Verify URLs in entries return 200. Skip local/relative links."""
    flags = []
    url_pattern = re.compile(r"https?://[^\s\)\]\"'`<>]+")

    # Deduplicate URLs
    seen_urls: dict[str, set[str]] = {}  # url -> set of entry_ids

    for entry in entries:
        for url in url_pattern.findall(entry["content"]):
            # Skip package registry URLs (they're checked separately)
            if any(skip in url for skip in (
                "pypi.org", "npmjs.com", "search.maven.org",
                "localhost", "127.0.0.1", "github.com/example",
            )):
                continue
            url = url.rstrip(".,;:'\"")
            if url not in seen_urls:
                seen_urls[url] = set()
            seen_urls[url].add(entry["id"])

    # Check each unique URL
    for url, entry_ids in seen_urls.items():
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "llm-kb-freshness/1.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                if resp.status >= 400:
                    flags.append({
                        "entry_id": ", ".join(sorted(entry_ids)),
                        "type": "link_check",
                        "severity": "warning",
                        "reason": f"URL returned HTTP {resp.status}: {url}",
                        "suggested_action": f"Update or remove broken link: {url}",
                    })
        except urllib.error.HTTPError as e:
            flags.append({
                "entry_id": ", ".join(sorted(entry_ids)),
                "type": "link_check",
                "severity": "warning",
                "reason": f"URL returned HTTP {e.code}: {url}",
                "suggested_action": f"Update or remove broken link: {url}",
            })
        except Exception:
            # Timeout or DNS failure — soft warning
            flags.append({
                "entry_id": ", ".join(sorted(entry_ids)),
                "type": "link_check",
                "severity": "info",
                "reason": f"URL unreachable (timeout/DNS): {url}",
                "suggested_action": f"Verify link manually: {url}",
            })

    return flags


# ---------------------------------------------------------------------------
# Strategy 4: Consistency Check
# ---------------------------------------------------------------------------

def check_consistency(entries: list[dict]) -> list[dict]:
    """Check for consistency issues across entries."""
    flags = []

    # Check 1: Entries referencing the same library should have compatible versions
    lib_versions: dict[str, dict[str, set[str]]] = {}  # lib -> {version -> {entry_ids}}

    for entry in entries:
        if not entry.get("version"):
            continue
        # Extract library references from content
        for lib in PYPI_PACKAGES_OF_INTEREST:
            if lib in entry["content"].lower():
                if lib not in lib_versions:
                    lib_versions[lib] = {}
                ver = entry["version"]
                if ver not in lib_versions[lib]:
                    lib_versions[lib][ver] = set()
                lib_versions[lib][ver].add(entry["id"])

    for lib, versions in lib_versions.items():
        if len(versions) > 1:
            # Multiple different version claims for the same lib
            ver_list = sorted(versions.keys())
            flags.append({
                "entry_id": ", ".join(
                    eid for v in versions for eid in versions[v]
                ),
                "type": "consistency",
                "severity": "info",
                "reason": f"Multiple version claims for {lib}: {', '.join(ver_list)}",
                "suggested_action": f"Standardize {lib} version across entries or add notes explaining differences",
            })

    # Check 2: Entry claiming version X but using patterns from version Y
    # (Simple heuristic: if entry says "3.8+" but uses union type syntax (|), it needs 3.10+)
    for entry in entries:
        version_str = entry.get("version", "")
        content = entry["content"]

        # Python: union type syntax `|` requires 3.10+
        if "3.8" in version_str or "3.9" in version_str:
            if re.search(r"\bstr\s*\|\s*None\b|\bint\s*\|\s*None\b|\bdict\s*\[.*\|\s*None", content):
                flags.append({
                    "entry_id": entry["id"],
                    "type": "consistency",
                    "severity": "warning",
                    "reason": f"Entry claims version {version_str} but uses union type syntax (|), which requires Python 3.10+",
                    "suggested_action": "Either update version to 3.10+ or use Optional[X] instead of X | None",
                })

        # Python: match/case requires 3.10+
        if ("3.8" in version_str or "3.9" in version_str) and re.search(r"\bmatch\s+\w+\s*:", content):
            flags.append({
                "entry_id": entry["id"],
                "type": "consistency",
                "severity": "warning",
                "reason": f"Entry claims version {version_str} but uses match/case, which requires Python 3.10+",
                "suggested_action": "Either update version to 3.10+ or remove match/case pattern",
            })

    return flags


# ---------------------------------------------------------------------------
# Staleness Check (date-based)
# ---------------------------------------------------------------------------

def check_staleness(entries: list[dict]) -> list[dict]:
    """Flag entries whose last_verified is older than STALE_MONTHS."""
    flags = []
    cutoff = datetime.now() - timedelta(days=STALE_MONTHS * 30)

    for entry in entries:
        lv = entry.get("last_verified", "")
        if not lv:
            flags.append({
                "entry_id": entry["id"],
                "type": "staleness",
                "severity": "warning",
                "reason": "No last_verified date",
                "suggested_action": "Add last_verified date to frontmatter",
            })
            continue

        try:
            verified_date = datetime.strptime(str(lv), "%Y-%m-%d")
            if verified_date < cutoff:
                months_ago = round((datetime.now() - verified_date).days / 30)
                flags.append({
                    "entry_id": entry["id"],
                    "type": "staleness",
                    "severity": "warning",
                    "reason": f"Last verified {lv} (~{months_ago} months ago)",
                    "suggested_action": "Review and update entry, then update last_verified date",
                })
        except (ValueError, TypeError):
            flags.append({
                "entry_id": entry["id"],
                "type": "staleness",
                "severity": "warning",
                "reason": f"Invalid last_verified format: {lv}",
                "suggested_action": "Fix last_verified date format (should be YYYY-MM-DD)",
            })

    return flags


# ---------------------------------------------------------------------------
# Fix Dates
# ---------------------------------------------------------------------------

def fix_dates(kb_path: Path, entries: list[dict], flagged_ids: set[str]) -> int:
    """Update last_verified dates for clean (non-flagged) entries."""
    today = datetime.now().strftime("%Y-%m-%d")
    updated = 0

    for entry in entries:
        if entry["id"] in flagged_ids:
            continue  # Skip flagged entries
        if entry.get("confidence") != "high":
            continue  # Only update high-confidence entries

        filepath = kb_path / entry["filepath"] if kb_path != Path(".") else Path(entry["filepath"])
        if not filepath.exists():
            continue

        content = filepath.read_text(encoding="utf-8")
        new_content = re.sub(
            r'^(last_verified:\s*")[^"]*(")',
            f'\\g<1>{today}\\2',
            content,
            count=1,
            flags=re.MULTILINE,
        )
        if new_content != content:
            filepath.write_text(new_content, encoding="utf-8")
            updated += 1

    return updated


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_console_report(
    entries: list[dict],
    all_flags: list[dict],
    elapsed: float,
    json_only: bool = False,
) -> str:
    """Generate a human-readable console report."""
    lines = []

    # Count by type
    by_type: dict[str, list[dict]] = {}
    for flag in all_flags:
        t = flag["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(flag)

    by_severity: dict[str, int] = {}
    for flag in all_flags:
        s = flag.get("severity", "info")
        by_severity[s] = by_severity.get(s, 0) + 1

    critical = by_severity.get("critical", 0)
    warnings = by_severity.get("warning", 0)
    infos = by_severity.get("info", 0)
    total_flags = len(all_flags)
    is_fresh = total_flags == 0

    if json_only:
        return ""  # No console output in JSON-only mode

    lines.append("")
    lines.append("=" * 70)
    lines.append(bold("  KNOWLEDGE BASE FRESHNESS REPORT"))
    lines.append("=" * 70)
    lines.append(f"  Date:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Entries:    {len(entries)}")
    lines.append(f"  Completed:  {elapsed:.1f}s")
    lines.append("-" * 70)

    if is_fresh:
        lines.append("")
        lines.append(green("  ✅ ALL CLEAN — No issues found!"))
        lines.append("")
    else:
        status_color = red if critical > 0 else yellow
        lines.append(f"  Status:     {status_color(f'{total_flags} issue(s) found')}")
        if critical:
            lines.append(f"  Critical:   {red(str(critical))}")
        if warnings:
            lines.append(f"  Warnings:   {yellow(str(warnings))}")
        if infos:
            lines.append(f"  Info:       {dim(str(infos))}")
        lines.append("-" * 70)

        # Detail breakdown
        for check_type in ("staleness", "deprecation", "version_check", "link_check", "consistency"):
            flags = by_type.get(check_type, [])
            if not flags:
                continue

            type_names = {
                "staleness": "STALE ENTRIES (date-based)",
                "deprecation": "DEPRECATED PATTERNS",
                "version_check": "VERSION CHECKS",
                "link_check": "BROKEN LINKS",
                "consistency": "CONSISTENCY ISSUES",
            }

            severity_emoji = {
                "critical": "🔴",
                "warning": "🟡",
                "info": "🔵",
            }

            lines.append("")
            lines.append(bold(f"  {type_names.get(check_type, check_type.upper())} ({len(flags)})"))
            lines.append("")

            for flag in flags:
                sev = flag.get("severity", "info")
                emoji = severity_emoji.get(sev, "⚪")
                color_fn = {"critical": red, "warning": yellow, "info": dim}.get(sev, str)
                lines.append(f"  {emoji} {color_fn(flag['entry_id'])}")
                lines.append(f"     {flag['reason']}")
                if flag.get("snippet"):
                    lines.append(f"     {dim(flag['snippet'])}")
                if flag.get("suggested_action"):
                    lines.append(f"     → {flag['suggested_action']}")

    lines.append("")
    lines.append("-" * 70)
    lines.append(f"  Breakdown: staleness={len(by_type.get('staleness', []))}, "
                 f"deprecation={len(by_type.get('deprecation', []))}, "
                 f"version={len(by_type.get('version_check', []))}, "
                 f"links={len(by_type.get('link_check', []))}, "
                 f"consistency={len(by_type.get('consistency', []))}")
    lines.append("=" * 70)

    if not is_fresh:
        lines.append("")
        lines.append(yellow("  ⚠️  Some entries need review — see report above."))
        lines.append("     Run with --fix-dates to update dates on clean entries.")
    lines.append("")

    return "\n".join(lines)


def generate_json_report(
    entries: list[dict],
    all_flags: list[dict],
    elapsed: float,
) -> dict:
    """Generate a structured JSON report."""
    by_type: dict[str, list[dict]] = {}
    for flag in all_flags:
        t = flag["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(flag)

    return {
        "timestamp": datetime.now().isoformat(),
        "entries_checked": len(entries),
        "total_issues": len(all_flags),
        "is_fresh": len(all_flags) == 0,
        "elapsed_seconds": round(elapsed, 1),
        "issues_by_type": {
            "staleness": len(by_type.get("staleness", [])),
            "deprecation": len(by_type.get("deprecation", [])),
            "version_check": len(by_type.get("version_check", [])),
            "link_check": len(by_type.get("link_check", [])),
            "consistency": len(by_type.get("consistency", [])),
        },
        "issues_by_severity": {
            "critical": sum(1 for f in all_flags if f.get("severity") == "critical"),
            "warning": sum(1 for f in all_flags if f.get("severity") == "warning"),
            "info": sum(1 for f in all_flags if f.get("severity") == "info"),
        },
        "flagged_entries": list(set(f["entry_id"] for f in all_flags)),
        "details": all_flags,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automated freshness check for knowledge base entries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/auto_freshness.py
  python scripts/auto_freshness.py --fix-dates
  python scripts/auto_freshness.py --json-only
  python scripts/auto_freshness.py --report-dir ./reports
  python scripts/auto_freshness.py --skip-link-check --skip-version-check
        """,
    )
    parser.add_argument("--fix-dates", action="store_true",
                        help="Update last_verified dates for clean (non-flagged) entries")
    parser.add_argument("--json-only", action="store_true",
                        help="Only output JSON (for CI consumption)")
    parser.add_argument("--report-dir", type=str, default="scripts",
                        help="Directory for JSON report output (default: scripts/)")
    parser.add_argument("--kb-path", type=str, default=".",
                        help="Path to knowledge base root")
    parser.add_argument("--skip-link-check", action="store_true",
                        help="Skip link checking (faster)")
    parser.add_argument("--skip-version-check", action="store_true",
                        help="Skip version checking (avoids network calls)")
    parser.add_argument("--skip-deprecation-check", action="store_true",
                        help="Skip deprecation pattern checking")
    parser.add_argument("--skip-consistency-check", action="store_true",
                        help="Skip consistency checking")
    parser.add_argument("--skip-staleness-check", action="store_true",
                        help="Skip staleness (date-based) check")
    parser.add_argument("--timeout", type=int, default=10,
                        help="Timeout in seconds for network requests (default: 10)")

    args = parser.parse_args()
    kb_path = Path(args.kb_path)

    if not kb_path.exists():
        print(f"Error: Knowledge base path '{kb_path}' does not exist", file=sys.stderr)
        return 2

    # Load entries
    entry_files = find_entry_files(kb_path)
    if not entry_files:
        print("Error: No knowledge base entries found", file=sys.stderr)
        return 2

    entries = [get_entry_path_info(f, kb_path) for f in entry_files]
    all_flags: list[dict] = []

    start_time = datetime.now()

    # Run selected checks
    if not args.skip_staleness_check:
        if not args.json_only:
            print(f"Checking staleness of {len(entries)} entries...")
        all_flags.extend(check_staleness(entries))

    if not args.skip_deprecation_check:
        if not args.json_only:
            print("Checking for deprecated patterns...")
        all_flags.extend(check_deprecated_patterns(entries))

    if not args.skip_version_check:
        if not args.json_only:
            print("Checking library versions (network calls)...")
        all_flags.extend(check_version_freshness(entries))

    if not args.skip_link_check:
        if not args.json_only:
            print("Checking links (network calls)...")
        all_flags.extend(check_links(entries, timeout=args.timeout))

    if not args.skip_consistency_check:
        if not args.json_only:
            print("Checking consistency...")
        all_flags.extend(check_consistency(entries))

    elapsed = (datetime.now() - start_time).total_seconds()

    # Fix dates if requested
    if args.fix_dates:
        if not args.json_only:
            print("Updating dates on clean entries...")
        flagged_ids = set(f["entry_id"] for f in all_flags)
        updated = fix_dates(kb_path, entries, flagged_ids)
        if not args.json_only:
            print(f"Updated dates for {updated} clean entries.")

    # Generate reports
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    json_report = generate_json_report(entries, all_flags, elapsed)
    json_path = report_dir / "freshness_report.json"
    json_path.write_text(json.dumps(json_report, indent=2, ensure_ascii=False), encoding="utf-8")

    if not args.json_only:
        print(generate_console_report(entries, all_flags, elapsed))
        print(f"JSON report saved to: {json_path}")

    # Exit code: 0 if all fresh, 1 if any issues
    return 0 if len(all_flags) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
