---
id: "bash-network-operations"
title: "Bash Network Operations: curl, wget, HTTP Requests, and JSON Parsing"
language: "bash"
category: "stdlib"
tags: ["bash", "curl", "wget", "http", "json", "jq", "network", "api"]
version: "n/a"
retrieval_hint: "bash curl patterns wget HTTP requests checking URLs downloading files JSON parsing jq"
last_verified: "2026-05-24"
confidence: "high"
---

# Bash Network Operations: curl, wget, HTTP Requests, and JSON Parsing

## When to Use
- Making HTTP requests from shell scripts
- Downloading files from URLs
- Checking if URLs are reachable
- Parsing JSON API responses with jq
- Automating API interactions

## Standard Pattern

```bash
#!/bin/bash
set -euo pipefail

# Basic GET request
curl -s "https://api.example.com/users"

# GET with headers
curl -s -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     "https://api.example.com/users"

# GET and parse JSON with jq
users=$(curl -s "https://api.example.com/users")
echo "$users" | jq '.[].name'
echo "$users" | jq '.[] | select(.active == true)'

# POST with JSON body
curl -s -X POST \
     -H "Content-Type: application/json" \
     -d '{"name": "Alice", "email": "alice@example.com"}' \
     "https://api.example.com/users"

# Check HTTP status code
status=$(curl -s -o /dev/null -w "%{http_code}" "https://api.example.com/health")
if [[ "$status" -eq 200 ]]; then
    echo "Service is healthy"
else
    echo "Service returned HTTP $status"
    exit 1
fi

# Check if URL is reachable (with timeout)
if curl -sf --max-time 5 "https://api.example.com/health" > /dev/null; then
    echo "URL is reachable"
else
    echo "URL is NOT reachable"
fi

# Download file
curl -L -o output.zip "https://example.com/file.zip"

# wget alternative
wget -O output.zip "https://example.com/file.zip"

# PUT request
curl -s -X PUT \
     -H "Content-Type: application/json" \
     -d '{"name": "Bob"}' \
     "https://api.example.com/users/1"

# DELETE request
curl -s -X DELETE \
     -H "Authorization: Bearer $TOKEN" \
     "https://api.example.com/users/1"

# Retry on failure
for i in {1..5}; do
    if curl -sf "https://api.example.com/health" > /dev/null; then
        echo "Success on attempt $i"
        break
    fi
    echo "Attempt $i failed, retrying..."
    sleep 5
done

# Send form data (multipart)
curl -s -F "file=@/path/to/file.pdf" \
     -F "description=My file" \
     "https://api.example.com/upload"

# Basic auth
curl -s -u "username:password" "https://api.example.com/protected"

# Save and reuse cookies
curl -s -c cookies.txt "https://api.example.com/login"
curl -s -b cookies.txt "https://api.example.com/protected"
```

## Common Mistakes

```bash
# WRONG: Not handling curl failures
response=$(curl -s "https://api.example.com/users")
# If curl fails, $response will be empty — no error raised!

# CORRECT: Check exit code or use --fail
if ! response=$(curl -sf "https://api.example.com/users"); then
    echo "API request failed" >&2
    exit 1
fi

# WRONG: Not quoting variables
curl -H Authorization: $TOKEN https://api.example.com
# If $TOKEN contains spaces, it breaks!

# CORRECT: Always quote variables
curl -H "Authorization: Bearer $TOKEN" "https://api.example.com"

# WRONG: Not using set -e (errors silently ignored)
curl -s "https://api.example.com/users" > /dev/null
# Script continues even if curl fails!

# CORRECT: Use set -euo pipefail at the top
set -euo pipefail

# WRONG: Not handling redirect
curl -s "http://example.com/api"  # May get 301!

# CORRECT: Use -L to follow redirects
curl -sL "http://example.com/api"

# WRONG: Not checking jq parse result
name=$(echo "$response" | jq -r '.name')
# If response is not valid JSON, jq fails silently

# CORRECT: Validate JSON before parsing
if ! echo "$response" | jq empty 2>/dev/null; then
    echo "Invalid JSON response" >&2
    exit 1
fi

# WRONG: Not using -r flag with jq (gets quoted strings)
name=$(echo "$response" | jq '.name')
# Returns: "Alice" (with quotes)

# CORRECT: Use -r for raw output
name=$(echo "$response" | jq -r '.name')
# Returns: Alice (no quotes)
```

## Gotchas
- `curl -s` suppresses the progress meter. Use `-S` with `-s` to still show errors: `curl -sS`.
- `curl -f` (`--fail`) returns non-zero exit code on HTTP errors (4xx, 5xx).
- `curl -L` follows redirects. Without it, you get the 301/302 response body.
- Always quote URL variables: `"$url"` not `$url`. URLs with `&` will break without quotes.
- `jq -r` gives raw output (without JSON quotes). Always use `-r` for extracting values.
- `set -euo pipefail` at the top of every script: exit on error, error on unset vars, catch pipe failures.
- `curl -o /dev/null -w "%{http_code}"` extracts just the HTTP status code.
- `curl -c` saves cookies, `-b` sends cookies. Useful for session management.

## Related
- bash/file-operations.md
- bash/text-processing.md
- bash/scripting-patterns.md
- bash/testing-debugging.md
