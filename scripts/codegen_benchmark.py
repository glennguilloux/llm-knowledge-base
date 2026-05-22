#!/usr/bin/env python3
"""Code Generation Benchmark — Prove the knowledge base works.

Tests code generation quality WITH and WITHOUT knowledge base retrieval.
Supports two modes:
  1. LLM mode: calls an LLM and scores output against criteria
  2. Prompt export mode: exports all prompts to benchmark_prompts/ for manual review

Usage:
    python scripts/codegen_benchmark.py --export-prompts
    python scripts/codegen_benchmark.py --provider ollama --model qwen2.5-coder:7b
    python scripts/codegen_benchmark.py --provider openai --model gpt-3.5-turbo
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_builder import build_prompt


# ---------------------------------------------------------------------------
# Coding tasks with quality criteria
# ---------------------------------------------------------------------------

CODING_TASKS = [
    # --- Python ---
    {
        "id": "py-1",
        "language": "python",
        "task": "Write a FastAPI endpoint that accepts a file upload, validates it's a PDF under 10MB, saves it to disk, and returns the file path.",
        "quality_criteria": [
            "handles missing file",
            "validates MIME type",
            "validates size",
            "uses Path for file path",
            "has error responses",
            "returns JSON",
        ],
    },
    {
        "id": "py-2",
        "language": "python",
        "task": "Write a Python function that hashes a file using SHA-256 with streaming and verifies it against an expected hash.",
        "quality_criteria": [
            "uses hashlib",
            "streams in chunks",
            "handles file not found",
            "handles permission errors",
            "returns bool or raises",
            "uses context manager",
        ],
    },
    {
        "id": "py-3",
        "language": "python",
        "task": "Write a SQLAlchemy 2.0 model for User with email (unique), hashed password, created_at, and a relationship to Post. Include a query to get users with more than 5 posts.",
        "quality_criteria": [
            "uses Mapped[] type hints",
            "uses relationship()",
            "uses func.count",
            "uses select() style",
            "email has unique=True",
            "password is not called 'password'",
        ],
    },
    # --- Java ---
    {
        "id": "java-1",
        "language": "java",
        "task": "Write a Spring Boot REST controller for a /api/users endpoint with GET (paginated), POST (with validation), and GET /{id}. Include proper error handling.",
        "quality_criteria": [
            "uses @RestController",
            "uses Pageable",
            "uses @Valid",
            "uses ResponseEntity",
            "handles NotFoundException",
            "uses Bean Validation annotations",
        ],
    },
    {
        "id": "java-2",
        "language": "java",
        "task": "Write a Java method that reads a file line by line, filters lines containing a keyword, and returns them as a List using Streams API.",
        "quality_criteria": [
            "uses Files.lines()",
            "uses try-with-resources",
            "uses .filter()",
            "uses .toList()",
            "handles IOException",
            "closes resources",
        ],
    },
    # --- TypeScript ---
    {
        "id": "ts-1",
        "language": "typescript",
        "task": "Write an Express middleware that validates a JWT token from the Authorization header, extracts the user ID, and attaches it to the request object.",
        "quality_criteria": [
            "extracts Bearer token",
            "validates JWT",
            "attaches to req object",
            "handles missing token",
            "handles invalid token",
            "calls next()",
            "proper TypeScript types",
        ],
    },
    {
        "id": "ts-2",
        "language": "typescript",
        "task": "Write a React hook that fetches data from an API with loading state, error state, and automatic retry on failure.",
        "quality_criteria": [
            "uses useState for loading/error/data",
            "uses useEffect",
            "implements retry logic",
            "handles cleanup/abort",
            "TypeScript generics",
            "handles empty state",
        ],
    },
    # --- Go ---
    {
        "id": "go-1",
        "language": "go",
        "task": "Write a Go HTTP handler that accepts JSON, validates it, saves to a database using database/sql, and returns the created resource.",
        "quality_criteria": [
            "uses json.Decoder",
            "validates input",
            "uses prepared statement",
            "returns inserted ID",
            "proper error handling",
            "sets Content-Type header",
        ],
    },
    {
        "id": "go-2",
        "language": "go",
        "task": "Write a Go function that runs N concurrent HTTP requests, collects results, and returns the first error or all results. Use context for timeout.",
        "quality_criteria": [
            "uses goroutines",
            "uses sync.WaitGroup or errgroup",
            "uses context.WithTimeout",
            "collects all results",
            "handles partial failure",
            "no goroutine leaks",
        ],
    },
    # --- Rust ---
    {
        "id": "rust-1",
        "language": "rust",
        "task": "Write an Axum handler that accepts JSON, validates it with serde, saves to a Vec in shared state, and returns the created item.",
        "quality_criteria": [
            "uses Axum extractors",
            "uses serde Deserialize/Serialize",
            "uses Arc<Mutex<Vec>>",
            "returns proper HTTP status",
            "handles JSON parse errors",
            "proper Rust error types",
        ],
    },
    # --- C# ---
    {
        "id": "csharp-1",
        "language": "csharp",
        "task": "Write an ASP.NET Core minimal API endpoint for user registration that validates input, hashes the password, saves to a database with Entity Framework, and returns a JWT token.",
        "quality_criteria": [
            "uses minimal API pattern",
            "validates input with FluentValidation or DataAnnotations",
            "hashes password (not plaintext)",
            "uses async/await",
            "uses Entity Framework SaveChangesAsync",
            "returns JWT token",
        ],
    },
    {
        "id": "csharp-2",
        "language": "csharp",
        "task": "Write a C# background service that polls a queue every 30 seconds, processes messages with retry logic (3 attempts), and logs failures.",
        "quality_criteria": [
            "inherits BackgroundService",
            "uses IHostedService or BackgroundService",
            "implements retry loop",
            "uses ILogger",
            "handles cancellation token",
            "proper async disposal",
        ],
    },
    # --- Bash ---
    {
        "id": "bash-1",
        "language": "bash",
        "task": "Write a Bash script that backs up a PostgreSQL database, compresses it, rotates old backups (keep last 7), and logs the operation.",
        "quality_criteria": [
            "uses set -euo pipefail",
            "uses pg_dump",
            "compresses with gzip",
            "rotates old backups",
            "logs to file",
            "handles errors",
        ],
    },
    {
        "id": "bash-2",
        "language": "bash",
        "task": "Write a Bash script that monitors a directory for new files, processes them (moves to archive), and sends an email notification for each file processed.",
        "quality_criteria": [
            "uses inotifywait or polling",
            "handles filenames with spaces",
            "moves to archive directory",
            "sends notification",
            "quotes all variables",
            "uses trap for cleanup",
        ],
    },
    # --- Django ---
    {
        "id": "django-1",
        "language": "python",
        "task": "Write a Django view that handles user registration with email validation, password hashing, and sends a welcome email — using Django's built-in auth system.",
        "quality_criteria": [
            "uses Django forms or serializer",
            "uses User.objects.create_user",
            "validates email format",
            "sends email with send_mail",
            "handles duplicate email",
            "returns proper HTTP response",
        ],
    },
    {
        "id": "django-2",
        "language": "python",
        "task": "Write a Django REST Framework viewset for a Blog model with list, create, retrieve, update, and delete. Include pagination, filtering by author, and proper permissions.",
        "quality_criteria": [
            "uses ModelViewSet",
            "defines serializer_class",
            "implements filtering",
            "uses permission_classes",
            "configures pagination",
            "handles 404",
        ],
    },
    # --- SQL ---
    {
        "id": "sql-1",
        "language": "sql",
        "task": "Write SQL queries to find the top 5 customers by total order amount, with their most recent order date, using proper indexing considerations.",
        "quality_criteria": [
            "uses GROUP BY",
            "uses JOIN",
            "uses ORDER BY with LIMIT",
            "considers indexing",
            "handles NULL values",
            "selects only needed columns",
        ],
    },
    # --- DevOps ---
    {
        "id": "devops-1",
        "language": "yaml",
        "task": "Write a Docker Compose file for a web app with a Node.js frontend, Python backend, PostgreSQL database, and Redis cache. Include health checks and volumes.",
        "quality_criteria": [
            "defines all 4 services",
            "uses healthcheck",
            "configures volumes",
            "sets environment variables",
            "uses depends_on with condition",
            "exposes correct ports",
        ],
    },
    {
        "id": "devops-2",
        "language": "yaml",
        "task": "Write a GitHub Actions workflow that runs tests, lints code, builds a Docker image, and pushes to a registry on push to main. Include caching.",
        "quality_criteria": [
            "defines on.push trigger",
            "uses jobs with steps",
            "runs tests",
            "builds Docker image",
            "uses cache action",
            "pushes to registry",
        ],
    },
    # --- Security ---
    {
        "id": "sec-1",
        "language": "python",
        "task": "Write a Python function that validates and sanitizes user input to prevent SQL injection, XSS, and path traversal attacks.",
        "quality_criteria": [
            "uses parameterized queries",
            "escapes HTML entities",
            "validates file paths",
            "uses allowlist approach",
            "handles edge cases",
            "returns sanitized output",
        ],
    },
]


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def build_bare_prompt(task: dict) -> str:
    """Build a prompt WITHOUT knowledge base context."""
    return f"""You are a coding assistant. Write production-quality code.

## Task

{task['task']}

## Requirements

- Write complete, working code
- Include error handling
- Follow language best practices
- Add brief comments for complex logic
"""


def build_kb_prompt(task: dict, profile: str | None = None) -> str:
    """Build a prompt WITH knowledge base retrieval, optionally profile-aware."""
    kwargs = {
        "query": task["task"],
        "max_tokens": 3000,
        "language": task["language"],
    }
    if profile:
        kwargs["profile"] = profile
    prompt, _metadata = build_prompt(**kwargs)
    return prompt


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_response(response: str, criteria: list[str]) -> tuple[int, list[dict]]:
    """Score a code response against quality criteria.

    Uses keyword/pattern matching as a proxy for quality assessment.
    Returns (score, details) where details is a list of {criterion, met, evidence}.
    """
    response_lower = response.lower()
    details = []

    # Pattern-based scoring heuristics
    patterns = {
        "handles missing file": ["none", "not found", "404", "missing", "no file", "file not"],
        "validates mime type": ["content_type", "mime", "content-type", "application/pdf", "mimetype"],
        "validates size": ["size", "10 * 1024 * 1024", "10485760", "max_size", "file_size", "10mb", "10*1024"],
        "uses path for file path": ["pathlib", "Path(", "pathlib.Path", "os.path"],
        "has error responses": ["HTTPException", "status_code", "400", "422", "error", "raise"],
        "returns json": ["json", "JSONResponse", "jsonify", "Json", "return {"],
        "uses hashlib": ["hashlib", "sha256", "sha256()"],
        "streams in chunks": ["chunk", "read(", "buffer", "for chunk", "block"],
        "handles file not found": ["FileNotFoundError", "not found", "exists()", "is_file"],
        "handles permission errors": ["PermissionError", "permission", "access denied"],
        "returns bool or raises": ["return true", "return false", "raise", "return bool"],
        "uses context manager": ["with ", "with(", "__enter__", "contextmanager"],
        "uses mapped[] type hints": ["Mapped[", "mapped_column", "Mapped"],
        "uses relationship()": ["relationship(", "Relationship"],
        "uses func.count": ["func.count", "func.count(", "count(", "group_by"],
        "uses select() style": ["select(", "Select", "stmt", "stmt = select"],
        "email has unique unique=true": ["unique=True", "unique=true", "Unique"],
        "password is not called 'password'": ["hashed_password", "password_hash", "hashed_pw"],
        "uses @restcontroller": ["@RestController", "@controller"],
        "uses pageable": ["Pageable", "PageRequest", "pageable"],
        "uses @valid": ["@Valid", "@valid"],
        "uses responseentity": ["ResponseEntity", "responseEntity"],
        "handles notfoundexception": ["NotFound", "not found", "404", "NotFoundException"],
        "uses bean validation annotations": ["@NotNull", "@NotBlank", "@NotEmpty", "@Size", "@Email", "@Valid"],
        "uses files.lines()": ["Files.lines", "files.lines", "BufferedReader"],
        "uses try-with-resources": ["try (", "try(", "try-with-resources", "using var", "using ("],
        "uses .filter()": [".filter(", ".Filter("],
        "uses .tolist()": [".toList(", ".ToList(", ".collect(", "Collectors.toList"],
        "handles ioexception": ["IOException", "ioexception", "throws", "catch"],
        "closes resources": ["close()", "using", "try-with-resources", "dispose"],
        "extracts bearer token": ["Bearer", "bearer", "authorization"],
        "validates jwt": ["jwt", "JWT", "verify", "decode", "jsonwebtoken"],
        "attaches to req object": ["req.user", "request.user", "req[", "res.locals"],
        "handles missing token": ["no token", "missing token", "401", "unauthorized"],
        "handles invalid token": ["invalid token", "token expired", "401", "jwt.verify"],
        "calls next()": ["next()", "next ("],
        "proper typescript types": ["interface ", "type ", ": string", ": number", ": boolean", "Request"],
        "uses usestate for loading/error/data": ["useState", "loading", "error"],
        "uses useeffect": ["useEffect"],
        "implements retry logic": ["retry", "attempt", "retries", "maxRetries"],
        "handles cleanup/abort": ["cleanup", "return ()", "abort", "unmount", "controller.abort"],
        "typescript generics": ["<T>", "<T,", "generic"],
        "handles empty state": ["null", "undefined", "loading", "empty", "initial"],
        "uses json.decoder": ["json.NewDecoder", "json.Decoder", "json.decode", "json.loads"],
        "validates input": ["validate", "required", "if !", "if not", "validation"],
        "uses prepared statement": ["Prepare(", "prepare(", "PREPARE", "$1", "?"],
        "returns inserted id": ["LastInsertId", "RETURNING", "lastrowid", "inserted_id", "id"],
        "proper error handling": ["if err != nil", "try:", "except", "catch", "Result<>"],
        "sets content-type header": ["Content-Type", "content-type", "Set(", "Header("],
        "uses goroutines": ["go func", "goroutine", "go "],
        "uses sync.waitgroup or errgroup": ["WaitGroup", "errgroup", "sync.WaitGroup"],
        "uses context.withtimeout": ["context.WithTimeout", "context.WithDeadline", "WithTimeout"],
        "collects all results": ["append(", "results", "collect", "mu.Lock"],
        "handles partial failure": ["err != nil", "error", "failed", "partial"],
        "no goroutine leaks": ["defer", "cancel", "Done()", "wg.Done"],
        "uses axum extractors": ["axum", "Json(", "Path(", "State(", "extract"],
        "uses serde deserialize/serialize": ["Deserialize", "Serialize", "serde"],
        "uses arc<mutex<vec>>": ["Arc<Mutex", "Arc::new(Mutex", "RwLock", "Mutex"],
        "returns proper http status": ["StatusCode", "status", "201", "200", "Created"],
        "handles json parse errors": ["JsonRejection", "parse error", "serde_json", "Deserialize"],
        "proper rust error types": ["Result<", "impl IntoResponse", "anyhow", "thiserror"],
        "uses minimal api pattern": ["app.Map", "MapGet", "MapPost", "builder.Services"],
        "validates input with fluentvalidation or dataannotations": ["ValidationResult", "[Required]", "[EmailAddress]", "FluentValidation"],
        "hashes password (not plaintext)": ["HashPassword", "BCrypt", "hash", "PasswordHash"],
        "uses async/await": ["async", "await", "Task<", "Async"],
        "uses entity framework savechangesasync": ["SaveChangesAsync", "DbContext", "DbSet"],
        "returns jwt token": ["Jwt", "token", "SecurityToken", "JwtSecurityToken"],
        "inherits backgroundservice": ["BackgroundService", "IHostedService"],
        "uses ihostedservice or backgroundservice": ["BackgroundService", "IHostedService", "ExecuteAsync"],
        "implements retry loop": ["retry", "attempt", "while", "for"],
        "uses ilogger": ["ILogger", "LogInformation", "LogError", "logger"],
        "handles cancellation token": ["CancellationToken", "stoppingToken", "cancellationToken"],
        "proper async disposal": ["DisposeAsync", "IAsyncDisposable", "using"],
        "uses set -euo pipefail": ["set -euo pipefail", "set -e", "set -o pipefail"],
        "uses pg_dump": ["pg_dump"],
        "compresses with gzip": ["gzip", "compress"],
        "rotates old backups": ["find", "mtime", "rm", "oldest", "keep", "rotate"],
        "logs to file": ["log", ">>", "tee", "echo"],
        "handles errors": ["set -e", "||", "if [", "exit 1", "trap"],
        "uses inotifywait or polling": ["inotifywait", "inotify", "polling", "watch", "fswatch"],
        "handles filenames with spaces": ['"$file"', '"${', '"$'],
        "moves to archive directory": ["mv", "archive", "move"],
        "sends notification": ["mail", "sendmail", "curl", "smtp", "notify"],
        "quotes all variables": ['"$', '"${'],
        "uses trap for cleanup": ["trap", "cleanup", "EXIT"],
        "uses django forms or serializer": ["forms.Form", "ModelForm", "Serializer", "form_class"],
        "uses user.objects.create_user": ["create_user", "create_superuser"],
        "validates email format": ["email", "Email", "@", "validate_email"],
        "sends email with send_mail": ["send_mail", "send_mail", "EmailMessage"],
        "handles duplicate email": ["IntegrityError", "unique", "already exists", "duplicate", "exists()"],
        "returns proper http response": ["HttpResponse", "JsonResponse", "redirect", "render"],
        "uses modelviewset": ["ModelViewSet", "ViewSet"],
        "defines serializer_class": ["serializer_class", "Serializer"],
        "implements filtering": ["filter", "FilterSet", "filterset_class", "queryset"],
        "uses permission_classes": ["permission_classes", "IsAuthenticated", "permissions"],
        "configures pagination": ["pagination", "PageNumberPagination", "page_size"],
        "handles 404": ["404", "get_object_or_404", "Http404", "NotFound"],
        "uses group by": ["GROUP BY", "group by"],
        "uses join": ["JOIN", "join", "INNER JOIN", "LEFT JOIN"],
        "uses order by with limit": ["ORDER BY", "LIMIT", "order by", "limit"],
        "considers indexing": ["INDEX", "index", "CREATE INDEX", "idx_"],
        "handles null values": ["NULL", "null", "COALESCE", "coalesce", "IS NOT NULL"],
        "selects only needed columns": ["SELECT id", "SELECT name", "SELECT email", "columns"],
        "defines all 4 services": ["services:", "backend:", "frontend:", "postgres:", "redis:"],
        "uses healthcheck": ["healthcheck", "health", "test:"],
        "configures volumes": ["volumes:", "volume:"],
        "sets environment variables": ["environment:", "env:", "POSTGRES_", "REDIS_"],
        "uses depends_on with condition": ["depends_on:", "condition:", "service_healthy"],
        "exposes correct ports": ["ports:", "expose:", "8080", "3000", "5432", "6379"],
        "defines on.push trigger": ["on:", "push:", "branches:"],
        "uses jobs with steps": ["jobs:", "steps:", "runs-on:"],
        "runs tests": ["test", "pytest", "npm test", "jest", "run:"],
        "builds docker image": ["docker build", "docker/build-push", "buildx"],
        "uses cache action": ["cache", "actions/cache", "restore-keys"],
        "pushes to registry": ["push", "docker/login-action", "registry", "ghcr.io", "ECR"],
        "uses parameterized queries": ["?", "$1", "parameterize", "prepared", "bind"],
        "escapes html entities": ["escape", "html_escape", "markupsafe", "cgi.escape", "sanitize"],
        "validates file paths": ["realpath", "abspath", "startswith", "resolve", "path traversal"],
        "uses allowlist approach": ["allowlist", "whitelist", "allowed", "valid"],
        "handles edge cases": ["empty", "none", "null", "edge", "missing"],
        "returns sanitized output": ["return", "sanitized", "clean", "safe"],
    }

    score = 0
    for criterion in criteria:
        key = criterion.lower()
        matched = False
        evidence = ""

        # Try exact match first
        if key in patterns:
            for pattern in patterns[key]:
                if pattern.lower() in response_lower:
                    matched = True
                    evidence = pattern
                    break

        # Fallback: check if any word from the criterion appears
        if not matched:
            words = [w for w in criterion.lower().split() if len(w) > 3]
            for word in words:
                if word in response_lower:
                    matched = True
                    evidence = f"(partial: {word})"
                    break

        if matched:
            score += 1

        details.append({
            "criterion": criterion,
            "met": matched,
            "evidence": evidence if matched else "",
        })

    return score, details


# ---------------------------------------------------------------------------
# LLM integration
# ---------------------------------------------------------------------------

def call_ollama(prompt: str, model: str, url: str = "http://localhost:11434") -> str:
    """Call Ollama API."""
    import urllib.request
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 2048},
    }).encode()
    req = urllib.request.Request(
        f"{url}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    return result.get("response", "")


def call_openai(prompt: str, model: str) -> str:
    """Call OpenAI API."""
    import urllib.request
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 2048,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    return result["choices"][0]["message"]["content"]


def call_llm(prompt: str, provider: str, model: str) -> str:
    """Dispatch to the right LLM provider."""
    if provider == "ollama":
        return call_ollama(prompt, model)
    elif provider == "openai":
        return call_openai(prompt, model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# ---------------------------------------------------------------------------
# Prompt export mode
# ---------------------------------------------------------------------------

def export_prompts(output_dir: Path, profile: str | None = None) -> None:
    """Export all prompts (with and without knowledge) to JSON files.

    Args:
        output_dir: Directory to write prompt files to
        profile: Model profile ("small", "medium", "large") for multi-profile export.
                 If None, exports with default (small) profile.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add profile suffix to filenames if specified
    suffix = f"-{profile}" if profile else ""

    all_prompts = []
    for task in CODING_TASKS:
        bare = build_bare_prompt(task)
        kb = build_kb_prompt(task, profile=profile)
        entry = {
            "task_id": task["id"],
            "language": task["language"],
            "task": task["task"],
            "quality_criteria": task["quality_criteria"],
            "prompt_without_kb": bare,
            "prompt_with_kb": kb,
        }
        if profile:
            entry["profile"] = profile
        all_prompts.append(entry)

        # Write individual prompt files
        task_file = output_dir / f"{task['id']}{suffix}.json"
        task_file.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write combined file
    combined_name = f"all_prompts{suffix}.json"
    combined = output_dir / combined_name
    combined.write_text(json.dumps(all_prompts, indent=2, ensure_ascii=False), encoding="utf-8")

    profile_label = f" (profile: {profile})" if profile else ""
    print(f"Exported {len(all_prompts)} prompt pairs to {output_dir}/{profile_label}")
    print(f"  Individual: {output_dir}/<task-id>{suffix}.json")
    print(f"  Combined:   {combined}")


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_benchmark(provider: str, model: str) -> None:
    """Run the full benchmark with an LLM."""
    total_criteria = sum(len(t["quality_criteria"]) for t in CODING_TASKS)

    bare_scores = []
    kb_scores = []
    results = []

    for i, task in enumerate(CODING_TASKS):
        print(f"\n[{i+1}/{len(CODING_TASKS)}] {task['id']}: {task['task'][:60]}...")

        bare_prompt = build_bare_prompt(task)
        kb_prompt = build_kb_prompt(task)

        print(f"  Calling {provider}/{model} (without KB)...")
        bare_response = call_llm(bare_prompt, provider, model)
        bare_score, bare_details = score_response(bare_response, task["quality_criteria"])

        print(f"  Calling {provider}/{model} (with KB)...")
        kb_response = call_llm(kb_prompt, provider, model)
        kb_score, kb_details = score_response(kb_response, task["quality_criteria"])

        bare_scores.append(bare_score)
        kb_scores.append(kb_score)

        results.append({
            "task_id": task["id"],
            "language": task["language"],
            "criteria_count": len(task["quality_criteria"]),
            "bare_score": bare_score,
            "kb_score": kb_score,
            "improvement": kb_score - bare_score,
            "bare_details": bare_details,
            "kb_details": kb_details,
        })

    # Print results
    print_results(results, model, total_criteria)


def print_results(results: list[dict], model: str, total_criteria: int) -> None:
    """Print formatted benchmark results."""
    total_bare = sum(r["bare_score"] for r in results)
    total_kb = sum(r["kb_score"] for r in results)

    bare_pct = (total_bare / total_criteria) * 100
    kb_pct = (total_kb / total_criteria) * 100
    improvement = kb_pct - bare_pct
    relative = (improvement / bare_pct * 100) if bare_pct > 0 else float("inf")

    bare_full = sum(1 for r in results if r["bare_score"] == r["criteria_count"])
    kb_full = sum(1 for r in results if r["kb_score"] == r["criteria_count"])

    print("\n" + "=" * 55)
    print("CODE GENERATION BENCHMARK RESULTS")
    print("=" * 55)
    print(f"Model: {model}")
    print(f"Tasks: {len(results)}")
    print(f"Criteria: {total_criteria} total")
    print()
    print("WITHOUT Knowledge Base:")
    print(f"  Score: {total_bare}/{total_criteria} ({bare_pct:.1f}%)")
    print(f"  Tasks fully correct: {bare_full}/{len(results)}")
    print()
    print("WITH Knowledge Base:")
    print(f"  Score: {total_kb}/{total_criteria} ({kb_pct:.1f}%)")
    print(f"  Tasks fully correct: {kb_full}/{len(results)}")
    print()
    print(f"IMPROVEMENT: +{improvement:.1f} percentage points (+{relative:.0f}% relative improvement)")
    print()

    # Show best/worst improvements
    sorted_by_imp = sorted(results, key=lambda r: r["improvement"], reverse=True)
    print("Best improvements:")
    for r in sorted_by_imp[:5]:
        if r["improvement"] > 0:
            print(f"  {r['task_id']:12s} {r['bare_score']}/{r['criteria_count']} -> {r['kb_score']}/{r['criteria_count']}  (+{r['improvement']})")

    no_improvement = [r for r in results if r["improvement"] == 0]
    if no_improvement:
        print("\nNo improvement:")
        for r in no_improvement:
            print(f"  {r['task_id']:12s} {r['bare_score']}/{r['criteria_count']} -> {r['kb_score']}/{r['criteria_count']}  (0) <- entry may need improvement")

    # Save detailed results
    results_file = Path("benchmark_results.json")
    results_file.write_text(json.dumps({
        "model": model,
        "total_tasks": len(results),
        "total_criteria": total_criteria,
        "bare_score": total_bare,
        "kb_score": total_kb,
        "bare_pct": bare_pct,
        "kb_pct": kb_pct,
        "improvement_pct_points": improvement,
        "tasks": results,
    }, indent=2), encoding="utf-8")
    print(f"\nDetailed results saved to {results_file}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Code generation benchmark for the knowledge base"
    )
    parser.add_argument(
        "--export-prompts",
        action="store_true",
        help="Export prompts to benchmark_prompts/ without calling an LLM",
    )
    parser.add_argument(
        "--export-dir",
        type=str,
        default="benchmark_prompts",
        help="Directory for exported prompts (default: benchmark_prompts)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        choices=["small", "medium", "large"],
        help="Model profile for prompt formatting (small=7B, medium=27B, large=70B)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["ollama", "openai"],
        help="LLM provider to use",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model name (e.g., qwen2.5-coder:7b, gpt-3.5-turbo)",
    )
    args = parser.parse_args()

    if args.export_prompts:
        if args.profile:
            export_prompts(Path(args.export_dir), profile=args.profile)
        else:
            # Export all three profiles
            for p in ["small", "medium", "large"]:
                export_prompts(Path(args.export_dir), profile=p)
        return 0

    if not args.provider or not args.model:
        parser.error("--provider and --model are required (or use --export-prompts)")

    run_benchmark(args.provider, args.model)
    return 0


if __name__ == "__main__":
    import os
    sys.exit(main())
