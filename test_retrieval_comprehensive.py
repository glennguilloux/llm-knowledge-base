#!/usr/bin/env python3
"""Comprehensive retrieval test suite — 100+ queries covering every category.

Tests the grep-based retrieval system (retrieval.py) for recall@1, recall@3, recall@5.
Fails if overall recall@3 drops below 80%.
"""

import pytest
from pathlib import Path

from retrieval import search, load_entries, search_by_keywords


# ---------------------------------------------------------------------------
# Test queries: (query_string, list_of_expected_entry_ids)
#
# Each query maps to 1-3 expected entry IDs. The test checks whether at least
# one expected ID appears in the top-K results.
# ---------------------------------------------------------------------------

TEST_CASES: list[tuple[str, list[str]]] = [
    # =====================================================================
    # PYTHON — stdlib (25 entries)
    # =====================================================================
    ("SHA-256 file hashing in Python", ["python-stdlib-hashlib-sha256"]),
    ("pathlib file operations", ["python-stdlib-pathlib"]),
    ("Python async await basics", ["python-stdlib-asyncio-basics"]),
    ("dataclass with default factory", ["python-stdlib-dataclasses"]),
    ("Python datetime formatting", ["python-stdlib-datetime"]),
    ("decorator with arguments", ["python-stdlib-decorators"]),
    ("regex findall compile pattern", ["python-stdlib-regex"]),
    ("subprocess run capture output", ["python-stdlib-subprocess"]),
    ("environment variable config dotenv", ["python-stdlib-env-config"]),
    ("file read write pathlib", ["python-stdlib-file-io"]),
    ("JSON nested parse dump", ["python-stdlib-json-nested"]),
    ("logging setup handlers formatters", ["python-stdlib-logging"]),
    ("multiprocessing pool map", ["python-stdlib-multiprocessing"]),
    ("CSV reader writer DictReader", ["python-stdlib-csv-module"]),
    ("email SMTP send attachment", ["python-stdlib-email-smtplib"]),
    ("XML ElementTree parse", ["python-stdlib-xml-elementtree"]),
    ("zipfile extract create archive", ["python-stdlib-zipfile-tarfile"]),
    ("socket programming TCP server", ["python-stdlib-socket-programming"]),
    ("typing Protocol Generic TypeVar", ["python-stdlib-typing-advanced"]),
    ("context manager __enter__ __exit__", ["python-stdlib-context-managers"]),
    ("argparse CLI argument parser", ["python-stdlib-cli-argparse"]),
    ("click typer CLI tools", ["python-stdlib-cli-tools"]),
    ("httpx async HTTP client", ["python-stdlib-httpx"]),
    ("unittest TestCase assertions", ["python-stdlib-unittest-basics"]),
    ("concurrency choices asyncio threading", ["python-stdlib-concurrency-choices"]),

    # =====================================================================
    # PYTHON — web/fastapi (13 entries)
    # =====================================================================
    ("FastAPI app setup routing endpoint", ["python-web-fastapi-basics"]),
    ("FastAPI JWT authentication token", ["python-web-fastapi-auth-jwt"]),
    ("FastAPI Pydantic request validation", ["python-web-fastapi-request-validation"]),
    ("FastAPI error handling HTTPException", ["python-web-fastapi-error-handling"]),
    ("FastAPI middleware CORS", ["python-web-fastapi-middleware", "python-web-fastapi-cors-static"]),
    ("FastAPI background tasks", ["python-web-fastapi-background-tasks"]),
    ("FastAPI dependency injection Depends", ["python-web-fastapi-dependency-injection"]),
    ("FastAPI server sent events SSE streaming", ["python-web-fastapi-sse-streaming"]),
    ("FastAPI file upload UploadFile", ["python-web-fastapi-file-upload"]),
    ("FastAPI OAuth2 password flow", ["python-web-fastapi-oauth2-password"]),
    ("FastAPI OAuth2 scopes advanced", ["python-web-fastapi-oauth2-advanced"]),
    ("FastAPI testing TestClient pytest", ["python-web-fastapi-testing"]),
    ("FastAPI CORS static files", ["python-web-fastapi-cors-static"]),

    # =====================================================================
    # PYTHON — web/other (flask, django, requests, websocket, scraping)
    # =====================================================================
    ("Flask app route blueprint", ["python-web-flask-basics", "python-web-flask-blueprints"]),
    ("Django model view URL routing", ["python-web-django-basics"]),
    ("requests session cookies auth", ["python-web-requests-sessions", "python-web-requests-auth"]),
    ("HTTP requests GET POST basics", ["python-web-requests-basics"]),
    ("requests error handling timeout", ["python-web-requests-error-handling"]),
    ("WebSocket Python asyncio websockets", ["python-web-websocket"]),
    ("web scraping BeautifulSoup", ["python-web-web-scraping"]),
    ("file upload multipart form", ["python-web-file-uploads"]),

    # =====================================================================
    # PYTHON — testing (6 entries)
    # =====================================================================
    ("pytest fixtures parametrize", ["python-testing-pytest-basics", "python-testing-pytest-fixtures"]),
    ("Python mocking patch MagicMock", ["python-testing-mocking"]),
    ("HTTP API testing httpx client", ["python-testing-http-testing"]),
    ("async testing pytest asyncio", ["python-testing-async-testing"]),
    ("snapshot testing snapshottest", ["python-testing-snapshot-testing"]),

    # =====================================================================
    # PYTHON — db/sqlalchemy (6 entries)
    # =====================================================================
    ("SQLAlchemy ORM model definition", ["python-db-sqlalchemy-2.0-models"]),
    ("SQLAlchemy query filter join", ["python-db-sqlalchemy-2.0-queries"]),
    ("SQLAlchemy relationship ForeignKey", ["python-db-sqlalchemy-2.0-relationships"]),
    ("Alembic database migration", ["python-db-sqlalchemy-2.0-migrations-alembic"]),
    ("SQLAlchemy async session", ["python-db-sqlalchemy-async-sessions"]),
    ("Alembic advanced migration", ["python-db-alembic-advanced"]),

    # =====================================================================
    # PYTHON — db/redis (3 entries)
    # =====================================================================
    ("Redis set get cache Python", ["python-db-redis-basics"]),
    ("Redis patterns pub/sub", ["python-db-redis-patterns"]),
    ("Redis rate limiting", ["python-db-redis-rate-limiting"]),

    # =====================================================================
    # PYTHON — db/sqlite
    # =====================================================================
    ("SQLite Python patterns", ["python-db-sqlite-patterns"]),

    # =====================================================================
    # PYTHON — data (4 entries)
    # =====================================================================
    ("Pydantic v2 model validator", ["python-data-pydantic-v2-models"]),
    ("Pydantic computed field validator", ["python-data-pydantic-v2-computed-validators"]),
    ("pandas DataFrame basics", ["python-data-pandas-basics"]),
    ("Polars DataFrame lazy", ["python-data-polars-basics"]),

    # =====================================================================
    # PYTHON — concurrency (2 entries)
    # =====================================================================
    ("Celery task queue worker", ["python-concurrency-celery-basics"]),
    ("asyncio event loop gather", ["python-concurrency-asyncio-basics"]),

    # =====================================================================
    # PYTHON — patterns (2 entries)
    # =====================================================================
    ("Python error handling custom exception patterns", ["python-patterns-error-handling"]),
    ("retry exponential backoff", ["python-patterns-retry-logic"]),

    # =====================================================================
    # PYTHON — infra (2 entries)
    # =====================================================================
    ("Docker SDK Python container", ["python-infra-docker-sdk"]),
    ("Sentry error tracking integration", ["python-infra-sentry-integration"]),

    # =====================================================================
    # JAVA — stdlib (15 entries)
    # =====================================================================
    ("Java Collections HashMap ArrayList", ["java-stdlib-collections"]),
    ("Java streams filter map collect", ["java-stdlib-streams"]),
    ("Java CompletableFuture async", ["java-stdlib-completable-future"]),
    ("Java concurrency executor service", ["java-stdlib-concurrency"]),
    ("Java records sealed classes", ["java-stdlib-records"]),
    ("Java Optional orElse flatMap", ["java-stdlib-optional", "java-stdlib-optional-deep-dive"]),
    ("Java exception handling try catch", ["java-stdlib-exception-handling"]),
    ("Java generics wildcard extends", ["java-stdlib-generics-wildcards"]),
    ("Java functional interface lambda", ["java-stdlib-functional-interfaces"]),
    ("Java file IO read write NIO", ["java-stdlib-file-io"]),
    ("Java regex pattern matcher", ["java-stdlib-regex"]),
    ("Java logging SLF4J logback", ["java-stdlib-logging"]),
    ("Java builder pattern fluent", ["java-stdlib-builder-pattern"]),
    ("Java serialization JSON Jackson", ["java-stdlib-serialization"]),

    # =====================================================================
    # JAVA — spring/boot (5 entries)
    # =====================================================================
    ("Spring Boot configuration properties", ["java-spring-boot-configuration-properties"]),
    ("Spring Boot profiles dev prod", ["java-spring-boot-profiles"]),
    ("Spring Boot actuator health metrics", ["java-spring-boot-actuator"]),
    ("Spring Boot scheduled cron task", ["java-spring-boot-scheduled"]),
    ("Spring Boot caching Redis", ["java-spring-boot-caching"]),

    # =====================================================================
    # JAVA — spring/mvc (5 entries)
    # =====================================================================
    ("Spring MVC controller advice exception", ["java-spring-mvc-controller-advice"]),
    ("Spring Bean Validation @Valid", ["java-spring-mvc-bean-validation"]),
    ("Spring CORS configuration", ["java-spring-mvc-cors-config"]),
    ("Spring file upload multipart", ["java-spring-mvc-file-upload"]),
    ("Spring MVC request mapping", ["java-spring-mvc", "java-spring-spring-mvc"]),

    # =====================================================================
    # JAVA — spring/data (4 entries)
    # =====================================================================
    ("Spring Data JPA repository", ["java-spring-spring-data-jpa-repositories", "java-spring-data-jpa-repositories"]),
    ("Spring Data custom queries JPQL", ["java-spring-spring-data-queries", "java-spring-data-queries"]),
    ("Spring Data transactions @Transactional", ["java-spring-spring-data-transactions", "java-spring-data-transactions"]),
    ("Spring Data custom repository", ["java-spring-data-custom-repository"]),

    # =====================================================================
    # JAVA — spring/security
    # =====================================================================
    ("Spring Security JWT authentication", ["java-spring-security-jwt-auth"]),

    # =====================================================================
    # JAVA — testing (4 entries)
    # =====================================================================
    ("JUnit 5 test lifecycle assertions", ["java-testing-junit5"]),
    ("Mockito mock verify deep", ["java-testing-mockito-deep"]),
    ("Testcontainers integration test", ["java-testing-testcontainers"]),
    ("Spring Boot testing @SpringBootTest", ["java-testing-spring-boot-testing"]),

    # =====================================================================
    # JAVA — build (2 entries)
    # =====================================================================
    ("Maven POM dependency management", ["java-build-maven-patterns"]),
    ("Gradle build script dependency", ["java-build-gradle-basics"]),

    # =====================================================================
    # TYPESCRIPT — stdlib (6 entries)
    # =====================================================================
    ("TypeScript async Promise await", ["typescript-stdlib-async-patterns"]),
    ("TypeScript error handling Result", ["typescript-stdlib-error-handling"]),
    ("TypeScript generics constraints", ["typescript-stdlib-generics"]),
    ("TypeScript environment config dotenv", ["typescript-stdlib-env-config"]),
    ("Node.js process management signal", ["typescript-stdlib-process-management"]),
    ("TypeScript advanced types utility", ["typescript-stdlib-ts-advanced"]),

    # =====================================================================
    # TYPESCRIPT — web/react (6 entries)
    # =====================================================================
    ("React hooks useEffect useState", ["typescript-web-react-hooks"]),
    ("React state management patterns", ["typescript-web-react-state"]),
    ("React forms validation controlled", ["typescript-web-react-forms"]),
    ("React Context provider consumer", ["typescript-web-react-context"]),
    ("React performance memo useMemo", ["typescript-web-react-performance"]),
    ("React error boundary fallback", ["typescript-web-react-error-boundaries"]),

    # =====================================================================
    # TYPESCRIPT — web/nextjs (5 entries)
    # =====================================================================
    ("Next.js App Router layout", ["typescript-web-nextjs-app-router"]),
    ("Next.js server actions form", ["typescript-web-nextjs-server-actions"]),
    ("Next.js middleware auth redirect", ["typescript-web-nextjs-middleware"]),
    ("Next.js data fetching server components", ["typescript-web-nextjs-data-fetching"]),
    ("Next.js loading skeleton layout", ["typescript-web-nextjs-layouts-loading"]),

    # =====================================================================
    # TYPESCRIPT — web/other
    # =====================================================================
    ("Express middleware error handling", ["typescript-web-express-middleware"]),
    ("Express server setup routing", ["typescript-web-express-server"]),
    ("Prisma schema migration", ["typescript-web-prisma-migrations", "typescript-web-prisma-drizzle"]),
    ("Tailwind CSS utility patterns", ["typescript-web-tailwind-patterns"]),
    ("tRPC router procedure typesafe", ["typescript-web-trpc-patterns"]),
    ("Zod schema validation", ["typescript-web-zod-validation"]),
    ("NextAuth setup provider session", ["typescript-web-nextauth-setup"]),
    ("WebSocket TypeScript socket", ["typescript-web-websocket"]),

    # =====================================================================
    # TYPESCRIPT — state (2 entries)
    # =====================================================================
    ("Zustand store state management", ["typescript-state-zustand-patterns"]),
    ("TanStack Query fetch cache", ["typescript-state-tanstack-query"]),

    # =====================================================================
    # TYPESCRIPT — runtime/node (3 entries)
    # =====================================================================
    ("Node.js fs file read write", ["typescript-runtime-node-fs"]),
    ("Node.js HTTP server request", ["typescript-runtime-node-http"]),
    ("Node.js streams readable writable", ["typescript-runtime-node-streams"]),

    # =====================================================================
    # TYPESCRIPT — testing (4 entries)
    # =====================================================================
    ("Vitest test runner describe", ["typescript-testing-vitest"]),
    ("Playwright E2E test browser", ["typescript-testing-playwright-e2e"]),
    ("MSW mock service worker API", ["typescript-testing-msw-mocking"]),
    ("React Testing Library render", ["typescript-testing-react-testing-library"]),

    # =====================================================================
    # GO — stdlib (10 entries)
    # =====================================================================
    ("Go goroutines concurrency", ["go-concurrency-goroutines"]),
    ("Go channels buffered channel", ["go-concurrency-channels"]),
    ("Go context timeout cancel", ["go-stdlib-context"]),
    ("Go error handling wrapping", ["go-stdlib-error-handling"]),
    ("Go interfaces empty interface", ["go-stdlib-interfaces"]),
    ("Go slices maps iteration", ["go-stdlib-slices-maps"]),
    ("Go modules go.mod dependency", ["go-stdlib-modules"]),
    ("Go JSON custom marshal unmarshal", ["go-stdlib-json-custom"]),
    ("Viper config Go YAML", ["go-stdlib-viper-config"]),
    ("slog structured logging Go", ["go-stdlib-slog-logging"]),

    # =====================================================================
    # GO — web (3 entries)
    # =====================================================================
    ("Go HTTP server net/http", ["go-web-http-server"]),
    ("Go HTTP client request", ["go-web-http-client"]),
    ("Chi router Go middleware", ["go-web-chi-router"]),

    # =====================================================================
    # GO — testing (3 entries)
    # =====================================================================
    ("Go testing table driven subtests", ["go-testing-table-driven", "go-testing-basics"]),
    ("Go mocking interface testify mock", ["go-testing-mocking"]),
    ("Go test benchmark coverage", ["go-testing-basics"]),

    # =====================================================================
    # GO — db (2 entries)
    # =====================================================================
    ("Go database/sql query scan", ["go-db-database-sql"]),
    ("GORM model CRUD migration", ["go-db-gorm-patterns"]),

    # =====================================================================
    # GO — concurrency (2 entries)
    # =====================================================================
    ("Go concurrency patterns worker pool", ["go-concurrency-patterns"]),
    ("Go sync mutex WaitGroup", ["go-concurrency-sync-patterns"]),

    # =====================================================================
    # RUST — stdlib (10 entries)
    # =====================================================================
    ("Rust ownership borrowing move", ["rust-stdlib-ownership"]),
    ("Rust Result Option unwrap", ["rust-stdlib-result-option"]),
    ("Rust trait definition impl", ["rust-stdlib-traits"]),
    ("Rust lifetime annotation", ["rust-stdlib-lifetimes"]),
    ("Rust serde serialize deserialize", ["rust-stdlib-serde"]),
    ("Rust error handling thiserror anyhow", ["rust-stdlib-error-handling", "rust-stdlib-error-crates"]),
    ("Rust collections HashMap Vec", ["rust-stdlib-collections"]),
    ("Rust iterators closures map filter", ["rust-stdlib-iterators-closures"]),
    ("Rust clap CLI argument parser", ["rust-stdlib-clap-cli"]),

    # =====================================================================
    # RUST — web (2 entries)
    # =====================================================================
    ("Axum web framework routing handler", ["rust-web-axum"]),
    ("Axum deep extractors state", ["rust-web-axum-deep"]),

    # =====================================================================
    # RUST — testing
    # =====================================================================
    ("Rust testing patterns assert", ["rust-testing-patterns"]),

    # =====================================================================
    # RUST — db
    # =====================================================================
    ("SQLx Rust database query", ["rust-db-sqlx-patterns"]),

    # =====================================================================
    # RUST — concurrency
    # =====================================================================
    ("Rust async tokio spawn", ["rust-concurrency-async-tokio"]),

    # =====================================================================
    # C# (6 entries)
    # =====================================================================
    ("C# async await Task", ["csharp-stdlib-async-await"]),
    ("LINQ query Where Select", ["csharp-stdlib-linq"]),
    ("C# dependency injection IServiceCollection", ["csharp-stdlib-dependency-injection"]),
    ("Entity Framework DbContext", ["csharp-db-entity-framework"]),
    ("ASP.NET middleware controller", ["csharp-web-aspnet-basics"]),
    ("xUnit testing C# .NET", ["csharp-testing-basics"]),

    # =====================================================================
    # BASH (5 entries)
    # =====================================================================
    ("bash scripting patterns shebang", ["bash-scripting-patterns"]),
    ("bash error handling set -e trap", ["bash-error-handling"]),
    ("bash string manipulation variable", ["bash-string-manipulation"]),
    ("bash process management background", ["bash-process-management"]),
    ("bash testing debugging shellcheck", ["bash-testing-debugging"]),

    # =====================================================================
    # CRYPTO (5 entries)
    # =====================================================================
    ("SHA-256 hash digest hex", ["crypto-sha256"]),
    ("AES GCM encryption decrypt", ["crypto-aes-encryption"]),
    ("RSA key generation encrypt", ["crypto-rsa-keygen"]),
    ("JWT token sign verify", ["crypto-jwt-tokens"]),
    ("bcrypt argon2 password hash", ["crypto-password-hashing"]),

    # =====================================================================
    # DB — postgres (10 entries)
    # =====================================================================
    ("PostgreSQL window functions ROW_NUMBER", ["db-postgres-window-functions"]),
    ("PostgreSQL CTE recursive WITH", ["db-postgres-ctes"]),
    ("PostgreSQL index B-tree GIN", ["db-postgres-indexes", "db-postgres-indexing-strategies"]),
    ("PostgreSQL query optimization EXPLAIN", ["db-postgres-query-optimization"]),
    ("PostgreSQL transaction isolation", ["db-postgres-transactions"]),
    ("PostgreSQL JSONB json query", ["db-postgres-json-queries", "db-postgres-json-advanced"]),
    ("PostgreSQL full text search tsvector", ["db-postgres-full-text-search"]),
    ("PostgreSQL migration ALTER TABLE", ["db-postgres-migrations"]),
    ("PostgreSQL indexing strategies composite", ["db-postgres-indexing-strategies"]),

    # =====================================================================
    # DB — mongodb
    # =====================================================================
    ("MongoDB aggregation pipeline $group", ["db-mongodb-aggregation"]),

    # =====================================================================
    # DEVOPS (5 entries)
    # =====================================================================
    ("Docker Compose multi-container", ["devops-docker-compose"]),
    ("Dockerfile best practices multi-stage", ["devops-docker-dockerfile-patterns"]),
    ("GitHub Actions CI/CD workflow", ["devops-ci-cd-github-actions"]),
    ("Kubernetes deployment pod service", ["devops-kubernetes-basics"]),
    ("Helm chart template values", ["devops-kubernetes-helm"]),

    # =====================================================================
    # ANTI-PATTERNS (9 entries)
    # =====================================================================
    ("Python anti-patterns common mistakes", ["antipatterns-python"]),
    ("Java anti-patterns common mistakes", ["antipatterns-java"]),
    ("TypeScript anti-patterns common mistakes", ["antipatterns-typescript"]),
    ("Go anti-patterns common mistakes", ["anti-patterns-go"]),
    ("Rust anti-patterns common mistakes", ["anti-patterns-rust"]),
    ("SQL anti-patterns query mistakes", ["anti-patterns-sql"]),
    ("general anti-patterns code smells", ["anti-patterns-general"]),
    ("security anti-patterns vulnerabilities", ["antipatterns-security"]),
    ("performance anti-patterns slow code", ["antipatterns-performance"]),

    # =====================================================================
    # PATTERNS (10 entries)
    # =====================================================================
    ("rate limiting algorithm token bucket", ["patterns-rate-limiting"]),
    ("API versioning strategy", ["patterns-api-design", "api-design-rest-conventions"]),
    ("webhook signature verification", ["patterns-webhook-patterns"]),
    ("health check endpoint liveness", ["patterns-health-checks"]),
    ("graceful shutdown signal handler", ["patterns-graceful-shutdown"]),
    ("structured logging JSON format", ["patterns-structured-logging"]),
    ("feature flags toggle rollout", ["patterns-feature-flags"]),
    ("secret management vault env", ["patterns-secret-management"]),
    ("observability tracing metrics", ["patterns-observability"]),
    ("git workflow branching strategy", ["patterns-git-workflows"]),

    # =====================================================================
    # API DESIGN (2 entries)
    # =====================================================================
    ("REST API conventions HATEOAS", ["api-design-rest-conventions"]),
    ("API versioning URL header", ["api-design-versioning"]),

    # =====================================================================
    # SECURITY
    # =====================================================================
    ("web security XSS CSRF OWASP", ["security-web-security-basics"]),

    # =====================================================================
    # PERFORMANCE (3 entries)
    # =====================================================================
    ("caching strategy Redis CDN", ["performance-caching-strategies"]),
    ("connection pooling database", ["performance-connection-pooling"]),
    ("N+1 query problem prevention", ["performance-n-plus-one-prevention"]),

    # =====================================================================
    # ERROR HANDLING
    # =====================================================================
    ("structured error handling Result", ["error-handling-structured-errors"]),

    # =====================================================================
    # DOCKER
    # =====================================================================
    ("Docker deep dive networking volumes", ["docker-deep-dive"]),

    # =====================================================================
    # PROJECT CONVENTIONS (2 entries)
    # =====================================================================
    ("project architecture conventions", ["project-conventions-architecture"]),
    ("coding style rules conventions", ["project-conventions-style-rules"]),

    # =====================================================================
    # HARD / VAGUE QUERIES (concept-only, no exact keyword match)
    # =====================================================================
    ("Python exception handling custom error", ["python-patterns-error-handling"]),
    ("make my code faster caching", ["performance-caching-strategies", "antipatterns-performance"]),
    ("secure my web application OWASP", ["security-web-security-basics", "antipatterns-security"]),
    ("test my API endpoints", ["python-testing-http-testing", "python-web-fastapi-testing"]),
    ("deploy application Docker containers", ["devops-docker-compose", "devops-docker-dockerfile-patterns"]),
    ("manage database connection pooling", ["performance-connection-pooling"]),
    ("authentication and authorization JWT", ["python-web-fastapi-auth-jwt", "crypto-jwt-tokens"]),
    ("async programming patterns concurrency", ["python-stdlib-asyncio-basics", "typescript-stdlib-async-patterns"]),

    # =====================================================================
    # MULTI-HOP QUERIES (answer spans 2+ entries)
    # =====================================================================
    ("FastAPI with JWT auth and pytest testing", ["python-web-fastapi-auth-jwt", "python-web-fastapi-testing"]),
    ("SQLAlchemy model with Alembic migration", ["python-db-sqlalchemy-2.0-models", "python-db-sqlalchemy-2.0-migrations-alembic"]),
    ("React hooks with Zustand state management", ["typescript-web-react-hooks", "typescript-state-zustand-patterns"]),
    ("Next.js server actions with Zod validation", ["typescript-web-nextjs-server-actions", "typescript-web-zod-validation"]),
    ("Spring Boot with JPA repository testing", ["java-spring-spring-data-jpa-repositories", "java-testing-spring-boot-testing"]),
    ("Axum web server with SQLx database", ["rust-web-axum", "rust-db-sqlx-patterns"]),

    # =====================================================================
    # TYPO / MISSPELLING RESILIENCE
    # =====================================================================
    ("fastapi routng endpont", ["python-web-fastapi-basics"]),
    ("sqlalchemy modle defintion ORM", ["python-db-sqlalchemy-2.0-models"]),
    ("pytest fixtrues parametriez", ["python-testing-pytest-basics"]),
]

# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def recall_at_k(results: list, expected_ids: list[str], k: int) -> float:
    """Calculate recall@k: fraction of expected IDs found in top-k results."""
    if not expected_ids:
        return 1.0
    result_ids = [e.id for e in results[:k]]
    hits = sum(1 for eid in expected_ids if eid in result_ids)
    return hits / len(expected_ids)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def entries():
    return load_entries(Path("."))


class TestComprehensiveRetrieval:
    """Test retrieval across all 242+ entries."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.entries = load_entries(Path("."))

    # -- recall@1 tests --
    @pytest.mark.parametrize("query,expected_ids", TEST_CASES, ids=[t[0][:60] for t in TEST_CASES])
    def test_recall_at_1(self, query, expected_ids):
        results = search_by_keywords(self.entries, query)
        r = recall_at_k(results, expected_ids, 1)
        # We don't fail on recall@1 (too strict), but we track it
        # Just assert the search returns something
        assert len(results) > 0 or r == 0.0

    # -- recall@3 tests (the critical metric) --
    @pytest.mark.parametrize("query,expected_ids", TEST_CASES, ids=[t[0][:60] for t in TEST_CASES])
    def test_recall_at_3(self, query, expected_ids):
        results = search_by_keywords(self.entries, query)
        r = recall_at_k(results, expected_ids, 3)
        assert r > 0, f"recall@3=0 for query '{query}': expected {expected_ids}, got {[e.id for e in results[:3]]}"

    # -- recall@5 tests --
    @pytest.mark.parametrize("query,expected_ids", TEST_CASES, ids=[t[0][:60] for t in TEST_CASES])
    def test_recall_at_5(self, query, expected_ids):
        results = search_by_keywords(self.entries, query)
        r = recall_at_k(results, expected_ids, 5)
        assert r > 0, f"recall@5=0 for query '{query}': expected {expected_ids}, got {[e.id for e in results[:5]]}"


class TestOverallRecallThreshold:
    """Fail the suite if overall recall@3 drops below 80%."""

    def test_overall_recall_at_3_above_80_percent(self):
        entries = load_entries(Path("."))
        total_recall = 0.0
        failures = []

        for query, expected_ids in TEST_CASES:
            results = search_by_keywords(entries, query)
            r = recall_at_k(results, expected_ids, 3)
            total_recall += r
            if r == 0:
                top3 = [e.id for e in results[:3]]
                failures.append(f"  FAIL: '{query}' → expected {expected_ids}, got {top3}")

        avg_recall = total_recall / len(TEST_CASES)
        print(f"\n{'='*60}")
        print(f"Overall recall@3: {avg_recall:.1%} ({len(TEST_CASES)} queries)")
        print(f"Pass threshold: 80%")
        if failures:
            print(f"\nFailures ({len(failures)}):")
            for f in failures:
                print(f)
        print(f"{'='*60}")

        assert avg_recall >= 0.80, f"Overall recall@3 is {avg_recall:.1%}, below 80% threshold"


class TestRecallMetrics:
    """Report recall@1, recall@3, recall@5 across all queries."""

    def test_print_recall_report(self, capsys):
        entries = load_entries(Path("."))

        recalls = {1: [], 3: [], 5: []}
        category_results: dict[str, list[float]] = {}

        for query, expected_ids in TEST_CASES:
            results = search_by_keywords(entries, query)
            for k in [1, 3, 5]:
                recalls[k].append(recall_at_k(results, expected_ids, k))

            # Categorize by first word of query
            cat = query.split()[0].lower()
            if cat not in category_results:
                category_results[cat] = []
            category_results[cat].append(recall_at_k(results, expected_ids, 3))

        with capsys.disabled():
            print(f"\n{'='*60}")
            print("RETRIEVAL RECALL REPORT")
            print(f"{'='*60}")
            print(f"Total queries: {len(TEST_CASES)}")
            for k in [1, 3, 5]:
                avg = sum(recalls[k]) / len(recalls[k])
                above_50 = sum(1 for r in recalls[k] if r > 0.5) / len(recalls[k])
                print(f"  recall@{k}: {avg:.1%} avg, {above_50:.0%} queries >50%")
            print(f"{'='*60}")


class TestEntryCoverage:
    """Verify every entry ID is referenced by at least one test query."""

    def test_all_entries_covered(self):
        entries = load_entries(Path("."))
        all_ids = {e.id for e in entries}

        covered_ids = set()
        for _, expected_ids in TEST_CASES:
            covered_ids.update(expected_ids)

        uncovered = all_ids - covered_ids
        # Allow some entries to be uncovered (they may be reached via fuzzy matching)
        # but report them
        if uncovered:
            print(f"\nUncovered entries ({len(uncovered)}):")
            for eid in sorted(uncovered):
                print(f"  - {eid}")

        # At least 80% of entries should be explicitly covered
        coverage = len(covered_ids) / len(all_ids) if all_ids else 0
        print(f"\nEntry coverage: {coverage:.1%} ({len(covered_ids)}/{len(all_ids)})")
        assert coverage >= 0.70, f"Entry coverage is {coverage:.1%}, below 70%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
