---
id: "bash-makefile-patterns"
title: "Makefile Patterns: Targets, Variables, Automation"
language: "bash"
category: "devops"
tags: ["bash", "makefile", "automation", "targets", "variables", "phony"]
version: "n/a"
retrieval_hint: "bash makefile targets variables .PHONY task automation automatic variables"
last_verified: "2026-05-24"
confidence: "high"
---

# Makefile Patterns: Targets, Variables, Automation

## When to Use
- Automating repetitive development tasks
- Building, testing, and deploying projects
- Documenting project commands in a standard way
- Creating reproducible build environments

## Standard Pattern

```makefile
# === Variables ===

# Simple (lazy) variable — evaluated each time
CC      = gcc
CFLAGS  = -Wall -Wextra -O2

# Simply-expanded (immediate) — evaluated once
LIBDIR := $(shell pkg-config --libdir)
VERSION := 1.0.0

# Conditional assignment (only if not already set)
OPTFLAGS ?= -O2

# Append
CFLAGS += -std=c11

# Automatic variables
# $@   — Target name
# $<   — First prerequisite
# $^   — All prerequisites
# $?   — Prerequisites newer than target
# $*   — Stem (match wildcard %)


# === Phony Targets ===
.PHONY: all clean test lint build deploy help

# First target is default
all: build test

# Build
build: bin/myapp

bin/myapp: src/main.c src/utils.c | bin/
	$(CC) $(CFLAGS) -o $@ $^

# Order-only prerequisite (| bin/) — only create if missing
bin/:
	mkdir -p $@

# Test
test: build
	./bin/myapp --test
	./scripts/run_tests.sh

# Lint
lint:
	shellcheck scripts/*.sh
	clang-tidy src/*.c -- $(CFLAGS)

# Clean
clean:
	rm -rf bin/
	rm -rf build/

# Install
install: build
	cp bin/myapp /usr/local/bin/

# Help (self-documenting)
help:
	@echo "Available targets:"
	@echo "  all       Build and test (default)"
	@echo "  build     Compile the project"
	@echo "  test      Run tests"
	@echo "  lint      Run linters"
	@echo "  clean     Remove build artifacts"
	@echo "  install   Install to /usr/local/bin"
	@echo "  deploy    Deploy to production"
	@echo "  help      Show this message"


# === Pattern Rules ===
%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

# Multiple targets with same recipe
build-dev build-prod: build
	@echo "Building for $(subst build-,,$@)"


# === Conditionals ===
ifeq ($(ENV),production)
	CFLAGS += -O3 -DNDEBUG
else
	CFLAGS += -g -DDEBUG
endif


# === Functions ===
SRCS := $(wildcard src/*.c)
OBJS := $(SRCS:.c=.o)
HEADERS := $(wildcard include/*.h)

# List to check if files exist
check-files:
	@for file in $(SRCS); do \
		if [ ! -f "$$file" ]; then \
			echo "Missing: $$file"; \
			exit 1; \
		fi; \
	done


# === Include other Makefiles ===
-include config.mk  # Optional include (no error if missing)


# === Multi-line Recipes ===
deploy:
	@echo "=== Deploying version $(VERSION) ==="
	@./scripts/build_docker.sh
	@./scripts/push_docker.sh
	@./scripts/deploy.sh staging
	@echo "=== Deployment complete ==="
```

## Common Mistakes

```makefile
# WRONG: Missing .PHONY for targets that don't produce files
clean:
	rm -rf build/
# If a file named "clean" exists, this target never runs!

# CORRECT: Declare phony targets
.PHONY: clean


# WRONG: Using = when := is needed (lazy vs immediate)
TIMESTAMP = $(shell date)  # Re-evaluated every time!
# Each use of $(TIMESTAMP) is a different timestamp

# CORRECT: Use := for immediate evaluation
TIMESTAMP := $(shell date)  # Evaluated once


# WRONG: Not escaping $ in shell commands (Make interprets $)
deploy:
	@echo "PID is $$"  # Make sees $ as variable reference

# CORRECT: Double $$ for shell variables
deploy:
	@echo "PID is $$$$"  # $$ → $ in shell


# WRONG: Using spaces instead of tabs in recipes
build:
	echo "Building..."  # Error: missing separator (must be tab)

# CORRECT: Use tab character before recipe lines
build:
	@echo "Building..."


# WRONG: Not using automatic variables (repeating target name)
src/%.o: src/%.c
	gcc -c -o src/%.o src/%.c  # Redundant, error-prone

# CORRECT: Use automatic variables
src/%.o: src/%.c
	$(CC) $(CFLAGS) -c -o $@ $<
```

## Gotchas
- **Tab vs spaces**: Makefile recipes MUST be indented with actual tab characters, not spaces. This is a Make syntax requirement. Most editors have a "use tabs in Makefiles" option.
- **Recursive variable expansion**: Variables defined with `=` are recursively expanded every time they're used. Use `:=` for simply-expanded (immediate) variables to avoid infinite loops and performance issues.
- **$(MAKE) vs make**: In recursive make calls, always use `$(MAKE)` instead of `make` to pass the same flags (like `-j` for parallel execution) to sub-makes.
- **Order-only prerequisites**: Use `|` after regular prerequisites to specify order-only prerequisites. These are only created if missing but don't trigger rebuilds when updated.
- **.DEFAULT_GOAL**: Set the default target with `.DEFAULT_GOAL := build` to override the first target as default.
- **Shell assignment**: `!=` assigns the output of a shell command to a variable (GNU Make 4.0+). Alternative: `VAR := $(shell command)`.
- **Include guard for variables**: Use `?=` for variables that should have a default but allow override from the command line: `make OPTFLAGS=-O3`.

## Related
- bash/scripting-patterns.md
- bash/ci-scripting.md
- bash/python-virtualenv.md
