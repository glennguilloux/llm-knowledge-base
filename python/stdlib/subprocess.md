---
id: "python-stdlib-subprocess"
title: "Running External Commands with subprocess"
language: "python"
category: "stdlib"
tags: ["subprocess", "shell", "command", "process", "exec"]
version: "3.10+"
retrieval_hint: "subprocess run shell command external process Popen"
last_verified: "2026-05-22"
confidence: "high"
---

# Running External Commands with subprocess

## When to Use
- Running shell commands from Python
- Calling external tools (git, ffmpeg, docker, etc.)
- Scripting system administration tasks
- Pipelining between processes

## Standard Pattern

```python
import subprocess

# Simple command execution
result = subprocess.run(["ls", "-la"], capture_output=True, text=True)
print(result.stdout)       # Standard output as string
print(result.returncode)   # 0 for success

# With error checking
result = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
# Raises CalledProcessError if returncode != 0

# With timeout
result = subprocess.run(
    ["ping", "-c", "3", "example.com"],
    capture_output=True,
    text=True,
    timeout=10,  # Raises TimeoutExpired after 10 seconds
)

# Piping between commands (without shell=True)
ps = subprocess.run(["ps", "aux"], capture_output=True, text=True)
grep = subprocess.run(
    ["grep", "python"],
    input=ps.stdout,
    capture_output=True,
    text=True,
)

# Environment variables
import os
env = os.environ.copy()
env["MY_VAR"] = "value"
result = subprocess.run(["my_tool"], env=env, capture_output=True, text=True)

# Working directory
result = subprocess.run(
    ["make", "build"],
    cwd="/path/to/project",
    capture_output=True,
    text=True,
    check=True,
)

# Interactive / long-running process
process = subprocess.Popen(
    ["python", "server.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)
for line in process.stdout:
    print(f"[server] {line.strip()}")
process.wait()

# stdin input to process
result = subprocess.run(
    ["bc"],  # Calculator
    input="2 + 3\n",
    capture_output=True,
    text=True,
)
print(result.stdout.strip())  # "5"
```

## Common Mistakes

```python
# WRONG: Using shell=True with user input
user_input = "file.txt; rm -rf /"
subprocess.run(f"cat {user_input}", shell=True)  # Command injection!

# CORRECT: Use list form (no shell interpretation)
subprocess.run(["cat", user_input], capture_output=True, text=True)

# WRONG: Not capturing output
result = subprocess.run(["ls"])  # Output goes to terminal, not captured

# CORRECT: capture_output=True
result = subprocess.run(["ls"], capture_output=True, text=True)
print(result.stdout)

# WRONG: Ignoring return code
result = subprocess.run(["git", "push"])
# Silently fails — no error checking

# CORRECT: Use check=True or check returncode
result = subprocess.run(["git", "push"], capture_output=True, text=True, check=True)

# WRONG: Using subprocess for simple string operations
result = subprocess.run(["echo", "hello"], capture_output=True, text=True)
greeting = result.stdout.strip()  # Just use: greeting = "hello"

# CORRECT: Use Python for Python things
greeting = "hello"

# WRONG: Not using text=True
result = subprocess.run(["ls"])  # Returns bytes, not string
print(result.stdout.decode())  # Manual decode needed

# CORRECT: text=True for string output
result = subprocess.run(["ls"], capture_output=True, text=True)
print(result.stdout)  # Already a string
```

## Gotchas
- `shell=True` interprets the command through the shell — security risk with untrusted input
- `capture_output=True` is equivalent to `stdout=subprocess.PIPE, stderr=subprocess.PIPE`
- `text=True` (or `encoding="utf-8"`) returns strings instead of bytes
- `check=True` raises `CalledProcessError` on non-zero exit — use for error handling
- `subprocess.run` blocks until the command finishes — use `Popen` for async
- `TimeoutExpired` is raised if `timeout` is exceeded — the process is killed
- `subprocess.PIPE` creates a pipe — must be consumed or the process may deadlock
- `shell=False` (default) requires a list — a string is treated as the executable name
- `env` parameter REPLACES the entire environment — copy `os.environ` and modify

## Related
- python/stdlib/file-io.md
- python/stdlib/env-config.md
- bash/process-management.md
