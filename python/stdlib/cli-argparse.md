---
id: "python-stdlib-cli-argparse"
title: "CLI Tools with argparse and click"
language: "python"
category: "stdlib"
tags: ["cli", "argparse", "click", "command-line", "argument-parsing"]
version: "3.10+"
retrieval_hint: "CLI argparse click command line arguments subcommands"
last_verified: "2026-05-22"
confidence: "high"
---

# CLI Tools with argparse and click

## When to Use
- Building command-line tools and scripts
- Parsing user input from terminal
- Creating tools with subcommands (git-style)
- Need help text and usage generation

## Standard Pattern

```python
# argparse (stdlib — no dependencies)
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Process some files")
    parser.add_argument("input", help="Input file path")
    parser.add_argument("-o", "--output", default="output.txt", help="Output file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--format", choices=["json", "csv", "text"], default="json")
    parser.add_argument("-n", "--count", type=int, default=10, help="Number of items")

    args = parser.parse_args()
    if args.verbose:
        print(f"Processing {args.input} -> {args.output}")
    # ... process ...

# Subcommands with argparse
def cli():
    parser = argparse.ArgumentParser(description="My tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create subcommand
    create = subparsers.add_parser("create", help="Create a resource")
    create.add_argument("name", help="Resource name")
    create.add_argument("--type", default="default")

    # list subcommand
    list_cmd = subparsers.add_parser("list", help="List resources")
    list_cmd.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()
    if args.command == "create":
        create_resource(args.name, args.type)
    elif args.command == "list":
        list_resources(args.limit)

# click (pip install click — more ergonomic)
import click

@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

@cli.command()
@click.argument("name")
@click.option("--type", "-t", default="default", help="Resource type")
@click.pass_context
def create(ctx, name, type):
    if ctx.obj["verbose"]:
        click.echo(f"Creating {type}: {name}")
    click.echo(f"Created {name}")

@cli.command()
@click.option("--limit", "-n", default=50, help="Max items to show")
def list(limit):
    for i in range(limit):
        click.echo(f"Item {i}")

if __name__ == "__main__":
    cli()
```

## Common Mistakes

```python
# WRONG: Using sys.argv directly
if sys.argv[1] == "--help":  # Fragile, no validation
    print("Usage: ...")

# CORRECT: Use argparse
parser = argparse.ArgumentParser()
args = parser.parse_args()  # Handles --help, errors, validation

# WRONG: Not providing help text
parser.add_argument("-f")  # User has no idea what -f does

# CORRECT: Always add help
parser.add_argument("-f", "--format", help="Output format (json, csv, text)")

# WRONG: Mixing business logic with argument parsing
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    args = parser.parse_args()
    # 200 lines of business logic here...

# CORRECT: Separate parsing from logic
def main():
    args = parse_args()
    process(args.input)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    return parser.parse_args()

def process(input_path: str):
    # Business logic here
    pass
```

## Gotchas
- `argparse` generates `--help` automatically — don't implement your own
- `action="store_true"` defaults to `False` when flag is absent
- `choices` restricts values and provides error messages automatically
- `click` uses decorators for cleaner syntax — but adds a dependency
- `click.argument` is positional, `click.option` is optional
- `click.Path(exists=True)` validates file existence
- `argparse` subcommands need `dest="command"` on `add_subparsers` to dispatch
- `click.echo` handles encoding issues better than `print`
- `@click.pass_context` passes the click Context object to the command

## Related
- python/stdlib/subprocess.md
- python/stdlib/env-config.md
- python/stdlib/file-io.md
