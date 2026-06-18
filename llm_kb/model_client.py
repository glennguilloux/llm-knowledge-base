"""
LLM invocation abstraction for `llm-kb ask`.

Provides a unified interface for calling Ollama, OpenAI-compatible, and
custom LLM endpoints. Configuration via ~/.config/llm-kb/config.toml
or environment variables.
"""

import os
import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG_DIR = Path.home() / ".config" / "llm-kb"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def _try_load_toml() -> dict:
    """Try to load config.toml using tomllib (stdlib 3.11+) or manual parsing."""
    if not CONFIG_FILE.exists():
        return {}

    try:
        import tomllib
        with open(CONFIG_FILE, "rb") as f:
            return tomllib.load(f)
    except (ImportError, Exception):
        pass

    # Fallback: basic TOML parser (no nested tables, just [section] key = val)
    result: dict = {}
    current_section = "root"
    try:
        text = CONFIG_FILE.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                current_section = stripped[1:-1].strip()
                if current_section not in result:
                    result[current_section] = {}
                continue
            if "=" in stripped:
                key, _, val = stripped.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                target = result
                if current_section != "root":
                    if current_section not in result:
                        result[current_section] = {}
                    target = result[current_section]
                if isinstance(target, dict):
                    target[key] = val
    except Exception:
        pass

    return result


def load_config() -> dict:
    """Load LLM provider configuration.

    Order of precedence (higher wins):
    1. ~/.config/llm-kb/config.toml
    2. Environment variables (LLM_KB_*)
    3. Defaults

    Returns:
        dict with keys: provider, ollama_host, ollama_model, openai_api_key,
        openai_base_url, openai_model, custom_endpoint, custom_api_key, custom_model
    """
    cfg = _try_load_toml()
    llm_section = cfg.get("llm", {}) if isinstance(cfg, dict) else {}

    config = {
        "provider": (
            os.environ.get("LLM_KB_PROVIDER")
            or (llm_section.get("provider") if isinstance(llm_section, dict) else None)
            or "ollama"
        ),
        "ollama_host": (
            os.environ.get("LLM_KB_OLLAMA_HOST")
            or (llm_section.get("ollama_host") if isinstance(llm_section, dict) else None)
            or "http://localhost:11434"
        ),
        "ollama_model": (
            os.environ.get("LLM_KB_OLLAMA_MODEL")
            or (llm_section.get("ollama_model") if isinstance(llm_section, dict) else None)
            or "qwen2.5-coder:7b"
        ),
        "openai_api_key": (
            os.environ.get("LLM_KB_OPENAI_API_KEY")
            or (llm_section.get("openai_api_key") if isinstance(llm_section, dict) else None)
            or ""
        ),
        "openai_base_url": (
            os.environ.get("LLM_KB_OPENAI_BASE_URL")
            or (llm_section.get("openai_base_url") if isinstance(llm_section, dict) else None)
            or "https://api.openai.com/v1"
        ),
        "openai_model": (
            os.environ.get("LLM_KB_OPENAI_MODEL")
            or (llm_section.get("openai_model") if isinstance(llm_section, dict) else None)
            or "gpt-4o-mini"
        ),
        "custom_endpoint": (
            os.environ.get("LLM_KB_CUSTOM_ENDPOINT")
            or (llm_section.get("custom_endpoint") if isinstance(llm_section, dict) else None)
            or ""
        ),
        "custom_api_key": (
            os.environ.get("LLM_KB_CUSTOM_API_KEY")
            or (llm_section.get("custom_api_key") if isinstance(llm_section, dict) else None)
            or ""
        ),
        "custom_model": (
            os.environ.get("LLM_KB_CUSTOM_MODEL")
            or (llm_section.get("custom_model") if isinstance(llm_section, dict) else None)
            or ""
        ),
    }
    return config


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _http_post(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    """Make an HTTP POST, preferring httpx, falling back to urllib."""
    try:
        import httpx
        resp = httpx.post(url, headers=headers, json=body, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except ImportError:
        return _urllib_post(url, headers, body, timeout)
    except Exception as e:
        raise ConnectionError(f"HTTP error: {e}") from e


def _urllib_post(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    """Fallback POST using urllib."""
    import urllib.request
    import urllib.error

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise ConnectionError(f"Connection failed: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise ConnectionError(f"Invalid JSON response: {e}") from e


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------


def ask_ollama(prompt: str, model: str = "qwen2.5-coder:7b", host: str = "http://localhost:11434") -> str:
    """Call Ollama's generate API and return the response text.

    Args:
        prompt: The prompt string to send
        model: Ollama model name (default: qwen2.5-coder:7b)
        host: Ollama server URL (default: http://localhost:11434)

    Returns:
        Response text from the model

    Raises:
        ConnectionError: If Ollama is not reachable

    Example:
        >>> reply = ask_ollama("Write a FastAPI endpoint", model="qwen2.5-coder:7b")
    """
    url = f"{host.rstrip('/')}/api/generate"
    headers = {"Content-Type": "application/json"}
    body = {"model": model, "prompt": prompt, "stream": False}

    try:
        data = _http_post(url, headers, body)
    except ConnectionError as e:
        raise ConnectionError(
            f"Ollama not reachable at {host}. Is it running? (ollama serve)\n"
            f"Caused by: {e}"
        ) from e

    if "response" not in data:
        raise ConnectionError(f"Unexpected Ollama response: {json.dumps(data, indent=2)[:200]}")

    return data["response"]


def ask_openai(
    prompt: str,
    model: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
) -> str:
    """Call an OpenAI-compatible chat completions API.

    Args:
        prompt: The prompt string to send (sent as user message)
        model: Model name (e.g., gpt-4o-mini, deepseek-chat)
        api_key: API key for authentication
        base_url: Base URL for the API (default: https://api.openai.com/v1)

    Returns:
        Response text from the model

    Raises:
        ConnectionError: If the API is not reachable or returns an error
        ValueError: If api_key is empty

    Example:
        >>> reply = ask_openai("Write a FastAPI endpoint", model="gpt-4o-mini",
        ...                    api_key="sk-...")
    """
    if not api_key:
        raise ValueError(
            "OpenAI API key not configured. "
            "Set LLM_KB_OPENAI_API_KEY or add to ~/.config/llm-kb/config.toml"
        )

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        data = _http_post(url, headers, body)
    except ConnectionError as e:
        raise ConnectionError(f"OpenAI-compatible API error at {base_url}:\n{e}") from e

    choices = data.get("choices", [])
    if not choices:
        raise ConnectionError(f"Unexpected API response (no choices): {json.dumps(data, indent=2)[:200]}")

    return choices[0]["message"]["content"]


def ask_custom(
    prompt: str,
    endpoint: str,
    api_key: str = "",
    model: str = "",
) -> str:
    """Call a custom LLM endpoint (generic HTTP POST).

    Sends JSON: {"prompt": prompt, "model": model} and expects
    {"response": "..."} in the response.

    Args:
        prompt: The prompt string to send
        endpoint: Full URL of the custom endpoint
        api_key: Optional Bearer token for authentication
        model: Optional model name to pass in the request body

    Returns:
        Response text from the model

    Raises:
        ConnectionError: If the endpoint is not reachable
    """
    if not endpoint:
        raise ValueError("Custom endpoint URL not configured. Set LLM_KB_CUSTOM_ENDPOINT.")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = {"prompt": prompt}
    if model:
        body["model"] = model

    try:
        data = _http_post(endpoint, headers, body)
    except ConnectionError as e:
        raise ConnectionError(f"Custom endpoint error at {endpoint}:\n{e}") from e

    if "response" not in data and "text" not in data:
        raise ConnectionError(f"Unexpected custom endpoint response: {json.dumps(data, indent=2)[:200]}")

    return data.get("response") or data.get("text", "")


# ---------------------------------------------------------------------------
# High-level ask
# ---------------------------------------------------------------------------


def ask(prompt: str, **kwargs) -> str:
    """High-level ask function that resolves provider from config or kwargs.

    Args:
        prompt: The prompt string to send to the LLM
        **kwargs: Override config values:
            provider: "ollama" (default), "openai", "custom"
            model: Override model name
            host: Ollama host override
            api_key: API key override (openai/custom)
            base_url: Base URL override (openai)
            endpoint: Custom endpoint URL override

    Returns:
        Response text from the LLM

    Raises:
        ValueError: Unknown provider
        ConnectionError: LLM endpoint unreachable

    Example:
        >>> # Use Ollama (default)
        >>> reply = ask("Write a FastAPI endpoint")
        >>>
        >>> # Use OpenAI
        >>> reply = ask("Write a FastAPI endpoint", provider="openai",
        ...             api_key="sk-...", model="gpt-4o-mini")
        >>>
        >>> # Use custom endpoint
        >>> reply = ask("Write a FastAPI endpoint", provider="custom",
        ...             endpoint="http://localhost:8000/generate")
    """
    config = load_config()

    provider = kwargs.get("provider") or config["provider"]

    if provider == "ollama":
        host = kwargs.get("host") or config["ollama_host"]
        model = kwargs.get("model") or config["ollama_model"]
        return ask_ollama(prompt, model=model, host=host)

    elif provider == "openai":
        api_key = kwargs.get("api_key") or config["openai_api_key"]
        base_url = kwargs.get("base_url") or config["openai_base_url"]
        model = kwargs.get("model") or config["openai_model"]
        return ask_openai(prompt, model=model, api_key=api_key, base_url=base_url)

    elif provider == "custom":
        endpoint = kwargs.get("endpoint") or config["custom_endpoint"]
        api_key = kwargs.get("api_key") or config["custom_api_key"]
        model = kwargs.get("model") or config["custom_model"]
        return ask_custom(prompt, endpoint=endpoint, api_key=api_key, model=model)

    else:
        raise ValueError(
            f"Unknown provider: {provider!r}. "
            f"Supported: ollama, openai, custom"
        )
