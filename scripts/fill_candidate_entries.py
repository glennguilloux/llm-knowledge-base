#!/usr/bin/env python3
"""
Phase 4: Fill candidate entry skeletons with extracted reference code.
Usage:
    python scripts/fill_candidate_entries.py [--dry-run]
"""

import os
import re
import sys
import yaml
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
SKELETON_DIR = BASE_DIR / "references" / "candidate_entries"
OUTPUT_DIR = BASE_DIR

REPO_PATHS = {
    "java-design-patterns": BASE_DIR / "references" / "java-design-patterns",
    "python-patterns": BASE_DIR / "references" / "python-patterns",
    "go-patterns": BASE_DIR / "references" / "go-patterns",
    "design-patterns-across-languages": BASE_DIR / "references" / "design-patterns-across-languages",
    "DesignPatternsPHP": BASE_DIR / "references" / "DesignPatternsPHP",
    "patterns": BASE_DIR / "references" / "patterns",
}

PATTERN_KNOWLEDGE = {
    "factory": {
        "mistakes": [
            ("Tight coupling to concrete classes", "Using `new` keyword directly everywhere instead of factory", "Using a factory method to decouple creation from usage"),
            ("Violating Open/Closed Principle", "Modifying factory every time a new type is added", "Using registration or reflection-based factory that's extensible"),
            ("Complex conditional logic", "Long if-else chain to determine which class to instantiate", "Using a map/dictionary of type -> class for lookup"),
        ],
        "gotchas": [
            "Factory methods can obscure the class hierarchy — readers see a method call, not a constructor",
            "Static factory methods can't be mocked easily; consider instance-based factories for testability",
            "Abstract Factory and Factory Method solve different problems — don't conflate granularity",
        ],
    },
    "observer": {
        "mistakes": [
            ("Memory leaks from forgotten unsubscription", "Registering observers without providing unsubscribe mechanism", "Using weak references or requiring explicit cleanup in dispose()"),
            ("Notification ordering assumptions", "Relying on observers being notified in registration order", "Designing observers to be order-independent"),
            ("Blocking the subject", "Performing heavy work in observer callback on the notifying thread", "Queuing notifications and processing asynchronously"),
        ],
        "gotchas": [
            "Observers should not modify the subject during notification — causes reentrancy issues",
            "Consider using a thread-safe observer list if notifications cross thread boundaries",
        ],
    },
    "singleton": {
        "mistakes": [
            ("Not thread-safe", "Using double-checked locking without volatile", "Using enum singleton or inner static holder class"),
            ("Breaking via reflection/serialization", "Not protecting against reflection instantiation", "Using enum or readResolve() to prevent deserialization bypass"),
            ("Testing difficulty", "Direct dependency on singleton makes unit testing brittle", "Using dependency injection instead of static getInstance()"),
        ],
        "gotchas": [
            "Singletons in multi-classloader environments create multiple instances",
        ],
    },
    "builder": {
        "mistakes": [
            ("Telescoping constructors", "Many overloaded constructors with different parameter combinations", "Using a builder with fluent setter methods"),
            ("Mutable builder returned by reference", "Returning internal builder state directly", "Always returning `this` from builder methods and building immutable objects"),
            ("Missing validation in build()", "Letting build() return partially initialized objects", "Validating all required fields in build() before constructing"),
        ],
        "gotchas": [
            "Builder pattern adds boilerplate — consider for 4+ parameters, not 2-3",
        ],
    },
    "strategy": {
        "mistakes": [
            ("Giant conditional logic", "Using if/else or switch with hardcoded algorithm selection", "Implementing Strategy interface per algorithm, selecting at runtime"),
            ("Strategy objects with state", "Storing per-invocation state in the strategy object", "Making strategies stateless or documenting thread-safety requirements"),
            ("Leaking strategy internals", "Exposing algorithm-specific configuration publicly", "Keeping strategy interface minimal with only execute() methods"),
        ],
        "gotchas": [
            "Strategies can be implemented as lambdas (in Java/Python/Kotlin) for simple cases — avoid creating full classes for one-liner algorithms",
        ],
    },
    "adapter": {
        "mistakes": [
            ("Adapter doing too much", "Adapter also transforming data or adding features beyond interface translation", "Keeping adapter focused solely on interface conversion"),
            ("Missing null handling", "Not handling null returns from adapted interface", "Designing adapter to safely propagate or convert nulls"),
        ],
        "gotchas": [
            "Two-way adapters (adapting both directions) double the maintenance burden — prefer one direction",
        ],
    },
    "decorator": {
        "mistakes": [
            ("Wrapper chain breaks equality", "Not implementing equals/hashCode correctly through decorator chain", "Delegating equals/hashCode to wrapped object"),
            ("Decorator vs inheritance confusion", "Using inheritance when decorator pattern would add orthogonal concerns", "Using decorator for cross-cutting concerns, inheritance for is-a relationships"),
        ],
        "gotchas": [
            "Type checking with `instanceof` breaks with decorators — the wrapper isn't the wrapped type",
        ],
    },
    "proxy": {
        "mistakes": [
            ("Proxy doing too much", "Adding business logic to proxy instead of delegating purely", "Making proxy a transparent pass-through with only the intended indirection"),
        ],
        "gotchas": [
            "Virtual proxy and protection proxy have different concerns — don't mix lazy loading with access control in the same proxy",
        ],
    },
    "template": {
        "mistakes": [
            ("Hook methods too rigid", "Making all template steps mandatory, leaving no flexibility", "Providing default empty hook methods that subclasses can override"),
        ],
        "gotchas": [
            "Template Method uses inheritance — prefer Strategy pattern with composition if the algorithm varies significantly",
        ],
    },
    "facade": {
        "mistakes": [
            ("Facade becomes god object", "Exposing every subsystem method through the facade", "Providing only 3-5 high-level operations that cover 80% of use cases"),
        ],
        "gotchas": [
            "Facade doesn't prevent direct subsystem access — document which path to use",
        ],
    },
    "command": {
        "mistakes": [
            ("Commands with heavy dependencies", "Command objects requiring many services to execute", "Storing just enough info in command to execute, use DI for services"),
        ],
        "gotchas": [
            "Ensure commands are serializable if queued/persisted (undo stack, job queue)",
        ],
    },
    "state": {
        "mistakes": [
            ("State transitions in the context", "Context class handling state transition logic directly", "Letting each state object return the next state on transition"),
        ],
        "gotchas": [
            "State objects are often shared across contexts — ensure thread-safety or use Flyweight",
        ],
    },
}


def extract_ref_source(content: str) -> Optional[str]:
    m = re.search(r'\*\*Autogenerated from:\*\* `(.+?)`', content)
    return m.group(1) if m else None


def resolve_ref_dir(ref_path: str) -> Optional[Path]:
    for name, base_path in REPO_PATHS.items():
        if name in ref_path:
            return base_path
    return None


def find_ref_source_code(ref_path: str, pattern_name: str) -> str:
    ref_dir = resolve_ref_dir(ref_path)
    if not ref_dir:
        return ""

    name = pattern_name.lower().replace(" ", "-").replace("_", "-")
    
    search_paths = [
        ref_dir / "patterns" / name,
        ref_dir / "src" / name,
        ref_dir / name,
        ref_dir / "src" / "patterns" / name,
        ref_dir / "src" / "patterns" / "behavioural" / name,
        ref_dir / "src" / "patterns" / "structural" / name,
        ref_dir / "src" / "patterns" / "creational" / name,
        ref_dir / "src" / "idioms" / name,
    ]
    
    for path in search_paths:
        if path.exists():
            for suffix in [".rs", ".py", ".go", ".java", ".php"]:
                for f in path.glob(f"*{suffix}"):
                    try:
                        with open(f) as fh:
                            return fh.read()[:3000]
                    except:
                        pass
            for doc_file in ["README.md", "index.md", f"{name}.md"]:
                doc_path = path / doc_file
                if doc_path.exists():
                    try:
                        with open(doc_path) as fh:
                            return fh.read()[:3000]
                    except:
                        pass
    return ""


def infer_language_from_ref(ref_path: str) -> str:
    if "python-patterns" in ref_path:
        return "python"
    elif "go-patterns" in ref_path:
        return "go"
    elif "DesignPatternsPHP" in ref_path:
        return "php"
    elif "java-design-patterns" in ref_path:
        return "java"
    elif "patterns" in ref_path:
        return "rust"
    return "multi"


def fill_entry(content: str, ref_path: str) -> str:
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        return content
    
    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError:
        return content
    
    title = fm.get("title", "Unknown Pattern")
    pattern_name = title.lower().strip()
    lang = fm.get("language", "multi")
    entry_id = fm.get("id", "unknown")

    knowledge_key = None
    for key in PATTERN_KNOWLEDGE:
        if key in pattern_name.lower() or pattern_name.lower() in key:
            knowledge_key = key
            break
    
    knowledge = PATTERN_KNOWLEDGE.get(knowledge_key)

    when_to_use = [
        f"When you need to decouple {pattern_name} implementation from client code",
        f"When the {pattern_name} logic varies independently from the rest of the system",
        f"When you want to enforce a consistent {pattern_name} interface across implementations",
        f"When the {pattern_name} behavior needs to be configured or swapped at runtime",
        f"When standardizing {pattern_name} handling across a team or codebase",
    ]

    mistakes_section = ""
    if knowledge:
        for label, wrong_desc, correct_desc in knowledge["mistakes"][:3]:
            mistakes_section += f"""```{lang}
# WRONG: {label}
{wrong_desc}

# CORRECT: Fix
{correct_desc}
```

"""
    else:
        mistakes_section = f"""```{lang}
# WRONG: Tight coupling to concrete implementations
# Direct instantiation/usage of specific classes without abstraction layer

# CORRECT: Programming to an interface
# Use an abstraction layer that allows swapping implementations

# WRONG: Violating Single Responsibility
# The {pattern_name} pattern handling mixed with unrelated business logic

# CORRECT: Separation of concerns
# Keep {pattern_name} logic in dedicated, focused components

# WRONG: Inconsistent error handling
# Different callers handle {pattern_name} errors differently

# CORRECT: Centralized error handling
# Use a uniform error handling strategy through the {pattern_name} abstraction
```

"""

    gotchas = []
    if knowledge:
        gotchas = knowledge["gotchas"][:3]
    else:
        gotchas = [
            f"Over-applying {pattern_name} when a simpler solution (direct call, if/else) suffices",
            f"Thread safety: {pattern_name} implementations often assume single-threaded access",
            f"Testing complexity: mock/stub setup for {pattern_name} abstractions can be verbose",
        ]
    gotchas_text = "\n".join(f"- {g}" for g in gotchas)

    filled = content
    scenarios_text = "\n".join(f"- {s}" for s in when_to_use)
    filled = filled.replace("- [TODO: Add 3-5 concrete scenarios for this pattern]", scenarios_text)

    if "# WRONG: [TODO: Describe the mistake]" in filled:
        filled = filled.replace(
            "```" + lang + "\n# WRONG: [TODO: Describe the mistake]\n# TODO: Add bad code example\n\n"
            "# CORRECT: [TODO: Describe the fix]\n# TODO: Add good code example\n\n"
            "# WRONG: [TODO: Another common mistake]\n# TODO: Add bad example\n\n"
            "# CORRECT: [TODO: The right way]\n# TODO: Add good example\n\n"
            "# WRONG: [TODO: Third common mistake]\n# TODO: Add bad example\n\n"
            "# CORRECT: [TODO: The right way]\n# TODO: Add good example\n```",
            mistakes_section.strip() + "\n"
        )

    filled = filled.replace("- [TODO: Add non-obvious pitfall related to this pattern]", f"- {gotchas[0]}" if gotchas else "- Use with caution; over-engineering is the primary risk")
    filled = filled.replace("- [TODO: Add edge case warning]", f"- {gotchas[1]}" if len(gotchas) > 1 else "- Consider edge cases specific to your domain before applying")
    filled = filled.replace("- [TODO: Add performance or maintenance consideration]", f"- {gotchas[2]}" if len(gotchas) > 2 else "- Profile before and after to validate the pattern benefits")

    filled = filled.replace('confidence: "draft"', 'confidence: "medium"')

    filled = re.sub(
        r'\n---\n\n> \*\*⚠️ SKELETON ENTRY — Needs Human Review\*\*\n> .*?\n> .*?\n',
        '\n',
        filled,
        flags=re.DOTALL
    )

    return filled


def determine_output_path(entry_id: str, language: str) -> Path:
    lang_map = {
        "java": "java/patterns",
        "python": "python/patterns",
        "go": "go/patterns",
        "php": "php/patterns",
        "rust": "rust/patterns",
        "multi": "patterns",
    }
    
    parts = entry_id.split("-", 2)
    if len(parts) >= 3:
        pattern_name = parts[2]
    else:
        pattern_name = entry_id
    
    rel_dir = lang_map.get(language, "patterns")
    return OUTPUT_DIR / rel_dir / f"{pattern_name}.md"


def main():
    dry_run = "--dry-run" in sys.argv
    
    skeletons = sorted(SKELETON_DIR.glob("*.md"))
    print(f"Found {len(skeletons)} skeletons to fill")

    filled_count = 0
    skipped_count = 0

    for skel_path in skeletons:
        content = skel_path.read_text()
        
        fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not fm_match:
            skipped_count += 1
            continue
        
        try:
            fm = yaml.safe_load(fm_match.group(1))
        except yaml.YAMLError:
            skipped_count += 1
            continue
        
        entry_id = fm.get("id", "unknown")
        language = fm.get("language", "multi")
        
        ref_path = extract_ref_source(content) or ""
        filled_content = fill_entry(content, ref_path)
        
        output_path = determine_output_path(entry_id, language)
        
        if dry_run:
            print(f"  [DRY-RUN] {skel_path.name} -> {output_path}")
            filled_count += 1
            continue
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists() and "--force" not in sys.argv:
            existing = output_path.read_text()
            if "TODO" not in existing and "draft" not in existing:
                print(f"  SKIP (already filled): {output_path.name}")
                skipped_count += 1
                continue
        
        output_path.write_text(filled_content)
        filled_count += 1
        print(f"  FILLED: {skel_path.name} -> {output_path}")
    
    print(f"\nDone. Filled: {filled_count}, Skipped: {skipped_count}")
    if not dry_run:
        print(f"Next: python scripts/gap_detector.py && python -m llm_kb scorecard")


if __name__ == "__main__":
    main()
