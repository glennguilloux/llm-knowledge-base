"""
Model profiles that control retrieval behavior and prompt formatting.

Different model sizes need different knowledge delivery strategies:
- 7B:   Needs exhaustive examples, every import, all mistakes spelled out
- 14B:  Similar to 7B but can handle slightly denser information
- 27B:  Knows standard APIs. Needs library-specific patterns and gotchas only.
- 32B+: Can handle condensed multi-topic context. Optimize for breadth over depth.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProfile:
    """Configuration that controls how knowledge is retrieved and formatted for a model size."""
    name: str
    min_params_b: float
    max_params_b: float
    default_context: int          # Default context window tokens
    max_entries: int              # Max entries to retrieve
    entry_mode: str               # "full" | "condensed" | "reference"
    include_mistakes: bool        # Include WRONG/CORRECT pairs?
    include_gotchas: bool         # Include Gotchas section?
    include_when_to_use: bool     # Include When to Use section?
    include_real_world: bool      # Include Real-World Example section?
    max_entry_tokens: int         # Max tokens per entry after formatting
    prioritize: list[str]         # What to prioritize in retrieval


PROFILES: dict[str, ModelProfile] = {
    "small": ModelProfile(
        name="small",
        min_params_b=0,
        max_params_b=14,
        default_context=4096,
        max_entries=3,
        entry_mode="full",
        include_mistakes=True,
        include_gotchas=True,
        include_when_to_use=True,
        include_real_world=False,     # Too long for 4K context
        max_entry_tokens=1500,
        prioritize=["exact_patterns", "common_mistakes"],
    ),
    "medium": ModelProfile(
        name="medium",
        min_params_b=14,
        max_params_b=32,
        default_context=8192,
        max_entries=5,
        entry_mode="condensed",
        include_mistakes=True,
        include_gotchas=True,
        include_when_to_use=False,    # 27B knows when to use things
        include_real_world=True,
        max_entry_tokens=800,
        prioritize=["gotchas", "version_specific", "integration_patterns"],
    ),
    "large": ModelProfile(
        name="large",
        min_params_b=32,
        max_params_b=999,
        default_context=16384,
        max_entries=8,
        entry_mode="reference",
        include_mistakes=False,        # Large models don't need this
        include_gotchas=True,
        include_when_to_use=False,
        include_real_world=False,
        max_entry_tokens=400,
        prioritize=["breadth", "cross_system", "advanced_patterns"],
    ),
}


# Common model name → profile mapping
MODEL_MAP: dict[str, str] = {
    # Small (7-14B)
    "qwen2.5-coder:7b": "small",
    "qwen2.5-coder:7b-instruct": "small",
    "codellama:7b": "small",
    "codellama:7b-instruct": "small",
    "codellama:13b": "small",
    "codellama:13b-instruct": "small",
    "deepseek-coder:6.7b": "small",
    "deepseek-coder:6.7b-instruct": "small",
    "starcoder2:7b": "small",
    "starcoder2:3b": "small",
    "starcoder2:15b": "small",
    "phi-3:14b": "small",
    "phi-3:mini": "small",
    "qwen2.5-coder:14b": "small",
    "qwen2.5-coder:14b-instruct": "small",
    "granite-code:8b": "small",

    # Medium (16-35B) — THE NEW TARGET
    "qwen2.5-coder:32b": "medium",
    "qwen2.5-coder:32b-instruct": "medium",
    "command-r:35b": "medium",
    "mixtral:8x7b": "medium",
    "mixtral:8x7b-instruct": "medium",
    "yi-coder:34b": "medium",
    "codestral:22b": "medium",
    "codestral-mamba:7b": "medium",   # Mamba architecture, strong at code
    "deepseek-coder-v2:16b": "medium",   # MoE, effective params ~32B
    "qwq:32b": "medium",
    "qwq:32b-preview": "medium",
    "gemma-2:27b": "medium",

    # Large (70B+)
    "llama3.1:70b": "large",
    "llama3.1:70b-instruct": "large",
    "llama3.3:70b": "large",
    "llama3.3:70b-instruct": "large",
    "qwen2.5:72b": "large",
    "qwen2.5:72b-instruct": "large",
    "deepseek-coder-v2:236b": "large",
    "codellama:70b": "large",
    "codellama:70b-instruct": "large",
    "command-r-plus:104b": "large",
}


def get_profile(model_name: str | None = None, size_hint: str | None = None) -> ModelProfile:
    """Get the appropriate model profile.

    Args:
        model_name: Model name (e.g., "qwen2.5-coder:32b")
        size_hint: One of "small", "medium", "large"

    If neither provided, defaults to "small" (safest).

    Returns:
        ModelProfile for the given model or hint.
    """
    if model_name and model_name.lower() in MODEL_MAP:
        return PROFILES[MODEL_MAP[model_name.lower()]]
    if size_hint and size_hint in PROFILES:
        return PROFILES[size_hint]
    return PROFILES["small"]


def list_models() -> list[dict]:
    """List all known models and their profiles.

    Returns:
        List of dicts with model_name, profile, and profile details.
    """
    result = []
    for model_name, profile_name in sorted(MODEL_MAP.items()):
        profile = PROFILES[profile_name]
        result.append({
            "model": model_name,
            "profile": profile_name,
            "params_range": f"{profile.min_params_b:.0f}-{profile.max_params_b:.0f}B",
            "context": profile.default_context,
            "max_entries": profile.max_entries,
            "entry_mode": profile.entry_mode,
        })
    return result


def describe_profile(profile: ModelProfile) -> str:
    """Get a human-readable description of a profile's settings."""
    includes = []
    excludes = []
    if profile.include_mistakes:
        includes.append("mistakes")
    else:
        excludes.append("mistakes")
    if profile.include_gotchas:
        includes.append("gotchas")
    else:
        excludes.append("gotchas")
    if profile.include_when_to_use:
        includes.append("when-to-use")
    else:
        excludes.append("when-to-use")
    if profile.include_real_world:
        includes.append("real-world examples")
    else:
        excludes.append("real-world examples")

    lines = [
        f"Profile: {profile.name} ({profile.min_params_b:.0f}-{profile.max_params_b:.0f}B parameters)",
        f"Context: {profile.default_context} tokens",
        f"Max entries: {profile.max_entries}",
        f"Mode: {profile.entry_mode}",
        f"Includes: {', '.join(includes) if includes else '(none beyond core)'}",
    ]
    if excludes:
        lines.append(f"Excludes: {', '.join(excludes)} (model knows these)")
    if profile.entry_mode == "condensed" and excludes:
        lines.append(f"Note: 27-32B models know standard APIs — only library-specific patterns needed")
    if profile.entry_mode == "reference":
        lines.append(f"Note: 70B+ models need only signatures + gotchas for breadth")

    return "\n".join(lines)
