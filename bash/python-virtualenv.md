---
id: "bash-python-virtualenv"
title: "Python Virtual Environment Management with Bash"
language: "bash"
category: "devops"
tags: ["bash", "python", "virtualenv", "venv", "pip", "dependency-management"]
version: "n/a"
retrieval_hint: "bash python virtualenv venv pipenv poetry dependency management activate deactivate automation"
last_verified: "2026-05-24"
confidence: "high"
---

# Python Virtual Environment Management with Bash

## When to Use
- Managing Python project dependencies in scripts
- Automating virtualenv creation and activation
- Ensuring reproducible environments across machines
- CI/CD pipelines for Python projects

## Standard Pattern

```bash
# === Create and Activate Virtual Environment ===

# Create venv
python3 -m venv .venv

# Activate
source .venv/bin/activate          # bash/zsh
source .venv/bin/activate.fish     # fish shell
.venv\\Scripts\\activate            # Windows cmd

# Deactivate
deactivate


# === Automated Setup Script ===

setup_python_env() {
    local venv_dir="${1:-.venv}"
    local requirements="${2:-requirements.txt}"
    local python_cmd="${3:-python3}"

    echo "=== Setting up Python environment ==="

    # Check Python version
    if ! command -v "$python_cmd" &>/dev/null; then
        echo "ERROR: $python_cmd not found" >&2
        return 1
    fi

    local python_version
    python_version=$("$python_cmd" --version 2>&1)
    echo "Using: $python_version"

    # Create venv if it doesn't exist
    if [[ ! -d "$venv_dir" ]]; then
        echo "Creating virtual environment: $venv_dir"
        "$python_cmd" -m venv "$venv_dir"
    else
        echo "Virtual environment exists: $venv_dir"
    fi

    # Install dependencies
    source "$venv_dir/bin/activate"

    # Upgrade pip first
    pip install --upgrade pip setuptools wheel

    if [[ -f "$requirements" ]]; then
        echo "Installing dependencies from: $requirements"
        pip install -r "$requirements"
    fi

    # Install dev dependencies if present
    if [[ -f "requirements-dev.txt" ]]; then
        echo "Installing dev dependencies"
        pip install -r requirements-dev.txt
    fi

    deactivate
    echo "=== Setup complete ==="
}


# === Requirements File Management ===

# Freeze exact versions (for deployment)
pip freeze > requirements-lock.txt

# Generate constraints file
pip list --format=freeze | sort > installed-packages.txt

# Diff requirements
diff_requirements() {
    local old="$1"
    local new="$2"
    comm -3 <(sort "$old") <(sort "$new")
}


# === Utility Functions ===

# Run a command inside the venv
run_in_venv() {
    local venv_dir="${1:-.venv}"
    shift
    source "$venv_dir/bin/activate"
    "$@"
    local exit_code=$?
    deactivate
    return $exit_code
}

# Example:
# run_in_venv .venv python -c "import django; print(django.VERSION)"


# Check if inside a virtual environment
in_venv() {
    [[ -n "${VIRTUAL_ENV:-}" ]]
}

in_venv && echo "Inside venv: $VIRTUAL_ENV" || echo "Not in a venv"


# Create project with venv
create_python_project() {
    local project="$1"
    mkdir -p "$project/src" "$project/tests"
    cd "$project" || return 1

    python3 -m venv .venv
    source .venv/bin/activate

    cat > requirements.txt <<'EOF'
# Core dependencies
# requests>=2.31.0
# click>=8.1.0
EOF

    cat > setup.cfg <<'EOF'
[metadata]
name = example
version = 0.1.0

[options]
packages = find:
install_requires =
EOF

    deactivate
    echo "Project '$project' created with virtual environment"
}


# === Docker Integration ===

# Build arg to avoid pip issues
# FROM python:3.11-slim
# ENV PIP_NO_CACHE_DIR=1
# ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first (layer caching)
# COPY requirements.txt .
# RUN pip install -r requirements.txt


# === CLI Entry Point Pattern ===

# Entry point that auto-manages venv
if [[ ! -d .venv ]]; then
    echo "First run: setting up environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

python -m myapp "$@"
```

## Common Mistakes

```bash
# WRONG: Using pip without virtualenv (pollutes system Python)
sudo pip install requests  # Modifies system Python — bad!

# CORRECT: Always use a virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install requests


# WRONG: Committing virtual environment to version control
git add .venv/  # Bloated, platform-specific, no benefit

# CORRECT: .gitignore entry
echo ".venv/" >> .gitignore


# WRONG: Not using --upgrade pip in setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # Old pip may fail to resolve dependencies

# CORRECT: Upgrade pip first
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt


# WRONG: Relying on global Python for reproducible builds
python setup.py develop  # Works on one machine, breaks on another

# CORRECT: Consistent environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]


# WRONG: Using system pip on macOS (Homebrew Python)
/usr/local/bin/pip3 install requests  # System Python — fragile!

# CORRECT: Use pyenv + venv
# Install: brew install pyenv
# pyenv install 3.11.7
# pyenv local 3.11.7
python3 -m venv .venv
source .venv/bin/activate


# WRONG: Not checking Python version compatibility
# Installing packages that require Python 3.10+ when running 3.8

# CORRECT: Check Python version in setup script
python3 -c "import sys; assert sys.version_info >= (3,9), 'Python 3.9+ required'"
```

## Gotchas
- **PATH ordering**: Activating a venv prepends to PATH. If anything is out of order, `python` and `pip` may resolve to system versions instead of venv versions. Check with `which python` after activation.
- **Bash shebang in venv scripts**: If you write a script with `#!/usr/bin/env python`, it may not use the venv's Python. Use `#!/usr/bin/env python3` and activate the venv first, or use pip-installed entry points.
- **deactivate is a shell function**: When you run `deactivate`, it's a shell function defined by the activate script, not a binary. Calling it from a subshell (`source .venv/bin/activate && deactivate`) works only if sourced in the same shell.
- **pip cache and CI**: In CI environments, pip's HTTP cache can grow unbounded. Set `PIP_NO_CACHE_DIR=1` to disable caching, or mount a persistent volume for the cache directory.
- **Platform-specific wheels**: Some packages (psycopg2, cryptography) need system libraries. Use the `--only-binary` flag or install platform-specific build dependencies via the system package manager before `pip install`.
- **pip-compile / poetry / pdm**: For lockfile-based reproducibility, consider pip-tools, Poetry, or PDM. They provide deterministic dependency resolution beyond what `pip freeze` alone offers.
- **VIRTUAL_ENV vs CONDA_PREFIX**: `VIRTUAL_ENV` is set by venv/virtualenv. `CONDA_PREFIX` is set by conda environments. Check both if you support both tools.

## Related
- bash/scripting-patterns.md
- bash/ci-scripting.md
- bash/error-handling.md
