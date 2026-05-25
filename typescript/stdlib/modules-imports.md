---
id: "typescript-stdlib-modules-imports"
title: "TypeScript Modules, Imports, and Exports"
language: "typescript"
category: "stdlib"
subcategory: "modules"
tags: ["modules", "import", "export", "barrel", "dynamic-import", "commonjs", "esm"]
version: "5.0+"
retrieval_hint: "TypeScript modules import export barrel files dynamic import CommonJS interop ESM"
last_verified: "2026-05-24"
confidence: "high"
---

# TypeScript Modules, Imports, and Exports

## When to Use
- Organizing code across multiple files with ES modules
- Creating public APIs for packages with barrel files
- Lazy-loading code with dynamic `import()`
- Importing only types to avoid runtime overhead
- Interoperating with CommonJS packages (Node.js ecosystem)

## Standard Pattern

```typescript
// === Named exports (preferred) ===
// math.ts
export function add(a: number, b: number): number {
  return a + b;
}

export function multiply(a: number, b: number): number {
  return a.b * b;
}

export const PI: number = 3.14159;

// === Default export (one per module) ===
// logger.ts
export default class Logger {
  constructor(private prefix: string) {}

  log(message: string): void {
    console.log(`[${this.prefix}] ${message}`);
  }
}

// === Importing ===
// main.ts
import Logger from "./logger";                    // default import
import { add, multiply, PI } from "./math";       // named imports
import { add as sum } from "./math";               // renamed import
import * as math from "./math";                    // namespace import
import type { Logger } from "./logger";            // type-only import

// === Re-exports and barrel files ===
// utils/index.ts (barrel file)
export { add, multiply, PI } from "./math";
export { default as Logger } from "./logger";
export type { LoggerConfig } from "./types";

// Consumers import from the barrel:
import { add, Logger } from "./utils";

// === Dynamic import() for code splitting ===
async function loadHeavyModule() {
  const { processData } = await import("./heavy-processor");
  return processData();
}

// Dynamic import with error handling
async function safeImport(modulePath: string): Promise<unknown> {
  try {
    const mod = await import(modulePath);
    return mod;
  } catch (error) {
    console.error(`Failed to load module: ${modulePath}`, error);
    throw error;
  }
}

// === Type-only imports (erased at compile time) ===
import type { User, UserRole } from "./types";
// These imports are completely removed from the JS output.
// Use when you only need the type, not the runtime value.

// === CommonJS interop ===
// Importing CommonJS default export (Node.js built-ins, older packages)
import fs from "fs";                    //esModuleInterop required
import * as path from "path";           // namespace import works without esModuleInterop

// require() style (avoid in new code, but sometimes needed)
import fs = require("fs");              // TypeScript-specific syntax

// Exporting for CommonJS consumers
export = { add, multiply };            // TypeScript-specific, rare
```

## Common Mistakes

```typescript
// WRONG: mixing default and named import syntax
import { Logger } from "./logger";  // Error if Logger is a default export!

// CORRECT: use the right syntax for the export type
import Logger from "./logger";      // default export
import { add } from "./math";       // named export

// WRONG: circular dependency between modules
// a.ts: import { b } from "./b";
// b.ts: import { a } from "./a";
// This causes runtime errors — one module will see undefined imports!

// CORRECT: refactor to break the cycle
// Move shared code to a third module, or use dynamic import() inside functions
// a.ts:
async function useB() {
  const { b } = await import("./b");
  return b();
}

// WRONG: barrel files that re-export everything (causes tree-shaking failures)
// index.ts
export * from "./module-a";
export * from "./module-b";
export * from "./module-c";
// Bundlers may include ALL modules even if only one is used!

// CORRECT: be explicit about what you re-export
// index.ts
export { usefulFunction } from "./module-a";
export { AnotherThing } from "./module-b";

// WRONG: using import without type-only when only the type is needed
import { UserConfig } from "./config";
// This emits a runtime import even if UserConfig is only used as a type!

// CORRECT: use import type to ensure it's erased at compile time
import type { UserConfig } from "./config";

// WRONG: dynamic import() without error handling
const mod = await import("./optional-module");
mod.doSomething(); // Crashes if module doesn't exist!

// CORRECT: always handle dynamic import failures
try {
  const mod = await import("./optional-module");
  mod.doSomething();
} catch {
  console.warn("optional-module not available");
}
```

## Gotchas
- **Circular dependencies** compile fine but cause `undefined` at runtime. Module A imports from B which imports from A — one of them will get an empty object. Use tools like `madge` to detect cycles.
- **`import type`** is completely erased from JavaScript output. If you use a type at runtime (e.g., as a value in a decorator or `instanceof` check), you must use a regular `import`, not `import type`.
- **Barrel files** (`index.ts` re-exports) are convenient but can defeat tree-shaking in bundlers like Webpack and Rollup. Explicit re-exports are safer than `export *`.
- **`esModuleInterop`** in `tsconfig.json` allows `import fs from "fs"` syntax for CommonJS modules. Without it, you need `import * as fs from "fs"` or `import fs = require("fs")`. Most projects should enable this flag.
- **Dynamic `import()`** returns a `Promise` — it is always async. You cannot use it synchronously. The resolved module object has a `.default` property for default exports.
- **`export default` vs named exports**: Named exports enable tree-shaking and allow consumers to import only what they need. Default exports are harder for bundlers to optimize. Prefer named exports for libraries.
- When a TypeScript file uses `export =` (CommonJS-style), you must consume it with `import x = require("x")` or enable `esModuleInterop` and use `import x from "x"`.

## Related
- typescript/stdlib/generics.md
- typescript/stdlib/async-patterns.md
