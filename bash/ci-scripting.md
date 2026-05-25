---
id: "bash-ci-scripting"
title: "CI/CD Scripting: Exit Codes, Artifacts, Output, Caching"
language: "bash"
category: "devops"
tags: ["bash", "ci", "cd", "github-actions", "gitlab-ci", "jenkins", "pipeline"]
version: "n/a"
retrieval_hint: "bash CI CD scripting exit codes artifacts caching pipeline patterns"
last_verified: "2026-05-24"
confidence: "high"
---

# CI/CD Scripting: Exit Codes, Artifacts, Output, Caching

## When to Use
- Writing pipeline scripts for GitHub Actions, GitLab CI, Jenkins, CircleCI
- Handling success/failure in automated workflows
- Managing build artifacts and caching between runs
- Producing structured output for CI systems to consume

## Standard Pattern

```bash
# === Exit Code Discipline ===

# Always set exit codes explicitly
set -euo pipefail

# set -e   : Exit on error
# set -u   : Error on undefined variables
# set -o pipefail : Fail pipeline if any command fails

# --- Patterns ---

# Non-fatal failures — don't abort but track them
errors=0
npm run lint || errors=$?
npm run test || errors=$?
exit $errors

# Step failure without aborting whole job
ci_step() {
    local step_name="$1"
    shift
    if "$@"; then
        echo "✓ $step_name"
    else
        echo "✗ $step_name failed" >&2
        return 1
    fi
}

# --- Conditional execution ---
if [[ "${CI:-}" == "true" ]]; then
    echo "Running in CI environment"
fi

if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
    echo "Running in GitHub Actions"
fi


# === Output for CI Platforms ===

# --- GitHub Actions ---
# Set outputs (consumed by next steps)
echo "status=passed" >> "$GITHUB_OUTPUT"
echo "version=$VERSION" >> "$GITHUB_OUTPUT"

# Set environment variables for subsequent steps
echo "DEPLOY_ENV=staging" >> "$GITHUB_ENV"

# Summary
echo "## Build Results" >> "$GITHUB_STEP_SUMMARY"
echo "- Coverage: 92%" >> "$GITHUB_STEP_SUMMARY"
echo "- Tests: 245 passed" >> "$GITHUB_STEP_SUMMARY"

# Annotations
echo "::warning file=src/main.sh,line=42::Possible bug detected"
echo "::error file=src/test.sh,line=10,title=Test Failure::Expected 5, got 3"

# Group log lines
echo "::group::Installing dependencies"
npm ci
echo "::endgroup::"


# --- GitLab CI ---
# Set output as dotenv
echo "BUILD_VERSION=$VERSION" > build.env

# Use reports artifacts
# In .gitlab-ci.yml:
# artifacts:
#   reports:
#     junit: test-results.xml


# --- Generic ---
# Machine-readable JSON output for tooling
output_json() {
    cat <<EOF
{"status":"$1","duration":$2,"coverage":$3}
EOF
}


# === Artifact Management ===

# Structured artifact creation
create_artifact() {
    local name="$1"
    local files="$2"

    local artifact_dir="artifacts/$name"
    mkdir -p "$artifact_dir"

    echo "Creating artifact: $name"
    cp -r $files "$artifact_dir/"

    # Create checksum manifest
    (cd "$artifact_dir" && find . -type f -exec sha256sum {} \; > checksums.txt)

    echo "Artifact path: $artifact_dir"
}

# Artifact versioning
ARTIFACT_VERSION="${CI_COMMIT_TAG:-${CI_COMMIT_SHORT_SHA:-dev}}"
ARTIFACT_NAME="myapp-${ARTIFACT_VERSION}.tar.gz"
tar czf "$ARTIFACT_NAME" build/


# === Caching ===

# Cache key pattern (composite key)
cache_key() {
    local os="$1"
    local deps_file="$2"
    echo "${os}-$(sha256sum "$deps_file" | cut -d' ' -f1)"
}

# Cache restoration with fallback
restore_cache() {
    local cache_dir="$1"
    local key="$2"
    local fallback_key="$3"

    if [[ -d "$cache_dir" ]]; then
        echo "Cache hit: $key"
        return 0
    fi

    echo "Cache miss, attempting restore..."
    restore_cache_from_storage "$cache_dir" "$key" || \
    restore_cache_from_storage "$cache_dir" "$fallback_key" || \
    echo "No cache found, will rebuild"
}


# === Parallel Job Safety ===

# Lock file pattern for concurrent access
acquire_lock() {
    local lockfile="$1"
    local fd
    exec {fd}>"$lockfile"
    if ! flock -n "$fd"; then
        echo "Another job holds lock: $lockfile"
        return 1
    fi
    echo "$fd" > "/tmp/lock-fd-$(basename "$lockfile")"
}


# === CI Env Detection ===

detect_ci() {
    if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
        echo "github-actions"
    elif [[ -n "${GITLAB_CI:-}" ]]; then
        echo "gitlab-ci"
    elif [[ -n "${JENKINS_URL:-}" ]]; then
        echo "jenkins"
    elif [[ -n "${CIRCLECI:-}" ]]; then
        echo "circleci"
    else
        echo "local"
    fi
}
```

## Common Mistakes

```bash
# WRONG: Not using set -e (script continues on failure)
cd /nonexistent  # This fails silently!
rm -rf *         # Runs in wrong directory! Catastrophic.

# CORRECT: Always use strict mode
set -euo pipefail
cd /nonexistent  # Script exits immediately with error


# WRONG: Missing fallback keys in cache restore
cache: myapp-v1-{{ hashFiles('package.json') }}
# If hash changes, cache miss → full rebuild

# CORRECT: Use fallback keys
# restore-keys: |
#   myapp-v1-
# → Falls back to latest matching cache if exact key misses


# WRONG: Using CI secrets in plain logs
echo "Deploying with token: $DEPLOY_TOKEN"  # Secret leaked!

# CORRECT: Mask secrets
echo "Deploying with token: ***"


# WRONG: Assuming working directory is always the same
./scripts/deploy.sh  # May fail if CI changes workdir

# CORRECT: Use absolute paths or CI-provided variables
"${GITHUB_WORKSPACE:-$(pwd)}/scripts/deploy.sh"


# WRONG: Mixing stdout (info) with stderr (errors)
echo "Error: build failed"  # Goes to stdout!

# CORRECT: Errors go to stderr
echo "Error: build failed" >&2
```

## Gotchas
- **set -e gotcha with commands in conditions**: `set -e` is suspended inside `if`, `while`, `until`, `||`, and `&&`. A command that fails inside `if condition; then` won't trigger `set -e`. This is intentional but often surprising.
- **CI environment variables differ per platform**: `CI=true` is common to most CI systems, but specific variables like `GITHUB_ACTIONS`, `GITLAB_CI`, `JENKINS_URL` are platform-specific. Use `detect_ci()` function for portable scripts.
- **Caching granularity**: Overly broad cache keys cause stale caches. Overly specific keys cause cache misses. Use a composite key (os + lockfile hash) with a broad fallback prefix.
- **Secret masking**: CI platforms automatically mask structured output but not variable expansion. Avoid `echo "Using $API_KEY"` — the expanded value may leak before masking rules apply.
- **Job timeout**: Always set a timeout for CI jobs to prevent runaway scripts. GitHub Actions default is 6 hours. GitLab default is 60 minutes. Explicitly set shorter timeouts for steps.
- **File descriptor limits**: CI runners may have restricted ulimits. Parallel test execution can hit `Too many open files`. Set `ulimit -n` in your script or runner config.
- **Pre-exit cleanup**: Use `trap` for cleanup actions that must run even on failure: `trap "docker compose down" EXIT`. This ensures resources are cleaned up whether the script succeeds or fails.

## Related
- bash/error-handling.md
- bash/scripting-patterns.md
- bash/makefile-patterns.md
