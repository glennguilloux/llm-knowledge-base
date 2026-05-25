---
id: "php-web-laravel-eloquent"
title: "Laravel Eloquent: Models, Relationships, Scopes, Collections"
language: "php"
category: "web"
tags: ["php", "laravel", "eloquent", "orm", "relationships", "collections"]
version: "10.x+"
retrieval_hint: "php laravel eloquent ORM models relationships scopes accessors collections eager loading"
last_verified: "2026-05-24"
confidence: "high"
---

# Laravel Eloquent: Models, Relationships, Scopes, Collections

## When to Use
- Database operations in Laravel applications
- Defining and querying relationships between models
- Adding custom query scopes and accessors
- Working with collections of models

## Standard Pattern

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Support\Collection;

// --- Model Definition ---
class User extends Model
{
    protected $fillable = [
        'name',
        'email',
        'password',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'is_active' => 'boolean',
        'settings' => 'array',   // JSON column
        'password' => 'hashed',  // Laravel 10+
    ];

    // --- Relationships ---
    public function posts(): HasMany
    {
        return $this->hasMany(Post::class);
    }

    public function roles(): BelongsToMany
    {
        return $this->belongsToMany(Role::class)
            ->withTimestamps()
            ->withPivot('assigned_by');
    }

    // --- Accessors ---
    public function getFullNameAttribute(): string
    {
        return trim("{$this->first_name} {$this->last_name}");
    }

    public function getStatusBadgeAttribute(): string
    {
        return $this->is_active
            ? '<span class="badge badge-success">Active</span>'
            : '<span class="badge badge-danger">Inactive</span>';
    }

    // --- Mutators ---
    public function setPasswordAttribute(string $value): void
    {
        $this->attributes['password'] = bcrypt($value);
    }

    // --- Local Scopes ---
    public function scopeActive(Builder $query): Builder
    {
        return $query->where('is_active', true);
    }

    public function scopeCreatedAfter(Builder $query, string $date): Builder
    {
        return $query->where('created_at', '>=', $date);
    }

    public function scopeWithRecentPosts(Builder $query): Builder
    {
        return $query->with(['posts' => function (HasMany $query) {
            $query->latest()->limit(5);
        }]);
    }
}

// --- Related Model ---
class Post extends Model
{
    protected $fillable = ['title', 'content', 'user_id'];

    public function user(): \Illuminate\Database\Eloquent\Relations\BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    // Global scope — always apply
    protected static function booted(): void
    {
        static::addGlobalScope('published', function (Builder $builder) {
            $builder->where('is_published', true);
        });
    }
}

// --- Query Examples ---
// Eager loading (avoid N+1)
$users = User::with('posts')->get();
foreach ($users as $user) {
    echo $user->posts->count();  // No extra queries
}

// Nested eager loading
$users = User::with('posts.comments')->get();

// Constrained eager loading
$users = User::with(['posts' => fn ($q) => $q->where('is_published', true)])->get();

// Lazy eager loading (if already queried)
$users = User::all();
$users->load('posts');

// Scopes
$activeUsers = User::active()->get();
$recentActive = User::active()->createdAfter('2024-01-01')->get();

// Aggregates
$count = User::active()->count();
$latest = User::latest()->first();
$avgAge = User::avg('age');

// --- Collection Methods ---
$users = User::all();
$names = $users->pluck('name');
$byRole = $users->groupBy(fn ($u) => $u->roles->first()?->name ?? 'none');
$admins = $users->filter(fn ($u) => $u->isAdmin());
$firstAdmin = $users->first(fn ($u) => $u->isAdmin());
$sorted = $users->sortByDesc('created_at');
$chunks = $users->chunk(10);

// --- Chunked Processing (for large datasets) ---
User::chunk(100, function (Collection $users) {
    foreach ($users as $user) {
        // Process without loading all into memory
    }
});

// Cursor (even more memory efficient)
foreach (User::cursor() as $user) {
    // Yields each model one at a time
}
```

## Common Mistakes

```php
<?php

// WRONG: N+1 query problem
$users = User::all();
foreach ($users as $user) {
    echo $user->posts->count();  // Queries posts for EACH user!
}

// CORRECT: Eager load
$users = User::with('posts')->get();
foreach ($users as $user) {
    echo $user->posts->count();  // No extra queries
}


// WRONG: Wrong relationship type
class User extends Model {
    // A user has many roles, not belongs to many with simple FK
    public function role(): BelongsTo {
        return $this->belongsTo(Role::class);
    }
}
// User->role will be null if user has multiple roles

// CORRECT: Choose the right relationship
public function roles(): BelongsToMany {
    return $this->belongsToMany(Role::class);
}


// WRONG: Forgetting pivot data in many-to-many
$user = User::find(1);
$role = Role::find(1);
$user->roles()->attach($role);  // Missing pivot data

// CORRECT: Include pivot data
$user->roles()->attach($role, ['assigned_by' => auth()->id()]);

// Also eager load pivot:
$user->load(['roles' => fn ($q) => $q->withPivot('assigned_by')]);


// WRONG: Loading all records without pagination
$users = User::all();  // Loads millions of users into memory

// CORRECT: Use pagination
$users = User::paginate(20);  // Returns LengthAwarePaginator

// Or lazy loading for processing
User::chunk(100, function ($users) { /* process in batches */ });
```

## Gotchas
- **Lazy loading vs eager loading**: By default, lazy loading is enabled. Disable it in production with `Model::preventLazyLoading()` in `AppServiceProvider` to catch N+1 queries during development.
- **`snake_case` convention**: Laravel assumes `snake_case` for database columns and `camelCase` for accessor methods. Accessor `getFullNameAttribute()` reads column `full_name` from the database.
- **Pivot table naming**: Many-to-many pivot tables are named by alphabetically combining singular model names (e.g., `role_user`, not `user_role`). Customize with the second argument to `belongsToMany()`.
- **`$fillable` vs `$guarded`**: Use one or the other, not both. `$fillable` is a whitelist (recommended). `$guarded` is a blacklist. Leaving both empty allows mass assignment on all attributes.
- **Collection vs Query Builder**: `User::where('active', true)->get()` returns a `Collection`. `User::where('active', true)->update(...)` returns the number of affected rows. They are not interchangeable.
- **Timestamps**: Eloquent expects `created_at` and `updated_at` columns by default. Disable with `public $timestamps = false`. Customize column names with `const CREATED_AT = 'created'`.
- **Soft deletes**: Use `SoftDeletes` trait for soft deletes. Queries automatically exclude soft-deleted records. Use `withTrashed()` to include them.

## Related
- php/web/laravel-basics.md
- php/web/laravel-middleware-auth.md
- php/web/laravel-testing.md
