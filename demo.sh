#!/bin/bash
# Demo: Knowledge Base → Prompt → Code
# Requires: Python 3.10+, no LLM needed (just shows the prompt)

set -e

# Pick the best python executable
if [ -f ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 &>/dev/null; then
  PYTHON="python3"
else
  PYTHON="python"
fi

echo "╔══════════════════════════════════════════════╗"
echo "║  LLM Knowledge Base — Live Demo              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Show stats
echo "📊 Knowledge Base Stats:"
$PYTHON -m llm_kb stats
echo ""

# Search demo
echo "🔍 Searching: 'FastAPI JWT authentication'"
echo "----------------------------------------"
$PYTHON -m llm_kb search "FastAPI JWT authentication" --lang python --top 1
echo ""

# Prompt demo
echo "📝 Building prompt for: 'Write a FastAPI endpoint with JWT auth'"
echo "------------------------------------------------------------"
$PYTHON -m llm_kb prompt "Write a FastAPI endpoint with JWT auth" --lang python --max-tokens 2048 | head -n 40
echo "  [... output truncated for readability ...]"
echo ""

echo "✅ To use with a real LLM, pipe the prompt output to your model:"
echo "   llm-kb prompt 'hash a file' | ollama run qwen2.5-coder:7b"
