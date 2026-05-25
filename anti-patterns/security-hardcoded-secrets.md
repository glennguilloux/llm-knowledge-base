---
id: "anti-patterns-security-hardcoded-secrets"
title: "Security Anti-Pattern: Hardcoded Secrets in Source Code"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "security", "secrets", "api-keys", "credentials", "git-secrets"]
version: "n/a"
retrieval_hint: "hardcoded secrets API keys passwords tokens in source code environment variables vault"
last_verified: "2026-05-24"
confidence: "high"
---

# Security Anti-Pattern: Hardcoded Secrets in Source Code

## When to Use
- Code reviews checking for leaked credentials
- Training LLMs to handle secrets properly
- Setting up pre-commit hooks and CI secret scanning
- Migrating from hardcoded config to secret management

## Standard Pattern

```python
# WRONG: Hardcoded API key in source
API_KEY = "sk-1234567890abcdef1234567890abcdef"
DATABASE_URL = "postgresql://admin:p@ssw0rd@db.example.com/prod"

# CORRECT: Environment variables with validation
import os
API_KEY = os.environ["API_KEY"]  # Fails fast if missing
DATABASE_URL = os.environ["DATABASE_URL"]

# CORRECT: Using python-dotenv for local dev
from dotenv import load_dotenv
load_dotenv()  # Loads .env file (must be in .gitignore)
API_KEY = os.environ["API_KEY"]
```

```javascript
// WRONG: Hardcoded secret in config module
const config = {
  stripeKey: "REPLACE_WITH_ENV_VAR",
  jwtSecret: "my-super-secret-key-123",
  dbPassword: "production-password-here"
};

// CORRECT: Read from environment
const config = {
  stripeKey: process.env.STRIPE_KEY,
  jwtSecret: process.env.JWT_SECRET,
  dbPassword: process.env.DB_PASSWORD
};
```

```yaml
# WRONG: Secrets in docker-compose.yml
services:
  app:
    environment:
      - DATABASE_URL=postgresql://admin:p@ssw0rd@db/prod
      - API_KEY=sk-1234567890abcdef

# CORRECT: Reference external secrets
services:
  app:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY}
    # Or use Docker secrets:
    secrets:
      - db_password
secrets:
  db_password:
    file: ./secrets/db_password.txt
```

```java
// WRONG: Hardcoded in properties file (committed to git)
// application.properties
// spring.datasource.password=productionpassword
// stripe.api.key=sk-demo-replace-with-env-var

// CORRECT: Use environment variables or vault
// application.properties
// spring.datasource.password=${DB_PASSWORD}
// spring.config.import=optional:vault://

@Configuration
public class VaultConfig {
    // HashiCorp Vault, AWS Secrets Manager, etc.
}
```

```bash
# WRONG: Password in script
#!/bin/bash
mysqldump -u root -p"SuperSecret123" mydb > backup.sql
curl -H "Authorization: Bearer sk-1234567890" https://api.example.com

# CORRECT: Use environment or secret files
#!/bin/bash
mysqldump -u root -p"${DB_PASSWORD}" mydb > backup.sql
curl -H "Authorization: Bearer ${API_KEY}" https://api.example.com
```

## Common Mistakes
Hardcoded secrets are the most common and most dangerous security anti-pattern. Developers put API keys, database passwords, and tokens directly in source code for convenience, then commit them to version control. Even if removed later, the secret persists in git history. Automated scanners like truffleHog, git-secrets, and GitHub secret scanning catch these in CI, but the best prevention is never committing them in the first place. Use environment variables for local development, secret managers (HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager) for production, and pre-commit hooks to block accidental commits.

## Gotchas
- Removing a secret from code does NOT remove it from git history — rotate the secret immediately if committed
- `.env` files must be in `.gitignore` BEFORE the first commit — adding them after still leaves them in history
- Docker image layers cache secrets — use multi-stage builds or build-time secrets (`--secret` flag)
- CI/CD logs may print environment variables — use masked/secret variables in GitHub Actions, GitLab CI
- Base64 encoding is NOT encryption — scanners detect `base64` encoded secrets too
- `git-secrets` (AWS tool) and `truffleHog` scan history; pre-commit hooks only catch new commits
- Private repositories are NOT safe — breaches, forks, and access changes expose hardcoded secrets
- API keys in frontend JavaScript are visible to every user — never put secrets in client-side code

## Related
- anti-patterns/docker-antipatterns.md
- security/web-security-basics.md
- python/stdlib/env-config.md
- anti-patterns/security-error-info-leak.md
- patterns/secret-management.md
