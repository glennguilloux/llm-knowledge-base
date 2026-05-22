#!/usr/bin/env python3
"""Update last_verified dates for high-confidence entries.

For entries with confidence: "high", sets last_verified to today's date.
For entries with confidence: "draft", leaves the date unchanged.

Usage:
    python scripts/update_freshness.py
    python scripts/update_freshness.py --dry-run
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml


def find_entry_files(kb_path: Path) -> list[Path]:
    """Find all knowledge base entry markdown files."""
    skip_files = {"README.md", "schema.md", "CONTRIBUTING.md", "LLM_CODEBASE_KNOWLEDGE_BASE.md"}
    files = []
    for md_file in sorted(kb_path.rglob("*.md")):
        if md_file.name in skip_files:
            continue
        if md_file.parent.name in ("templates", ".github"):
            continue
        files.append(md_file)
    return files


def update_freshness(kb_path: Path, dry_run: bool = False) -> tuple[int, int]:
    """Update last_verified dates for high-confidence entries.

    Returns:
        Tuple of (updated_count, draft_count)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    updated = 0
    drafts = 0

    for filepath in find_entry_files(kb_path):
        content = filepath.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            continue

        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            continue

        if not isinstance(meta, dict):
            continue

        confidence = meta.get("confidence", "draft")
        current_date = str(meta.get("last_verified", ""))

        if confidence == "high":
            if current_date != today:
                # Replace the last_verified line in frontmatter
                new_content = re.sub(
                    r'^(last_verified:\s*")[^"]*(")',
                    f'\\g<1>{today}\\2',
                    content,
                    count=1,
                    flags=re.MULTILINE,
                )
                if not dry_run:
                    filepath.write_text(new_content, encoding="utf-8")
                updated += 1
        else:
            drafts += 1

    return updated, drafts


def main() -> int:
    parser = argparse.ArgumentParser(description="Update freshness dates for high-confidence entries")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated without writing")
    parser.add_argument("--kb-path", type=str, default=".", help="Path to knowledge base root")
    args = parser.parse_args()

    kb_path = Path(args.kb_path)
    updated, drafts = update_freshness(kb_path, dry_run=args.dry_run)

    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {updated} dates. {drafts} drafts left unchanged.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
