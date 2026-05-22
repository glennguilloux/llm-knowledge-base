---
id: "java-spring-mvc-file-upload"
title: "Spring MVC File Upload and Download"
language: "java"
category: "web"
subcategory: "api-framework"
tags: ["spring", "mvc", "file", "upload", "download", "multipart", "streaming"]
version: "17+"
retrieval_hint: "Spring MVC file upload download MultipartFile ResponseEntity streaming"
last_verified: "2026-05-22"
confidence: "high"
---

# Spring MVC File Upload and Download

## When to Use
- User file uploads (images, documents, CSVs)
- Serving generated files (reports, exports)
- Processing uploaded data (import CSV, process images)
- Streaming large files without loading into memory

## Standard Pattern

```java
// --- application.yml ---
// spring:
//   servlet:
//     multipart:
//       max-file-size: 10MB
//       max-request-size: 10MB

// --- File upload controller ---
@RestController
@RequestMapping("/api/files")
public class FileController {
    private static final long MAX_SIZE = 10 * 1024 * 1024;  // 10MB
    private static final Set<String> ALLOWED_TYPES = Set.of(
        "image/jpeg", "image/png", "application/pdf"
    );

    private final FileStorageService storageService;

    public FileController(FileStorageService storageService) {
        this.storageService = storageService;
    }

    @PostMapping("/upload")
    public ResponseEntity<FileInfo> upload(@RequestParam("file") MultipartFile file) {
        // Validate
        if (file.isEmpty()) {
            throw new IllegalArgumentException("File is empty");
        }
        if (file.getSize() > MAX_SIZE) {
            throw new IllegalArgumentException("File too large");
        }
        if (!ALLOWED_TYPES.contains(file.getContentType())) {
            throw new IllegalArgumentException("File type not allowed");
        }

        // Store
        String filename = storageService.store(file);
        return ResponseEntity.status(201).body(new FileInfo(filename, file.getSize(), file.getContentType()));
    }

    @PostMapping("/upload/multiple")
    public ResponseEntity<List<FileInfo>> uploadMultiple(
            @RequestParam("files") List<MultipartFile> files) {
        List<FileInfo> results = files.stream()
            .map(this::uploadSingle)
            .toList();
        return ResponseEntity.ok(results);
    }

    // --- File download ---
    @GetMapping("/download/{filename}")
    public ResponseEntity<Resource> download(@PathVariable String filename) {
        Resource resource = storageService.loadAsResource(filename);
        String contentType = "application/octet-stream";

        return ResponseEntity.ok()
            .contentType(MediaType.parseMediaType(contentType))
            .header(HttpHeaders.CONTENT_DISPOSITION,
                "attachment; filename=\"" + resource.getFilename() + "\"")
            .body(resource);
    }

    // --- Streaming large file ---
    @GetMapping("/stream/{filename}")
    public ResponseEntity<StreamingResponseBody> stream(@PathVariable String filename) {
        Path filePath = storageService.load(filename);
        StreamingResponseBody stream = outputStream -> {
            try (InputStream input = Files.newInputStream(filePath)) {
                input.transferTo(outputStream);
            }
        };

        return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_OCTET_STREAM)
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + filename + "\"")
            .body(stream);
    }
}

// --- File storage service ---
@Service
public class FileStorageService {
    private final Path root = Path.of("uploads");

    public FileStorageService() {
        Files.createDirectories(root);
    }

    public String store(MultipartFile file) {
        String filename = UUID.randomUUID() + "_" + file.getOriginalFilename();
        Path target = root.resolve(filename);
        file.transferTo(target);
        return filename;
    }

    public Resource loadAsResource(String filename) {
        Path file = root.resolve(filename);
        Resource resource = new FileSystemResource(file);
        if (!resource.exists()) {
            throw new ResourceNotFoundException("File", filename);
        }
        return resource;
    }
}
```

## Common Mistakes

```java
// WRONG: No file size limit (OOM risk)
// spring.servlet.multipart.max-file-size not set

// CORRECT: Set limits in application.yml
// spring.servlet.multipart.max-file-size=10MB
// spring.servlet.multipart.max-request-size=10MB

// WRONG: Using original filename directly (path traversal)
String filename = file.getOriginalFilename();
Path target = root.resolve(filename);  // Could be "../../etc/passwd"

// CORRECT: Generate safe filename
String filename = UUID.randomUUID() + "_" + Path.of(file.getOriginalFilename()).getFileName();

// WRONG: Loading entire file into memory for download
byte[] data = Files.readAllBytes(filePath);  // OOM for large files
return ResponseEntity.ok(data);

// CORRECT: Stream the file
return ResponseEntity.ok()
    .contentType(MediaType.APPLICATION_OCTET_STREAM)
    .body(new FileSystemResource(filePath));

// WRONG: Not closing streams
InputStream input = resource.getInputStream();  // Resource leak!

// CORRECT: Use try-with-resources
try (InputStream input = resource.getInputStream()) {
    input.transferTo(outputStream);
}
```

## Gotchas
- `MultipartFile.transferTo(File)` moves the temp file — don't use the MultipartFile after
- Default max file size is 1MB — set `spring.servlet.multipart.max-file-size` for larger files
- `@RequestParam("file") MultipartFile` matches the form field name
- Use `FileSystemResource` for files on disk; `ByteArrayResource` for in-memory data
- `Content-Disposition: attachment` triggers download; `inline` displays in browser
- `StreamingResponseBody` writes directly to the response — good for large files
- Temp files are cleaned up after the request — don't rely on them persisting
- For production, use cloud storage (S3, GCS) instead of local filesystem

## Related
- java/spring/spring-mvc.md
- java/spring/boot-basics.md
- java/spring/mvc/cors-config.md
