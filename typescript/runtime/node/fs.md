---
id: "typescript-runtime-node-fs"
title: "Node.js File System with fs/promises"
language: "typescript"
category: "stdlib"
subcategory: "filesystem"
tags: ["fs", "file", "read", "write", "path", "node"]
version: "18+"
retrieval_hint: "Node.js fs file read write path promises"
last_verified: "2026-05-24"
confidence: "high"
---

# Node.js File System with fs/promises

## When to Use
- Reading and writing files
- File system operations (create, delete, rename)
- Directory operations
- File metadata

## Standard Pattern

```typescript
import { readFile, writeFile, mkdir, readdir, stat, unlink, rename } from 'fs/promises';
import { join, dirname } from 'path';

// Read file
async function readTextFile(path: string): Promise<string> {
  return readFile(path, 'utf-8');
}

async function readJSONFile<T>(path: string): Promise<T> {
  const content = await readFile(path, 'utf-8');
  return JSON.parse(content) as T;
}

// Write file
async function writeTextFile(path: string, content: string): Promise<void> {
  await writeFile(path, content, 'utf-8');
}

async function writeJSONFile<T>(path: string, data: T): Promise<void> {
  const content = JSON.stringify(data, null, 2);
  await writeFile(path, content, 'utf-8');
}

// Create directory (recursive)
async function ensureDir(path: string): Promise<void> {
  await mkdir(path, { recursive: true });
}

// List directory
async function listFiles(dir: string): Promise<string[]> {
  const entries = await readdir(dir, { withFileTypes: true });
  return entries
    .filter(entry => entry.isFile())
    .map(entry => entry.name);
}

// File exists
async function fileExists(path: string): Promise<boolean> {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

// Delete file
async function deleteFile(path: string): Promise<void> {
  await unlink(path);
}

// Rename/move file
async function moveFile(oldPath: string, newPath: string): Promise<void> {
  await ensureDir(dirname(newPath));
  await rename(oldPath, newPath);
}

// Read with stream (large files)
import { createReadStream } from 'fs';
import { createInterface } from 'readline';

async function readLines(filePath: string): AsyncIterable<string> {
  const stream = createReadStream(filePath, { encoding: 'utf-8' });
  return createInterface({ input: stream });
}
```

## Common Mistakes

```typescript
// WRONG: Using sync methods
const data = fs.readFileSync('file.txt', 'utf-8');  // Blocks event loop!

// CORRECT: Use async/await
const data = await readFile('file.txt', 'utf-8');

// WRONG: Not handling errors
const data = await readFile('file.txt', 'utf-8');  // Throws if file doesn't exist!

// CORRECT: Check existence or catch errors
if (await fileExists('file.txt')) {
  const data = await readFile('file.txt', 'utf-8');
}

// WRONG: Reading large file into memory
const data = await readFile('huge-file.bin');  // Memory explosion!

// CORRECT: Use streams for large files
const stream = createReadStream('huge-file.bin');
```

## Gotchas
- `fs/promises` is the modern API (avoid callback-based `fs`)
- `readFile` returns `Buffer` by default; specify `'utf-8'` for string
- `mkdir` with `{ recursive: true }` creates parent directories
- `stat` throws if file doesn't exist — check with try/catch
- `readdir` returns names by default; use `{ withFileTypes: true }` for Dirent objects
- Use `path.join()` for cross-platform path construction
- Streams are more memory-efficient for large files

## Related
- typescript/runtime/node/http.md
- typescript/runtime/node/streams.md
