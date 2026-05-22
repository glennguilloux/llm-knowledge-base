"""MCP Server for LLM Knowledge Base.

Expose knowledge base retrieval as MCP tools that any MCP client can call.

Usage:
  # Configure in claude_desktop_config.json:
  {
    "mcpServers": {
      "llm-kb": {
        "command": "python",
        "args": ["-m", "llm_kb.mcp_server"]
      }
    }
  }
"""

from mcp.server.fastmcp import FastMCP
from llm_kb import retrieve, build_prompt, get_stats
from llm_kb.retrieve import load_entries
from llm_kb.profiles import get_profile, list_models, describe_profile

# Create FastMCP server
mcp = FastMCP("LLM-KB")


@mcp.tool()
def search_knowledge(query: str, language: str | None = None, top_k: int = 3) -> list[dict]:
    """Search for relevant coding patterns within the knowledge base.
    
    Args:
        query: Natural language query (e.g., "how to hash a file in Python")
        language: Filter by language (optional)
        top_k: Number of entries to return (default: 3)
    """
    return retrieve(query, language=language, top_k=top_k)


@mcp.tool()
def build_code_prompt(
    query: str,
    language: str | None = None,
    max_tokens: int = 4096,
    model: str | None = None,
) -> str:
    """Build a system prompt optimized for the specified model.

    Automatically adjusts retrieval count, entry detail level, and
    system prompt verbosity based on model capabilities.

    Args:
        query: What code you want to build (e.g., "write a REST API")
        language: Target programming language
        max_tokens: Context window size
        model: Model name (e.g., "qwen2.5-coder:32b") for auto-profiling
    """
    return build_prompt(query, language=language, max_tokens=max_tokens, model=model)


@mcp.tool()
def list_languages() -> list[str]:
    """List all programming languages covered in the knowledge base."""
    stats = get_stats()
    return stats["languages"]


@mcp.tool()
def get_entry(entry_id: str) -> dict | None:
    """Get a specific knowledge base entry by ID.

    Args:
         entry_id: The ID of the entry (e.g., "python-stdlib-hashlib-sha256")
    """
    entries = load_entries()
    for e in entries:
        if e.id == entry_id:
            return {
                "id": e.id,
                "title": e.title,
                "language": e.language,
                "category": e.category,
                "tags": e.tags,
                "content": e.content,
            }
    return None


@mcp.tool()
def get_model_profile(model_name: str | None = None, size_hint: str | None = None) -> dict:
    """Get the profile settings for a model.

    Args:
        model_name: Model name (e.g., "qwen2.5-coder:32b")
        size_hint: One of "small", "medium", "large"

    Returns:
        Dict with: name, params_range, default_context, max_entries,
        entry_mode, includes, excludes
    """
    profile = get_profile(model_name=model_name, size_hint=size_hint)
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

    return {
        "name": profile.name,
        "params_range": f"{profile.min_params_b:.0f}-{profile.max_params_b:.0f}B",
        "default_context": profile.default_context,
        "max_entries": profile.max_entries,
        "entry_mode": profile.entry_mode,
        "max_entry_tokens": profile.max_entry_tokens,
        "includes": includes,
        "excludes": excludes,
    }


@mcp.tool()
def list_supported_models() -> list[dict]:
    """List all known models and their profile assignments."""
    return list_models()


if __name__ == "__main__":
    # Start FastMCP server
    mcp.run()
