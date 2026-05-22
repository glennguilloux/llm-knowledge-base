#!/usr/bin/env python3
"""Context Window Budget Calculator.

Calculate how many knowledge base entries fit in a model's context window,
given query size, system prompt overhead, and entry token counts.

Usage:
    python scripts/context_budget.py
    python scripts/context_budget.py --model-context 8192 --query "write a FastAPI endpoint"
    python scripts/context_budget.py --model-context 16384 --top-k 5
"""

import argparse
import sys
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from retrieval import load_entries, search, KBEntry


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough: ~4 chars per token for English/code)."""
    return len(text) // 4


def estimate_entry_tokens(entry: KBEntry) -> int:
    """Estimate tokens for a single knowledge entry."""
    return estimate_tokens(entry.content)


def calculate_budget(
    model_context: int = 8192,
    query_tokens: int = 200,
    system_prompt_tokens: int = 300,
    response_reserve: int = 1024,
    top_k: int = 5,
    query: str | None = None,
    kb_path: Path = Path("."),
) -> dict:
    """Calculate context window budget.

    Returns a dict with:
    - total_budget: model context window
    - overhead: system prompt + query + response reserve
    - available_for_knowledge: tokens left for entries
    - entries: list of (entry, tokens) that fit
    - entries_fit: how many entries fit
    - budget_report: formatted string
    """
    entries = load_entries(kb_path)

    if query:
        results = search(query, top_k=top_k, kb_path=kb_path)
    else:
        # Use entries sorted by confidence
        results = entries[:top_k]

    overhead = system_prompt_tokens + query_tokens + response_reserve
    available = model_context - overhead

    fitted = []
    used = 0

    for entry in results:
        entry_tokens = estimate_entry_tokens(entry)
        if used + entry_tokens <= available:
            fitted.append((entry, entry_tokens))
            used += entry_tokens
        else:
            # Try condensed version
            condensed = extract_condensed(entry)
            condensed_tokens = estimate_tokens(condensed)
            if used + condensed_tokens <= available:
                fitted.append((entry, condensed_tokens))
                used += condensed_tokens

    budget_report = format_report(
        model_context=model_context,
        query_tokens=query_tokens,
        system_prompt_tokens=system_prompt_tokens,
        response_reserve=response_reserve,
        overhead=overhead,
        available=available,
        used=used,
        fitted=fitted,
        total_entries=len(entries),
    )

    return {
        "total_budget": model_context,
        "overhead": overhead,
        "available_for_knowledge": available,
        "used_for_knowledge": used,
        "remaining": available - used,
        "entries": fitted,
        "entries_fit": len(fitted),
        "budget_report": budget_report,
    }


def extract_condensed(entry: KBEntry) -> str:
    """Extract condensed version: Standard Pattern + Gotchas only."""
    import re
    content = entry.content

    parts = []
    # Get title
    title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
    if title_match:
        parts.append(f"# {title_match.group(1)}")

    # Get Standard Pattern section
    sp_match = re.search(r"## Standard Pattern\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if sp_match:
        parts.append("## Standard Pattern\n" + sp_match.group(1).strip())

    # Get Gotchas section
    g_match = re.search(r"## Gotchas\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if g_match:
        parts.append("## Gotchas\n" + g_match.group(1).strip())

    return "\n\n".join(parts)


def format_report(
    model_context: int,
    query_tokens: int,
    system_prompt_tokens: int,
    response_reserve: int,
    overhead: int,
    available: int,
    used: int,
    fitted: list[tuple[KBEntry, int]],
    total_entries: int,
) -> str:
    """Format a human-readable budget report."""
    lines = []
    lines.append("=" * 60)
    lines.append("CONTEXT WINDOW BUDGET REPORT")
    lines.append("=" * 60)
    lines.append(f"Model context window:    {model_context:>6} tokens")
    lines.append(f"System prompt:           {system_prompt_tokens:>6} tokens")
    lines.append(f"Query (estimated):       {query_tokens:>6} tokens")
    lines.append(f"Response reserve:        {response_reserve:>6} tokens")
    lines.append(f"{'─'*40}")
    lines.append(f"Total overhead:          {overhead:>6} tokens")
    lines.append(f"Available for knowledge: {available:>6} tokens")
    lines.append(f"{'─'*40}")

    if fitted:
        lines.append(f"\nRetrieved entries ({len(fitted)} of {total_entries} total):")
        for i, (entry, tokens) in enumerate(fitted, 1):
            lines.append(f"  {i}. [{tokens:>5} tok] {entry.title} ({entry.id})")
        lines.append(f"{'─'*40}")
        lines.append(f"Knowledge tokens used:   {used:>6}")
        lines.append(f"Remaining budget:        {available - used:>6}")
    else:
        lines.append("\nNo entries fit in the budget!")

    # Budget utilization
    if available > 0:
        util = used / available * 100
        lines.append(f"\nBudget utilization: {util:.0f}%")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Context Window Budget Calculator")
    parser.add_argument("--model-context", type=int, default=8192,
                        help="Model context window in tokens (default: 8192)")
    parser.add_argument("--query", type=str, default=None,
                        help="User query to retrieve entries for")
    parser.add_argument("--query-tokens", type=int, default=200,
                        help="Estimated query token count (default: 200)")
    parser.add_argument("--system-tokens", type=int, default=300,
                        help="System prompt token count (default: 300)")
    parser.add_argument("--response-reserve", type=int, default=1024,
                        help="Tokens to reserve for response (default: 1024)")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Number of entries to retrieve (default: 5)")
    parser.add_argument("--kb-path", type=str, default=".",
                        help="Path to knowledge base root")

    args = parser.parse_args()

    result = calculate_budget(
        model_context=args.model_context,
        query_tokens=args.query_tokens,
        system_prompt_tokens=args.system_tokens,
        response_reserve=args.response_reserve,
        top_k=args.top_k,
        query=args.query,
        kb_path=Path(args.kb_path),
    )

    print(result["budget_report"])

    # Also show common context sizes
    if not args.query:
        print("\n" + "=" * 60)
        print("QUICK REFERENCE: Entries fitting by context size")
        print("=" * 60)
        entries = load_entries(Path(args.kb_path))
        avg_tokens = sum(estimate_entry_tokens(e) for e in entries) / len(entries)
        for ctx in [2048, 4096, 8192, 16384, 32768, 65536, 131072]:
            avail = ctx - args.system_tokens - args.query_tokens - args.response_reserve
            max_entries = max(0, int(avail / avg_tokens))
            print(f"  {ctx:>7} tokens → ~{max_entries} entries (avg {avg_tokens:.0f} tok/entry)")
        print("=" * 60)


if __name__ == "__main__":
    main()
