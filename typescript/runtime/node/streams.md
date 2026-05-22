---
id: "typescript-runtime-node-streams"
title: "Node.js Streams"
language: "typescript"
category: "stdlib"
subcategory: "io"
tags: ["stream", "readable", "writable", "transform", "pipe"]
version: "18+"
retrieval_hint: "Node.js stream readable writable transform pipe"
last_verified: "2026-05-22"
confidence: "high"
---

# Node.js Streams

## When to Use
- Processing large files
- Transforming data in transit
- Piping data between sources and destinations
- Memory-efficient I/O

## Standard Pattern

```typescript
import { createReadStream, createWriteStream } from 'fs';
import { Transform, pipeline } from 'stream';
import { createGzip, createGunzip } from 'zlib';

// Read stream
const readStream = createReadStream('input.txt', { encoding: 'utf-8' });
readStream.on('data', (chunk: string) => {
  console.log(`Received ${chunk.length} characters`);
});
readStream.on('end', () => console.log('Done'));
readStream.on('error', (err) => console.error('Error:', err));

// Write stream
const writeStream = createWriteStream('output.txt');
writeStream.write('Hello, ');
writeStream.write('World!');
writeStream.end();

// Transform stream
class UpperCaseTransform extends Transform {
  _transform(chunk: Buffer, encoding: string, callback: Function): void {
    this.push(chunk.toString().toUpperCase());
    callback();
  }
}

// Pipe chain
createReadStream('input.txt')
  .pipe(new UpperCaseTransform())
  .pipe(createWriteStream('output.txt'));

// Compress file
createReadStream('input.txt')
  .pipe(createGzip())
  .pipe(createWriteStream('input.txt.gz'));

// Decompress file
createReadStream('input.txt.gz')
  .pipe(createGunzip())
  .pipe(createWriteStream('input.txt'));

// Async iteration
import { pipeline as pipelinePromise } from 'stream/promises';

async function processFile(inputPath: string, outputPath: string): Promise<void> {
  await pipelinePromise(
    createReadStream(inputPath),
    new UpperCaseTransform(),
    createWriteStream(outputPath),
  );
}
```

## Common Mistakes

```typescript
// WRONG: Reading entire file into memory
const data = await readFile('huge.bin');  // Memory explosion!

// CORRECT: Use streams
const stream = createReadStream('huge.bin');
stream.on('data', (chunk) => processChunk(chunk));

// WRONG: Not handling errors
stream.pipe(transform).pipe(output);  // Unhandled errors!

// CORRECT: Use pipeline for error handling
pipeline(stream, transform, output, (err) => {
  if (err) console.error('Pipeline failed:', err);
});
```

## Gotchas
- Streams are event-based: 'data', 'end', 'error', 'finish'
- `pipe()` automatically handles backpressure
- `pipeline()` (stream/promises) handles errors properly
- Transform streams must implement `_transform()` method
- Call `writeStream.end()` when done writing
- Backpressure: if consumer is slow, producer pauses automatically
- Use `highWaterMark` option to control buffer size

## Related
- typescript/runtime/node/fs.md
- typescript/runtime/node/http.md
