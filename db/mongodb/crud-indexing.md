---
id: "db-mongodb-crud-indexing"
title: "MongoDB CRUD Operations and Indexing"
language: "javascript"
category: "db"
subcategory: "document-store"
tags: ["mongodb", "nosql", "crud", "indexing", "bulkwrite", "query-optimization"]
version: "7.0+"
retrieval_hint: "MongoDB CRUD insert update delete index compound text explain query optimization"
last_verified: "2026-05-24"
confidence: "high"
---

# MongoDB CRUD Operations and Indexing

## When to Use
- Document-oriented data with flexible schemas
- High write throughput with insertMany or bulkWrite
- Full-text search across document fields
- Query optimization with compound and text indexes
- Upsert patterns for idempotent writes

## Standard Pattern

```javascript
const { MongoClient } = require("mongodb");

const client = new MongoClient("mongodb://localhost:27017");
const db = client.db("myapp");
const users = db.collection("users");

// --- Single document CRUD ---
await users.insertOne({ name: "Alice", email: "alice@example.com", age: 30 });

const found = await users.findOne({ email: "alice@example.com" });

await users.updateOne({ email: "alice@example.com" }, { $set: { age: 31 } });

await users.deleteOne({ email: "alice@example.com" });

// --- Bulk operations ---
await users.insertMany([
  { name: "Bob", email: "bob@example.com", age: 25 },
  { name: "Carol", email: "carol@example.com", age: 28 },
  { name: "Dave", email: "dave@example.com", age: 35 },
]);

// bulkWrite for mixed operations
const bulkOps = [
  { insertOne: { document: { name: "Eve", email: "eve@example.com", age: 22 } } },
  { updateOne: { filter: { name: "Bob" }, update: { $set: { age: 26 } } } },
  { deleteOne: { filter: { name: "Dave" } } },
];
const bulkResult = await users.bulkWrite(bulkOps);
console.log(`Inserted: ${bulkResult.insertedCount}, Updated: ${bulkResult.modifiedCount}`);

// --- Upsert (insert if not exists, update if exists) ---
await users.updateOne(
  { email: "alice@example.com" },
  {
    $set: { name: "Alice Updated" },
    $setOnInsert: { email: "alice@example.com", createdAt: new Date() },
  },
  { upsert: true }
);

// --- Indexes ---
// Single field
await users.createIndex({ email: 1 }, { unique: true });

// Compound index (prefix queries use this)
await users.createIndex({ age: 1, name: 1 });

// Text index for full-text search
await users.createIndex({ name: "text", email: "text" });
const textResults = await users.find({ $text: { $search: "alice" } }).toArray();

// Explain plan
const plan = await users.find({ age: { $gt: 25 } }).explain("executionStats");
console.log("Documents examined:", plan.executionStats.totalDocsExamined);
console.log("Index used:", plan.executionStats.executionStages.inputStage?.indexName);
```

## Common Mistakes

```javascript
// WRONG: No index on frequently queried field
// Every query scans the entire collection (COLLSCAN)
const result = await users.find({ email: "alice@example.com" }).toArray();

// CORRECT: Create an index on the query field
await users.createIndex({ email: 1 }, { unique: true });
const result = await users.find({ email: "alice@example.com" }).toArray();

// WRONG: Using insertOne in a loop for bulk data
for (const user of userArray) {
  await users.insertOne(user); // N round trips
}

// CORRECT: Use insertMany for bulk inserts
await users.insertMany(userArray, { ordered: false }); // Single round trip

// WRONG: Querying without projection (returns all fields)
const user = await users.findOne({ email: "alice@example.com" });

// CORRECT: Project only needed fields
const user = await users.findOne(
  { email: "alice@example.com" },
  { projection: { name: 1, email: 1, age: 1 } }
);
```

## Gotchas
- `insertMany` with `ordered: true` (default) stops on first error; use `ordered: false` to continue past errors
- Compound index `{ a: 1, b: 1 }` supports queries on `a` alone but NOT on `b` alone (prefix rule)
- Text indexes are expensive to maintain and only one per collection is allowed
- `bulkWrite` has a default limit of 100,000 operations per batch — split larger batches
- `updateMany` returns `{ matchedCount, modifiedCount }` — `matchedCount` can differ from `modifiedCount` if the document already has the target values
- `$text` search cannot be combined with `$natural` sort or hint
- Index intersection (using two separate indexes for one query) exists but is less efficient than a compound index
- `createIndex` blocks the connection by default in older drivers — use `{ background: true }` or background option

## Related
- db/mongodb/aggregation.md
- db/mongodb/schema-design.md
- db/postgres/indexes.md
- db/postgres/indexing-strategies.md
