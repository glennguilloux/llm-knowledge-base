---
id: "db-postgres-full-text-search"
title: "PostgreSQL Full-Text Search"
language: "sql"
category: "db"
subcategory: "search"
tags: ["postgres", "full-text", "search", "tsvector", "tsquery", "ranking"]
version: "14+"
retrieval_hint: "PostgreSQL full text search tsvector tsquery ranking"
last_verified: "2026-05-22"
confidence: "high"
---

# PostgreSQL Full-Text Search

## When to Use
- Searching text content
- Relevance ranking
- Multi-language search
- Replacing LIKE queries

## Standard Pattern

```sql
-- Add tsvector column
ALTER TABLE posts ADD COLUMN search_vector tsvector;

-- Populate search vector
UPDATE posts SET search_vector =
    to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, ''));

-- Create GIN index
CREATE INDEX idx_posts_search ON posts USING gin(search_vector);

-- Trigger to auto-update search vector
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', coalesce(NEW.title, '') || ' ' || coalesce(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER posts_search_update
    BEFORE INSERT OR UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Search with ranking
SELECT
    id,
    title,
    ts_rank(search_vector, query) AS rank
FROM posts, to_tsquery('english', 'postgresql & indexing') AS query
WHERE search_vector @@ query
ORDER BY rank DESC;

-- Search with highlighting
SELECT
    id,
    ts_headline('english', content, query, 'StartSel=<b>, StopSel=</b>') AS highlighted
FROM posts, to_tsquery('english', 'postgresql') AS query
WHERE search_vector @@ query;

-- Phrase search
SELECT * FROM posts WHERE search_vector @@ phraseto_tsquery('english', 'full text search');

-- Simple search (less precise)
SELECT * FROM posts WHERE search_vector @@ plainto_tsquery('english', 'how to use indexes');
```

## Common Mistakes

```sql
-- WRONG: Using LIKE for text search
SELECT * FROM posts WHERE content LIKE '%postgresql%';  -- Slow, no index!

-- CORRECT: Use full-text search
SELECT * FROM posts WHERE search_vector @@ to_tsquery('english', 'postgresql');

-- WRONG: Not indexing search vector
SELECT * FROM posts WHERE search_vector @@ query;  -- Full table scan!

-- CORRECT: Create GIN index
CREATE INDEX idx_posts_search ON posts USING gin(search_vector);
```

## Gotchas
- `tsvector` stores lexemes (normalized words)
- `tsquery` represents a search query
- `@@` is the text search match operator
- `ts_rank()` returns relevance score
- `ts_headline()` highlights matching terms
- Use `plainto_tsquery()` for simple queries, `to_tsquery()` for advanced
- GIN index is required for fast text search

## Related
- db/postgres/indexes.md
- db/postgres/json-queries.md
