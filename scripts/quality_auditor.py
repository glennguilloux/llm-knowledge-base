#!/usr/bin/env python3
"""
Deep quality audit of ALL knowledge base entries.
Goes beyond validate_kb.py (which checks schema) to check CONTENT quality.

Checks:
1. WRONG/CORRECT pairs: Must have >= 3 pairs. Count them.
2. Gotchas: Must have >= 3 bullet points. Count them.
3. Related links: Must have >= 2 links. Verify each link points to an existing file.
4. Code examples: Must have at least 1 fenced code block in Standard Pattern.
5. Code imports: Python entries should include imports in code blocks.
6. Entry length: Flag entries shorter than 30 lines (likely too thin) or
   longer than 500 lines (won't fit in small model context).
7. Confidence audit: Entries with confidence: "high" that have < 3 gotchas or
   < 3 mistakes should be downgraded to "medium".
8. Content freshness: Check for deprecated patterns:
   - Python: import cgi, urllib.urlopen, async async, print without parens
   - Java: new Date(), javax.xml.bind, Vector
   - TypeScript: require(), var declarations, moment.
   - Go: io/ioutil (deprecated 1.16+)
   - Rust: try! macro (replaced by ?)
   - PHP: mysql_ functions, ?> closing tags
   - Kotlin: javaClass<> (use ::class.java)
9. Duplicate detection: Find entries with near-identical Standard Pattern code.
10. Cross-reference integrity: Every Related link must resolve. Every entry
    should BE referenced by at least one other entry (orphans are gaps).

Output:
- Console report with color-coded issues (RED=critical, YELLOW=warning)
- JSON report: scripts/quality_audit.json
- Markdown report: scripts/quality_audit.md with fix recommendations
- Exit code: 0 if all pass, 1 if critical issues found

Usage:
  python scripts/quality_auditor.py
  python scripts/quality_auditor.py --fix-confidence  # Auto-downgrade overstated confidence
  python scripts/quality_auditor.py --entry python/stdlib/hashlib-sha256.md  # Audit single entry
"""

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# ANSI Colors
# ---------------------------------------------------------------------------

class C:
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Entry discovery (mirrors validate_kb.py logic)
# ---------------------------------------------------------------------------

SKIP_FILES = {
    "README.md", "schema.md", "CONTRIBUTING.md", "RELEASE_CHECKLIST.md",
    "LLM_CODEBASE_KNOWLEDGE_BASE.md", "CHANGELOG.md", "LICENSE",
}
SKIP_PARENTS = {"templates", ".github", "docs", "architecture", "scripts", "benchmark_prompts", "prompts", "build", "__pycache__", "node_modules"}


def discover_entries(kb_root: Path) -> list[Path]:
    """Find all knowledge base entry .md files."""
    files = []
    for md_file in sorted(kb_root.rglob("*.md")):
        if any(part.startswith(".") for part in md_file.parts):
            continue
        if md_file.name in SKIP_FILES:
            continue
        if any(p.name in SKIP_PARENTS for p in md_file.parents):
            continue
        files.append(md_file)
    return files


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from entry content."""
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    try:
        import yaml
        return yaml.safe_load(match.group(1))
    except Exception:
        return None


def get_body(content: str) -> str:
    """Return content after frontmatter."""
    match = re.match(r"^---\n.*?\n---\n?", content, re.DOTALL)
    if match:
        return content[match.end():]
    return content


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

def extract_section(content: str, heading: str) -> str:
    """Extract the text of a section by heading name.

    Skips headings that appear inside fenced code blocks.
    """
    lines = content.split("\n")
    in_section = False
    in_code_block = False
    result_lines = []

    for line in lines:
        # Track code block state
        if re.match(r"^```\w*\s*$", line):
            in_code_block = not in_code_block

        if in_section:
            # Stop at next real heading (not inside code block)
            if not in_code_block and re.match(r"^##\s+\S", line):
                break
            result_lines.append(line)
        elif not in_code_block and line.strip() == heading:
            in_section = True

    return "\n".join(result_lines)


def extract_standard_pattern(content: str) -> str:
    """Extract the Standard Pattern section text."""
    return extract_section(content, "## Standard Pattern")


def extract_common_mistakes(content: str) -> str:
    """Extract the Common Mistakes section text."""
    return extract_section(content, "## Common Mistakes")


def extract_gotchas(content: str) -> str:
    """Extract the Gotchas section text."""
    return extract_section(content, "## Gotchas")


def extract_related(content: str) -> str:
    """Extract the Related section text."""
    return extract_section(content, "## Related")


# ---------------------------------------------------------------------------
# Check 1: WRONG/CORRECT pairs
# ---------------------------------------------------------------------------

def count_wrong_correct_pairs(content: str) -> int:
    """Count WRONG/CORRECT pairs in Common Mistakes AND Standard Pattern.

    Anti-pattern entries often place WRONG/CORRECT pairs in Standard Pattern
    instead of Common Mistakes. Check both sections.

    Supports language-specific comment styles:
    - # WRONG / # CORRECT (Python, Bash, YAML, Ruby)
    - // WRONG / // CORRECT (Java, TypeScript, Go, Rust, C#, Kotlin, Swift, PHP)
    - -- WRONG / -- CORRECT (SQL)
    - <!-- WRONG --> / <!-- CORRECT --> (HTML)
    """
    # Check Common Mistakes first
    cm_text = extract_common_mistakes(content)
    sp_text = extract_standard_pattern(content)
    combined = cm_text + "\n" + sp_text
    wrong_count = len(re.findall(r"(?:#|//|--|<!--)\s*WRONG", combined))
    correct_count = len(re.findall(r"(?:#|//|--|<!--)\s*CORRECT", combined))
    return min(wrong_count, correct_count)


# ---------------------------------------------------------------------------
# Check 2: Gotchas count
# ---------------------------------------------------------------------------

def count_gotchas(content: str) -> int:
    """Count gotcha bullet points."""
    g_text = extract_gotchas(content)
    if not g_text:
        return 0
    return len(re.findall(r"^-\s+\S", g_text, re.MULTILINE))


# ---------------------------------------------------------------------------
# Check 3: Related links
# ---------------------------------------------------------------------------

def get_related_links(content: str) -> list[str]:
    """Extract Related link targets (paths ending in .md).

    Handles both formats:
    - path/to/file.md
    - [text](path/to/file.md)
    """
    r_text = extract_related(content)
    if not r_text:
        return []
    # Match markdown links [text](path.md) and plain paths - path.md
    md_links = re.findall(r"\[.*?\]\((.+?\.md)\)", r_text)
    plain_links = re.findall(r"^-\s+(.+\.md)\s*$", r_text, re.MULTILINE)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for link in md_links + plain_links:
        if link not in seen:
            seen.add(link)
            result.append(link)
    return result


def get_all_link_targets(content: str) -> list[str]:
    """Extract all link-like targets from Related (including anchors)."""
    r_text = extract_related(content)
    if not r_text:
        return []
    # Match lines starting with - that contain .md
    return re.findall(r"^-\s+(.+\.md\S*)", r_text, re.MULTILINE)


# ---------------------------------------------------------------------------
# Check 4: Code blocks in Standard Pattern
# ---------------------------------------------------------------------------

def count_code_blocks_in_pattern(content: str) -> int:
    """Count fenced code blocks inside Standard Pattern section.

    For anti-pattern entries, also checks Common Mistakes section
    since some anti-patterns put their code examples there.
    """
    sp_text = extract_standard_pattern(content)
    sp_blocks = len(re.findall(r"```\w*\n", sp_text)) if sp_text else 0

    # Anti-pattern entries sometimes put code in Common Mistakes
    if sp_blocks == 0:
        cm_text = extract_common_mistakes(content)
        cm_blocks = len(re.findall(r"```\w*\n", cm_text)) if cm_text else 0
        return cm_blocks

    return sp_blocks


# ---------------------------------------------------------------------------
# Check 5: Python imports
# ---------------------------------------------------------------------------

def has_imports_in_code(content: str, language: str) -> bool:
    """Check if code blocks contain import statements for the given language."""
    if language not in ("python", "typescript", "javascript", "go", "rust", "java", "kotlin"):
        return True  # Not applicable

    sp_text = extract_standard_pattern(content)
    if not sp_text:
        return False

    # Extract code blocks
    code_blocks = re.findall(r"```\w*\n(.*?)```", sp_text, re.DOTALL)
    if not code_blocks:
        return False

    full_code = "\n".join(code_blocks)

    import_patterns = {
        "python": r"^(?:from\s+\S+\s+)?import\s+",
        "typescript": r"(?:^import\s+|^const\s+\S+\s*=\s*require)",
        "javascript": r"(?:^import\s+|^const\s+\S+\s*=\s*require)",
        "go": r'^import\s+[\("]',
        "rust": r"^use\s+",
        "java": r"^import\s+",
        "kotlin": r"^import\s+",
    }

    pattern = import_patterns.get(language)
    if not pattern:
        return True

    return bool(re.search(pattern, full_code, re.MULTILINE))


# ---------------------------------------------------------------------------
# Check 6: Entry length
# ---------------------------------------------------------------------------

def get_line_count(content: str) -> int:
    """Count total lines in entry."""
    return len(content.split("\n"))


# ---------------------------------------------------------------------------
# Check 7: Confidence audit
# ---------------------------------------------------------------------------

def should_downgrade_confidence(content: str, meta: dict) -> bool:
    """Check if confidence should be downgraded from high to medium."""
    if meta.get("confidence") != "high":
        return False
    mistakes = count_wrong_correct_pairs(content)
    gotchas = count_gotchas(content)
    # Downgrade if thin content
    return mistakes < 3 or gotchas < 3


# ---------------------------------------------------------------------------
# Check 8: Deprecated patterns
# ---------------------------------------------------------------------------

DEPRECATED_PATTERNS = {
    "python": [
        (r"\bimport\s+cgi\b", "cgi module is deprecated since Python 3.11, removed in 3.13"),
        (r"\burllib\.urlopen\b", "Use urllib.request.urlopen instead"),
        (r"\basync\s+async\b", "Invalid syntax — async is a keyword"),
        (r"\bprint\s+[^(]", "Python 3 requires print() with parentheses"),
        (r"\bhas_key\b", "dict.has_key() removed in Python 3, use 'in' operator"),
        (r"\braw_input\b", "raw_input() removed in Python 3, use input()"),
    ],
    "java": [
        (r"(?<!\.)new\s+Date\(\)", "Use java.time.Instant or LocalDateTime instead of java.util.Date()"),
        (r"\bjavax\.xml\.bind\b", "javax.xml.bind (JAXB) removed in Java 11+, use jakarta.xml.bind"),
        (r"\bjava\.util\.Vector\b", "Vector is legacy — use ArrayList"),
        (r"\bjava\.util\.Hashtable\b", "Hashtable is legacy — use ConcurrentHashMap or HashMap"),
        (r"\bEnumeration<", "Enumeration is legacy — use Iterator"),
    ],
    "typescript": [
        (r"(?<!\w)var\s+\w+", "Use const/let instead of var"),
        (r"(?<!\w)moment\.", "moment.js is in maintenance mode — use date-fns or dayjs"),
    ],
    "go": [
        (r"\bio/ioutil\b", "io/ioutil deprecated since Go 1.16 — use io and os packages"),
    ],
    "rust": [
        (r"\btry!\s*\(", "try!() macro deprecated — use ? operator"),
    ],
    "php": [
        (r"\bmysql_\w+\s*\(", "mysql_* functions removed in PHP 7 — use PDO or mysqli"),
        (r"\?>\s*$", "Closing ?> tag is discouraged in PHP files"),
    ],
    "kotlin": [
        (r"\.javaClass<", "Use ::class.java instead of .javaClass<>"),
    ],
}


def find_deprecated_patterns(content: str, language: str) -> list[tuple[str, str]]:
    """Find deprecated patterns in Standard Pattern code examples.

    Only checks the Standard Pattern section — Common Mistakes intentionally
    shows deprecated code as WRONG examples.
    """
    issues = []
    patterns = DEPRECATED_PATTERNS.get(language, [])
    if not patterns:
        return issues

    # Only check Standard Pattern section code blocks
    sp_text = extract_standard_pattern(content)
    if not sp_text:
        return issues

    code_blocks = re.findall(r"```\w*\n(.*?)```", sp_text, re.DOTALL)
    full_code = "\n".join(code_blocks)

    # Filter out comment-only lines to avoid false positives
    lines = full_code.split("\n")
    non_comment_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        non_comment_lines.append(line)
    filtered_code = "\n".join(non_comment_lines)

    for pattern, reason in patterns:
        if re.search(pattern, filtered_code):
            issues.append((pattern, reason))
    return issues


# ---------------------------------------------------------------------------
# Check 9: Duplicate detection
# ---------------------------------------------------------------------------

def get_pattern_hash(content: str) -> str | None:
    """Hash the Standard Pattern code block for duplicate detection."""
    sp_text = extract_standard_pattern(content)
    if not sp_text:
        return None
    # Extract just the code
    code_blocks = re.findall(r"```\w*\n(.*?)```", sp_text, re.DOTALL)
    if not code_blocks:
        return None
    combined = "\n".join(code_blocks)
    # Normalize whitespace
    normalized = re.sub(r"\s+", " ", combined.strip())
    if len(normalized) < 50:
        return None  # Too short to meaningfully compare
    return hashlib.md5(normalized.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Check 10: Cross-reference integrity
# ---------------------------------------------------------------------------

def build_reference_map(entries: dict[str, tuple[Path, str]]) -> dict[str, set[str]]:
    """Build a map of which entries reference which other entries."""
    refs = defaultdict(set)  # target_path -> set of source entry IDs
    for entry_id, (fpath, content) in entries.items():
        links = get_related_links(content)
        for link in links:
            refs[link].add(entry_id)
    return refs


def find_orphans(entries: dict[str, tuple[Path, str]], ref_map: dict[str, set[str]]) -> list[str]:
    """Find entries not referenced by any other entry."""
    orphans = []
    for entry_id, (fpath, content) in entries.items():
        # Check if any other entry references this file
        rel_path = str(fpath)
        is_referenced = False
        for target, sources in ref_map.items():
            if entry_id in sources:
                is_referenced = True
                break
        # Also check by file path
        if not is_referenced:
            for target, sources in ref_map.items():
                target_clean = target.split("#")[0]  # Strip anchors
                try:
                    target_resolved = Path(target_clean).resolve()
                    if target_resolved == fpath.resolve():
                        is_referenced = True
                        break
                except Exception:
                    pass
        if not is_referenced:
            orphans.append(entry_id)
    return orphans


# ---------------------------------------------------------------------------
# Single entry audit
# ---------------------------------------------------------------------------

class EntryIssue:
    """Represents a single issue found in an entry."""
    def __init__(self, check: str, severity: str, message: str, fix: str = ""):
        self.check = check
        self.severity = severity  # "critical", "warning", "info"
        self.message = message
        self.fix = fix

    def to_dict(self):
        d = {"check": self.check, "severity": self.severity, "message": self.message}
        if self.fix:
            d["fix"] = self.fix
        return d


def audit_entry(fpath: Path, content: str, meta: dict,
                entry_id_map: dict[str, tuple[Path, str]],
                ref_map: dict[str, set[str]],
                pattern_hashes: dict[str, list[str]]) -> list[EntryIssue]:
    """Run all quality checks on a single entry."""
    issues = []
    language = meta.get("language", "")
    entry_id = meta.get("id", str(fpath))
    rel_path = str(fpath)

    # Check 1: WRONG/CORRECT pairs
    pairs = count_wrong_correct_pairs(content)
    if pairs < 3:
        severity = "critical" if pairs < 2 else "warning"
        issues.append(EntryIssue(
            "wrong_correct_pairs", severity,
            f"Only {pairs} WRONG/CORRECT pairs (need >= 3)",
            f"Add {3 - pairs} more WRONG/CORRECT pairs showing real mistakes models make"
        ))

    # Check 2: Gotchas
    gotchas = count_gotchas(content)
    if gotchas < 3:
        severity = "critical" if gotchas < 2 else "warning"
        issues.append(EntryIssue(
            "gotchas", severity,
            f"Only {gotchas} gotcha bullet points (need >= 3)",
            f"Add {3 - gotchas} more gotcha bullet points for non-obvious pitfalls"
        ))

    # Check 3: Related links
    links = get_related_links(content)
    if len(links) < 2:
        issues.append(EntryIssue(
            "related_links_count", "warning",
            f"Only {len(links)} Related links (need >= 2)",
            "Add more Related links pointing to relevant entries"
        ))

    # Check 3b: Broken Related links
    broken_links = []
    for link in links:
        link_clean = link.split("#")[0]  # Strip anchors
        target = Path(link_clean)
        if not target.exists():
            # Try relative to entry directory
            entry_dir = fpath.parent
            if not (entry_dir / target).exists():
                broken_links.append(link)
    if broken_links:
        issues.append(EntryIssue(
            "broken_related_links", "critical",
            f"Broken Related links: {broken_links}",
            "Fix links to point to existing files or remove them"
        ))

    # Check 4: Code blocks in Standard Pattern
    code_block_count = count_code_blocks_in_pattern(content)
    if code_block_count < 1:
        issues.append(EntryIssue(
            "code_blocks", "critical",
            "No fenced code blocks found in Standard Pattern section",
            "Add at least one fenced code block with language tag to Standard Pattern"
        ))

    # Check 5: Language imports in code (skip for anti-patterns — their code is illustrative)
    is_antipattern = "anti-pattern" in str(fpath) or "antipattern" in str(fpath)
    if not is_antipattern and language in ("python", "typescript", "javascript", "go", "rust", "java", "kotlin"):
        if not has_imports_in_code(content, language):
            issues.append(EntryIssue(
                "missing_imports", "info",
                f"Standard Pattern code block lacks {language} import statements",
                f"Consider adding import statements to make the code example self-contained"
            ))

    # Check 6: Entry length
    line_count = get_line_count(content)
    if line_count < 30:
        issues.append(EntryIssue(
            "entry_too_short", "warning",
            f"Entry is only {line_count} lines (likely too thin)",
            "Expand the entry with more examples, gotchas, or context"
        ))
    elif line_count > 500:
        issues.append(EntryIssue(
            "entry_too_long", "warning",
            f"Entry is {line_count} lines (max 500 recommended)",
            "Condense the entry — move verbose examples to a separate entry"
        ))

    # Check 7: Confidence audit
    if should_downgrade_confidence(content, meta):
        issues.append(EntryIssue(
            "overstated_confidence", "warning",
            f"Confidence 'high' but only {pairs} pairs and {gotchas} gotchas",
            "Downgrade confidence to 'medium' or add more content"
        ))

    # Check 8: Deprecated patterns (skip for anti-patterns — their code is intentionally wrong)
    deprecated = find_deprecated_patterns(content, language) if not is_antipattern else []
    for pattern, reason in deprecated:
        issues.append(EntryIssue(
            "deprecated_pattern", "warning",
            f"Deprecated pattern found: {reason}",
            f"Replace deprecated usage with modern alternative"
        ))

    # Check 9: Duplicate detection
    phash = get_pattern_hash(content)
    if phash and phash in pattern_hashes:
        dupes = [eid for eid in pattern_hashes[phash] if eid != entry_id]
        if dupes:
            issues.append(EntryIssue(
                "duplicate_pattern", "info",
                f"Standard Pattern nearly identical to: {', '.join(dupes[:3])}",
                "Differentiate the pattern or consolidate entries"
            ))

    # Check 10: Orphan detection
    is_orphan = True
    for target, sources in ref_map.items():
        target_clean = target.split("#")[0]
        try:
            if Path(target_clean).resolve() == fpath.resolve():
                is_orphan = False
                break
        except Exception:
            pass
        # Also check by matching entry ID
        if entry_id in sources:
            is_orphan = False
            break
    if is_orphan:
        issues.append(EntryIssue(
            "orphan_entry", "warning",
            "Entry is not referenced by any other entry (orphan)",
            "Add a Related link from a nearby entry to connect it to the knowledge graph"
        ))

    return issues


# ---------------------------------------------------------------------------
# Full audit orchestration
# ---------------------------------------------------------------------------

def run_audit(kb_root: Path, target_entry: str | None = None,
              fix_confidence: bool = False) -> dict:
    """Run the complete quality audit.

    Returns a dict with the audit results.
    """
    # Discover entries
    if target_entry:
        target_path = kb_root / target_entry
        if not target_path.exists():
            print(f"{C.RED}Entry not found: {target_entry}{C.RESET}")
            sys.exit(1)
        entry_files = [target_path]
    else:
        entry_files = discover_entries(kb_root)

    print(f"{C.BOLD}Quality Audit — {len(entry_files)} entries{C.RESET}\n")

    # Load all entries
    entry_id_map: dict[str, tuple[Path, str]] = {}
    pattern_hashes: dict[str, list[str]] = defaultdict(list)
    all_meta: dict[str, dict] = {}

    for fpath in entry_files:
        try:
            content = fpath.read_text(encoding="utf-8")
        except Exception as e:
            print(f"{C.RED}ERROR reading {fpath}: {e}{C.RESET}")
            continue
        meta = parse_frontmatter(content)
        if not meta:
            continue
        entry_id = meta.get("id", str(fpath))
        entry_id_map[entry_id] = (fpath, content)
        all_meta[entry_id] = meta

        phash = get_pattern_hash(content)
        if phash:
            pattern_hashes[phash].append(entry_id)

    # Build cross-reference map
    ref_map = build_reference_map(entry_id_map)

    # Audit each entry
    results: dict[str, dict] = {}
    critical_count = 0
    warning_count = 0
    fixable_confidence = []

    for entry_id, (fpath, content) in entry_id_map.items():
        meta = all_meta[entry_id]
        issues = audit_entry(fpath, content, meta, entry_id_map, ref_map, pattern_hashes)

        critical_issues = [i for i in issues if i.severity == "critical"]
        warning_issues = [i for i in issues if i.severity == "warning"]
        info_issues = [i for i in issues if i.severity == "info"]

        critical_count += len(critical_issues)
        warning_count += len(warning_issues)

        if any(i.check == "overstated_confidence" for i in issues):
            fixable_confidence.append((entry_id, fpath, content, meta))

        results[entry_id] = {
            "file": str(fpath),
            "language": meta.get("language", ""),
            "confidence": meta.get("confidence", ""),
            "critical": [i.to_dict() for i in critical_issues],
            "warnings": [i.to_dict() for i in warning_issues],
            "info": [i.to_dict() for i in info_issues],
            "pair_count": count_wrong_correct_pairs(content),
            "gotcha_count": count_gotchas(content),
            "related_count": len(get_related_links(content)),
            "line_count": get_line_count(content),
        }

    # Fix confidence if requested
    fixed_count = 0
    if fix_confidence and fixable_confidence:
        print(f"\n{C.CYAN}Fixing confidence for {len(fixable_confidence)} entries...{C.RESET}")
        for entry_id, fpath, content, meta in fixable_confidence:
            # Replace confidence: "high" with confidence: "medium" in the frontmatter
            new_content = re.sub(
                r'(confidence:\s*["\']?)high(["\']?)',
                r'\1medium\2',
                content,
                count=1
            )
            fpath.write_text(new_content, encoding="utf-8")
            fixed_count += 1
            print(f"  {C.GREEN}Fixed{C.RESET} {entry_id}")

    # Print console report
    print_report(results, critical_count, warning_count)

    # Build summary
    summary = {
        "total_entries": len(entry_id_map),
        "critical_issues": critical_count,
        "warning_issues": warning_count,
        "confidence_fixes": fixed_count,
        "entries": results,
    }

    return summary


# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------

def print_report(results: dict, critical_count: int, warning_count: int):
    """Print color-coded console report."""
    # Group by severity
    critical_entries = {k: v for k, v in results.items() if v["critical"]}
    warning_entries = {k: v for k, v in results.items() if v["warnings"] and not v["critical"]}
    clean_entries = {k: v for k, v in results.items() if not v["critical"] and not v["warnings"]}

    # Summary header
    print(f"{'='*60}")
    print(f"{C.BOLD}QUALITY AUDIT RESULTS{C.RESET}")
    print(f"{'='*60}")
    print(f"Total entries audited: {len(results)}")
    print(f"  {C.GREEN}Clean:{C.RESET} {len(clean_entries)}")
    print(f"  {C.YELLOW}Warnings:{C.RESET} {len(warning_entries)} entries ({warning_count} issues)")
    print(f"  {C.RED}Critical:{C.RESET} {len(critical_entries)} entries ({critical_count} issues)")

    # Stats
    pair_counts = [v["pair_count"] for v in results.values()]
    gotcha_counts = [v["gotcha_count"] for v in results.values()]
    print(f"\nContent depth:")
    print(f"  WRONG/CORRECT pairs: min={min(pair_counts)} avg={sum(pair_counts)/len(pair_counts):.1f} max={max(pair_counts)}")
    print(f"  Gotchas: min={min(gotcha_counts)} avg={sum(gotcha_counts)/len(gotcha_counts):.1f} max={max(gotcha_counts)}")

    # Critical issues
    if critical_entries:
        print(f"\n{C.RED}{C.BOLD}CRITICAL ISSUES ({len(critical_entries)} entries):{C.RESET}")
        print(f"{'─'*60}")
        for entry_id, data in sorted(critical_entries.items()):
            print(f"\n  {C.RED}■{C.RESET} {C.BOLD}{entry_id}{C.RESET} ({data['file']})")
            for issue in data["critical"]:
                print(f"    {C.RED}✗{C.RESET} [{issue['check']}] {issue['message']}")
                if issue.get("fix"):
                    print(f"      {C.CYAN}→{C.RESET} {issue['fix']}")

    # Warning issues
    if warning_entries:
        print(f"\n{C.YELLOW}{C.BOLD}WARNING ISSUES ({len(warning_entries)} entries):{C.RESET}")
        print(f"{'─'*60}")
        for entry_id, data in sorted(warning_entries.items()):
            print(f"\n  {C.YELLOW}▲{C.RESET} {C.BOLD}{entry_id}{C.RESET}")
            for issue in data["warnings"]:
                print(f"    {C.YELLOW}⚠{C.RESET} [{issue['check']}] {issue['message']}")

    # Issue type breakdown
    all_issues = []
    for data in results.values():
        all_issues.extend(data["critical"] + data["warnings"] + data["info"])
    if all_issues:
        issue_types = defaultdict(int)
        for issue in all_issues:
            issue_types[issue["check"]] += 1
        print(f"\n{C.BOLD}Issue Breakdown:{C.RESET}")
        for check, count in sorted(issue_types.items(), key=lambda x: -x[1]):
            print(f"  {check}: {count}")

    print(f"\n{'='*60}")
    if critical_count > 0:
        print(f"{C.RED}{C.BOLD}AUDIT FAILED — {critical_count} critical issues found{C.RESET}")
    else:
        print(f"{C.GREEN}{C.BOLD}AUDIT PASSED — No critical issues{C.RESET}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# JSON report
# ---------------------------------------------------------------------------

def write_json_report(summary: dict, output_path: Path):
    """Write JSON report."""
    # Make paths serializable
    report = {
        "audit_date": datetime.now().isoformat(),
        "total_entries": summary["total_entries"],
        "critical_issues": summary["critical_issues"],
        "warning_issues": summary["warning_issues"],
        "confidence_fixes": summary["confidence_fixes"],
        "entries": {}
    }
    for entry_id, data in summary["entries"].items():
        report["entries"][entry_id] = data

    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nJSON report: {output_path}")


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def write_markdown_report(summary: dict, output_path: Path):
    """Write Markdown report with fix recommendations."""
    results = summary["entries"]
    critical_entries = {k: v for k, v in results.items() if v["critical"]}
    warning_entries = {k: v for k, v in results.items() if v["warnings"] and not v["critical"]}

    lines = [
        "# Quality Audit Report",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Entries audited**: {summary['total_entries']}",
        f"**Critical issues**: {summary['critical_issues']}",
        f"**Warnings**: {summary['warning_issues']}",
        f"**Confidence fixes applied**: {summary['confidence_fixes']}",
        "",
    ]

    # Stats
    pair_counts = [v["pair_count"] for v in results.values()]
    gotcha_counts = [v["gotcha_count"] for v in results.values()]
    lines.extend([
        "## Content Depth Summary",
        "",
        f"| Metric | Min | Avg | Max |",
        f"|--------|-----|-----|-----|",
        f"| WRONG/CORRECT pairs | {min(pair_counts)} | {sum(pair_counts)/len(pair_counts):.1f} | {max(pair_counts)} |",
        f"| Gotchas | {min(gotcha_counts)} | {sum(gotcha_counts)/len(gotcha_counts):.1f} | {max(gotcha_counts)} |",
        "",
    ])

    # Critical issues
    if critical_entries:
        lines.extend([
            "## Critical Issues (must fix)",
            "",
        ])
        for entry_id, data in sorted(critical_entries.items()):
            lines.append(f"### `{entry_id}`")
            lines.append(f"**File**: `{data['file']}`")
            lines.append("")
            for issue in data["critical"]:
                lines.append(f"- **[{issue['check']}]** {issue['message']}")
                if issue.get("fix"):
                    lines.append(f"  - Fix: {issue['fix']}")
            lines.append("")

    # Warning issues
    if warning_entries:
        lines.extend([
            "## Warnings (should fix)",
            "",
        ])
        for entry_id, data in sorted(warning_entries.items()):
            lines.append(f"### `{entry_id}`")
            for issue in data["warnings"]:
                lines.append(f"- **[{issue['check']}]** {issue['message']}")
                if issue.get("fix"):
                    lines.append(f"  - Fix: {issue['fix']}")
            lines.append("")

    # Orphan entries
    orphans = [k for k, v in results.items()
               if any(i["check"] == "orphan_entry" for i in v["critical"] + v["warnings"])]
    if orphans:
        lines.extend([
            "## Orphan Entries (not referenced by others)",
            "",
            "These entries need Related links from neighboring entries:",
            "",
        ])
        for oid in sorted(orphans):
            lines.append(f"- `{oid}`")
        lines.append("")

    # Overstated confidence
    overstated = [k for k, v in results.items()
                  if any(i["check"] == "overstated_confidence" for i in v["critical"] + v["warnings"])]
    if overstated:
        lines.extend([
            "## Overstated Confidence",
            "",
            "These entries claim 'high' confidence but have thin content:",
            "",
        ])
        for oid in sorted(overstated):
            data = results[oid]
            lines.append(f"- `{oid}` — {data['pair_count']} pairs, {data['gotcha_count']} gotchas")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown report: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Deep quality audit of knowledge base entries"
    )
    parser.add_argument(
        "--fix-confidence", action="store_true",
        help="Auto-downgrade overstated confidence from 'high' to 'medium'"
    )
    parser.add_argument(
        "--entry", type=str, default=None,
        help="Audit a single entry (e.g. python/stdlib/hashlib-sha256.md)"
    )
    parser.add_argument(
        "--kb-root", type=str, default=".",
        help="Path to knowledge base root (default: current directory)"
    )
    parser.add_argument(
        "--json-only", action="store_true",
        help="Only output JSON report (no console colors)"
    )
    args = parser.parse_args()

    kb_root = Path(args.kb_root).resolve()

    summary = run_audit(
        kb_root,
        target_entry=args.entry,
        fix_confidence=args.fix_confidence,
    )

    # Write reports
    scripts_dir = kb_root / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    write_json_report(summary, scripts_dir / "quality_audit.json")
    write_markdown_report(summary, scripts_dir / "quality_audit.md")

    # Exit code
    has_critical = summary["critical_issues"] > 0
    sys.exit(1 if has_critical else 0)


if __name__ == "__main__":
    main()
