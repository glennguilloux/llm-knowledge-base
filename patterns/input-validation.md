---
id: "patterns-input-validation"
title: "Input Validation Patterns"
language: "multi"
category: "patterns"
tags: ["validation", "input", "security", "sanitization", "injection", "whitelist"]
version: "1.0+"
retrieval_hint: "input validation whitelist sanitization injection prevention security"
last_verified: "2026-05-24"
confidence: "high"
---

# Input Validation Patterns

## When to Use
- Accepting any data from users, APIs, or external systems
- Building web forms, API endpoints, or CLI tools
- Storing data in databases (preventing injection)
- Rendering user content in HTML/UI (preventing XSS)
- Passing data to system commands or file operations

## Standard Pattern

```python
import re
from typing import Optional
from pydantic import BaseModel, field_validator, ValidationError


# --- Python with Pydantic ---

class CreateUserRequest(BaseModel):
    username: str
    email: str
    age: int
    bio: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,32}$", v):
            raise ValueError(
                "Username must be 3-32 chars: letters, digits, underscores"
            )
        return v.lower()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150")
        return v

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 500:
            raise ValueError("Bio must be under 500 characters")
        return v
```

```go
// --- Go ---

package main

import (
    "errors"
    "fmt"
    "net/mail"
    "regexp"
    "strings"
    "unicode/utf8"
)

var usernameRe = regexp.MustCompile(`^[a-zA-Z0-9_]{3,32}$`)

type CreateUserInput struct {
    Username string `json:"username" validate:"required"`
    Email    string `json:"email" validate:"required"`
    Age      int    `json:"age" validate:"required"`
    Bio      string `json:"bio"`
}

func (u *CreateUserInput) Validate() error {
    u.Username = strings.ToLower(strings.TrimSpace(u.Username))
    if !usernameRe.MatchString(u.Username) {
        return errors.New("username must be 3-32 chars: letters, digits, underscores")
    }

    u.Email = strings.ToLower(strings.TrimSpace(u.Email))
    if _, err := mail.ParseAddress(u.Email); err != nil {
        return errors.New("invalid email format")
    }

    if u.Age < 0 || u.Age > 150 {
        return errors.New("age must be between 0 and 150")
    }

    if utf8.RuneCountInString(u.Bio) > 500 {
        return errors.New("bio must be under 500 characters")
    }

    return nil
}
```

```typescript
// --- TypeScript ---

interface CreateUserInput {
  username: string;
  email: string;
  age: number;
  bio?: string;
}

const USERNAME_RE = /^[a-zA-Z0-9_]{3,32}$/;

class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValidationError";
  }
}

function validateCreateUser(input: CreateUserInput): CreateUserInput {
  const username = input.username.trim().toLowerCase();
  if (!USERNAME_RE.test(username)) {
    throw new ValidationError("Username must be 3-32 chars: letters, digits, underscores");
  }

  const email = input.email.trim().toLowerCase();
  if (!email.includes("@") || !email.includes(".")) {
    throw new ValidationError("Invalid email format");
  }

  const age = Number(input.age);
  if (!Number.isInteger(age) || age < 0 || age > 150) {
    throw new ValidationError("Age must be an integer between 0 and 150");
  }

  const bio = inputbio?.slice(0, 500);

  return { username, email, age, bio };
}
```

## Common Mistakes

```python
# WRONG: Blacklist approach (trying to block bad inputs)
def bad_validate(username):
    forbidden = ["admin", "root", "DROP", "--", "'"]
    for word in forbidden:
        if word in username:
            raise ValueError("Invalid")
    return username  # Misses countless other dangerous inputs!

# CORRECT: Whitelist approach (only allow known-good patterns)
def good_validate(username: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValueError("Only letters, digits, underscores allowed")
    return username

# WRONG: Trusting client-side validation only
# Client-side JS validates length, but attacker can send anything via curl

# CORRECT: Always validate server-side
@app.post("/api/users")
async def create_user(user_data: CreateUserRequest):  # Pydantic validates
    ...

# WRONG: Type coercion without checking
age = int(request.args.get("age", ""))  # Crashes on "abc"

# CORRECT: Validate before coercion
try:
    age = int(request.args.get("age", ""))
except (ValueError, TypeError):
    raise HTTPException(400, "age must be an integer")

# WRONG: Sanitizing instead of validating
user_input = user_input.replace("<script>", "")  # Easily bypassed

# CORRECT: Validate format, then encode for context
if not is_valid_username(user_input):
    raise ValidationError("Invalid username")
# Encode when rendering: html.escape(user_input)
```

## Gotchas
- **Whitelist > Blacklist**: It's impossible to enumerate all bad inputs. Define what IS allowed, not what isn't
- **Validation != Sanitization**: Validation rejects bad input. Sanitization transforms it. Prefer rejection
- **Context matters**: Input safe for SQL may be dangerous for HTML. Validate once, encode for each output context
- **Length limits**: Always cap string length before processing — prevents ReDoS and memory exhaustion
- **Type coercion dangers**: `parseInt("0x10")` = 16, `parseInt("10abc")` = 10, `parseInt("")` = NaN — be explicit
- **SQL injection**: Use parameterized queries/prepared statements — never concatenate user input into SQL
- **HTML/JS injection**: Output encoding (HTML entities) is the defense, not input filtering
- **Unicode normalization**: "ｓｅｌｅｃｔ" (fullwidth) bypasses some filters — normalize before validation
- **File uploads**: Validate extension, MIME type, AND file content. Never trust the client-provided filename for storage

## Related
- python/stdlib/logging-structured.md
- go/stdlib/security-basics.md
- java/stdlib/security-basics.md
- patterns/error-monitoring.md
- security/web-security-basics.md
