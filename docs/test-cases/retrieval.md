# Retrieval Test Cases

Source: `TEST_CASES` in `test_retrieval_comprehensive.py`.

These are representative cases, not the full catalog. Add rows when a new entry or retrieval behavior needs coverage.

## Evaluation rules

- Each case has a query and one or more expected entry IDs.
- `recall@1` is tracked, but not a hard fail for every case.
- `recall@3` must return at least one expected entry ID.
- `recall@5` must return at least one expected entry ID.
- Overall `recall@3` must stay at or above 80 percent.

## Representative cases

| Area | Query | Expected entry IDs | Case type |
| --- | --- | --- | --- |
| Python stdlib | `SHA-256 file hashing in Python` | `python-stdlib-hashlib-sha256` | Direct keyword |
| Python stdlib | `pathlib file operations` | `python-stdlib-pathlib` | Direct keyword |
| Python stdlib | `Python async await basics` | `python-stdlib-asyncio-basics` | Direct keyword |
| Python web | `FastAPI JWT authentication token` | `python-web-fastapi-auth-jwt` | Direct keyword |
| Python web | `FastAPI middleware CORS` | `python-web-fastapi-middleware`, `python-web-fastapi-cors-static` | Multi-candidate |
| Python web | `FastAPI with JWT auth and pytest testing` | `python-web-fastapi-auth-jwt`, `python-web-fastapi-testing` | Multi-hop |
| TypeScript web | `React hooks useEffect useState` | `typescript-web-react-hooks` | Direct keyword |
| TypeScript stdlib | `TypeScript async Promise await` | `typescript-stdlib-async-patterns` | Sanity retrieval |
| TypeScript web | `Next.js server actions with Zod validation` | `typescript-web-nextjs-server-actions`, `typescript-web-zod-validation` | Multi-hop |
| Go | `Go goroutines concurrency` | `go-concurrency-goroutines` | Direct keyword |
| Rust | `Rust ownership borrowing move` | `rust-stdlib-ownership` | Direct keyword |
| C# | `C# dependency injection IServiceCollection` | `csharp-stdlib-dependency-injection` | Direct keyword |
| Java | `Spring Security JWT authentication` | `java-spring-security-jwt-auth` | Direct keyword |
| Java | `Spring Boot with JPA repository testing` | `java-spring-data-custom-repository`, `java-testing-spring-boot-testing` | Multi-hop |
| Rust | `Axum web server with SQLx database` | `rust-web-axum`, `rust-db-sqlx-patterns` | Multi-hop |
| DB | `PostgreSQL index B-tree GIN` | `db-postgres-indexes`, `db-postgres-indexing-strategies` | Multi-candidate |
| DB | `PostgreSQL JSONB advanced query` | `db-postgres-json-advanced` | Direct keyword |
| DB | `MongoDB aggregation pipeline $group` | `db-mongodb-aggregation` | Direct keyword |
| Redis/cache | `Redis patterns cache aside` | `java-spring-boot-caching`, `python-db-redis-patterns` | Cross-language |
| DevOps | `Docker Compose multi-container` | `devops-docker-compose` | Direct keyword |
| DevOps | `CI caching GitHub Actions npm pip` | `devops-ci-cd-github-actions`, `anti-patterns-ci-no-cache` | Multi-candidate |
| API design | `API versioning strategy` | `anti-patterns-api-versioning-anti-patterns`, `api-design-versioning`, `antipatterns-api` | Multi-candidate |
| Patterns | `health check endpoint liveness` | `patterns-health-checks` | Direct keyword |
| Security | `web security XSS CSRF OWASP` | `security-web-security-basics` | Direct keyword |
| Security | `authentication and authorization JWT` | `python-web-fastapi-auth-jwt`, `crypto-jwt-tokens` | Cross-language |
| Crypto | `JWT token sign verify` | `crypto-jwt-tokens` | Direct keyword |
| Anti-patterns | `make my code faster caching` | `anti-patterns-ci-no-cache` | Vague intent |
| Anti-patterns | `hardcoded secrets API keys in source code` | `anti-patterns-security-hardcoded-secrets` | Direct keyword |
| Performance | `N+1 query ORM eager loading` | `anti-patterns-perf-n-plus-one` | Direct keyword |
| Typo resilience | `fastapi routng endpont` | `python-web-fastapi-basics` | Typo |
| Typo resilience | `pytest fixtrues parametriez` | `python-testing-pytest-basics` | Typo |
| Kotlin | `Kotlin coroutines async flow` | `kotlin-stdlib-coroutines` | Direct keyword |
| PHP | `PHP Laravel routing controller` | `php-web-laravel-basics` | Direct keyword |
| Swift | `Swift optional guard unwrap` | `swift-stdlib-optionals` | Direct keyword |
| Bash | `bash scripting patterns shebang` | `bash-scripting-patterns` | Direct keyword |
| Project docs | `knowledge base integration guide` | `docs/integration-guide.md` | Project doc |

## Notes

- Do not add external LLM calls to these retrieval cases.
- Do not add `/healthz` or `/readyz` checks. This is not a web service.
- Project docs are documented for coverage tracking but are not knowledge entries loaded by `retrieve()`.
- Keep PR-facing retrieval sanity small. Run the full case set only for regression or release checks.
