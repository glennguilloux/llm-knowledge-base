"""Query expansion for smarter retrieval.

Expands abbreviations, synonyms, and common variants before searching
so that "jwt" also matches entries tagged "authentication" or "oauth".
"""

import re
from typing import List

# ---------------------------------------------------------------------------
# Expansion map: abbreviation / shorthand -> list of expansions
# ---------------------------------------------------------------------------

EXPANSION_MAP: dict[str, list[str]] = {
    # Auth / Security
    "jwt": ["jwt", "json web token", "auth", "authentication", "token", "oauth"],
    "oauth": ["oauth", "auth", "authentication", "authorization", "token", "jwt"],
    "auth": ["auth", "authentication", "authorization"],
    "cors": ["cors", "cross-origin", "cross origin resource sharing"],
    "csrf": ["csrf", "cross-site request forgery", "cross site request forgery"],
    "xss": ["xss", "cross-site scripting", "cross site scripting", "sanitize"],
    "sql injection": ["sql injection", "sqli", "sql injection prevention"],
    "rbac": ["rbac", "role-based access control", "role based access control", "roles", "authorization"],

    # Databases / ORMs
    "orm": ["orm", "object relational mapping", "sqlalchemy", "hibernate", "prisma", "entity framework"],
    "sqlalchemy": ["sqlalchemy", "orm", "alembic", "sqlalchemy 2.0", "sql"],
    "alembic": ["alembic", "migration", "sqlalchemy migration", "database migration"],
    "prisma": ["prisma", "orm", "typescript orm", "database client"],
    "sql": ["sql", "query", "database", "relational database", "rdbms", "postgresql", "mysql"],
    "nosql": ["nosql", "no sql", "mongodb", "redis", "couchdb", "dynamodb"],
    "acid": ["acid", "transaction", "atomicity", "consistency", "isolation", "durability"],

    # CI / DevOps
    "ci": ["ci", "continuous integration", "github actions", "gitlab ci", "circleci", "automation"],
    "cd": ["cd", "continuous deployment", "continuous delivery", "deploy", "release"],
    "devops": ["devops", "ci/cd", "deployment", "infrastructure", "ops"],
    "docker": ["docker", "container", "containerization", "dockerfile"],
    "k8s": ["k8s", "kubernetes", "kube", "container orchestration", "pods"],

    # Async / Concurrency
    "async": ["async", "asynchronous", "asyncio", "concurrent", "non-blocking"],
    "await": ["await", "async", "asynchronous"],
    "concurrency": ["concurrency", "parallel", "threading", "multithreading", "asyncio"],
    "gIL": ["gil", "global interpreter lock", "cpython gil", "threading"],
    "deadlock": ["deadlock", "deadlock prevention", "lock ordering", "mutex"],

    # Web / API
    "api": ["api", "rest", "rest api", "endpoint", "web service", "http"],
    "rest": ["rest", "restful", "rest api", "http", "endpoint"],
    "http": ["http", "https", "request", "response", "rest", "web"],
    "websocket": ["websocket", "ws", "real-time", "real time", "full-duplex"],
    "graphql": ["graphql", "gql", "query language", "api"],
    "rpc": ["rpc", "remote procedure call", "grpc", "api"],

    # Testing
    "tdd": ["tdd", "test-driven development", "test driven development", "testing", "unittest"],
    "unit test": ["unit test", "unittest", "pytest", "testing", "test"],
    "pytest": ["pytest", "testing", "fixtures", "parametrize", "python test"],

    # Python ecosystem
    "pydantic": ["pydantic", "data validation", "basemodel", "validation"],
    "fastapi": ["fastapi", "api", "rest", "web framework", "asgi"],
    "asgi": ["asgi", "asynchronous server gateway interface", "uvicorn", "fastapi"],
    "wsgi": ["wsgi", "web server gateway interface", "flask", "django"],

    # TypeScript / JS ecosystem
    "ts": ["ts", "typescript", "types", "type system"],
    "js": ["js", "javascript", "ecmascript", "es6"],
    "react": ["react", "reactjs", "react.js", "frontend", "ui", "component"],
    "dom": ["dom", "document object model", "browser api", "web api"],

    # Java ecosystem
    "jvm": ["jvm", "java virtual machine", "java", "kotlin", "scala"],
    "jpa": ["jpa", "java persistence api", "hibernate", "orm", "entity"],
    "spring": ["spring", "spring boot", "spring framework", "java framework"],
    "maven": ["maven", "build tool", "dependency management", "java"],

    # Go ecosystem
    "golang": ["golang", "go", "golang programming"],
    "goroutine": ["goroutine", "go routine", "concurrent", "go concurrency"],
    "defer": ["defer", "cleanup", "go defer", "resource cleanup"],

    # Rust ecosystem
    "rustc": ["rustc", "rust compiler", "rust"],
    "cargo": ["cargo", "rust package manager", "rust build", "rust"],
    "tokio": ["tokio", "async runtime", "rust async", "async"],

    # General
    "cli": ["cli", "command line", "command-line", "terminal", "shell", "command line interface"],
    "ide": ["ide", "integrated development environment", "editor", "vscode", "intellij"],
    "sdk": ["sdk", "software development kit", "library", "api", "toolkit"],
    "json": ["json", "serialization", "data interchange", "javascript object notation"],
    "xml": ["xml", "extensible markup language", "markup", "serialization"],
    "yaml": ["yaml", "yml", "configuration", "serialization", "data format"],
    "regex": ["regex", "regular expression", "pattern matching", "re"],
    "jwt auth": ["jwt auth", "jwt authentication", "jwt", "token auth", "bearer token"],
}

# ---------------------------------------------------------------------------
# Dynamic expansion helpers
# ---------------------------------------------------------------------------

# Common short words in queries that aren't useful to expand
_STOP_WORDS = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or", "is", "it", "be"}


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens."""
    return re.findall(r"[a-zA-Z][a-zA-Z0-9#+.-]*", text.lower())


def expand_query(query: str, use_dynamic: bool = True) -> list[str]:
    """Expand a search query into multiple query variants.

    Returns the original query plus expanded forms. The caller can run
    keyword search for each variant and merge results.

    Args:
        query: Original search query (e.g., "JWT auth FastAPI")
        use_dynamic: Whether to also expand multi-word patterns

    Returns:
        List of query strings to search with. The first element is always
        the original query.
    """
    if not query or not query.strip():
        return [query]

    expansions: set[str] = set()
    expansions.add(query.strip())
    query_lower = query.strip().lower()

    # 1. Direct map lookup (check full query first, then tokens)
    if query_lower in EXPANSION_MAP:
        for term in EXPANSION_MAP[query_lower]:
            expansions.add(term)

    # 2. Token-level expansion
    tokens = _tokenize(query_lower)
    for token in tokens:
        if token in _STOP_WORDS:
            continue
        if token in EXPANSION_MAP:
            for term in EXPANSION_MAP[token]:
                if term not in _STOP_WORDS:
                    expansions.add(term)

    # 3. Multi-word pattern matching
    if use_dynamic:
        # Check if any known multi-word key is a substring of the query
        for known, terms in EXPANSION_MAP.items():
            if " " in known and known in query_lower:
                for term in terms:
                    expansions.add(term)

    # 4. Synonym substitution: build expanded query strings
    query_tokens = query.split()
    variant_tokens: list[str] = []
    for qt in query_tokens:
        qt_lower = qt.lower().strip(",.!?;:")
        if qt_lower in EXPANSION_MAP:
            for exp in EXPANSION_MAP[qt_lower]:
                if exp.lower() != qt_lower and exp not in _STOP_WORDS:
                    variant_tokens.append(exp)
                    break
            else:
                variant_tokens.append(qt)
        else:
            variant_tokens.append(qt)
    variant = " ".join(variant_tokens)
    if variant.lower() != query.strip().lower():
        expansions.add(variant)

    return list(expansions)


# ---------------------------------------------------------------------------
# Convenience: build expansion string for the scoring function
# ---------------------------------------------------------------------------

def get_expansion_text(query: str) -> str:
    """Return a single string containing the query plus all expansions.

    Useful for feeding into the keyword scoring function so that
    "jwt" also matches entries with "authentication" or "token".
    """
    expanded = expand_query(query)
    return " ".join(expanded)
