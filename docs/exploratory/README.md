# Exploratory Testing

Use this directory for time-boxed investigations that are too open-ended for ordinary regression tests.

## What belongs here

- Retrieval failure investigations.
- Prompt-quality comparisons across model profiles.
- Edge-case notes that may become future tests.
- Manual checks for CLI, retrieval, MCP, or prompt output.
- Findings from failed smoke/sanity tests.

## What does not belong here

- Deterministic tests. Put those in `test_*.py`.
- External LLM credentials or secrets.
- Long-running benchmark output.
- Claims that replace automated assertions.

## Session template

```md
# Exploratory Session: YYYY-MM-DD topic

## Goal
What behavior or failure mode are you investigating?

## Setup
- Python version:
- Install command:
- Commands run:

## Observations
- Observation 1
- Observation 2

## Candidate test cases
- Query or command:
- Expected result:
- Actual result:

## Follow-up
- [ ] Add automated regression test if behavior should be guaranteed.
- [ ] Update docs if behavior is intentional.
- [ ] Close as exploratory-only if not worth automating.
```

## Good outcomes

- A new automated smoke, sanity, or regression test.
- A clarified retrieval expectation in `docs/test-cases/retrieval.md`.
- A docs update explaining intentional behavior.
- A bug report with exact commands and output.
