---
id: "php-stdlib-file-io"
title: "PHP File I/O: Reading, Writing, CSV, and Uploads"
language: "php"
category: "stdlib"
tags: ["php", "file-io", "file-get-contents", "fopen", "csv", "uploads", "directory"]
version: "8.2+"
retrieval_hint: "php file_get_contents fopen fwrite CSV operations uploading files temporary files directory operations"
last_verified: "2026-05-24"
confidence: "high"
---

# PHP File I/O: Reading, Writing, CSV, and Uploads

## When to Use
- Reading and writing files in PHP
- Processing CSV file uploads
- Working with file system operations
- Handling temporary files and directories

## Standard Pattern

```php
<?php

// Simple file read — entire file to string
$content = file_get_contents('config.json');
if ($content === false) {
    throw new RuntimeException('Cannot read config.json');
}

// Simple file write — string to file
$result = file_put_contents('output.txt', 'Hello, World!', LOCK_EX);
if ($result === false) {
    throw new RuntimeException('Cannot write output.txt');
}

// Append to file
file_put_contents('log.txt', "New log entry\n", FILE_APPEND | LOCK_EX);

// Reading file line by line (memory efficient for large files)
$handle = fopen('large-file.txt', 'r');
if (!$handle) {
    throw new RuntimeException('Cannot open large-file.txt');
}
try {
    while (($line = fgets($handle)) !== false) {
        $line = rtrim($line, "\r\n");
        processLine($line);
    }
} finally {
    fclose($handle);
}

// Writing line by line
$handle = fopen('output.csv', 'w');
try {
    foreach ($rows as $row) {
        fwrite($handle, implode(',', $row) . "\n");
    }
} finally {
    fclose($handle);
}

// CSV operations with fgetcsv/fputcsv
// Reading CSV
$handle = fopen('data.csv', 'r');
try {
    $header = fgetcsv($handle);  // Read header row
    while (($row = fgetcsv($handle)) !== false) {
        $record = array_combine($header, $row);
        processRecord($record);
    }
} finally {
    fclose($handle);
}

// Writing CSV
$handle = fopen('output.csv', 'w');
try {
    fputcsv($handle, ['Name', 'Email', 'Age']);  // Header
    foreach ($users as $user) {
        fputcsv($handle, [$user->name, $user->email, $user->age]);
    }
} finally {
    fclose($handle);
}

// File upload handling
function handleUpload(array $file): string {
    // Check for upload errors
    if ($file['error'] !== UPLOAD_ERR_OK) {
        throw new RuntimeException('Upload failed with error code: ' . $file['error']);
    }
    
    // Validate file type (not just extension!)
    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $mimeType = $finfo->file($file['tmp_name']);
    $allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    if (!in_array($mimeType, $allowedTypes, true)) {
        throw new RuntimeException('Invalid file type: ' . $mimeType);
    }
    
    // Validate file size
    $maxSize = 5 * 1024 * 1024;  // 5MB
    if ($file['size'] > $maxSize) {
        throw new RuntimeException('File too large');
    }
    
    // Generate safe filename
    $extension = pathinfo($file['name'], PATHINFO_EXTENSION);
    $safeName = bin2hex(random_bytes(16)) . '.' . $extension;
    $destination = '/uploads/' . $safeName;
    
    // Move uploaded file
    if (!move_uploaded_file($file['tmp_name'], $destination)) {
        throw new RuntimeException('Failed to move uploaded file');
    }
    
    return $destination;
}

// Temporary files
$tempFile = tmpfile();  // Creates a temporary file that's deleted when closed
fwrite($tempFile, 'Temporary data');
rewind($tempFile);
$content = stream_get_contents($tempFile);
fclose($tempFile);  // File is automatically deleted

// Named temporary file
$tempPath = tempnam(sys_get_temp_dir(), 'prefix_');
file_put_contents($tempPath, 'data');
// ... use and clean up
unlink($tempPath);

// Directory operations
if (!is_dir('cache')) {
    mkdir('cache', 0755, true);  // Recursive directory creation
}

// Iterate directory
$files = scandir('uploads/');
foreach ($files as $file) {
    if ($file === '.' || $file === '..') continue;
    $path = 'uploads/' . $file;
    if (is_file($path)) {
        echo filesize($path) . " bytes: $file\n";
    }
}

// Glob for pattern matching
$csvFiles = glob('data/*.csv');
$phpFiles = glob('src/**/*.php', GLOB_BRACE);  // Limited recursive

// Recursive directory iteration
$iterator = new RecursiveDirectoryIterator('src/');
$files = new RecursiveIteratorIterator($iterator);
foreach ($files as $file) {
    if ($file->isFile() && $file->getExtension() === 'php') {
        echo $file->getPathname() . "\n";
    }
}

// Check file existence and permissions
if (file_exists('config.json') && is_readable('config.json')) {
    $content = file_get_contents('config.json');
}
```

## Common Mistakes

```php
<?php

// WRONG: Not checking return value of file_get_contents
$content = file_get_contents('config.json');
$data = json_decode($content);  // Crashes if file doesn't exist (false passed to json_decode)

// CORRECT: Check return value
$content = file_get_contents('config.json');
if ($content === false) {
    throw new RuntimeException('Cannot read config.json');
}

// WRONG: Not using LOCK_EX when writing (race condition)
file_put_contents('counter.txt', $newCount);  // Another process might write simultaneously!

// CORRECT: Use LOCK_EX for atomic writes
file_put_contents('counter.txt', $newCount, LOCK_EX);

// WRONG: Using $_FILES['file']['name'] as filename (security risk)
$target = 'uploads/' . $_FILES['file']['name'];  // User could send "../../../etc/passwd"

// CORRECT: Generate a safe filename
$extension = pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION);
$safeName = bin2hex(random_bytes(16)) . '.' . $extension;
$target = 'uploads/' . $safeName;

// WRONG: Using copy() for uploaded files instead of move_uploaded_file
copy($_FILES['file']['tmp_name'], $target);  // Bypasses upload security checks!

// CORRECT: Always use move_uploaded_file for uploads
move_uploaded_file($_FILES['file']['tmp_name'], $target);

// WRONG: Not closing file handles (resource leak)
$handle = fopen('file.txt', 'r');
$content = fread($handle, filesize('file.txt'));
// Forgot fclose() — file handle leaks!

// CORRECT: Use try/finally or file_get_contents
$handle = fopen('file.txt', 'r');
try {
    $content = fread($handle, filesize('file.txt'));
} finally {
    fclose($handle);
}

// WRONG: Validating uploads by extension only (easily spoofed)
$ext = pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION);
if ($ext === 'jpg') { /* accept */ }  // User can rename .php to .jpg!

// CORRECT: Validate MIME type with finfo
$finfo = new finfo(FILEINFO_MIME_TYPE);
$mimeType = $finfo->file($_FILES['file']['tmp_name']);
if (in_array($mimeType, ['image/jpeg', 'image/png'])) {
    // Accept
}
```

## Gotchas
- `file_get_contents()` returns `false` on failure. Always check with `=== false`.
- `LOCK_EX` in `file_put_contents()` prevents race conditions when multiple processes write simultaneously.
- `move_uploaded_file()` is the ONLY safe way to handle uploads. It checks the file was actually uploaded via HTTP POST.
- Never trust `$_FILES['file']['name']` — generate your own safe filename.
- `fgetcsv()`/`fputcsv()` handle CSV quoting and escaping automatically — don't build CSV manually.
- `fopen()` returns `false` on failure. Always check the return value.
- `tmpfile()` creates a file that's automatically deleted when closed or at script end.
- `tempnam()` creates a file that persists — you must `unlink()` it yourself.
- `scandir()` returns `.` and `..` entries — filter them out.
- Use `RecursiveDirectoryIterator` instead of `glob()` for deep directory traversal.

## Related
- php/stdlib/basics.md
- php/stdlib/error-handling.md
- php/web/laravel-basics.md
- php/security/common-vulnerabilities.md
