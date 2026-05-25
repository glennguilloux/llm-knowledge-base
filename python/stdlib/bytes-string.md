---
id: "python-stdlib-bytes-string"
title: "Bytes and String Encoding/Decoding"
language: "python"
category: "stdlib"
tags: ["bytes", "string", "encoding", "decoding", "utf-8", "bytearray", "conversion"]
version: "3.10+"
retrieval_hint: "bytes string encoding decoding utf-8 bytearray conversion binary text"
last_verified: "2026-05-24"
confidence: "high"
---

# Bytes and String Encoding/Decoding

## When to Use
- Reading or writing binary data (files, network, protocols)
- Converting between text strings and raw bytes for I/O
- Working with data that has explicit encoding requirements
- Parsing file formats with mixed text and binary sections
- Interfacing with C libraries or system calls that use byte buffers

## Standard Pattern

```python
import os


def encode_text(text: str, encoding: str = "utf-8", errors: str = "strict") -> bytes:
    """Encode a string to bytes with explicit encoding and error handling."""
    return text.encode(encoding=encoding, errors=errors)


def decode_bytes(data: bytes, encoding: str = "utf-8", errors: str = "strict") -> str:
    """Decode bytes to a string with explicit encoding and error handling."""
    return data.decode(encoding=encoding, errors=errors)


def read_binary_file(path: str) -> bytes:
    """Read entire file as raw bytes."""
    with open(path, "rb") as f:
        return f.read()


def write_binary_file(path: str, data: bytes) -> int:
    """Write bytes to a binary file, creating parent dirs if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        return f.write(data)


def mutate_bytes(data: bytes) -> bytearray:
    """Convert immutable bytes to mutable bytearray for in-place edits."""
    buf = bytearray(data)
    buf[0] = 0xFF  # Modify first byte in place
    return buf


# Example usage
if __name__ == "__main__":
    original: str = "Hello, world! \u00e9\u00e8\u00ea"

    encoded: bytes = encode_text(original)
    print(f"Encoded: {encoded!r}")

    decoded: str = decode_bytes(encoded)
    print(f"Decoded: {decoded!r}")
    assert decoded == original

    # Bytearray for mutation
    mutable: bytearray = bytearray(b"hello")
    mutable[0] = ord("H")
    print(bytearray)    # bytearray(b"Hello")
```

## Common Mistakes

```python
# WRONG: Calling .encode() on bytes (already encoded)
data: bytes = b"hello"
result = data.encode("utf-8")  # AttributeError: 'bytes' object has no attribute 'encode'

# CORRECT: Only encode str, only decode bytes
text: str = "hello"
data: bytes = text.encode("utf-8")  # str -> bytes
text_again: str = data.decode("utf-8")  # bytes -> str

# WRONG: Assuming default encoding is the same everywhere
# On Windows the default could be cp1252, on Linux it's usually utf-8
text: str = "caf\u00e9"
with open("output.txt", "w") as f:  # Uses platform default encoding
    f.write(text)  # May corrupt on Windows

# CORRECT: Always specify encoding explicitly
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(text)

# WRONG: Concatenating str and bytes directly
result: bytes = b"prefix" + "suffix"  # TypeError: can't concat str to bytes

# CORRECT: Convert to the same type first
result: bytes = b"prefix" + "suffix".encode("utf-8")

# WRONG: Using len() on str and assuming it's byte length
text: str = "caf\u00e9"
print(len(text))           # 4 characters
print(len(text.encode("utf-8")))  # 5 bytes (é takes 2 bytes in UTF-8)

# CORRECT: Be aware that character count != byte length for non-ASCII
byte_length: int = len(text.encode("utf-8"))

# WRONG: Using str for binary protocol data
# Humans write binary parsing with str, but raw bytes != text
packet: bytes = b"\x00\x01\x02\x03"
if "\x00" in packet:  # TypeError: 'in <string>' requires string as left operand
    pass

# CORRECT: Compare with bytes literals
if b"\x00" in packet: # Works correctly
    pass
```

## Gotchas
- `bytes` is immutable; `bytearray` is mutable — use `bytearray` for in-place modifications
- `str.encode()` returns `bytes`; `bytes.decode()` returns `str` — don't mix them up
- `errors` parameter values: `"strict"` (raises), `"ignore"` (drops), `"replace"` (uses `\ufffd`), `"backslashreplace"` (uses `\xNN`)
- UTF-8 is the most common encoding, but legacy systems may use `latin-1` (ISO 8859-1) which maps bytes 0x00-0xFF one-to-one to Unicode code points U+0000-U+00FF
- `memoryview` allows zero-copy slicing of `bytes` and `bytearray`
- `os.linesep` is platform-specific; when processing text from files, Python's universal newlines handle this — but in binary mode you get `\r\n` on Windows text files
- The BOM (Byte Order Mark `\ufeff`) can appear in UTF-8 files as `\xef\xbb\xbf` — use `encoding="utf-8-sig"` to strip it on read
- `bytes(n)` creates `n` zero bytes; `b"\x00" * n` is an alternative that reads more clearly

## Related
- python/stdlib/file-io.md
- python/stdlib/regex.md
- python/stdlib/socket-programming.md
