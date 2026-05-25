---
id: "bash-testing-debugging"
title: "Testing and Debugging Shell Scripts"
language: "bash"
category: "testing"
tags: ["bash", "shell", "testing", "debugging", "shellcheck", "bats"]
version: "n/a"
retrieval_hint: "bash test debug set -x bats shellcheck"
last_verified: "2026-05-24"
confidence: "high"
---

# Testing and Debugging Shell Scripts

## When to Use
- Writing tests for shell scripts
- Debugging failing scripts
- Ensuring scripts work correctly before deployment
- Static analysis of shell code

## Standard Pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

# Debugging: trace execution
set -x  # Print each command before executing (with expanded variables)
# ... code to debug ...
set +x  # Disable tracing

# Run entire script with tracing: bash -x script.sh

# Debug function
debug() {
    [[ "${DEBUG:-false}" == true ]] && echo "[DEBUG] $*" >&2
}
debug "Processing file: $filename"

# shellcheck: static analysis (install: apt install shellcheck)
# Run: shellcheck script.sh
# Common directives:
# shellcheck disable=SC2086  # Disable specific warning
# shellcheck source=lib.sh   # Tell shellcheck about sourced files

# bats-core: bash testing framework (install: npm install -g bats)
# File: test_script.bats

# === BATS test file (save as test_script.bats) ===
# #!/usr/bin/env bats
#
# setup() {
#     load 'test_helper'
#     export TMPDIR=$(mktemp -d)
# }
#
# teardown() {
#     rm -rf "$TMPDIR"
# }
#
# @test "script exits with error on missing file" {
#     run ./script.sh nonexistent.txt
#     [ "$status" -eq 1 ]
#     [[ "$output" == *"not found"* ]]
# }
#
# @test "script processes valid input" {
#     echo "test data" > "$TMPDIR/input.txt"
#     run ./script.sh "$TMPDIR/input.txt"
#     [ "$status" -eq 0 ]
#     [[ "$output" == *"processed"* ]]
# }
#
# @test "script handles empty input" {
#     touch "$TMPDIR/empty.txt"
#     run ./script.sh "$TMPDIR/empty.txt"
#     [ "$status" -eq 0 ]
# }
# === END BATS ===

# Simple assert functions for non-bats testing
assert_equals() {
    local expected="$1" actual="$2" msg="${3:-}"
    if [[ "$expected" != "$actual" ]]; then
        echo "FAIL: ${msg:-assert_equals}: expected '$expected', got '$actual'" >&2
        return 1
    fi
}

assert_exit_code() {
    local expected="$1"
    shift
    "$@"
    local actual=$?
    if [[ "$expected" -ne "$actual" ]]; then
        echo "FAIL: expected exit code $expected, got $actual" >&2
        return 1
    fi
}

assert_contains() {
    local haystack="$1" needle="$2" msg="${3:-}"
    if [[ "$haystack" != *"$needle"* ]]; then
        echo "FAIL: ${msg:-assert_contains}: '$needle' not found in output" >&2
        return 1
    fi
}

# Test isolation: use temporary directory
setup_test_env() {
    TEST_DIR=$(mktemp -d)
    export TEST_DIR
    cd "$TEST_DIR"
}

cleanup_test_env() {
    cd /
    rm -rf "$TEST_DIR"
}
trap cleanup_test_env EXIT

# Mocking commands for tests
mock_command() {
    local cmd="$1" output="$2"
    local mock_dir="$TEST_DIR/bin"
    mkdir -p "$mock_dir"
    cat > "$mock_dir/$cmd" <<EOF
#!/usr/bin/env bash
echo "$output"
exit 0
EOF
    chmod +x "$mock_dir/$cmd"
    export PATH="$mock_dir:$PATH"
}
```

## Common Mistakes

```bash
# WRONG: Testing in production directories
cd /app
./script.sh  # May modify real files

# CORRECT: Use temporary directories
TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT
cd "$TEST_DIR"

# WRONG: Not running shellcheck
# Assumes script is correct — misses quoting issues, portability problems

# CORRECT: Always run shellcheck
shellcheck -x script.sh  # -x follows source directives

# WRONG: Testing only success paths
run ./script.sh valid_input.txt
[ "$status" -eq 0 ]
# What about error cases?

# CORRECT: Test both success and failure
run ./script.sh valid_input.txt
[ "$status" -eq 0 ]

run ./script.sh
[ "$status" -eq 1 ]

run ./script.sh nonexistent.txt
[ "$status" -eq 1 ]
[[ "$output" == *"not found"* ]]

# WRONG: Not cleaning up test artifacts
setup() {
    create_test_data  # Leaves files behind on failure
}

# CORRECT: Always use teardown
setup() {
    export TEST_DIR=$(mktemp -d)
}
teardown() {
    rm -rf "$TEST_DIR"
}

# WRONG: Using echo for test output (can't capture cleanly)
my_function() {
    echo "result"
    return 0
}
result=$(my_function)  # Captures echo, not return value

# CORRECT: Use stdout for data, stderr for logging
my_function() {
    echo "result"         # Data to stdout
    echo "log" >&2       # Logs to stderr
    return 0
}
```

## Gotchas
- `set -x` prints to stderr — use `bash -x script.sh` to trace the entire script
- `bats` is the de facto standard for bash testing — install with `npm install -g bats`
- `run` in bats captures stdout, stderr, and exit status in `$output` and `$status`
- `shellcheck` catches 90% of common bash mistakes — always run it
- `set -e` in tests can interfere with assertions — bats handles this internally
- Test isolation prevents tests from affecting each other — always use temp dirs
- Mocking allows testing scripts that depend on external commands
- `assert_equals` and friends are simple but effective for non-bats testing
- `DEBUG=true ./script.sh` enables debug output without modifying the script
- `bats --tap test_script.bats` outputs TAP format for CI integration
- `shellcheck source=script.sh` lets shellcheck follow `source` commands
- Always test edge cases: empty input, missing files, permission errors

## Related
- bash/scripting-patterns.md
- bash/error-handling.md
- python/testing/pytest-basics.md
