---
id: "db-postgres-json-advanced"
title: "Advanced JSON/JSONB Operations"
language: "sql"
category: "db"
tags: ["sql", "postgresql", "json", "jsonb", "document", "query"]
version: "14+"
retrieval_hint: "jsonb operators ->> #> @> jsonb_path_query"
last_verified: "2026-05-24"
confidence: "high"
---

# Advanced JSON/JSONB Operations

## When to Use
- Storing semi-structured or document-like data
- Flexible schemas without ALTER TABLE
- Querying nested JSON structures
- API response storage and retrieval

## Standard Pattern

```sql
-- JSONB vs JSON: always prefer JSONB (binary, indexable, faster)
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert JSONB
INSERT INTO events (data) VALUES (
    '{"type": "click", "user": {"id": 1, "name": "Alice"}, "tags": ["web", "mobile"]}'
);

-- Access operators
SELECT
    data -> 'user' AS user_obj,           -- Returns JSONB object
    data ->> 'type' AS event_type,        -- Returns text
    data #> '{user, name}' AS nested_obj, -- Returns JSONB at path
    data #>> '{user, name}' AS nested_text -- Returns text at path
FROM events;

-- Containment operator @> (GIN-indexable)
SELECT * FROM events WHERE data @> '{"type": "click"}';
SELECT * FROM events WHERE data @> '{"user": {"id": 1}}';

-- Existence operator ?
SELECT * FROM events WHERE data ? 'tags';
SELECT * FROM events WHERE data ?| ARRAY['tags', 'metadata'];
SELECT * FROM events WHERE data ?& ARRAY['type', 'user'];

-- jsonb_path_query (SQL/JSON path, PG 12+)
SELECT * FROM events WHERE jsonb_path_exists(data, '$.user.id == 1');
SELECT jsonb_path_query(data, '$.user.name') FROM events;
SELECT jsonb_path_query_array(data, '$.tags[*]') FROM events;

-- Build JSON
SELECT jsonb_build_object(
    'id', 1,
    'name', 'Alice',
    'tags', jsonb_build_array('admin', 'user')
);

-- Aggregate to JSON
SELECT jsonb_agg(jsonb_build_object('id', id, 'name', name)) FROM users;

-- Update nested JSONB
UPDATE events SET data = jsonb_set(data, '{user, name}', '"Bob"');
UPDATE events SET data = data #- '{user, email}';  -- Remove key
UPDATE events SET data = data || '{"new_key": "value"}';  -- Merge

-- GIN index for containment queries
CREATE INDEX idx_events_data ON events USING GIN (data);
-- Supports @>, ?, ?|, ?& operators

-- Path index for specific keys
CREATE INDEX idx_events_type ON events ((data ->> 'type'));
-- Supports WHERE data ->> 'type' = 'click'

-- JSONB aggregation with GROUP BY
SELECT
    data ->> 'type' AS event_type,
    COUNT(*) AS count
FROM events
GROUP BY data ->> 'type';

-- Lateral join to unnest JSONB arrays
SELECT e.id, tag.value
FROM events e, LATERAL jsonb_array_elements_text(e.data -> 'tags') AS tag;
```

## Common Mistakes

```sql
-- WRONG: Using JSON instead of JSONB
CREATE TABLE events (data JSON);  -- Text storage, no indexing, slow queries

-- CORRECT: Use JSONB (binary, indexable)
CREATE TABLE events (data JSONB);

-- WRONG: Using ->> when you need JSONB (loses type info)
SELECT data ->> 'user' FROM events;  -- Returns text, not JSONB
-- Can't use @> on text result

-- CORRECT: Use -> for JSONB, ->> for text
SELECT data -> 'user' FROM events;   -- Returns JSONB (can use @>)
SELECT data ->> 'type' FROM events;  -- Returns text (for comparison)

-- WRONG: No index on JSONB queries
SELECT * FROM events WHERE data @> '{"type": "click"}';
-- Sequential scan on large table

-- CORRECT: Create GIN index
CREATE INDEX idx_events_data ON events USING GIN (data);

-- WRONG: Updating entire JSONB for one field change
UPDATE events SET data = '{"type": "click", "user": {"id": 1, "name": "Bob"}}';
-- Overwrites other fields

-- CORRECT: Use jsonb_set for partial updates
UPDATE events SET data = jsonb_set(data, '{user, name}', '"Bob"');

-- WRONG: Casting JSONB to text for comparison
SELECT * FROM events WHERE data::text LIKE '%click%';
-- No index, slow, matches partial strings

-- CORRECT: Use containment operator
SELECT * FROM events WHERE data @> '{"type": "click"}';

-- WRONG: Not handling missing keys
SELECT data ->> 'nonexistent' FROM events;  -- Returns NULL silently
-- May cause unexpected NULL propagation

-- CORRECT: Check existence first
SELECT * FROM events WHERE data ? 'required_key';
```

## Gotchas
- `JSONB` is almost always better than `JSON` — binary storage, indexable, faster
- `->` returns JSONB (object/array), `->>` returns text (scalar values)
- `#>` returns JSONB at a path, `#>>` returns text at a path
- `@>` containment operator is GIN-indexable — the primary optimization path
- `jsonb_set` creates the path if it doesn't exist — use `||` for top-level merge
- `#-` operator removes a key at a specified path
- `jsonb_path_query` (SQL/JSON path) is more powerful than operators for complex queries
- GIN index on JSONB supports `@>`, `?`, `?|`, `?&` — not `->` or `->>`
- For specific key queries, create expression index: `(data ->> 'type')`
- JSONB is larger on disk than normalized columns — consider trade-offs
- `jsonb_array_elements` unnests an array into rows; `jsonb_array_elements_text` returns text
- JSONB keys are unordered — `{"a":1,"b":2}` equals `{"b":2,"a":1}`

## Related
- db/postgres/indexing-strategies.md
- db/postgres/query-optimization.md
- db/postgres/ctes.md
