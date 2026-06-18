---
id: "php-web-laravel-basics"
title: "Laravel Basics: Routes, Controllers, Eloquent, and Validation"
language: "php"
category: "web"
tags: ["php", "laravel", "routes", "controllers", "eloquent", "blade", "validation"]
version: "10.x+"
retrieval_hint: "php laravel routes controllers middleware Eloquent ORM migrations Blade templates validation"
last_verified: "2026-05-24"
confidence: "high"
---

# Laravel Basics: Routes, Controllers, Eloquent, and Validation

## When to Use
- Building web applications with Laravel
- Creating REST APIs with Laravel
- Working with Eloquent ORM for database operations
- Using Blade templates for server-side rendering

## Standard Pattern

```php
<?php

// routes/web.php — Define routes
use App\Http\Controllers\UserController;

Route::get('/users', [UserController::class, 'index']);
Route::get('/users/{user}', [UserController::class, 'show']);
Route::post('/users', [UserController::class, 'store']);
Route::put('/users/{user}', [UserController::class, 'update']);
Route::delete('/users/{user}', [UserController::class, 'destroy']);

// Route model binding — auto-inject User model
Route::get('/users/{user}', function (User $user) {
    return $user;  // Automatically resolved by ID
});

// routes/api.php — API routes (no CSRF, no session)
Route::apiResource('users', UserController::class);

// Controller
namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;

class UserController extends Controller
{
    public function index()
    {
        $users = User::paginate(20);  // Paginated results
        return view('users.index', compact('users'));
    }

    public function show(User $user)
    {
        return view('users.show', compact('user'));
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users',
            'password' => 'required|min:8',
        ]);

        $user = User::create($validated);
        return redirect()->route('users.show', $user);
    }

    public function update(Request $request, User $user)
    {
        $validated = $request->validate([
            'name' => 'sometimes|string|max:255',
            'email' => 'sometimes|email|unique:users,email,' . $user->id,
        ]);

        $user->update($validated);
        return redirect()->route('users.show', $user);
    }

    public function destroy(User $user)
    {
        $user->delete();
        return redirect()->route('users.index');
    }
}

// Eloquent Model
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class User extends Model
{
    protected $fillable = ['name', 'email', 'password'];
    protected $hidden = ['password', 'remember_token'];
    protected $casts = [
        'email_verified_at' => 'datetime',
        'password' => 'hashed',  // Laravel 10+
    ];

    // Relationships
    public function posts()
    {
        return $this->hasMany(Post::class);
    }

    public function roles()
    {
        return $this->belongsToMany(Role::class);
    }

    // Scopes
    public function scopeActive($query)
    {
        return $query->where('active', true);
    }

    // Accessor
    public function getFullNameAttribute(): string
    {
        return $this->first_name . ' ' . $this->last_name;
    }
}

// Eloquent queries
$users = User::all();
$user = User::find(1);
$user = User::where('email', 'alice@example.com')->first();
$users = User::where('active', true)->orderBy('name')->paginate(20);
$user = User::create(['name' => 'Alice', 'email' => 'a@b.com']);
$user->update(['name' => 'Bob']);
$user->delete();

// Blade template (resources/views/users/index.blade.php)
// @extends('layouts.app')
// @section('content')
// <h1>Users</h1>
// @forelse ($users as $user)
//     <div>{{ $user->name }} ({{ $user->email }})</div>
// @empty
//     <p>No users found.</p>
// @endforelse
// {{ $users->links() }}  // Pagination links
// @endsection

// Middleware
Route::middleware(['auth', 'verified'])->group(function () {
    Route::resource('posts', PostController::class);
});

// Validation (Form Request)
namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreUserRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users,email',
            'password' => 'required|min:8|confirmed',
        ];
    }
}
```

## Common Mistakes

```php
<?php

// WRONG: N+1 query problem in Blade
// @foreach ($users as $user)
//     {{ $user->posts->count() }}  // One query per user!
// @endforeach

// CORRECT: Eager load relationships
$users = User::with('posts')->get();
// @foreach ($users as $user)
//     {{ $user->posts->count() }}  // No extra query
// @endforeach

// WRONG: Not using mass assignment protection
User::create($request->all());  // User could set 'is_admin' => true!

// CORRECT: Use $fillable or $guarded
class User extends Model {
    protected $fillable = ['name', 'email', 'password'];
}

// Or validate first:
User::create($request->validated());

// WRONG: Not using route model binding
public function show($id) {
    $user = User::find($id);  // Returns null if not found
    // No 404 automatically
}

// CORRECT: Use route model binding
public function show(User $user) {
    // Automatically returns 404 if user not found
    return view('users.show', compact('user'));
}

// WRONG: Using DB facade instead of Eloquent for simple queries
$users = DB::table('users')->where('active', 1)->get();
// Returns stdClass objects, no model features

// CORRECT: Use Eloquent for model-based queries
$users = User::where('active', true)->get();
// Returns User model instances with relationships, accessors, etc.

// WRONG: Not using pagination for large datasets
$users = User::all();  // Loads ALL users into memory!

// CORRECT: Always paginate
$users = User::paginate(20);
```

## Gotchas
- Eloquent uses `snake_case` for database columns by default (`first_name` maps to `firstName` accessor).
- `$fillable` defines which fields can be mass-assigned. `$guarded` defines which cannot. Use one or the other.
- Route model binding automatically returns 404 if the model is not found.
- `with('relation')` eager loads relationships to avoid N+1 queries. Always eager load in loops.
- Blade `{{ }}` auto-escapes output with `htmlspecialchars()`. Use `{!! !!}` for raw HTML (dangerous!).
- Laravel middleware runs before the controller. Use it for auth, logging, CORS, etc.
- `FormRequest` classes centralize validation logic and keep controllers clean.
- Eloquent `update()` returns the number of affected rows. `save()` returns boolean.
- Migrations are version-controlled schema changes. Always use them instead of manual SQL.

## Related
- php/stdlib/basics.md
- php/db/pdo.md
- php/stdlib/error-handling.md
- php/security/common-vulnerabilities.md
