---
id: "python-stdlib-shutil"
title: "File and Directory Operations with shutil"
language: "python"
category: "stdlib"
tags: ["shutil", "copy", "move", "rmtree", "archive", "directory"]
version: "3.10+"
retrieval_hint: "shutil copy file move rmtree archive directory tree"
last_verified: "2026-05-24"
confidence: "high"
---

# File and Directory Operations with shutil

## When to Use
- Copying files or entire directory trees
- Moving files/directories across filesystems
- Recursively deleting directories
- Creating and extracting archives (zip, tar)
- Getting disk usage information

## Standard Pattern

```python
import shutil
from pathlib import Path


# --- Copying files ---

# Copy file (preserves permissions, not metadata)
shutil.copy("source.txt", "dest.txt")

# Copy file (preserves permissions AND metadata — preferred)
shutil.copy2("source.txt", "dest.txt")

# Copy file to directory (keeps original filename)
shutil.copy2("source.txt", "/path/to/destination_dir/")

# Copy file content only (no permissions)
shutil.copyfile("source.txt", "dest.txt")


# --- Copying directories ---

# Copy entire directory tree
shutil.copytree("src_dir", "dst_dir")

# Copy directory, ignoring certain files
shutil.copytree(
    "src_dir",
    "dst_dir",
    ignore=shutil.ignore_patterns("*.pyc", "__pycache__", ".git"),
)

# Copy with metadata preservation (dirs_exist_ok for overwriting)
shutil.copytree("src_dir", "dst_dir", dirs_exist_ok=True)


# --- Moving and removing ---

# Move file or directory (works across filesystems)
shutil.move("old_location", "new_location")

# Recursively delete a directory tree
shutil.rmtree("directory_to_delete")

# Rmtree with error handler
def on_error(func, path, exc_info):
    """Handle errors during rmtree (e.g., read-only files)."""
    import os
    os.chmod(path, 0o700)
    func(path)

shrmtree("protected_dir", onerror=on_error)


# --- Archives ---

# Create a zip archive of a directory
shutil.make_archive("archive_name", "zip", "source_dir")

# Create a tar.gz archive
shutil.make_archive("archive_name", "gztar", "source_dir")

# Extract an archive
shutil.unpack_archive("archive_name.zip", "extract_dir")

# List supported formats
formats = shutil.get_archive_formats()
# [('bztar', 'bzip2\'ed tar-file'), ('gztar', 'gzip\'ed tar-file'),
#  ('tar', 'uncompressed tar file'), ('xztar', 'xz\'ed tar-file'), ('zip', 'ZIP file')]


# --- Disk usage ---

total, used, free = shutil.disk_usage("/")
print(f"Total: {total // (1024**3)} GB")
print(f"Used:  {used // (1024**3)} GB")
print(f"Free:  {free // (1024**3)} GB")


# --- Safe copy with pathlib ---

def safe_copy(src: str | Path, dst: str | Path) -> Path:
    """Copy a file, creating parent directories if needed."""
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        raise FileNotFoundError(f"Source not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    return Path(shutil.copy2(str(src), str(dst)))
```

## Common Mistakes

```python
# WRONG: copytree to existing directory raises FileExistsError
shutil.copytree("src", "existing_dir")  # ERROR!

# CORRECT: Use dirs_exist_ok=True (Python 3.8+)
shutil.copytree("src", "existing_dir", dirs_exist_ok=True)

# WRONG: copyfile doesn't preserve permissions or metadata
shutil.copyfile("source.txt", "dest.txt")  # Only copies content

# CORRECT: Use copy2 to preserve metadata
shutil.copy2("source.txt", "dest.txt")  # Preserves permissions + timestamps

# WRONG: rmtree on a file raises NotADirectoryError
shutil.rmtree("some_file.txt")  # ERROR!

# CORRECT: Check type or use os.remove for files
import os
if os.path.isfile("some_file.txt"):
    os.remove("some_file.txt")
else:
    shutil.rmtree("some_file.txt")

# WRONG: copy doesn't create parent directories
shutil.copy2("file.txt", "/nonexistent/dir/file.txt")  # FileNotFoundError

# CORRECT: Create parents first
Path("/nonexistent/dir").mkdir(parents=True, exist_ok=True)
shutil.copy2("file.txt", "/nonexistent/dir/file.txt")

# WRONG: move across filesystems may fail with rename
shutil.move("/mnt/a/file", "/mnt/b/file")  # May fail if different filesystems

# CORRECT: shutil.move handles cross-filesystem automatically
# It copies then deletes — but be aware it's not atomic
```

## Gotchas
- `copytree` requires the destination to NOT exist by default — use `dirs_exist_ok=True` to allow overwriting
- `copy2` preserves metadata (permissions, timestamps); `copy` only preserves permissions; `copyfile` preserves neither
- `shutil.move` across filesystems does a copy-then-delete, not an atomic rename
- `rmtree` is irreversible — there's no trash/recycle bin. Consider `send2trash` package for safer deletion
- `copytree` with `symlinks=True` copies the symlink itself, not the target
- `shutil.disk_usage` returns bytes — divide by `1024**3` for GB
- `make_archive`'s first argument is the base name (without extension) — the format suffix is added automatically
- `ignore_patterns` returns a callable for `copytree`'s `ignore` parameter — don't call it yourself
- `shutil.which("program")` finds an executable on PATH (like `which` in shell)

## Related
- python/stdlib/pathlib.md
- python/stdlib/file-io.md
- python/stdlib/zipfile-tarfile.md
