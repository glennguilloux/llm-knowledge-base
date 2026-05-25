---
id: "bash-git-automation"
title: "Bash Git Automation: Hooks, Batch Operations, and Release Tagging"
language: "bash"
category: "stdlib"
tags: ["bash", "git", "hooks", "automation", "batch", "changelog", "release", "tagging"]
version: "n/a"
retrieval_hint: "bash git hooks batch operations checking branch status automated commits changelog generation release tagging"
last_verified: "2026-05-24"
confidence: "high"
---

# Bash Git Automation: Hooks, Batch Operations, and Release Tagging

## When to Use
- Automating Git workflows in scripts
- Creating Git hooks for validation
- Batch operations on multiple repositories
- Generating changelogs and release notes
- Automated release tagging

## Standard Pattern

```bash
#!/bin/bash
set -euo pipefail

# Check branch status
get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

is_branch_clean() {
    [[ -z $(git status --porcelain) ]]
}

# Check if we're on main/master
branch=$(get_current_branch)
if [[ "$branch" != "main" ]]; then
    echo "Not on main branch (currently on '$branch')"
    exit 1
fi

# Check for uncommitted changes
if ! is_branch_clean; then
    echo "Working directory has uncommitted changes"
    git status --short
    exit 1
fi

# Git hooks — pre-commit example
# Save as .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
set -euo pipefail

# Run linting
echo "Running linter..."
if ! make lint; then
    echo "Lint failed. Commit aborted."
    exit 1
fi

# Run tests
echo "Running tests..."
if ! make test; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "Pre-commit checks passed!"
HOOK
chmod +x .git/hooks/pre-commit

# Batch operations on multiple repos
repos=("/path/to/repo1" "/path/to/repo2" "/path/to/repo3")

for repo in "${repos[@]}"; do
    echo "=== Processing: $repo ==="
    cd "$repo"
    git pull --rebase
    if ! is_branch_clean; then
        echo "Skipping $repo — uncommitted changes"
        continue
    fi
    echo ""
done

# Generate changelog from git commits
generate_changelog() {
    local since="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo '')}"
    
    echo "# Changelog"
    echo ""
    echo "## Features"
    git log "${since}..HEAD" --pretty=format:"- %s (%h)" --grep="feat:" | sed 's/feat: //'
    echo ""
    echo "## Bug Fixes"
    git log "${since}..HEAD" --pretty=format:"- %s (%h)" --grep="fix:" | sed 's/fix: //'
    echo ""
    echo "## Other Changes"
    git log "${since}..HEAD" --pretty=format:"- %s (%h)" --grep="chore:" | sed 's/chore: //'
}

# Release tagging
create_release() {
    local version="$1"
    
    if ! echo "$version" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+$'; then
        echo "Invalid version format. Use: vX.Y.Z"
        return 1
    fi
    
    if ! is_branch_clean; then
        echo "Working directory is not clean. Commit changes first."
        return 1
    fi
    
    git pull --rebase
    
    # Create annotated tag
    git tag -a "$version" -m "Release $version"
    git push origin "$(get_current_branch)"
    git push origin "$version"
    
    echo "Released $version!"
}

# Get last N commits
recent_commits() {
    local count="${1:-10}"
    git log --oneline -n "$count" --pretty=format:"%h %s (%an, %ar)"
}

# Show files changed in last commit
files_in_last_commit() {
    git diff-tree --no-commit-id --name-only -r HEAD
}

# Check if tag exists
tag_exists() {
    git rev-parse "$1" >/dev/null 2>&1
}
```

## Common Mistakes

```bash
# WRONG: Not checking if git command succeeded
git pull
# Script continues even if pull fails!

# CORRECT: Check exit code
if ! git pull --rebase; then
    echo "Pull failed" >&2
    exit 1
fi

# WRONG: Not making hooks executable
cp pre-commit .git/hooks/pre-commit
# Hook won't run — not executable!

# CORRECT: Make hooks executable
chmod +x .git/hooks/pre-commit

# WRONG: Using git log without specifying range
git log --oneline  # Could be thousands of lines!

# CORRECT: Specify a range
git log --oneline -n 20  # Last 20 commits

# WRONG: Not handling merge conflicts in automation
git pull --rebase  # May fail with merge conflicts!

# CORRECT: Handle conflicts
if ! git pull --rebase; then
    echo "Merge conflict detected. Aborting."
    git rebase --abort
    exit 1
fi

# WRONG: Using git push without specifying branch
git push  # May push to unexpected remote/branch!

# CORRECT: Specify branch explicitly
git push origin main

# WRONG: Not verifying tag doesn't already exist
git tag -a v1.0.0 -m "Release"  # Fails if tag exists!

# CORRECT: Check first
if git rev-parse v1.0.0 >/dev/null 2>&1; then
    echo "Tag v1.0.0 already exists"
    exit 1
fi
```

## Gotchas
- Git hooks are NOT committed to the repository. Use a script to install them in `.git/hooks/`.
- `git status --porcelain` gives machine-readable output. Perfect for scripts.
- `git tag -a` creates an annotated tag (recommended for releases). `git tag` creates a lightweight tag.
- `git log --grep` filters commits by message. Use with `--oneline` for summaries.
- `git diff-tree --no-commit-id --name-only -r HEAD` lists files changed in the last commit.
- Conventional commits format: `type: description` (feat, fix, chore, docs, etc.).
- `git describe --tags --abbrev=0` gets the most recent tag.
- Always use `set -euo pipefail` in automation scripts to fail on errors.

## Related
- bash/network-operations.md
- bash/file-operations.md
- bash/text-processing.md
- bash/scripting-patterns.md
