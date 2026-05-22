---
id: "db-mongodb-change-streams-transactions"
title: "MongoDB Change Streams and Transactions"
language: "javascript"
category: "db"
subcategory: "document-store"
tags: ["mongodb", "nosql", "change-streams", "transactions", "sessions", "real-time", "event-driven"]
version: "7.0+"
retrieval_hint: "MongoDB change streams watch transactions sessions real-time event processing retryable writes"
last_verified: "2026-05-22"
confidence: "high"
---

# MongoDB Change Streams and Transactions

## When to Use
- Real-time event processing from database changes
- Event-driven architectures (microservice communication)
- Multi-document ACID transactions across collections
- Audit logging from database operations
- Syncing data to external systems (search indexes, caches)

## Standard Pattern

```javascript
const { MongoClient } = require("mongodb");

const client = new MongoClient("mongodb://localhost:27017");
const db = client.db("myapp");

// --- Change Stream: watch a collection ---
const changeStream = db.collection("orders").watch(
  [{ $match: { operationType: { $in: ["insert", "update", "replace"] } } }],
  { fullDocument: "updateLookup" } // include full document on updates
);

changeStream.on("change", (change) => {
  console.log(`Operation: ${change.operationType}`);
  console.log(`Document ID: ${change.documentKey._id}`);

  switch (change.operationType) {
    case "insert":
      console.log("New order:", change.fullDocument);
      break;
    case "update":
      console.log("Updated fields:", change.updateDescription.updatedFields);
      break;
    case "delete":
      console.log("Deleted:", change.documentKey._id);
      break;
  }
});

// Graceful shutdown
process.on("SIGINT", async () => {
  await changeStream.close();
  await client.close();
});

// --- Change Stream with resume token (fault tolerance) ---
let resumeToken = null;
async function watchWithResume() {
  const pipeline = [{ $match: { operationType: "insert" } }];
  const options = { resumeAfter: resumeToken, fullDocument: "updateLookup" };

  const stream = db.collection("orders").watch(pipeline, options);

  stream.on("change", (change) => {
    resumeToken = change._id; // save for resume
    processChange(change);
  });

  stream.on("error", async (err) => {
    console.error("Stream error:", err.message);
    await stream.close();
    setTimeout(watchWithResume, 5000); // reconnect after delay
  });
}

// --- Multi-document transaction ---
async function transferFunds(fromAccountId, toAccountId, amount) {
  const session = client.startSession();

  try {
    session.startTransaction({
      readConcern: { level: "snapshot" },
      writeConcern: { w: "majority" },
      readPreference: "primary",
    });

    const accounts = db.collection("accounts");

    const from = await accounts.findOne({ _id: fromAccountId }, { session });
    if (from.balance < amount) {
      throw new Error("Insufficient funds");
    }

    await accounts.updateOne(
      { _id: fromAccountId },
      { $inc: { balance: -amount } },
      { session }
    );

    await accounts.updateOne(
      { _id: toAccountId },
      { $inc: { balance: amount } },
      { session }
    );

    // Record the transaction
    await db.collection("transactions").insertOne(
      { from: fromAccountId, to: toAccountId, amount, date: new Date() },
      { session }
    );

    await session.commitTransaction();
    console.log("Transfer complete");
  } catch (err) {
    await session.abortTransaction();
    console.error("Transfer failed:", err.message);
    throw err;
  } finally {
    session.endSession();
  }
}

// --- Retryable transaction with automatic retries ---
async function runTransactionWithRetry(txnFunc, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const session = client.startSession();
    try {
      session.startTransaction();
      const result = await txnFunc(session);
      await session.commitTransaction();
      return result;
    } catch (err) {
      await session.abortTransaction();
      if (err.hasErrorLabel && err.hasErrorLabel("TransientTransactionError") && attempt < maxRetries) {
        console.log(`Transient error, retrying (attempt ${attempt})...`);
        continue;
      }
      throw err;
    } finally {
      session.endSession();
    }
  }
}

// Usage
await runTransactionWithRetry(async (session) => {
  await db.collection("inventory").updateOne(
    { productId: "abc", qty: { $gte: 1 } },
    { $inc: { qty: -1 } },
    { session }
  );
  await db.collection("orders").insertOne(
    { productId: "abc", userId: "user1", status: "confirmed" },
    { session }
  );
});
```

## Common Mistakes

```javascript
// WRONG: Using transactions without replica set
// Transactions require a replica set (even single-node replica set for dev)
const session = client.startSession();
session.startTransaction(); // MongoServerError: Transaction numbers are only allowed on a replica set

// CORRECT: Ensure replica set is configured
// For local dev: mongod --replSet rs0 --bind_ip localhost
// Then: rs.initiate() in mongosh

// WRONG: Not handling resume token, losing events on restart
const stream = db.collection("orders").watch();
stream.on("change", (change) => {
  processChange(change); // if process crashes, events are lost
});

// CORRECT: Persist resume token for fault tolerance
const stream = db.collection("orders").watch();
stream.on("change", async (change) => {
  await saveResumeToken(change._id); // persist to file/DB
  processChange(change);
});
// On restart: resumeAfter: lastSavedToken

// WRONG: Keeping transactions open too long
session.startTransaction();
await longRunningOperation(); // holds locks, can cause write conflicts
await anotherLongOperation();
await session.commitTransaction();

// CORRECT: Keep transactions short — do heavy work outside
const preparedData = await longRunningOperation(); // outside transaction
session.startTransaction();
await db.collection("orders").insertOne(preparedData, { session });
await session.commitTransaction();
```

## Gotchas
- Transactions require a replica set — single-node replica set works for development
- Maximum transaction runtime is 60 seconds by default (configurable with `transactionLifetimeLimitSeconds`)
- Change streams require MongoDB 3.6+ and work only on replica sets or sharded clusters
- `resumeAfter` token expires after the oplog window — use `startAfter` for more resilient resumption
- Transactions across multiple collections hold locks on all involved collections — keep them small
- Write conflicts in transactions trigger automatic retry by the driver (configurable)
- Change streams on sharded collections may receive events out of order per-shard
- `fullDocument: "updateLookup"` adds latency — only use when you need the full document on updates
- Transactions do not support operations on capped collections or `$lookup` in change streams

## Related
- db/mongodb/crud-indexing.md
- db/mongodb/aggregation-advanced.md
- db/postgres/transactions.md
- patterns/graceful-shutdown.md
