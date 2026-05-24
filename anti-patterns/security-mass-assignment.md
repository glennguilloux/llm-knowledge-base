---
id: "anti-patterns-security-mass-assignment"
title: "Security Anti-Pattern: Mass Assignment and Overposting"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "security", "mass-assignment", "overposting", "orm", "dto"]
version: "n/a"
retrieval_hint: "mass assignment overposting accepting full user object ORM Pydantic DTO role escalation"
last_verified: "2026-05-24"
confidence: "high"
---

# Security Anti-Pattern: Mass Assignment and Overposting

## When to Use
- Building API endpoints that accept user profile updates
- Reviewing ORM model usage in request handlers
- Designing request/response DTOs for REST APIs
- Security audits of user input handling

## Standard Pattern

```python
# WRONG: Pydantic model exposes all fields
from pydantic import BaseModel

class UserUpdate(BaseModel):
    email: str
    name: str
    is_admin: bool  # Attacker sends {"is_admin": true} in profile update
    password_hash: str

@app.put("/users/{user_id}")
async def update_user(user_id: int, data: UserUpdate):
    db.update(user_id, data.dict())  # All fields written to DB

# CORRECT: Separate public and admin models
from pydantic import BaseModel

class UserProfileUpdate(BaseModel):
    email: str
    name: str

class AdminUserUpdate(BaseModel):
    email: str
    name: str
    is_admin: bool

@app.put("/users/{user_id}")
async def update_user(user_id: int, data: UserProfileUpdate):
    db.update(user_id, data.dict())  # Only safe fields
```

```python
# WRONG: Django mass assignment
def update_user(request, user_id):
    user = User.objects.get(id=user_id)
    for key, value in request.POST.items():
        setattr(user, key, value)  # Attacker sets is_staff=True
    user.save()

# CORRECT: Django explicit fields
from django.forms import ModelForm

class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['email', 'name']  # Whitelist, not exclude

# CORRECT: Manual assignment
def update_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.email = request.POST['email']
    user.name = request.POST['name']
    user.save()
```

```java
// WRONG: Spring binding full entity
@PutMapping("/users/{id}")
public User updateUser(@PathVariable Long id, @RequestBody User user) {
    user.setId(id);
    return userRepository.save(user);  // Attacker sets role=admin
}

// CORRECT: Use DTO
@PutMapping("/users/{id}")
public User updateUser(@PathVariable Long id, @RequestBody UserUpdateDto dto) {
    User user = userRepository.findById(id);
    user.setEmail(dto.getEmail());
    user.setName(dto.getName());
    return userRepository.save(user);
}

// CORRECT: JsonIgnore on sensitive fields
public class User {
    private String email;
    private String name;
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private String role;  // Cannot be set via JSON
    @JsonProperty(access = JsonProperty.Access.READ_ONLY)
    private String passwordHash;
}
```

```typescript
// WRONG: TypeORM save with full body
@Put('/users/:id')
async update(@Param('id') id: number, @Body() body: User) {
  return this.userRepository.save({ id, ...body });  // Attacker sets role
}

// CORRECT: Pick only allowed fields
class UpdateUserDto {
  @IsString() email: string;
  @IsString() name: string;
}

@Put('/users/:id')
async update(@Param('id') id: number, @Body() body: UpdateUserDto) {
  return this.userRepository.update(id, {
    email: body.email,
    name: body.name
  });
}
```

## Common Mistakes
Mass assignment vulnerabilities occur when an application accepts a full JSON object or form data and writes all fields to the database without filtering. Attackers add extra fields like `is_admin`, `role`, or `balance` to escalate privileges or manipulate data. This was the root cause of the 2012 GitHub mass assignment vulnerability. The fix is explicit field selection: use DTOs that only include writable fields, ORM-level field whitelisting, or manual property assignment. Never pass raw request bodies directly to ORM save/update methods.

## Gotchas
- Django's `exclude` is fragile — adding a new model field automatically makes it writable; prefer explicit `fields` whitelist
- Pydantic v2's `model_dump()` still includes all fields — use separate schemas for create vs update
- Spring's `@ModelAttribute` binds ALL request parameters to the model — use `@InitBinder` with `setDisallowedFields`
- Nested objects are mass-assigned too — `{ "profile": { "verified": true } }` can set nested fields
- HTTP PUT replaces the entire resource, PATCH updates specific fields — both need field filtering
- GraphQL input types have the same problem — restrict writable fields in the schema
- Even with `readonly` TypeScript types, the runtime JSON has no type enforcement

## Related
- security/web-security-basics.md
- python/web/fastapi/request-validation.md
- api-design/rest-conventions.md
