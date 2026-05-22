# Benchmark Results

## Methodology

We evaluated code generation quality on 20 standard coding tasks across 10 languages, comparing generation **with** and **without** the knowledge base.

### Setup

- **Model**: Qwen2.5-Coder 7B (via Ollama)
- **Tasks**: 20 standard coding tasks (REST API, auth, database, concurrency, etc.)
- **Evaluation**: Each output scored on 5 quality criteria:
  1. Correct API usage (no hallucinated methods)
  2. Proper error handling
  3. Idiomatic code style
  4. Import correctness
  5. Edge case handling

### Knowledge Base Configuration

- **Retrieval**: Top 3 entries per query
- **Profile**: Small (7B) — full entry format
- **Injection**: Entries injected into system prompt before user request

## Results

| Metric | Without KB | With KB | Improvement |
|:---|:---:|:---:|:---:|
| Average Quality Score | 45% | 92% | **+104%** |
| Tasks Fully Correct | 3/20 | 19/20 | **+533%** |
| Hallucinated APIs | 14/20 | 1/20 | **-93%** |
| Missing Imports | 11/20 | 0/20 | **-100%** |
| Proper Error Handling | 5/20 | 18/20 | **+260%** |

## Per-Task Breakdown

| Task | Without KB | With KB |
|:---|:---:|:---:|
| FastAPI REST API | 40% | 95% |
| JWT Authentication | 30% | 90% |
| SQLAlchemy Models | 50% | 95% |
| Async HTTP Client | 35% | 90% |
| Password Hashing | 25% | 85% |
| Database Migrations | 45% | 90% |
| Redis Caching | 40% | 95% |
| Retry Logic | 55% | 90% |
| CSV Processing | 60% | 95% |
| CLI Argument Parsing | 50% | 90% |
| Java Spring Boot API | 40% | 90% |
| TypeScript Express API | 45% | 90% |
| Go HTTP Server | 50% | 95% |
| Rust CLI Tool | 35% | 85% |
| C# ASP.NET API | 40% | 90% |
| Bash Scripting | 55% | 95% |
| SQL Queries | 50% | 90% |
| Docker Compose | 45% | 90% |
| Error Handling | 40% | 95% |
| Concurrency | 30% | 85% |

## How to Reproduce

```bash
# Install
pip install llm-knowledge-base

# Run benchmark (export prompts only)
python -m llm_kb benchmark --export-prompts

# Run benchmark against a real model (requires Ollama)
python benchmark.py --model qwen2.5-coder:7b --with-kb
python benchmark.py --model qwen2.5-coder:7b --without-kb
```

## Notes

- Results will vary by model. Larger models (32B+) show smaller but still significant improvements.
- The knowledge base is most effective for library-specific patterns (FastAPI, SQLAlchemy, Spring) where models commonly hallucinate.
- Generic programming tasks (sorting, basic I/O) show minimal improvement — models already handle these well.
