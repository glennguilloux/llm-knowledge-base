---
id: "db-mongodb-schema-design"
title: "MongoDB Schema Design Patterns"
language: "javascript"
category: "db"
subcategory: "document-store"
tags: ["mongodb", "nosql", "schema", "embedding", "referencing", "modeling", "validation"]
version: "7.0+"
retrieval_hint: "MongoDB schema design embedding referencing one-to-many validation modeling normalization"
last_verified: "2026-05-22"
confidence: "high"
---

# MongoDB Schema Design Patterns

## When to Use
- Deciding between embedding documents vs referencing separate collections
- Modeling one-to-one, one-to-many, and many-to-many relationships
- Enforcing document structure with JSON Schema validation
- Versioning document schemas across application releases

## Standard Pattern

```javascript
const { MongoClient } = require("mongodb");

const client = new MongoClient("mongodb://localhost:27017");
const db = client.db("myapp");

// --- Embedding: one-to-few (comments on a blog post) ---
// Embed when child documents are always accessed with parent
// and the number of children is bounded (< ~500)
await db.createCollection("posts");
const posts = db.collection("posts");

await posts.insertOne({
  title: "My Blog Post",
  author: "Alice",
  comments: [
    { user: "Bob", text: "Great post!", createdAt: new Date() },
    { user: "Carol", text: "Thanks for sharing", createdAt: new Date() },
  ],
  commentCount: 2,
});

// --- Referencing: one-to-many (orders → products) ---
// Reference when child set is unbounded or accessed independently
await db.createCollection("orders");
await db.createCollection("products");
const orders = db.collection("orders");
const products = db.collection("products");

const product = await products.insertOne({ name: "Widget", price: 9.99 });
await orders.insertOne({
  userId: "user123",
  productIds: [product.insertedId],
  total: 9.99,
  status: "pending",
  createdAt: new Date(),
});

// Resolve references with $lookup
const orderWithProducts = await orders.aggregate([
  { $match: { userId: "user123" } },
  {
    $lookup: {
      from: "products",
      localField: "productIds",
      foreignField: "_id",
      as: "products",
    },
  },
]).toArray();

// --- Many-to-many: students ↔ courses ---
// Use array of references on one side
await db.createCollection("students");
const students = db.collection("students");

const courseId1 = new (require("mongodb").ObjectId)();
const courseId2 = new (require("mongodb").ObjectId)();

await students.insertOne({
  name: "Dave",
  enrolledCourses: [courseId1, courseId2],
  enrollmentDate: new Date(),
});

// --- Schema validation ---
await db.createCollection("validated_users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["name", "email", "age"],
      properties: {
        name: { bsonType: "string", description: "Must be a string" },
        email: { bsonType: "string", pattern: "^.+@.+\\..+$", description: "Must be a valid email" },
        age: { bsonType: "int", minimum: 0, maximum: 150 },
        status: { enum: ["active", "inactive", "suspended"] },
      },
    },
  },
  validationLevel: "strict", // "strict" rejects invalid, "moderate" allows existing invalid docs
  validationAction: "error", // "error" rejects, "warn" logs but allows
});

// --- Schema versioning ---
// Add a schemaVersion field to handle migrations gracefully
await db.collection("users").insertOne({
  schemaVersion: 2,
  name: "Eve",
  email: "eve@example.com",
  profile: { bio: "Hello", avatar: "url" }, // v2 added profile
});

// Query: handle both versions in application code
const user = await db.collection("users").findOne({ email: "eve@example.com" });
if (user.schemaVersion < 2) {
  user.profile = { bio: "", avatar: "" }; // Apply migration in memory
}
```

## Common Mistakes

```javascript
// WRONG: Embedding unbounded array (e.g., all user activity logs)
await users.insertOne({
  name: "Alice",
  activityLog: [
    // grows without limit, exceeds 16MB document limit
    ...millionsOfEntries,
  ],
});

// CORRECT: Reference unbounded data in separate collection
await db.collection("activity_logs").insertMany([
  { userId: aliceId, action: "login", timestamp: new Date() },
  { userId: aliceId, action: "purchase", timestamp: new Date() },
]);

// WRONG: No schema validation, relying only on application code
// Different services write inconsistent documents
await db.collection("orders").insertOne({ amount: "ten dollars" }); // string not number

// CORRECT: Use JSON Schema validation at the database level
await db.createCollection("orders", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["amount"],
      properties: { amount: { bsonType: "double" } },
    },
  },
});
```

## Gotchas
- MongoDB documents have a 16MB size limit — embedding large arrays can hit this
- `$lookup` (JOIN) is expensive — if you frequently join, consider embedding instead
- Referencing requires extra queries but gives independent access and avoids document size issues
- Schema validation with `validationLevel: "moderate"` only enforces on updates, not existing documents
- Denormalization (embedding) improves read performance but makes updates more complex (must update all copies)
- `_id` is automatically indexed and unique — use it as your primary key, don't add a separate `id` field
- Arrays in MongoDB are indexed element-wise — indexing an array of objects creates multikey indexes
- `validationAction: "warn"` logs but allows invalid writes — useful during migration but dangerous in production

## Related
- db/mongodb/crud-indexing.md
- db/mongodb/aggregation.md
- db/mongodb/aggregation-advanced.md
- db/postgres/indexes.md
