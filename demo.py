#!/usr/bin/env python3
"""Interactive demo of the LLM Knowledge Base Python API."""

import sys
from pathlib import Path

# Insert package root to path to run demo even pre-installation
sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_kb import retrieve, build_prompt, get_stats


def main():
    print("=" * 60)
    print("LLM Knowledge Base — Python API Demo")
    print("=" * 60)

    # 1. Fetch Stats
    print("\n[1] Fetching Statistics...")
    stats = get_stats()
    print(f"Loaded {stats['total_entries']} curated entries.")
    print(f"Overall Quality Score: {stats['quality_score']}/100")
    print(f"Languages covered ({len(stats['languages'])}): {', '.join(stats['languages'][:7])}...")

    # 2. Search Retrieval
    query = "FastAPI JWT authentication"
    print(f"\n[2] Querying: '{query}'")
    results = retrieve(query, language="python", top_k=1)
    
    if results:
        entry = results[0]
        print(f"Found Entry: {entry['title']} ({entry['id']})")
        print(f"Category: {entry['category']} | Tags: {', '.join(entry['tags'])}")
    else:
        print("No matching entries found.")

    # 3. Dynamic Prompt Generation
    print("\n[3] Generating prompt with budget constraints (max_tokens=4096)...")
    prompt = build_prompt("write a REST API with JWT authorization", language="python", max_tokens=4096)
    
    # Print the first few lines of the prompt
    lines = prompt.splitlines()
    print("-" * 50)
    for line in lines[:20]:
        print(line)
    print("...")
    print("-" * 50)
    print(f"Generated complete prompt ({len(prompt)} chars). Ready to feed into your LLM!")
    print("\nDone! Try running 'llm-kb --help' for the CLI commands.")


if __name__ == "__main__":
    main()
