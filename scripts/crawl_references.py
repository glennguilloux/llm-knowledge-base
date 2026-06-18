#!/usr/bin/env python3
"""
Harvest entry skeletons from the references/ directory.

Scans each cloned reference repo for documented patterns, cross-references
against existing entry IDs/titles, and auto-generates markdown skeletons
with frontmatter + Standard Pattern section scaffolded from the reference code.

Output: references/candidate_entries/ — ready for human review.

Usage:
    python scripts/crawl_references.py
    python scripts/crawl_references.py --output-dir my_entries/
    python scripts/crawl_references.py --dry-run
    python scripts/crawl_references.py --only python-patterns
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Protocol

# ---------------------------------------------------------------------------
# Repo descriptors — how to find patterns in each reference repo
# ---------------------------------------------------------------------------

PATTERN_LOCATORS: dict[str, dict] = {
    "python-patterns": {
        "root": "references/python-patterns",
        "type": "python_files_in_dirs",
        "dirs": ["patterns/creational", "patterns/structural", "patterns/behavioral"],
        "language": "python",
        "entry_dir": "python/patterns",
        "category": "patterns",
        "glob": "*.py",
        "get_name": lambda stem: stem.replace("_", " ").replace("-", " ").title(),
        "doc_extract": "module_docstring",
    },
    "go-patterns": {
        "root": "references/go-patterns",
        "type": "markdown_files_in_dirs",
        "dirs": [
            "creational", "structural", "behavioral",
            "concurrency", "synchronization", "messaging",
            "stability", "idiom",
        ],
        "language": "go",
        "entry_dir": "go/patterns",
        "category": "patterns",
        "glob": "*.md",
        "get_name": lambda stem: stem.replace("_", " ").replace("-", " ").title(),
        "doc_extract": "first_heading_and_para",
    },
    "java-design-patterns": {
        "root": "references/java-design-patterns",
        "type": "dir_names",
        "dirs": None,  # Scan all top-level subdirs (skip known non-pattern dirs)
        "skip_dirs": {
            ".mvn", ".github", ".git", "src", "target", "etc",
            ".all-contributorsrc", ".editorconfig",
        },
        "language": "java",
        "entry_dir": "java/patterns",
        "category": "patterns",
        "get_name": lambda name: name.replace("-", " ").replace("_", " ").title(),
        "doc_extract": "readme_or_info",
    },
    "DesignPatternsPHP": {
        "root": "references/DesignPatternsPHP",
        "type": "dir_names",
        "dirs": ["Behavioral", "Creational", "Structural", "More"],
        "skip_dirs": set(),
        "language": "php",
        "entry_dir": "php/patterns",
        "category": "patterns",
        "get_name": lambda name: name.replace("-", " ").replace("_", " ").title(),
        "doc_extract": "readme_or_info",
    },
    "design-patterns-across-languages": {
        "root": "references/design-patterns-across-languages",
        "type": "dir_names",
        "dirs": ["creational", "structural", "behavioral"],
        "skip_dirs": set(),
        "language": "multi",
        "entry_dir": "patterns",
        "category": "patterns",
        "get_name": lambda name: name.replace("-", " ").replace("_", " ").title(),
        "doc_extract": "readme_or_info",
    },
    "patterns": {
        "root": "references/patterns",
        "type": "markdown_files_in_dirs",
        "dirs": ["src"],
        "language": "multi",
        "entry_dir": "patterns",
        "category": "patterns",
        "glob": "*.md",
        "get_name": lambda stem: stem.replace("-", " ").replace("_", " ").title(),
        "doc_extract": "first_heading_and_para",
    },
}

# Entries to skip (already well-covered)
SKIP_PATTERNS = {
    "python": {"abstract factory", "factory", "builder", "singleton", "adapter",
               "bridge", "composite", "decorator", "facade", "proxy",
               "chain of responsibility", "command", "iterator", "mediator",
               "memento", "observer", "state", "strategy", "template", "visitor",
               "prototype", "dependency injection", "flyweight", "front controller",
               "mvc", "servant", "specification", "registry", "borg",
               "pool", "lazy evaluation", "publish subscribe",
               "blackboard", "graph search", "hsm",
               "chaining method", "catalog"},
    "go": {"abstract factory", "builder", "factory method", "singleton",
           "decorator", "proxy", "observer", "strategy",
           "object pool", "semaphore",
           "bounded parallelism", "generators", "parallelism",
           "fan-in", "fan-out", "publish/subscribe",
           "circuit-breaker", "circuit breaker",
           "functional options", "timing functions",
           "producer consumer"},
    "java": {"abstract factory", "builder", "singleton", "adapter",
             "bridge", "composite", "decorator", "facade", "flyweight", "proxy",
             "chain of responsibility", "command", "iterator", "mediator",
             "memento", "observer", "state", "strategy", "template method", "visitor",
             "dependency injection", "factory method", "factory",
             "prototype", "mvc", "model-view-controller",
             "dao", "data access object", "repository", "service layer",
             "dto", "data transfer object", "value object",
             "specification", "interpreter", "null object",
             "event sourcing", "cqrs", "saga",
             "strangler", "throttling", "retry", "circuit breaker",
             "pipeline", "reactor", "publish-subscribe", "publish subscribe",
             "twin", "type object", "currency", "money",
             "feature toggle", "health check", "retry"},
    "php": {"abstract factory", "factory", "builder", "singleton",
            "adapter", "bridge", "composite", "decorator", "facade",
            "proxy", "chain of responsibility", "command", "iterator",
            "mediator", "memento", "observer", "state", "strategy",
            "template", "visitor", "dependency injection",
            "prototype", "null object", "factory method",
            "registry", "specification", "data transfer object",
            "value object"},
}


# ---------------------------------------------------------------------------
# Pattern extraction functions
# ---------------------------------------------------------------------------

def extract_module_docstring(filepath: Path) -> str:
    """Extract the module-level docstring from a Python file."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    # Match triple-quoted string at module level
    match = re.search(
        r'^"""(.*?)"""', content, re.DOTALL
    )
    if match:
        text = match.group(1).strip()
        # Take first 300 chars
        lines = text.strip().split("\n")
        return "\n".join(lines[:6]).strip()
    return ""


def extract_first_heading_and_para(filepath: Path) -> str:
    """Extract the first heading and first paragraph from a markdown file."""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    result_parts = []
    for line in lines:
        if line.startswith("#"):
            result_parts.append(line.lstrip("#").strip())
        elif line.strip() and not line.startswith("#") and not line.startswith("```"):
            result_parts.append(line.strip()[:200])
            break
    return "\n".join(result_parts) if result_parts else ""


def extract_readme_or_info(repo_root: Path, pattern_name: str) -> str:
    """Extract description from a pattern's README or info file."""
    # Try README.md, README, readme.md, then index.md
    for candidate in ["README.md", "README", "readme.md", "index.md", "info.md"]:
        fp = repo_root / pattern_name / candidate
        if fp.exists():
            content = fp.read_text(encoding="utf-8", errors="replace")
            lines = content.split("\n")
            parts = []
            for line in lines:
                if line.startswith("#"):
                    parts.append(line.lstrip("#").strip())
                elif line.strip() and not line.startswith("```") and len(line.strip()) > 20:
                    parts.append(line.strip()[:200])
                    break
            return "\n".join(parts) if parts else ""
    return ""


def safe_slug(name: str) -> str:
    """Convert a pattern name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def entry_id(language: str, category: str, slug: str) -> str:
    """Generate a canonical entry ID."""
    return f"{language}-{category}-{slug}"


def existing_entry_ids(kb_path: Path) -> set[str]:
    """Collect all existing entry IDs from the knowledge base."""
    ids = set()
    for md_file in kb_path.rglob("*.md"):
        if md_file.name in ("README.md", "schema.md", "CONTRIBUTING.md"):
            continue
        if md_file.parent.name == "templates":
            continue
        if any(part.startswith(".") for part in md_file.parts):
            continue
        content = md_file.read_text(encoding="utf-8", errors="replace")
        match = re.match(r"^---\n.*?^id:\s*\"(.+?)\".*?\n---", content, re.DOTALL | re.MULTILINE)
        if match:
            ids.add(match.group(1))
        else:
            # Fallback: use filename stem
            ids.add(f"{md_file.parent.name}-{md_file.stem}")
    return ids


# ---------------------------------------------------------------------------
# Skeleton generation
# ---------------------------------------------------------------------------

SKELETON_TEMPLATE = """---
id: "{entry_id}"
title: "{title}"
language: "{language}"
category: "{category}"
tags: [{tags}]
version: "{version}"
retrieval_hint: "{retrieval_hint}"
last_verified: "{today}"
confidence: "draft"
---

# {title}

> **Autogenerated from:** `{source_repo}`

## When to Use
- [TODO: Add 3-5 concrete scenarios for this pattern]

## Standard Pattern

```{code_tag}
{standard_pattern}
```

## Common Mistakes

```{code_tag}
# WRONG: [TODO: Describe the mistake]
# TODO: Add bad code example

# CORRECT: [TODO: Describe the fix]
# TODO: Add good code example

# WRONG: [TODO: Another common mistake]
# TODO: Add bad example

# CORRECT: [TODO: The right way]
# TODO: Add good example

# WRONG: [TODO: Third common mistake]
# TODO: Add bad example

# CORRECT: [TODO: The right way]
# TODO: Add good example
```

## Gotchas
- [TODO: Add non-obvious pitfall related to this pattern]
- [TODO: Add edge case warning]
- [TODO: Add performance or maintenance consideration]

## Related
- {related}

---

> **⚠️ SKELETON ENTRY — Needs Human Review**
> Auto-generated by `scripts/crawl_references.py` from `{source_repo}`.
> Fill in TODO sections, verify patterns, and change `confidence` to `high` or `medium`.
"""


def generate_skeleton(
    pattern_name: str,
    description: str,
    source_code: str,
    source_repo: str,
    language: str,
    category: str,
    kb_path: Path,
) -> str | None:
    """Generate a skeleton markdown entry for a pattern.

    Returns None if the pattern already exists in the KB.
    """
    slug = safe_slug(pattern_name)
    eid = entry_id(language, category, slug)

    # Version defaults per language
    versions = {
        "python": "3.10+",
        "go": "1.21+",
        "java": "17+",
        "php": "8.1+",
        "multi": "N/A",
    }
    code_tags = {
        "python": "python",
        "go": "go",
        "java": "java",
        "php": "php",
        "multi": "text",
    }
    related_defaults = {
        "python": "python/stdlib/pathlib.md",
        "go": "go/stdlib/error-handling.md",
        "java": "java/stdlib/collections.md",
        "php": "php/stdlib/basics.md",
        "multi": "patterns/design-patterns-overview.md",
    }

    version = versions.get(language, "N/A")
    code_tag = code_tags.get(language, "text")
    related = related_defaults.get(language, "")

    # Build tags
    tag_parts = [
        f'"{slug}"',
        f'"{language}"',
        f'"{category}"',
    ]
    tags_str = ", ".join(tag_parts)

    # Build retrieval hint
    hint = f"{pattern_name} {language} {category} design pattern"

    # Format standard pattern (truncate if too long)
    if source_code:
        lines = source_code.split("\n")
        # For Python, limit to ~40 lines; for markdown, extract code blocks
        code_snippet = "\n".join(lines[:40])
        if len(lines) > 40:
            code_snippet += "\n# ... (truncated for skeleton)"
    else:
        code_snippet = f"// TODO: Add {language} implementation of {pattern_name}"

    return SKELETON_TEMPLATE.format(
        entry_id=eid,
        title=pattern_name.title(),
        language=language,
        category=category,
        tags=tags_str,
        version=version,
        retrieval_hint=hint,
        today=datetime.now().strftime("%Y-%m-%d"),
        source_repo=source_repo,
        code_tag=code_tag,
        standard_pattern=code_snippet,
        related=related,
    )


# ---------------------------------------------------------------------------
# Repo-specific scanners
# ---------------------------------------------------------------------------

def scan_python_files(descriptor: dict, kb_path: Path, existing_ids: set[str]) -> list[tuple[str, str]]:
    """Scan a repo with Python files in categorized directories (python-patterns)."""
    repo_root = kb_path / descriptor["root"]
    candidates = []

    for subdir in descriptor["dirs"]:
        dir_path = repo_root / subdir
        if not dir_path.exists():
            continue
        for py_file in sorted(dir_path.glob(descriptor["glob"])):
            pattern_name = descriptor["get_name"](py_file.stem)
            pattern_name_lower = pattern_name.lower()

            if pattern_name_lower in SKIP_PATTERNS.get("python", set()):
                continue

            # Check if already exists
            slug = safe_slug(pattern_name)
            eid = entry_id(descriptor["language"], descriptor["category"], slug)
            if eid in existing_ids:
                continue

            # Extract docstring
            doc = extract_module_docstring(py_file)
            source_code = py_file.read_text(encoding="utf-8", errors="replace")

            skeleton = generate_skeleton(
                pattern_name=pattern_name,
                description=doc,
                source_code=source_code,
                source_repo=descriptor["root"],
                language=descriptor["language"],
                category=descriptor["category"],
                kb_path=kb_path,
            )
            if skeleton:
                candidates.append((skeleton, py_file.stem))

    return candidates


def scan_markdown_files(descriptor: dict, kb_path: Path, existing_ids: set[str]) -> list[tuple[str, str]]:
    """Scan a repo with markdown files in directories (go-patterns, patterns)."""
    repo_root = kb_path / descriptor["root"]
    candidates = []

    for subdir in descriptor["dirs"]:
        dir_path = repo_root / subdir
        if not dir_path.exists():
            continue
        for md_file in sorted(dir_path.glob(descriptor["glob"])):
            if md_file.name.lower() in ("readme.md", "summary.md", "book.json"):
                continue
            pattern_name = descriptor["get_name"](md_file.stem)
            pattern_name_lower = pattern_name.lower()

            lang = descriptor["language"]
            if lang in SKIP_PATTERNS and pattern_name_lower in SKIP_PATTERNS[lang]:
                continue

            # Check if already exists
            slug = safe_slug(pattern_name)
            eid = entry_id(descriptor["language"], descriptor["category"], slug)
            if eid in existing_ids:
                continue

            # Extract description and code blocks
            desc = extract_first_heading_and_para(md_file)
            content = md_file.read_text(encoding="utf-8", errors="replace")

            # Try to extract code blocks from the markdown
            code_blocks = re.findall(
                r"```(?:\w+)?\s*\n(.*?)```", content, re.DOTALL
            )
            source_code = "\n\n".join(code_blocks[:3]) if code_blocks else f"// See {descriptor['root']}/{subdir}/{md_file.name}"

            skeleton = generate_skeleton(
                pattern_name=pattern_name,
                description=desc,
                source_code=source_code,
                source_repo=f"{descriptor['root']}/{subdir}",
                language=descriptor["language"],
                category=descriptor["category"],
                kb_path=kb_path,
            )
            if skeleton:
                candidates.append((skeleton, md_file.stem))

    return candidates


def scan_dir_names(descriptor: dict, kb_path: Path, existing_ids: set[str]) -> list[tuple[str, str]]:
    """Scan a repo where each subdirectory is a pattern (java-design-patterns, DesignPatternsPHP)."""
    repo_root = kb_path / descriptor["root"]
    candidates = []

    dirs_to_scan = descriptor["dirs"] if descriptor["dirs"] else [
        d.name for d in sorted(repo_root.iterdir())
        if d.is_dir() and not d.name.startswith(".") and d.name not in descriptor.get("skip_dirs", set())
    ]

    for subdir in dirs_to_scan:
        dir_path = repo_root / subdir
        if not dir_path.is_dir():
            continue

        pattern_name = descriptor["get_name"](subdir)
        pattern_name_lower = pattern_name.lower()

        lang = descriptor["language"]
        if lang in SKIP_PATTERNS and pattern_name_lower in SKIP_PATTERNS[lang]:
            continue

        # Check if already exists
        slug = safe_slug(pattern_name)
        eid = entry_id(descriptor["language"], descriptor["category"], slug)
        if eid in existing_ids:
            continue

        # Extract description from README
        desc = extract_readme_or_info(repo_root, subdir)

        # Try to find source code
        source_code = ""
        if descriptor["language"] == "java":
            # Look for Java source files
            java_files = list(dir_path.rglob("*.java"))
            if java_files:
                # Use the first non-test, non-Etc source file
                for jf in java_files:
                    if "test" not in jf.name.lower() and "etc" not in jf.parts:
                        source_code = jf.read_text(encoding="utf-8", errors="replace")[:2000]
                        break
                if not source_code and java_files:
                    source_code = java_files[0].read_text(encoding="utf-8", errors="replace")[:2000]
        elif descriptor["language"] == "php":
            # Look for PHP source files
            php_files = list(dir_path.rglob("*.php"))
            if php_files:
                for pf in php_files:
                    if "test" not in pf.name.lower():
                        source_code = pf.read_text(encoding="utf-8", errors="replace")[:2000]
                        break
                if not source_code and php_files:
                    source_code = php_files[0].read_text(encoding="utf-8", errors="replace")[:2000]

        skeleton = generate_skeleton(
            pattern_name=pattern_name,
            description=desc,
            source_code=source_code,
            source_repo=f"{descriptor['root']}/{subdir}",
            language=descriptor["language"],
            category=descriptor["category"],
            kb_path=kb_path,
        )
        if skeleton:
            candidates.append((skeleton, subdir))

    return candidates


# ---------------------------------------------------------------------------
# Programmatic API
# ---------------------------------------------------------------------------

def run_crawl(kb_path: str = ".", output_dir: str = "references/candidate_entries",
              dry_run: bool = False, only_repo: str | None = None,
              force: bool = False) -> int:
    """Run reference repo crawl and generate candidate entry skeletons.

    Args:
        kb_path: Path to knowledge base root.
        output_dir: Output directory for generated skeletons (relative to kb_path).
        dry_run: If True, show what would be generated without writing files.
        only_repo: If set, only scan a specific repo (e.g., 'python-patterns').
        force: If True, regenerate skeletons even if entry already exists.

    Returns:
        Number of candidate entries generated.
    """
    kb_path_resolved = Path(kb_path).resolve()
    if not kb_path_resolved.exists():
        print(f"Error: Path '{kb_path_resolved}' does not exist", file=sys.stderr)
        return 0

    output_path = kb_path_resolved / output_dir
    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)

    # Load existing entry IDs for dedup
    existing_ids: set[str] = set()
    if not force:
        existing_ids = existing_entry_ids(kb_path_resolved)
        print(f"Found {len(existing_ids)} existing entry IDs")

    repos_to_scan = [only_repo] if only_repo else list(PATTERN_LOCATORS.keys())

    total_candidates = 0

    for repo_name in repos_to_scan:
        if repo_name not in PATTERN_LOCATORS:
            print(f"  Unknown repo: {repo_name}", file=sys.stderr)
            continue

        descriptor = PATTERN_LOCATORS[repo_name]
        repo_path = kb_path_resolved / descriptor["root"]

        if not repo_path.exists():
            print(f"  Skipping {repo_name}: not found at {repo_path}")
            continue

        scan_type = descriptor["type"]
        print(f"\n  Scanning {repo_name}...")

        candidates: list[tuple[str, str]] = []

        if scan_type == "python_files_in_dirs":
            candidates = scan_python_files(descriptor, kb_path_resolved, existing_ids)
        elif scan_type == "markdown_files_in_dirs":
            candidates = scan_markdown_files(descriptor, kb_path_resolved, existing_ids)
        elif scan_type == "dir_names":
            candidates = scan_dir_names(descriptor, kb_path_resolved, existing_ids)
        else:
            print(f"  Unknown scan type: {scan_type}")

        print(f"  Found {len(candidates)} new candidate patterns")

        for skeleton, stem in candidates:
            slug = safe_slug(stem)
            filename = f"{slug}.md"
            filepath = output_path / filename

            if not dry_run:
                filepath.write_text(skeleton, encoding="utf-8")
                print(f"    Generated: {filepath}")
            else:
                print(f"    [DRY RUN] Would generate: {filepath}")

        total_candidates += len(candidates)

    print(f"\nTotal new candidate entries: {total_candidates}")
    return total_candidates


# ---------------------------------------------------------------------------
# Main (CLI)
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Harvest entry skeletons from references/ repos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--output-dir", type=str, default="references/candidate_entries",
                        help="Output directory for generated skeletons (relative to KB root)")
    parser.add_argument("--kb-path", type=str, default=".",
                        help="Path to knowledge base root")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be generated without writing files")
    parser.add_argument("--only", type=str, default=None,
                        help="Only scan a specific repo (e.g., 'python-patterns')")
    parser.add_argument("--force", action="store_true",
                        help="Regenerate skeletons even if entry already exists")
    args = parser.parse_args()

    return run_crawl(
        kb_path=args.kb_path,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        only_repo=args.only,
        force=args.force,
    )


if __name__ == "__main__":
    sys.exit(main())
