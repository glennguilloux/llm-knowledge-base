#!/usr/bin/env python3
"""Validate all knowledge base entries against the schema."""

import re
import sys
from pathlib import Path

import yaml

REQUIRED_FIELDS = {
    "id",
    "title",
    "language",
    "category",
    "tags",
    "retrieval_hint",
    "last_verified",
    "confidence",
}

VALID_CONFIDENCE = {"high", "medium", "draft"}
VALID_LANGUAGES = {"python", "java", "typescript", "multi", "sql", "yaml", "docker", "javascript", "go", "rust", "bash", "csharp", "shell"}
VALID_CATEGORIES = {
    "stdlib",
    "web",
    "db",
    "testing",
    "data",
    "patterns",
    "crypto",
    "devops",
    "project-conventions",
    "anti-patterns",
    "concurrency",
    "security",
    "performance",
    "api-design",
    "build",
        "error-handling",
}

REQUIRED_SECTIONS = [
    "## When to Use",
    "## Standard Pattern",
    "## Common Mistakes",
    "## Gotchas",
]


def validate_frontmatter(filepath: Path) -> list[str]:
    """Check YAML frontmatter has all required fields and valid values."""
    errors = []
    content = filepath.read_text(encoding="utf-8")

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return ["Missing YAML frontmatter"]

    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return [f"Invalid YAML: {e}"]

    if not isinstance(meta, dict):
        return ["Frontmatter is not a YAML mapping"]

    missing = REQUIRED_FIELDS - set(meta.keys())
    if missing:
        errors.append(f"Missing fields: {missing}")

    if meta.get("confidence") not in VALID_CONFIDENCE:
        errors.append(f"Invalid confidence: {meta.get('confidence')}")

    if meta.get("language") not in VALID_LANGUAGES:
        errors.append(f"Invalid language: {meta.get('language')}")

    if meta.get("category") not in VALID_CATEGORIES:
        errors.append(f"Invalid category: {meta.get('category')}")

    if not isinstance(meta.get("tags"), list):
        errors.append("'tags' must be a list")

    if meta.get("last_verified"):
        try:
            str(meta["last_verified"])  # Just check it's parseable
        except Exception:
            errors.append(f"Invalid last_verified date: {meta['last_verified']}")

    return errors


def validate_sections(filepath: Path) -> list[str]:
    """Check that required sections exist."""
    errors = []
    content = filepath.read_text(encoding="utf-8")

    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"Missing section: {section}")

    return errors


def validate_code_blocks(filepath: Path) -> list[str]:
    """Check that code blocks have language tags."""
    errors = []
    content = filepath.read_text(encoding="utf-8")

    # Skip frontmatter
    frontmatter_end = content.find("---", 3)
    if frontmatter_end > 0:
        body = content[frontmatter_end + 3 :]
    else:
        body = content

    in_code_block = False
    bare_opening_count = 0

    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_code_block:
                # Opening a code block
                if stripped == "```":
                    bare_opening_count += 1
                in_code_block = True
            else:
                # Closing a code block
                in_code_block = False

    if bare_opening_count:
        errors.append(
            f"Found {bare_opening_count} code block(s) without language tag"
        )

    return errors


def validate_freshness(filepath: Path) -> list[str]:
    """Warn if high-confidence entries have last_verified older than 6 months."""
    warnings = []
    content = filepath.read_text(encoding="utf-8")

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return warnings

    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return warnings

    if not isinstance(meta, dict):
        return warnings

    if meta.get("confidence") != "high":
        return warnings

    lv = meta.get("last_verified", "")
    if not lv:
        warnings.append("WARNING: high-confidence entry missing last_verified")
        return warnings

    try:
        from datetime import datetime, timedelta
        verified_date = datetime.strptime(str(lv), "%Y-%m-%d")
        cutoff = datetime.now() - timedelta(days=180)
        if verified_date < cutoff:
            warnings.append(f"WARNING: high-confidence entry last_verified is {lv} (>6 months ago)")
    except ValueError:
        warnings.append(f"WARNING: invalid last_verified date format: {lv}")

    return warnings


def validate_entry(filepath: Path) -> list[str]:
    """Run all validation checks on a single entry."""
    errors = []
    errors.extend(validate_frontmatter(filepath))
    errors.extend(validate_sections(filepath))
    errors.extend(validate_code_blocks(filepath))
    return errors


def validate_entry_with_warnings(filepath: Path) -> tuple[list[str], list[str]]:
    """Run validation checks and return (errors, warnings) separately."""
    errors = validate_entry(filepath)
    warnings = validate_freshness(filepath)
    return errors, warnings


def main() -> int:
    """Validate all knowledge base entries."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate knowledge base entries")
    parser.add_argument("--show-warnings", action="store_true",
                        help="Show freshness warnings for high-confidence entries")
    args, _ = parser.parse_known_args()

    kb_path = Path(".")
    errors_found = False
    total = 0
    passed = 0
    warning_count = 0

    for md_file in sorted(kb_path.rglob("*.md")):
        # Skip hidden directories, virtual envs, and non-entry files
        if any(part.startswith(".") for part in md_file.parts):
            continue
        if md_file.name in (
            "README.md",
            "schema.md",
            "CONTRIBUTING.md", "RELEASE_CHECKLIST.md",
            "LLM_CODEBASE_KNOWLEDGE_BASE.md",
            "CHANGELOG.md",
            "LICENSE",
        ):
            continue
        if any(p.name in ("templates", ".github", "docs", "architecture", "scripts", "benchmark_prompts", "prompts") for p in md_file.parents):
            continue

        total += 1
        if args.show_warnings:
            errors, warnings = validate_entry_with_warnings(md_file)
            for w in warnings:
                print(f"WARN {md_file}: {w}")
                warning_count += 1
        else:
            errors = validate_entry(md_file)

        if errors:
            print(f"FAIL {md_file}")
            for err in errors:
                print(f"     - {err}")
            errors_found = True
        else:
            print(f"OK   {md_file}")
            passed += 1

    print(f"\n{'='*40}")
    print(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")
    if args.show_warnings:
        print(f"Warnings: {warning_count}")

    return 1 if errors_found else 0


if __name__ == "__main__":
    sys.exit(main())
