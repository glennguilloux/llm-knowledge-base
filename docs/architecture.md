# LLM Codebase Knowledge Base — Project Design Document

> A retrieval-ready structured knowledge repository that enables smaller LLMs to write production-quality code without memorizing entire language ecosystems.

---

## 1. Problem Statement

Smaller coding models (7B–14B parameters) are fast, cheap, and runnable locally — but they hallucinate syntax, misuse APIs, and invent nonexistent methods. They fail on:

- **Uncommon but critical patterns** (e.g., correct SHA-256 streaming in Python, Spring Security filter chains)
- **Library-specific conventions** (e.g., psycopg3 vs psycopg2 differences, FastAPI dependency injection)
- **Language gotchas** (e.g., Python's mutable default arguments, Java's try-with-resources)
- **Project-specific conventions** (e.g., "we use Pydantic v2, not v1," "all DB queries go through the repository layer")

A large model (Claude Opus, GPT-4) can generate this knowledge. A small model just needs to **retrieve** it at prompt time.

---

## 2. Architecture Overview

```
┌─────────────────────┐
│  Claude Opus / GPT-4 │──── Curates & generates ────┐
│  (Knowledge Curator)  │                             │
└─────────────────────┘                              ▼
                                          ┌──────────────────────┐
                                          │  Knowledge Base Repo  │
                                          │  (structured files)   │
                                          └──────────┬───────────┘
                                                     │
                                          ┌──────────▼───────────┐
                                          │  Retrieval Layer      │
                                          │  (vector DB / grep)   │
                                          └──────────┬───────────┘
                                                     │
                                          ┌──────────▼───────────┐
                                          │  Small LLM (7B–14B)   │
                                          │  (Code Generator)     │
                                          └──────────────────────┘
```

**Flow:**

1. **Curate** — Use a frontier model to generate, validate, and organize knowledge entries.
2. **Store** — Persist as structured Markdown/YAML/JSON in a version-controlled repository.
3. **Index** — Build embeddings for semantic search or keep it simple with keyword grep.
4. **Retrieve** — At code-generation time, pull relevant entries and inject into the small model's context window.
5. **Validate** — Run generated code through tests and linters; feed errors back for correction.

---

## 3. Folder Structure

```
knowledge-base/
├── README.md                          # Index and usage guide
├── schema.md                          # Entry format specification
│
├── python/
│   ├── stdlib/
│   │   ├── hashlib-sha256.md          # SHA-256 hashing patterns
│   │   ├── pathlib.md                 # File path operations
│   │   ├── asyncio-basics.md          # Async/await patterns
│   │   ├── dataclasses.md             # Dataclass patterns
│   │   ├── context-managers.md        # with-statement patterns
│   │   ├── logging.md                 # Structured logging
│   │   └── typing-advanced.md         # Type hints, generics, protocols
│   │
│   ├── web/
│   │   ├── fastapi/
│   │   │   ├── basics.md              # App setup, routing, dependencies
│   │   │   ├── auth-jwt.md            # JWT authentication flow
│   │   │   ├── request-validation.md  # Pydantic request models
│   │   │   ├── error-handling.md      # HTTPException patterns
│   │   │   ├── middleware.md          # Custom middleware
│   │   │   ├── testing.md             # TestClient patterns
│   │   │   └── file-uploads.md        # UploadFile handling
│   │   │
│   │   ├── requests/
│   │   │   ├── basics.md              # GET/POST/PUT/DELETE
│   │   │   ├── sessions.md            # Session persistence
│   │   │   ├── auth.md                # Basic, Bearer, OAuth
│   │   │   ├── error-handling.md      # Timeouts, retries, status codes
│   │   │   └── streaming.md           # Streaming responses
│   │   │
│   │   └── flask/
│   │       └── basics.md
│   │
│   ├── db/
│   │   ├── sqlalchemy-2.0/
│   │   │   ├── models.md              # Declarative models
│   │   │   ├── queries.md             # Select, insert, update, delete
│   │   │   ├── relationships.md       # Foreign keys, many-to-many
│   │   │   ├── migrations-alembic.md  # Migration management
│   │   │   └── async.md              # Async session patterns
│   │   │
│   │   ├── psycopg/
│   │   │   ├── basics.md              # Connection, cursors
│   │   │   ├── pooling.md             # Connection pooling
│   │   │   └── async.md              # Async psycopg
│   │   │
│   │   └── redis/
│   │       ├── basics.md              # Set, get, expire
│   │       └── pubsub.md              # Pub/sub patterns
│   │
│   ├── testing/
│   │   ├── pytest-basics.md           # Fixtures, parametrize, markers
│   │   ├── mocking.md                 # unittest.mock, pytest-mock
│   │   ├── http-testing.md            # Testing API endpoints
│   │   └── fixtures-patterns.md       # Reusable test fixtures
│   │
│   ├── data/
│   │   ├── pydantic-v2/
│   │   │   ├── models.md              # BaseModel, validators
│   │   │   ├── serialization.md       # model_dump, JSON schema
│   │   │   └── settings.md            # BaseSettings for config
│   │   │
│   │   └── pandas/
│   │       └── common-operations.md   # Read, filter, group, merge
│   │
│   └── patterns/
│       ├── error-handling.md          # Exception hierarchies
│       ├── retry-logic.md             # Tenacity, exponential backoff
│       ├── env-config.md              # dotenv, typed settings
│       └── cli-click.md              # Click CLI patterns
│
├── java/
│   ├── stdlib/
│   │   ├── collections.md             # List, Map, Set patterns
│   │   ├── streams.md                 # Stream API operations
│   │   ├── io-nio.md                  # File I/O, NIO.2
│   │   ├── concurrency.md             # ExecutorService, CompletableFuture
│   │   ├── records.md                 # Java 16+ records
│   │   └── optional.md                # Optional patterns
│   │
│   ├── spring/
│   │   ├── boot-basics.md             # @SpringBootApplication, config
│   │   ├── spring-mvc.md              # @RestController, request mapping
│   │   ├── spring-security/
│   │   │   ├── jwt-auth.md            # JWT filter chain
│   │   │   ├── oauth2.md              # OAuth2 client/resource server
│   │   │   └── method-security.md     # @PreAuthorize, @PostFilter
│   │   │
│   │   ├── spring-data/
│   │   │   ├── jpa-repositories.md    # Repository interfaces
│   │   │   ├── queries.md             # Derived, @Query, Specification
│   │   │   └── transactions.md        # @Transactional patterns
│   │   │
│   │   └── spring-test.md             # @SpringBootTest, MockMvc
│   │
│   ├── build/
│   │   ├── maven/
│   │   │   ├── pom-structure.md       # POM file patterns
│   │   │   └── multi-module.md        # Multi-module projects
│   │   │
│   │   └── gradle/
│   │       └── build-setup.md         # build.gradle.kts patterns
│   │
│   └── testing/
│       ├── junit5.md                  # @Test, assertions, parameterized
│       ├── mockito.md                 # Mocking patterns
│       └── testcontainers.md          # Integration testing with Docker
│
├── typescript/
│   ├── stdlib/
│   │   ├── async-patterns.md          # Promises, async iterators
│   │   ├── error-handling.md          # Typed errors, Result pattern
│   │   └── generics.md                # Generic types, utility types
│   │
│   ├── runtime/
│   │   ├── node/
│   │   │   ├── fs.md                  # fs/promises patterns
│   │   │   ├── http.md                # HTTP server/client
│   │   │   ├── streams.md             # Readable, Writable, Transform
│   │   │   ├── child-process.md       # spawn, exec patterns
│   │   │   └── workers.md             # Worker threads
│   │   │
│   │   └── bun/
│   │       └── basics.md              # Bun-specific APIs
│   │
│   ├── web/
│   │   ├── nextjs/
│   │   │   ├── app-router.md          # App directory patterns
│   │   │   ├── server-actions.md      # Server actions
│   │   │   ├── middleware.md          # Next middleware
│   │   │   └── data-fetching.md       # ISR, SSR, SSG patterns
│   │   │
│   │   └── react/
│   │       ├── hooks.md               # Custom hooks patterns
│   │       ├── state.md               # useState, useReducer, Zustand
│   │       └── forms.md               # Controlled components, react-hook-form
│   │
│   └── testing/
│       ├── vitest.md                  # Vitest setup and patterns
│       └── playwright.md              # E2E testing
│
├── crypto/
│   ├── sha256.md                      # SHA-256 in Python, Java, TS
│   ├── aes-encryption.md              # AES-GCM encryption/decryption
│   ├── rsa-keygen.md                  # RSA key generation and usage
│   ├── jwt-tokens.md                  # JWT creation and validation
│   └── password-hashing.md            # bcrypt, argon2 patterns
│
├── db/
│   ├── postgres/
│   │   ├── migrations.md              # Migration SQL patterns
│   │   ├── indexes.md                 # Index strategies
│   │   ├── json-queries.md            # JSONB query patterns
│   │   └── full-text-search.md        # tsvector, tsquery
│   │
│   ├── mysql/
│   │   └── basics.md                  # Common MySQL patterns
│   │
│   └── mongodb/
│       └── aggregation.md             # Aggregation pipeline
│
├── devops/
│   ├── docker/
│   │   ├── dockerfile-patterns.md     # Multi-stage, slim images
│   │   └── compose.md                 # docker-compose patterns
│   │
│   ├── ci-cd/
│   │   ├── github-actions.md          # Workflow YAML patterns
│   │   └── gitlab-ci.md              # .gitlab-ci.yml patterns
│   │
│   └── kubernetes/
│       ├── basics.md                  # Pod, Deployment, Service
│       └── helm.md                    # Helm chart patterns
│
└── project-conventions/               # Project-specific overrides
    ├── style-rules.md                 # Code style decisions
    ├── naming.md                      # Naming conventions
    ├── architecture.md                # Architecture decisions
    └── banned-patterns.md             # Patterns not to use
```

---

## 4. Entry Schema

Every knowledge entry follows this structure:

```yaml
---
# Frontmatter (machine-readable metadata)
id: "python-stdlib-hashlib-sha256"
title: "SHA-256 Hashing with hashlib"
language: "python"
category: "stdlib"
subcategory: "cryptography"
tags: ["hashlib", "sha256", "checksum", "integrity"]
version: "3.12+"          # Language/library version
retrieval_hint: "SHA-256 hashing file checksum integrity verify"
last_verified: "2025-01-15"
confidence: "high"         # high | medium | draft
---

# SHA-256 Hashing with hashlib

## When to Use
- Verifying file integrity (downloads, transfers)
- Storing non-reversible identifiers (NOT for passwords — use bcrypt/argon2)
- Creating deterministic fingerprints of data

## Standard Pattern

import hashlib

def hash_string(data: str) -> str:
    """Hash a string with SHA-256."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def hash_file(filepath: str, chunk_size: int = 8192) -> str:
    """Hash a file with SHA-256 using streaming (memory-efficient)."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()

## Common Mistakes

# WRONG: Forgetting to encode strings
hashlib.sha256("hello")           # TypeError

# WRONG: Using SHA-256 for passwords
hashlib.sha256(password.encode()).hexdigest()  # Vulnerable to rainbow tables

# CORRECT: For passwords, use argon2 or bcrypt
from argon2 import PasswordHasher
ph = PasswordHasher()
hash = ph.hash(password)

## Gotchas
- hashlib.sha256() returns bytes; use .hexdigest() for string output
- For HMAC (message authentication), use hmac module, not raw SHA-256
- SHA-256 output is always 64 hex characters (256 bits)

## Related
- python/stdlib/hmac.md
- crypto/password-hashing.md
```

### Schema Fields Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier: `{lang}-{category}-{topic}` |
| `title` | string | Yes | Human-readable title |
| `language` | string | Yes | Primary language (python, java, typescript, etc.) |
| `category` | string | Yes | Domain category (stdlib, web, db, testing, etc.) |
| `subcategory` | string | No | Further classification |
| `tags` | string[] | Yes | Searchable keywords |
| `version` | string | No | Minimum language/library version |
| `retrieval_hint` | string | Yes | Keywords for semantic/keyword retrieval |
| `last_verified` | date | Yes | When this was last validated against real code |
| `confidence` | enum | Yes | `high` (tested), `medium` (reviewed), `draft` (generated) |

---

## 5. Retrieval System

### Option A: Simple — File-Based Grep (Zero Dependencies)

```bash
# Search for SHA-256 related knowledge
grep -rl "sha256" knowledge-base/

# Search by tag
grep -rl "tags:.*hashlib" knowledge-base/

# Search by language
find knowledge-base/python -name "*.md" | head -20
```

**Pros:** Zero setup, git-trackable, works offline.
**Cons:** No semantic search, no ranking.

### Option B: Vector Database (Semantic Search)

```
┌─────────────┐     embed      ┌──────────────┐
│ Knowledge    │───────────────►│ Vector Store  │
│ Base (MD)    │                │ (Qdrant/      │
└─────────────┘                 │  ChromaDB)    │
                                └──────┬───────┘
                                       │ similarity search
                                ┌──────▼───────┐
                                │ Query         │
                                │ "How do I     │
                                │ hash a file?" │
                                └──────────────┘
```

**Recommended stack:**

| Component | Tool | Why |
|-----------|------|-----|
| Embedding model | `BAAI/bge-small-en-v1.5` | Fast, local, good quality |
| Vector store | ChromaDB or Qdrant | Lightweight, embedded mode |
| Chunking | One entry = one chunk | Entries are already atomic |
| Metadata filter | Language, category, tags | Pre-filter before embedding search |

### Option C: Hybrid (Recommended for Production)

1. **Metadata filter** — narrow by language + category first
2. **Vector search** — find semantically relevant entries
3. **Keyword boost** — bump entries containing exact query terms
4. **Recency boost** — prefer recently verified entries

```python
def retrieve(query: str, language: str, top_k: int = 3) -> list[KnowledgeEntry]:
    """Retrieve relevant knowledge entries for a code generation query."""
    
    # Step 1: Filter by language
    candidates = filter_by_metadata(language=language)
    
    # Step 2: Semantic search
    query_embedding = embed(query)
    results = vector_store.search(
        query_embedding,
        filter={"language": language},
        limit=top_k * 2,  # Over-fetch for re-ranking
    )
    
    # Step 3: Re-rank with keyword overlap
    ranked = rerank(results, query)
    
    return ranked[:top_k]
```

---

## 6. Prompt Templates

### System Prompt for Small LLM

```
You are a code generation assistant. Before writing any code, ALWAYS check
the provided knowledge entries for relevant patterns and examples.

RULES:
1. Follow the patterns in the knowledge entries EXACTLY unless the user
   explicitly requests a different approach.
2. If no knowledge entry matches the task, say "No reference found for [topic]"
   and write your best attempt, marking it with a # UNCERTAIN comment.
3. Never invent API methods or parameters not shown in the entries.
4. Include error handling as shown in the patterns — never write bare try/catch.
5. Use the import style shown in the entries.

KNOWLEDGE ENTRIES:
{retrieved_entries}
```

### Retrieval Prompt Builder

```python
def build_prompt(user_request: str, language: str) -> str:
    """Build a full prompt with retrieved knowledge for the small LLM."""
    
    # Retrieve relevant entries
    entries = retrieve(query=user_request, language=language, top_k=3)
    
    # Format entries as context
    knowledge_block = "\n\n---\n\n".join(
        f"[Reference: {e.title}]\n{e.content}" 
        for e in entries
    )
    
    return f"""{SYSTEM_PROMPT}

{knowledge_block}

---

USER REQUEST:
{user_request}

Write the code following the knowledge entry patterns above."""
```

### Curation Prompt (for Claude Opus / GPT-4)

```
You are curating a knowledge base entry for smaller LLMs to use as reference
when writing code. The entry must be COMPLETE and CORRECT — a small model will
copy these patterns verbatim.

Create a knowledge base entry for: {topic}
Language: {language}
Category: {category}

The entry MUST include:
1. Frontmatter with all required schema fields
2. "When to Use" section
3. "Standard Pattern" section with complete, runnable code
4. "Common Mistakes" section showing WRONG vs CORRECT examples
5. "Gotchas" section listing non-obvious pitfalls
6. "Related" section linking to other entries

The code examples must:
- Include all necessary imports
- Use type hints where applicable
- Include docstrings
- Handle errors (no bare try/except)
- Be compatible with {version}+

Output in Markdown with YAML frontmatter.
```

---

## 7. Example Entries

### Entry: Python Requests — Basics

```yaml
---
id: "python-web-requests-basics"
title: "HTTP Requests with requests Library"
language: "python"
category: "web"
subcategory: "http-client"
tags: ["requests", "http", "get", "post", "api"]
version: "3.10+"
retrieval_hint: "HTTP GET POST requests API call REST client"
last_verified: "2025-01-15"
confidence: "high"
---

# HTTP Requests with requests Library

## When to Use
- Calling REST APIs
- Downloading web resources
- Interacting with third-party services
- Quick HTTP debugging

## Standard Pattern

import requests
from requests.exceptions import RequestException, Timeout

def get_json(url: str, timeout: int = 10) -> dict:
    """Make a GET request and return JSON response."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Timeout:
        raise RequestException(f"Request to {url} timed out after {timeout}s")
    except requests.HTTPError as e:
        raise RequestException(f"HTTP {e.response.status_code}: {e}")

def post_json(url: str, data: dict, timeout: int = 10) -> dict:
    """POST JSON data and return response."""
    response = requests.post(
        url,
        json=data,           # Automatically sets Content-Type
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()

## Common Mistakes

# WRONG: No timeout — can hang forever
requests.get("https://api.example.com/data")

# CORRECT: Always set a timeout
requests.get("https://api.example.com/data", timeout=10)

# WRONG: Using data= for JSON payload
requests.post(url, data={"key": "value"})  # Sends as form-encoded

# CORRECT: Use json= for JSON payload
requests.post(url, json={"key": "value"})  # Sends as application/json

## Gotchas
- Always set a timeout. Network calls without timeouts can block indefinitely.
- response.json() can raise requests.exceptions.JSONDecodeError
- Use response.raise_for_status() to catch HTTP errors early
- For session persistence (cookies, connection pooling), use requests.Session()
- The timeout parameter is (connect_timeout, read_timeout) as a tuple

## Related
- python/web/requests/auth.md
- python/web/requests/error-handling.md
- python/web/requests/sessions.md
```

### Entry: Java Spring Security — JWT Auth

```yaml
---
id: "java-spring-security-jwt-auth"
title: "JWT Authentication with Spring Security"
language: "java"
category: "spring"
subcategory: "security"
tags: ["jwt", "spring-security", "authentication", "filter", "token"]
version: "17+"
retrieval_hint: "JWT JSON Web Token authentication Spring Security filter chain"
last_verified: "2025-01-15"
confidence: "high"
---

# JWT Authentication with Spring Security

## When to Use
- Stateless API authentication
- Microservices token validation
- Mobile/single-page app auth flows

## Standard Pattern

### 1. Security Configuration

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtAuthFilter;
    private final AuthenticationProvider authenticationProvider;

    public SecurityConfig(JwtAuthenticationFilter jwtAuthFilter,
                          AuthenticationProvider authenticationProvider) {
        this.jwtAuthFilter = jwtAuthFilter;
        this.authenticationProvider = authenticationProvider;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .authenticationProvider(authenticationProvider)
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }
}

### 2. JWT Filter

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        final String authHeader = request.getHeader("Authorization");

        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        String jwt = authHeader.substring(7);
        String username = jwtService.extractUsername(jwt);

        if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);

            if (jwtService.isTokenValid(jwt, userDetails)) {
                UsernamePasswordAuthenticationToken authToken =
                    new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities()
                    );
                authToken.setDetails(new WebAuthenticationDetailsSource()
                    .buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }
        }

        filterChain.doFilter(request, response);
    }
}

## Common Mistakes

// WRONG: Not validating the token signature
String username = JWT.decode(token).getSubject(); // No signature check!

// CORRECT: Always validate signature and claims
Claims claims = Jwts.parserBuilder()
    .setSigningKey(getSigningKey())
    .build()
    .parseClaimsJws(token)
    .getBody();

// WRONG: Storing JWT in localStorage (XSS vulnerable)
// CORRECT: Use httpOnly cookies or Authorization header

## Gotchas
- Always use STATELESS session management with JWT
- The filter must call filterChain.doFilter() even if auth fails
- Extract token from "Authorization: Bearer <token>" header
- JWTs are not encrypted — don't put secrets in claims
- Set reasonable expiration (15min access + refresh token pattern)

## Related
- java/spring/spring-security/oauth2.md
- crypto/jwt-tokens.md
```

### Entry: Crypto — SHA-256 Cross-Language

```yaml
---
id: "crypto-sha256"
title: "SHA-256 Hashing Across Languages"
language: "multi"
category: "crypto"
subcategory: "hashing"
tags: ["sha256", "hash", "checksum", "integrity", "hashlib", "message-digest"]
version: "n/a"
retrieval_hint: "SHA-256 hash checksum verify file integrity fingerprint"
last_verified: "2025-01-15"
confidence: "high"
---

# SHA-256 Hashing Across Languages

## When to Use
- File integrity verification (downloads, backups)
- Content-addressable storage (git-like hashing)
- Data deduplication fingerprints
- Deterministic identifiers from content

## NEVER Use For
- Password storage → use bcrypt, argon2, or scrypt
- Encryption → SHA-256 is one-way, not encryption
- HMAC → use the dedicated HMAC construction instead

## Python

import hashlib

# Hash a string
hashlib.sha256("hello world".encode("utf-8")).hexdigest()
# → 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'

# Hash a file (streaming — memory efficient)
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

## Java

import java.security.MessageDigest;
import java.nio.file.Files;
import java.nio.file.Path;

// Hash a string
MessageDigest digest = MessageDigest.getInstance("SHA-256");
byte[] hash = digest.digest("hello world".getBytes(StandardCharsets.UTF_8));

// Convert to hex
String hex = HexFormat.of().formatHex(hash);

// Hash a file
byte[] fileHash = digest.digest(Files.readAllBytes(Path.of("file.txt")));

## TypeScript (Node.js)

import { createHash } from "crypto";

// Hash a string
createHash("sha256").update("hello world").digest("hex");

// Hash a file (streaming)
import { createReadStream } from "fs";

async function sha256File(path: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const hash = createHash("sha256");
    createReadStream(path)
      .on("data", (chunk) => hash.update(chunk))
      .on("end", () => resolve(hash.digest("hex")))
      .on("error", reject);
  });
}

## Gotchas
- SHA-256 output is always 64 hex characters (32 bytes, 256 bits)
- Encoding matters: UTF-8 vs ASCII vs Latin-1 produce different hashes
- Streaming is essential for large files — don't load entire file into memory
- Python's .hexdigest() returns lowercase; Java's HexFormat can be uppercase
- Node's crypto module is synchronous for strings but use streams for files

## Related
- crypto/password-hashing.md
- crypto/aes-encryption.md
- crypto/jwt-tokens.md
```

---

## 8. Validation Pipeline

Knowledge entries decay. Automated validation prevents staleness.

```
┌─────────────────┐
│ Knowledge Entry  │
└────────┬────────┘
         │
    ┌────▼─────┐
    │  Schema   │──── Invalid ──► Fix or flag as draft
    │  Check    │
    └────┬─────┘
         │ Valid
    ┌────▼─────┐
    │   Code    │──── Fails ────► Fix code example
    │  Extract  │
    └────┬─────┘
         │ Extracted
    ┌────▼─────┐
    │    Run    │──── Errors ───► Fix or update version tag
    │   Tests   │
    └────┬─────┘
         │ Pass
    ┌────▼─────┐
    │   Lint    │──── Warnings ─► Fix style
    │  Check    │
    └────┬─────┘
         │ Clean
    ┌────▼─────┐
    │  Update   │
    │  verified │
    │   date    │
    └───────────┘
```

### Validation Script (Python)

```python
#!/usr/bin/env python3
"""Validate all knowledge base entries."""

import re
import subprocess
import sys
from pathlib import Path
import yaml

REQUIRED_FIELDS = {"id", "title", "language", "category", "tags", 
                   "retrieval_hint", "last_verified", "confidence"}

def validate_frontmatter(filepath: Path) -> list[str]:
    """Check YAML frontmatter has all required fields."""
    errors = []
    content = filepath.read_text()
    
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return ["Missing YAML frontmatter"]
    
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return [f"Invalid YAML: {e}"]
    
    missing = REQUIRED_FIELDS - set(meta.keys())
    if missing:
        errors.append(f"Missing fields: {missing}")
    
    if meta.get("confidence") not in ("high", "medium", "draft"):
        errors.append(f"Invalid confidence: {meta.get('confidence')}")
    
    return errors

def extract_code_blocks(filepath: Path) -> list[str]:
    """Extract fenced code blocks from markdown."""
    content = filepath.read_text()
    return re.findall(r"```(?:python|java|typescript|javascript|bash)\n(.*?)```", 
                      content, re.DOTALL)

def main():
    kb_path = Path("knowledge-base")
    errors_found = False
    
    for md_file in kb_path.rglob("*.md"):
        if md_file.name == "README.md":
            continue
        
        errors = validate_frontmatter(md_file)
        if errors:
            print(f"FAIL {md_file}: {'; '.join(errors)}")
            errors_found = True
        else:
            print(f"OK   {md_file}")
    
    sys.exit(1 if errors_found else 0)

if __name__ == "__main__":
    main()
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Week 1)

- [ ] Create repository with folder structure
- [ ] Write schema specification (`schema.md`)
- [ ] Build validation script
- [ ] Curate 10 seed entries (Python stdlib + crypto)

### Phase 2: Core Knowledge (Week 2–3)

- [ ] Expand to 50 entries across Python, Java, TypeScript
- [ ] Add project-conventions template
- [ ] Set up basic grep-based retrieval
- [ ] Write system prompt template
- [ ] Test with a 7B model (e.g., Qwen2.5-Coder-7B)

### Phase 3: Semantic Search (Week 4)

- [ ] Set up ChromaDB or Qdrant
- [ ] Generate embeddings for all entries
- [ ] Build retrieval API
- [ ] Add hybrid ranking (metadata + vector + keyword)
- [ ] Benchmark retrieval accuracy

### Phase 4: Production (Week 5–6)

- [ ] Integrate with code generation pipeline
- [ ] Add validation CI (run on every PR)
- [ ] Build curation dashboard (optional)
- [ ] Write usage guide for contributors
- [ ] Performance testing with real coding tasks

---

## 10. Tech Stack Recommendations

| Layer | Recommended | Alternative | Notes |
|-------|-------------|-------------|-------|
| Storage | Git repo (Markdown) | SQLite, MongoDB | Start simple, migrate later |
| Embedding | `bge-small-en-v1.5` | `all-MiniLM-L6-v2` | Local, fast, good quality |
| Vector DB | ChromaDB | Qdrant, pgvector | ChromaDB is easiest to start |
| Retrieval | Custom Python | LangChain, LlamaIndex | Custom is simpler for this use case |
| Small LLM | Qwen2.5-Coder-7B | DeepSeek-Coder-V2-Lite | Both run on consumer hardware |
| Validation | pytest + ruff + checkstyle | Custom scripts | Use language-native tools |
| CI | GitHub Actions | GitLab CI | Run validation on every PR |

---

## 11. Key Design Decisions

### Why Markdown, not JSON/YAML?
- Human-readable and editable
- Natural for code examples with syntax highlighting
- Git-diffable
- LLMs generate Markdown natively
- YAML frontmatter provides machine-readable metadata

### Why One Entry Per File?
- Atomic retrieval — fetch exactly what you need
- Independent validation — test one entry at a time
- Git history — track changes per topic
- Parallel curation — multiple people/agents can work simultaneously

### Why Not Just RAG on Documentation?
- Official docs explain concepts; this shows **patterns**
- Entries include **common mistakes** and **gotchas** — docs don't
- Entries are **opinionated** — they show the ONE recommended way, not all ways
- Entries include **cross-references** — connecting related topics

### Why Not Fine-Tuning?
- Knowledge changes frequently (library updates, new patterns)
- Fine-tuning is expensive and slow to update
- Retrieval is instant to update — just edit a file
- You can mix and match knowledge per-project
- Smaller context + retrieval often beats fine-tuning for code tasks

---

## 12. Quick Start

```bash
# 1. Create the repo
mkdir knowledge-base && cd knowledge-base
git init

# 2. Copy the folder structure from Section 3
# 3. Copy the schema from Section 4
# 4. Copy seed entries from Section 7

# 5. Validate
python validate_kb.py

# 6. Test retrieval
grep -rl "sha256" . --include="*.md"

# 7. Use with your small LLM
# Inject retrieved entries into the prompt (see Section 6)
```

---

*This document was designed for use with Claude Opus as the knowledge curator and smaller models (7B–14B) as the code consumers. The architecture is intentionally simple — start with files and grep, upgrade to vectors when you need semantic search.*
