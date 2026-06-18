#!/usr/bin/env python3
"""
[DEPRECATED] Grep-based retrieval for the knowledge base.

⚠️  This module is deprecated. Use `llm_kb.retrieve` instead:
    from llm_kb.retrieve import search, load_entries, KBEntry

The package version (`llm_kb.retrieve`) is the canonical module with
all features including hybrid search, cross-reference boosting, and
result diversification.
"""

import warnings

warnings.warn(
    "retrieval.py is deprecated. Use `llm_kb.retrieve` instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the canonical package module
from llm_kb.retrieve import (  # noqa: F401, F403
    KBEntry,
    get_kb_path,
    load_entries,
    search,
    search_by_keywords,
    search_by_language,
    search_by_tags,
    search_expanded,
    hybrid_search,
    score_cross_reference_boost,
    diversify_results,
)
from llm_kb.retrieve import parse_entry as _package_parse_entry


# Preserve the standalone parse_entry for backward compatibility
def parse_entry(filepath):
    """Parse a knowledge base entry from a markdown file.

    Deprecated: use llm_kb.retrieve.parse_entry instead.
    """
    return _package_parse_entry(filepath)
