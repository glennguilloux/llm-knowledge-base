#!/bin/bash
# Batch validate all knowledge base entries

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KB_DIR="$(dirname "$SCRIPT_DIR")"

cd "$KB_DIR"

echo "Validating knowledge base entries..."
echo ""

python3 validate_kb.py

echo ""
echo "Running retrieval tests..."
echo ""

python3 -m pytest test_retrieval.py -v

echo ""
echo "Validation complete!"
