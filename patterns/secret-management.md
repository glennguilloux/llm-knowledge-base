---
id: "patterns-secret-management"
title: "Secret Management Patterns"
language: "multi"
category: "security"
subcategory: "secrets"
tags: ["secrets", "vault", "env", "encryption", "rotation", "management"]
version: ""
retrieval_hint: "Secret management environment variables vault rotation encryption"
last_verified: "2026-05-22"
confidence: "high"
---

# Secret Management Patterns

## When to Use
- Storing API keys, database credentials, and certificates
- Rotating secrets without redeployment
- Auditing secret access
- Sharing secrets across services and environments

## Standard Pattern

```python
# --- Environment variables (simplest) ---
import os

DATABASE_URL = os.environ["DATABASE_URL"]  # Required — fails if missing
API_KEY = os.environ.get("API_KEY", "")    # Optional with default
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# --- .env file for development (NEVER commit) ---
# .env.example (committed — template)
# DATABASE_URL=postgresql://localhost:5432/mydb
# API_KEY=your-key-here

# .env (gitignored — actual values)
# DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
# API_KEY=sk-abc123

# --- Pydantic settings with validation ---
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    api_key: str
    debug: bool = False

    model_config = {"env_file": ".env"}

settings = Settings()  # Validates at startup
```

```yaml
# --- Docker secrets ---
# docker-compose.yml
# services:
#   app:
#     image: myapp
#     secrets:
#       - db_password
#       - api_key
#     environment:
#       DB_PASSWORD_FILE: /run/secrets/db_password
#
# secrets:
#   db_password:
#     file: ./secrets/db_password.txt
```

```bash
# --- HashiCorp Vault integration ---
# Read secret
vault kv get -field=password secret/myapp/database

# In application
import hvac
client = hvac.Client(url='http://vault:8200')
secret = client.secrets.kv.v2.read_secret_version(path='myapp/database')
db_password = secret['data']['data']['password']
```

## Common Mistakes

```text
# WRONG: Hardcoding secrets in source code
API_KEY = "sk-abc123xyz"  # Committed to git!
DATABASE_URL = "postgres://user:password@host/db"

# CORRECT: Use environment variables
API_KEY = os.environ["API_KEY"]

# WRONG: Committing .env file
git add .env  # Secrets in version control!

# CORRECT: Add .env to .gitignore
echo ".env" >> .gitignore

# WRONG: Passing secrets as command-line arguments
python app.py --api-key=sk-abc123  # Visible in process list!

# CORRECT: Use environment variables or files
export API_KEY=sk-abc123
python app.py

# WRONG: Logging secrets
logger.info(f"Connecting to {database_url}")  # Logs password!

# CORRECT: Log sanitized connection info
logger.info(f"Connecting to {host}:{port}/{database}")
```

## Gotchas
- Never commit secrets to version control — use `.gitignore` and pre-commit hooks
- Use `os.environ["KEY"]` (required) vs `os.environ.get("KEY")` (optional) appropriately
- Rotate secrets regularly — automate with Vault, AWS Secrets Manager, or similar
- Use different secrets per environment (dev, staging, prod)
- Audit secret access — log who accessed what and when
- Prefer short-lived credentials (IAM roles, temporary tokens) over long-lived ones
- Use secret managers (Vault, AWS SM, GCP SM) for production, `.env` for development
- Pre-commit hooks can scan for accidentally committed secrets (e.g., `detect-secrets`)

## Related
- security/web-security-basics.md
- patterns/feature-flags.md
- python/stdlib/env-config.md
