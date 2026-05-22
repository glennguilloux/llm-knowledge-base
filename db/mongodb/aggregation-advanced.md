---
id: "db-mongodb-aggregation-advanced"
title: "MongoDB Advanced Aggregation Pipeline"
language: "javascript"
category: "db"
subcategory: "document-store"
tags: ["mongodb", "nosql", "aggregation", "pipeline", "lookup", "facet", "bucket", "analytics"]
version: "7.0+"
retrieval_hint: "MongoDB aggregation pipeline $lookup $facet $bucket $unwind $group $project analytics reporting"
last_verified: "2026-05-22"
confidence: "high"
---

# MongoDB Advanced Aggregation Pipeline

## When to Use
- Complex analytics and reporting queries
- Joining data across collections with `$lookup`
- Multi-faceted search with `$facet`
- Histogram and bucket-based grouping
- Pipeline optimization for large datasets

## Standard Pattern

```javascript
const { MongoClient } = require("mongodb");
const client = new MongoClient("mongodb://localhost:27017");
const db = client.db("analytics");

// --- $lookup: join orders with products ---
const ordersWithProducts = await db.collection("orders").aggregate([
  { $match: { status: "completed", createdAt: { $gte: new Date("2025-01-01") } } },
  {
    $lookup: {
      from: "products",
      localField: "productId",
      foreignField: "_id",
      as: "product",
    },
  },
  { $unwind: "$product" }, // flatten the single-element array
  {
    $project: {
      orderId: "$_id",
      productName: "$product.name",
      price: "$product.price",
      quantity: 1,
      total: { $multiply: ["$product.price", "$quantity"] },
      createdAt: 1,
    },
  },
  { $sort: { total: -1 } },
  { $limit: 100 },
]).toArray();

// --- $facet: run multiple aggregations in one pass ---
const dashboard = await db.collection("orders").aggregate([
  {
    $facet: {
      // Facet 1: revenue by month
      revenueByMonth: [
        {
          $group: {
            _id: { $dateToString: { format: "%Y-%m", date: "$createdAt" } },
            revenue: { $sum: "$total" },
            count: { $sum: 1 },
          },
        },
        { $sort: { _id: 1 } },
      ],
      // Facet 2: top customers
      topCustomers: [
        { $group: { _id: "$userId", totalSpent: { $sum: "$total" } } },
        { $sort: { totalSpent: -1 } },
        { $limit: 5 },
      ],
      // Facet 3: order status distribution
      statusDistribution: [
        { $group: { _id: "$status", count: { $sum: 1 } } },
      ],
    },
  },
]).toArray();

// --- $bucket: histogram of order totals ---
const priceBuckets = await db.collection("orders").aggregate([
  {
    $bucket: {
      groupBy: "$total",
      boundaries: [0, 10, 25, 50, 100, 250, 500, 1000],
      default: "1000+",
      output: {
        count: { $sum: 1 },
        avgTotal: { $avg: "$total" },
        orderIds: { $push: "$_id" },
      },
    },
  },
]).toArray();

// --- $bucketAuto: automatic equal-count buckets ---
const autoBuckets = await db.collection("orders").aggregate([
  {
    $bucketAuto: {
      groupBy: "$total",
      buckets: 5,
      output: {
        count: { $sum: 1 },
        minTotal: { $min: "$total" },
        maxTotal: { $max: "$total" },
      },
    },
  },
]).toArray();

// --- Pipeline optimization: $match and $sort early ---
const optimized = await db.collection("orders").aggregate([
  // $match first — uses indexes and reduces documents processed
  { $match: { status: "completed", createdAt: { $gte: new Date("2025-01-01") } } },
  // $sort before $group if possible — can use index
  { $sort: { createdAt: -1 } },
  // $project early to reduce document size in pipeline
  { $project: { userId: 1, total: 1, createdAt: 1 } },
  { $group: { _id: "$userId", totalSpent: { $sum: "$total" }, count: { $sum: 1 } } },
  { $sort: { totalSpent: -1 } },
  { $limit: 20 },
], { allowDiskUse: true }).toArray(); // allowDiskUse for large datasets

// --- $unwind with preserveNullAndEmptyArrays ---
const withOptional = await db.collection("orders").aggregate([
  {
    $lookup: {
      from: "reviews",
      localField: "_id",
      foreignField: "orderId",
      as: "review",
    },
  },
  {
    $unwind: {
      path: "$review",
      preserveNullAndEmptyArrays: true, // keep orders without reviews
    },
  },
]).toArray();
```

## Common Mistakes

```javascript
// WRONG: $match after $group — processes entire collection first
await db.collection("orders").aggregate([
  { $group: { _id: "$userId", total: { $sum: "$total" } } },
  { $match: { total: { $gt: 100 } } }, // filters after grouping
]);

// CORRECT: $match before $group — uses indexes, reduces input
await db.collection("orders").aggregate([
  { $match: { status: "completed" } }, // indexed filter first
  { $group: { _id: "$userId", total: { $sum: "$total" } } },
  { $match: { total: { $gt: 100 } } }, // post-group filter is fine
]);

// WRONG: Not handling $lookup returning empty array
await db.collection("orders").aggregate([
  { $lookup: { from: "users", localField: "userId", foreignField: "_id", as: "user" } },
  { $project: { userName: "$user.name" } }, // user.name is undefined, it's an array!
]);

// CORRECT: $unwind after $lookup to get a single document
await db.collection("orders").aggregate([
  { $lookup: { from: "users", localField: "userId", foreignField: "_id", as: "user" } },
  { $unwind: "$user" },
  { $project: { userName: "$user.name" } },
]);
```

## Gotchas
- `$lookup` uses equality matching only — no range or regex joins
- `$unwind` on a missing field throws an error unless `preserveNullAndEmptyArrays: true`
- Pipelines exceeding 100MB memory fail by default — use `{ allowDiskUse: true }` for large datasets
- `$facet` runs all sub-pipelines on the same input — no filtering between facets
- `$bucket` requires sorted boundaries and throws if no documents match (use `default` to catch)
- Pipeline stages execute in order — `$match` after `$group` cannot use indexes
- `$lookup` does not use indexes on the foreign collection by default — index the `foreignField`
- `$project` after `$group` can reduce memory usage by discarding unused fields early
- MongoDB 7.0+ supports `$setWindowFields` for window functions similar to SQL

## Related
- db/mongodb/aggregation.md
- db/mongodb/crud-indexing.md
- db/mongodb/schema-design.md
- db/postgres/window-functions.md
- db/postgres/query-optimization.md
