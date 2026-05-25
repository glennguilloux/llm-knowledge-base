---
id: "db-postgres-json-queries"
title: "PostgreSQL JSONB Queries"
language: "sql"
category: "db"
subcategory: "json"
tags: ["postgres", "jsonb", "json", "query", "path", "operator"]
version: "14+"
retrieval_hint: "PostgreSQL JSONB json query path operator"
last_verified: "2026-05-24"
confidence: "high"
---

# PostgreSQL JSONB Queries

## When to Use
- Semi-structured data storage
- Flexible schemas
- Document-like data
- Configuration storage

## Standard Pattern

```sql
-- Create table with JSONB
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Insert JSONB data
INSERT INTO items (name, metadata) VALUES
    ('Widget', '{"color": "red", "size": "large", "tags": ["sale", "new"]}');

-- Extract values
SELECT metadata->>'color' AS color FROM items;  -- Returns text
SELECT metadata->'size' AS size FROM items;  -- Returns JSONB
SELECT metadata#>>'{tags,0}' AS first_tag FROM items;  -- Nested path

-- Filter by JSONB value
SELECT * FROM items WHERE metadata->>'color' = 'red';
SELECT * FROM items WHERE metadata @> '{"color": "red"}';  -- Contains
SELECT * FROM items WHERE metadata ? 'tags';  -- Key exists
SELECT * FROM items WHERE metadata ?| array['color', 'size'];  -- Any key exists
SELECT * FROM items WHERE metadata ?& array['color', 'size'];  -- All keys exist

-- Update JSONB
UPDATE items SET metadata = metadata || '{"price": 9.99}' WHERE id = 1;  -- Merge
UPDATE items SET metadata = metadata - 'tags' WHERE id = 1;  -- Remove key
UPDATE items SET metadata = jsonb_set(metadata, '{color}', '"blue"') WHERE id = 1;  -- Set nested

-- Index JSONB
CREATE INDEX idx_metadata ON items USING gin(metadata);  -- GIN index
CREATE INDEX idx_metadata_color ON items USING gin((metadata->'color'));  -- Specific key

-- Aggregate
SELECT
    metadata->>'color' AS color,
    COUNT(*) AS count
FROM items
GROUP BY metadata->>'color';
```

## Common Mistakes

```sql
-- WRONG: Using ->> for comparison (returns text, not JSONB)
SELECT * FROM items WHERE metadata->'price' > 10;  -- Error: can't compare JSONB with int

-- CORRECT: Cast to appropriate type
SELECT * FROM items WHERE (metadata->>'price')::numeric > 10;

-- WRONG: No index on JSONB column
SELECT * FROM items WHERE metadata @> '{"color": "red"}';  -- Full scan!

-- CORRECT: Create GIN index
CREATE INDEX idx_metadata ON items USING gin(metadata);

-- WRONG: Using -> instead of ->> for text comparison
SELECT * FROM items WHERE metadata->'color' = 'red';  -- JSONB = text fails!

-- CORRECT: Use ->> to extract as text for comparison
SELECT * FROM items WHERE metadata->>'color' = 'red';
```

## Gotchas
- `->` returns JSONB; `->>` returns text
- `#>>` extracts nested path as text
- `@>` checks if left contains right (most useful operator)
- `?` checks if key exists
- GIN index supports `@>`, `?`, `?|`, `?&` operators
- Cast `->>` to `numeric`, `boolean`, etc. for comparisons
- Use `jsonb_set()` for updating nested values

## Related
- db/postgres/indexes.md
- db/postgres/full-text-search.md
