---
id: "anti-patterns-python-shutil-rmtree"
title: "Python Anti-Pattern: shutil.rmtree Footguns"
language: "python"
category: "anti-patterns"
tags: ["antipatterns", "python", "shutil", "filesystem", "rmtree", "permissions"]
version: "n/a"
retrieval_hint: "shutil.rmtree symlink delete read-only permission error onerror ignore_errors race condition FileNotFoundError"
last_verified: "2026-05-24"
confidence: "high"
---

# Python Anti-Pattern: shutil.rmtree Footguns

## When to Use
- Cleaning up temporary directories in tests or CI
- Implementing recursive directory deletion with proper error handling
- Reviewing code that deletes directory trees for edge cases
- Understanding the pitfalls of `shutil.rmtree` vs `os.walk` + `os.remove`

## Standard Pattern

```python
import os
import shutil
import tempfile
from pathlib import Path

# WRONG: rmtree on a symlink to a directory deletes the TARGET, not the link
# Given: /tmp/link -> /tmp/target/
os.symlink("/tmp/target", "/tmp/link")
shutil.rmtree("/tmp/link")   # Deletes /tmp/target/, leaves /tmp/link dangling

# CORRECT: Check and handle symlinks before rmtree
link_path = Path("/tmp/link")
if link_path.is_symlink():
    link_path.unlink()  # Just remove the symlink itself
else:
    shutil.rmtree(str(link_path))

# WRONG: rmtree on read-only files (e.g., from a Git checkout or CI artifact)
tmpdir = tempfile.mkdtemp()
readonly_file = Path(tmpdir) / "protected.txt"
readonly_file.write_text("data")
readonly_file.chmod(0o444)  # Read-only
try:
    shutil.rmtree(tmpdir)
except PermissionError:
    print("Failed! rmtree can't delete read-only files")

# CORRECT: Use onerror to handle permission errors
def handle_rm_error(func, path, exc_info):
    """Remove read-only flag and retry."""
    os.chmod(path, 0o755)
    func(path)

shutil.rmtree(tmpdir, onerror=handle_rm_error)

# WRONG: rmtree on a non-existent path (race condition)
# If another process deletes the temp dir between check and rmtree:
if os.path.exists(tmpdir_str):
    # Another process deletes it HERE
    shutil.rmtree(tmpdir_str)  # FileNotFoundError!

# CORRECT: Ignore FileNotFoundError or use ignore_errors
import errno

def safe_rmtree(path):
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass  # Already gone — that's fine

# WRONG: Using ignore_errors=True without logging (masking real problems)
shutil.rmtree("/tmp/build-cache", ignore_errors=True)
# You'll never know if permissions, symlinks, or mount issues caused failures

# CORRECT: Log errors while still being resilient
def logged_rmtree(path):
    def _onerror(func, path, exc_info):
        print(f"Warning: {func.__name__} failed on {path}: {exc_info[1]}")
    shutil.rmtree(path, onerror=_onerror)

# WRONG: Using rmtree on a mounted filesystem mount point
# /mnt/nfs/ is a mount. rmtree will fail or cause I/O errors
try:
    shutil.rmtree("/mnt/nfs/build-output")
except OSError as e:
    print(f"Mount-related error: {e}")

# CORRECT: Use os.listdir for mount points
def clean_mount(mount_path):
    """Clean contents of a mount without trying to remove the mount point."""
    for entry in os.listdir(mount_path):
        entry_path = os.path.join(mount_path, entry)
        if os.path.isfile(entry_path) or os.path.islink(entry_path):
            os.unlink(entry_path)
        elif os.path.isdir(entry_path):
            shutil.rmtree(entry_path, ignore_errors=True)

# WRONG: os.walk + os.remove (reinventing rmtree, often slower)
def manual_rmtree(path):
    # This has its own issues (permissions, symlinks, etc.)
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(path)

# CORRECT: Use shutil.rmtree directly with proper error handling
def robust_rmtree(path: str) -> None:
    """Remove a directory tree with proper error handling."""
    path_obj = Path(path)
    if not path_obj.exists():
        return
    if path_obj.is_symlink():
        path_obj.unlink()
        return
    def _onerror(func, path, exc_info):
        exc = exc_info[1]
        if isinstance(exc, PermissionError):
            os.chmod(path, 0o755)
            func(path)
        elif isinstance(exc, FileNotFoundError):
            pass  # Race condition — fine
        else:
            raise exc
    shutil.rmtree(str(path_obj), onerror=_onerror)
```

## Common Mistakes
The most dangerous footgun is calling `shutil.rmtree()` on a symlink pointing to a directory — it deletes the symlink's **target**, not the symlink itself. Second: trying to rmtree a directory tree containing read-only files raises `PermissionError` — you need an `onerror` handler to chmod and retry. Third: ignoring errors with `ignore_errors=True` can silently mask permission failures, mount errors, or disk-full conditions.

## Gotchas
- `shutil.rmtree()` on a symlink deletes the **target directory**, not the symlink — always check `is_symlink()` first
- Read-only files (mode & 0o222 == 0) cause `PermissionError` because `rmtree` calls `os.remove()` which fails on readonly POSIX files
- `rmtree.avoids_symlinks` is `True` by default — symlink files are NOT followed, but symlink **directories** ARE deleted (the target, not the link)
- Race condition: if the directory is deleted between your existence check and the rmtree call, you get `FileNotFoundError`
- NFS/samba mounts: rmtree on a mount point can hang or produce `Device or resource busy`
- Windows: files opened by other processes can't be deleted; `PermissionError` is common
- `onerror` callable receives `(func, path, exc_info)` — `func` is the failed function (e.g., `os.unlink`, `os.rmdir`), not the path
- `tempfile.TemporaryDirectory` uses a custom cleanup that handles some of these edge cases — prefer it for temp dirs
- `os.walk` + manual `os.remove`/`os.rmdir` is significantly slower than `shutil.rmtree` for deep trees because `rmtree` is implemented in C
- `shutil.rmtree` on a path longer than 260 characters fails on Windows unless extended-length path prefix `\\?\` is used
- The `onexc` parameter (Python 3.12+) replaces `onerror` with a simpler signature: `onexc(func, path, exc)` — use it if 3.12+ is your target

## Related
- anti-patterns/python-antipatterns.md
- python/stdlib/file-io.md
