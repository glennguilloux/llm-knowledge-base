---
id: "python-stdlib-env-config"
title: "Environment Variables and Configuration"
language: "python"
category: "stdlib"
tags: ["environment", "config", "dotenv", "pydantic-settings", "secrets", "12-factor"]
version: "3.10+"
retrieval_hint: "environment variables os.environ getenv dotenv config pydantic-settings"
last_verified: "2026-05-24"
confidence: "high"
---

# Environment Variables and Configuration

## When to Use
- Managing application configuration across environments (dev, staging, prod)
- Loading secrets from environment variables
- Implementing 12-factor app configuration
- Validating configuration at startup

## Standard Pattern

```python
import os
from pathlib import Path

# Reading environment variables
database_url = os.environ["DATABASE_URL"]  # KeyError if missing
debug = os.getenv("DEBUG", "false").lower() == "true"  # With default
port = int(os.getenv("PORT", "8000"))

# Loading .env files with python-dotenv
from dotenv import load_dotenv
load_dotenv()  # Loads .env file into os.environ

# Pydantic Settings (validated configuration)
from pydantic_settings import BaseSettings
from pydantic import Field

class AppSettings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)
    allowed_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

# Usage — validated at creation time
settings = AppSettings()  # Raises ValidationError if required vars missing

# Hierarchical config with defaults
class Config:
    def __init__(self):
        self.debug = self._get_bool("DEBUG", False)
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "5432"))
        self.db_name = os.getenv("DB_NAME", "myapp")
        self.db_url = os.getenv(
            "DATABASE_URL",
            f"postgresql://{self.db_host}:{self.db_port}/{self.db_name}",
        )

    @staticmethod
    def _get_bool(key: str, default: bool) -> bool:
        value = os.getenv(key, str(default))
        return value.lower() in ("true", "1", "yes")

config = Config()
```

## Common Mistakes

```python
# WRONG: Hardcoding secrets in source code
DATABASE_URL = "postgresql://admin:password123@prod-db/myapp"
API_KEY = "sk-1234567890abcdef"  # Exposed in version control!

# CORRECT: Use environment variables
DATABASE_URL = os.environ["DATABASE_URL"]
API_KEY = os.environ["API_KEY"]

# WRONG: Not validating required variables at startup
db_url = os.getenv("DATABASE_URL")  # None — fails later at runtime

# CORRECT: Validate early with clear error
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL environment variable is required")

# WRONG: Committed .env file with secrets
# .env should be in .gitignore

# CORRECT: .env.example with placeholder values
# .env.example:
# DATABASE_URL=postgresql://user:pass@localhost/myapp
# API_KEY=your-api-key-here

# WRONG: Casting without error handling
port = int(os.getenv("PORT"))  # TypeError if PORT is not set or not a number

# CORRECT: Safe casting with defaults
port = int(os.getenv("PORT", "8000"))

# WRONG: Using os.environ for optional values
value = os.environ["OPTIONAL_KEY"]  # KeyError if not set

# CORRECT: Use os.getenv for optional values
value = os.getenv("OPTIONAL_KEY", "default_value")
```

## Gotchas
- `os.environ["KEY"]` raises `KeyError` if missing — use `os.getenv("KEY")` for optional values
- `.env` files should ALWAYS be in `.gitignore` — they contain secrets
- `pydantic-settings` validates configuration at startup — fail fast, not at first request
- Environment variables are always strings — convert to int/bool manually
- `load_dotenv()` does NOT override existing environment variables by default
- Docker/Kubernetes inject environment variables — don't rely on `.env` files in containers
- 12-factor app principle: config lives in the environment, not in code
- `SECRET_KEY` should be at least 32 characters for HMAC/SHA-based signing

## Related
- python/stdlib/file-io.md
- python/web/fastapi/basics.md
- security/web-security-basics.md
