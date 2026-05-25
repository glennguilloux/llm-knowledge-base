---
id: "antipatterns-configuration"
title: "Configuration Anti-Patterns: Hardcoded Values, No Environment Separation, and Secrets in Config"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "configuration", "hardcoded", "environment", "secrets", "validation", "defaults"]
version: "n/a"
retrieval_hint: "configuration antipatterns hardcoded values no environment separation config in code no validation no defaults secrets in config files"
last_verified: "2026-05-24"
confidence: "high"
---

# Configuration Anti-Patterns: Hardcoded Values, No Environment Separation, and Secrets in Config

## When to Use
- Reviewing configuration management
- Training LLMs to handle configuration properly
- Setting up application configuration
- Understanding configuration best practices

## Standard Pattern

```python
# === Python Examples ===

# WRONG: Hardcoded values
DATABASE_URL = "postgresql://user:password@localhost:5432/mydb"
API_KEY = "sk-1234567890"
DEBUG = True
MAX_RETRIES = 3

# CORRECT: Use environment variables with defaults
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/mydb")
API_KEY = os.environ["API_KEY"]  # Required — fails fast if missing
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))

# WRONG: No environment separation
# Same config for dev, staging, and production!

# CORRECT: Environment-specific configuration
import os

ENV = os.environ.get("APP_ENV", "development")

if ENV == "production":
    DATABASE_URL = os.environ["DATABASE_URL"]  # Required
    DEBUG = False
    LOG_LEVEL = "WARNING"
elif ENV == "staging":
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://staging:5432/mydb")
    DEBUG = False
    LOG_LEVEL = "INFO"
else:  # development
    DATABASE_URL = "postgresql://localhost:5432/mydb"
    DEBUG = True
    LOG_LEVEL = "DEBUG"

# WRONG: Secrets in config files (committed to Git)
# config.py:
# DATABASE_PASSWORD = "supersecret"
# API_KEY = "sk-1234567890"

# CORRECT: Secrets from environment or secret manager
# config.py:
# DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"]
# API_KEY = os.environ["API_KEY"]

# .env file (in .gitignore):
# DATABASE_PASSWORD=supersecret
# API_KEY=sk-1234567890

# WRONG: No validation (app crashes later with confusing error)
database_url = os.environ.get("DATABASE_URL")
# If None, crashes when trying to connect with confusing error

# CORRECT: Validate configuration at startup
def validate_config():
    required = ["DATABASE_URL", "API_KEY", "REDIS_URL"]
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise SystemExit(f"Missing required config: {', '.join(missing)}")
    print("Configuration validated successfully")

# WRONG: No defaults (app fails to start without all env vars)
debug = os.environ["DEBUG"]  # KeyError if not set!

# CORRECT: Provide sensible defaults
debug = os.environ.get("DEBUG", "false").lower() == "true"
port = int(os.environ.get("PORT", "8080"))
workers = int(os.environ.get("WORKERS", "4"))

# WRONG: Configuration in code (can't change without redeploying)
class Config:
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # Hardcoded!
    ALLOWED_EXTENSIONS = ["jpg", "png"]  # Hardcoded!

# CORRECT: Configuration from environment
class Config:
    MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))
    ALLOWED_EXTENSIONS = os.environ.get("ALLOWED_EXTENSIONS", "jpg,png").split(",")

# WRONG: Using .env file in production
# .env file is for development only!

# CORRECT: Use proper secret management in production
# - Docker secrets
# - Kubernetes secrets
# - AWS Secrets Manager / Parameter Store
# - HashiCorp Vault
# - Azure Key Vault
```

## Common Mistakes
- Hardcoded values — changing config requires code changes and redeployment
- No environment separation — same configuration for dev, staging, and production
- Secrets in config files — committed to Git, visible to anyone with repo access
- No validation — app crashes later with confusing errors instead of failing fast
- No defaults — app fails to start without all environment variables set
- Configuration in code — can't change behavior without redeploying

## Gotchas
- **NEVER** commit secrets to Git. Use environment variables or secret managers.
- Validate configuration at startup. Fail fast with clear error messages.
- Provide sensible defaults for non-critical configuration.
- Use `.env` files for development only. Add `.env` to `.gitignore`.
- In production, use proper secret management (Vault, AWS Secrets Manager, K8s secrets).
- Environment variables are strings. Convert to proper types (int, bool, list).
- Use `os.environ["KEY"]` for required vars (fails fast) and `os.environ.get("KEY", default)` for optional.
- Configuration should be externalized — same code, different configs per environment.
- Use a config library (pydantic-settings, python-decouple) for type-safe configuration.

## Related
- anti-patterns/docker-antipatterns.md
- anti-patterns/git-antipatterns.md
- anti-patterns/error-handling-antipatterns.md
- patterns/secret-management.md
