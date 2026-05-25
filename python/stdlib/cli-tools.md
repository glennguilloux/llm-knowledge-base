---
id: "python-stdlib-cli-tools"
title: "CLI Tools with argparse and click"
language: "python"
category: "stdlib"
tags: ["cli", "argparse", "click", "command-line", "arguments", "options", "subcommands"]
version: "3.10+"
retrieval_hint: "CLI command line argparse click arguments options subcommands terminal"
last_verified: "2026-05-24"
confidence: "high"
---

# CLI Tools with argparse and click

## When to Use
- Building command-line utilities and scripts
- Creating developer tools with subcommands (git-style)
- Processing command-line arguments with validation
- Building CLI entry points for Python packages

## Standard Pattern

```python
import argparse
import sys
from pathlib import Path

import click


# --- argparse (stdlib, no dependencies) ---
def build_argparser() -> argparse.ArgumentParser:
    """Build argument parser for a file processor."""
    parser = argparse.ArgumentParser(
        description="Process files in a directory",
        prog="file-processor",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory to process",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("output"),
        help="Output directory (default: output)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "text"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=100,
        help="Maximum number of files to process",
    )
    return parser


def main_argparse() -> None:
    """Entry point using argparse."""
    parser = build_argparser()
    args = parser.parse_args()

    if not args.directory.is_dir():
        parser.error(f"{args.directory} is not a directory")

    if args.verbose:
        print(f"Processing {args.directory}...")

    # Process files...
    files = list(args.directory.glob("*"))[: args.max_files]
    for f in files:
        if args.verbose:
            print(f"  Processing {f.name}")


# --- click (third-party, more ergonomic) ---
@click.group()
@click.version_option(version="1.0.0")
def cli() -> None:
    """File processor CLI tool."""
    pass


@cli.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--output", "-o", type=click.Path(path_type=Path), default="output")
@click.option("--format", "-f", type=click.Choice(["json", "csv", "text"]), default="json")
@click.option("--max-files", type=int, default=100, help="Max files to process")
def process(directory: Path, verbose: bool, output: Path, format: str, max_files: int) -> None:
    """Process files in a directory."""
    if verbose:
        click.echo(f"Processing {directory}...")

    files = list(directory.glob("*"))[:max_files]
    for f in files:
        if verbose:
            click.echo(f"  Processing {f.name}")


@cli.command()
@click.argument("filename", type=click.Path(exists=True, path_type=Path))
def validate(filename: Path) -> None:
    """Validate a file."""
    click.echo(f"Validating {filename}...")
    # Validation logic here


# --- Subcommands with click ---
@cli.group()
def db() -> None:
    """Database management commands."""
    pass


@db.command()
@click.option("--seed", is_flag=True, help="Seed with sample data")
def migrate(seed: bool) -> None:
    """Run database migrations."""
    click.echo("Running migrations...")
    if seed:
        click.echo("Seeding data...")


@db.command()
def reset() -> None:
    """Reset database."""
    click.confirm("Are you sure?", abort=True)
    click.echo("Resetting database...")


# Entry point for pyproject.toml:
# [project.scripts]
# my-tool = "my_package.cli:cli"
```

## Common Mistakes

```python
# WRONG: Using sys.argv directly
import sys
if sys.argv[1] == "--verbose":  # Fragile, no help, no validation
    verbose = True

# CORRECT: Use argparse or click
parser = argparse.ArgumentParser()
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()

# WRONG: Not handling missing required arguments
parser.add_argument("filename")  # Crashes with unhelpful error if missing

# CORRECT: argparse handles this automatically with a good error message
parser.add_argument("filename", type=Path, help="File to process")

# WRONG: Mixing argument parsing with business logic
def main():
    args = argparse.ArgumentParser().parse_args()
    if args.command == "process":
        process_files(args.dir)  # All logic in one function
    elif args.command == "validate":
        validate_file(args.file)

# CORRECT: Use click groups for subcommands
@cli.group()
def cmd(): pass

@cmd.command()
def process(): ...

@cmd.command()
def validate(): ...

# WRONG: Not using type conversion
parser.add_argument("--count")  # args.count is a string
result = args.count * 2  # "55" not 10!

# CORRECT: Specify type
parser.add_argument("--count", type=int)  # args.count is int
```

## Gotchas
- `argparse` is in the stdlib; `click` requires `pip install click` but is more ergonomic
- `click.Path(exists=True)` validates the path exists before the function runs
- `argparse` subparsers use `add_subparsers()`; `click` uses `@group` and `@group.command()`
- `click.confirm()` prompts the user for yes/no — useful for destructive operations
- `type=click.Choice(...)` restricts values; `argparse` uses `choices=[...]`
- Both frameworks auto-generate `--help` output
- Use `@click.pass_context` to pass shared state between click commands

## Related
- python/stdlib/env-config.md
- python/stdlib/subprocess.md
