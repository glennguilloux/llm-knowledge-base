---
id: "swift-stdlib-file-io"
title: "File I/O in Swift: FileManager, Data, Sandboxing"
language: "swift"
category: "stdlib"
tags: ["swift", "file-io", "filemanager", "sandbox", "json"]
version: "5.9+"
retrieval_hint: "swift file I/O FileManager Data sandboxing JSON encoding decoding"
last_verified: "2026-05-24"
confidence: "high"
---

# File I/O in Swift: FileManager, Data, Sandboxing

## When to Use
- Reading and writing files from disk
- Working with the app sandbox on iOS/macOS
- Managing file URLs and directories
- Encoding/decoding Codable data to files

## Standard Pattern

```swift
import Foundation

// --- Sandbox-Aware Directory Access ---
struct FileStorage {
    let fileManager: FileManager

    init(fileManager: FileManager = .default) {
        self.fileManager = fileManager
    }

    // Get Documents directory (app sandbox)
    func documentsDirectory() throws -> URL {
        try fileManager.url(
            for: .documentDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
    }

    // Get Caches directory (not backed up, can be purged)
    func cachesDirectory() throws -> URL {
        try fileManager.url(
            for: .cachesDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
    }

    // Get temporary directory
    func temporaryDirectory() -> URL {
        fileManager.temporaryDirectory
    }

    // --- File Operations ---
    func write(data: Data, to filename: String, in directory: URL) throws {
        let fileURL = directory.appendingPathComponent(filename)
        try data.write(to: fileURL, options: .atomic)
    }

    func read(from filename: String, in directory: URL) throws -> Data {
        let fileURL = directory.appendingPathComponent(filename)
        return try Data(contentsOf: fileURL)
    }

    func delete(filename: String, in directory: URL) throws {
        let fileURL = directory.appendingPathComponent(filename)
        try fileManager.removeItem(at: fileURL)
    }

    func fileExists(filename: String, in directory: URL) -> Bool {
        let fileURL = directory.appendingPathComponent(filename)
        return fileManager.fileExists(atPath: fileURL.path)
    }

    // --- Codable Convenience ---
    func writeCodable<T: Encodable>(_ value: T, to filename: String) throws {
        let dir = try documentsDirectory()
        let data = try JSONEncoder().encode(value)
        try write(data: data, to: filename, in: dir)
    }

    func readCodable<T: Decodable>(_ type: T.Type, from filename: String) throws -> T {
        let dir = try documentsDirectory()
        let data = try read(from: filename, in: dir)
        return try JSONDecoder().decode(type, from: data)
    }

    // --- Directory Contents ---
    func contentsOf(directory: URL) throws -> [URL] {
        try fileManager.contentsOfDirectory(
            at: directory,
            includingPropertiesForKeys: [.contentModificationDateKey],
            options: [.skipsHiddenFiles]
        )
    }
}

// --- Usage Example ---
struct UserSettings: Codable {
    var username: String
    var isDarkMode: Bool
    var fontSize: Double
}

let storage = FileStorage()
let settings = UserSettings(username: "alice", isDarkMode: true, fontSize: 14.0)

// Save settings
try storage.writeCodable(settings, to: "settings.json")

// Load settings
let loaded: UserSettings = try storage.readCodable(UserSettings.self, from: "settings.json")
print(loaded.username)  // alice

// --- iCloud Backup Exclusion ---
func excludeFromBackup(url: URL) throws {
    var resourceValues = URLResourceValues()
    resourceValues.isExcludedFromBackup = true
    var mutableURL = url
    try mutableURL.setResourceValues(resourceValues)
}

// --- Security-Scoped Access (macOS sandbox) ---
func readSecuredFile(from url: URL) throws -> String {
    guard url.startAccessingSecurityScopedResource() else {
        throw FileError.accessDenied
    }
    defer { url.stopAccessingSecurityScopedResource() }
    return try String(contentsOf: url, encoding: .utf8)
}

enum FileError: Error {
    case accessDenied
    fileNotFound
}
```

## Common Mistakes

```swift
// WRONG: Hardcoding file paths (breaks in sandbox)
let path = "/Users/alice/Documents/data.json"
let data = try Data(contentsOf: URL(fileURLWithPath: path))  // Fails on iOS!

// CORRECT: Use sandbox-relative paths
let docs = try FileManager.default.url(
    for: .documentDirectory, in: .userDomainMask, appropriateFor: nil, create: false
)
let fileURL = docs.appendingPathComponent("data.json")
let data = try Data(contentsOf: fileURL)


// WRONG: Not handling file coordination (reading while writing)
// Background thread writes, main thread reads — corrupted data

// CORRECT: Use NSFileCoordinator
let coordinator = NSFileCoordinator()
var readError: NSError?
coordinator.coordinate(readingItemAt: fileURL, options: .withoutChanges, error: &readError) { url in
    data = try? Data(contentsOf: url)
}


// WRONG: Wrong search path for app data
// Using .applicationSupportDirectory instead of .documentDirectory
let appSupport = try FileManager.default.url(
    for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true
)
// Application Support is for persistent data, Documents is for user-facing files // Both valid, just different purposes

// CORRECT: Choose the right directory
// .documentDirectory — User-facing files (visible in Files app)
// .applicationSupportDirectory — App-private persistent data (not backed up fully)
// .cachesDirectory — Temporary cached data (can be purged by system)
```

## Gotchas
- **Sandbox boundaries**: iOS apps cannot access files outside their sandbox without user permission (document picker, shared container). macOS apps have the same restriction when sandboxed.
- **iCloud backup**: Files in Documents are backed up to iCloud by default. Exclude caches and temporary data with `isExcludedFromBackup` to avoid rejection for storing too much.
- **File protection**: iOS supports `FileProtectionType` (`.complete`, `.completeUnlessOpen`, `.completeUntilFirstUserAuthentication`). Files created while the device is locked may fail to read.
- **Security-scoped bookmarks**: For persistent access to user-selected files, use security-scoped bookmarks. Regular URLs become invalid after app restart.
- **Atomic writes**: `.atomic` write option writes to a temporary file, then renames it. This prevents partial writes from crashes but is slightly slower.
- **Thread safety**: `FileManager` is thread-safe for reads, but writes to the same file from multiple threads can cause data corruption. Use `NSFileCoordinator` for shared file access.
- **Unicode filenames**: Filenames can contain characters that are valid on one filesystem but not another. Always validate or sanitize user-provided filenames.

## Related
- swift/stdlib/json-codable.md
- swift/stdlib/networking.md
