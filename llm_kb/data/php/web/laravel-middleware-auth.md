---
id: "php-web-laravel-middleware-auth"
title: "Laravel Middleware, Authentication, and Authorization"
language: "php"
category: "web"
tags: ["php", "laravel", "middleware", "auth", "policies", "sanctum"]
version: "10.x+"
retrieval_hint: "php laravel middleware authentication authorization policies gates sanctum"
last_verified: "2026-05-24"
confidence: "high"
---

# Laravel Middleware, Authentication, and Authorization

## When to Use
- Adding custom middleware to Laravel apps
- Implementing authentication with Laravel Breeze/Jetstream/Sanctum
- Authorizing user actions with policies and gates
- Protecting API routes with token-based auth (Sanctum)

## Standard Pattern

```php
<?php

namespace App\Http;

use Illuminate\Foundation\Http\Kernel as HttpKernel;

// --- Kernel: Middleware Registration ---
// app/Http/Kernel.php
class Kernel extends HttpKernel
{
    // Global middleware (runs on every request)
    protected $middleware = [
        \App\Http\Middleware\TrustProxies::class,
        \Illuminate\Http\Middleware\HandleCors::class,
        \App\Http\Middleware\PreventRequestsDuringMaintenance::class,
        \Illuminate\Foundation\Http\Middleware\ValidatePostSize::class,
        \App\Http\Middleware\TrimStrings::class,
        \Illuminate\Foundation\Http\Middleware\ConvertEmptyStringsToNull::class,
    ];

    // Named middleware (applied to routes)
    protected $middlewareAliases = [
        'auth'             => \App\Http\Middleware\Authenticate::class,
        'auth.basic'       => \Illuminate\Auth\Middleware\AuthenticateWithBasicAuth::class,
        'auth.session'     => \Illuminate\Session\Middleware\AuthenticateSession::class,
        'cache.headers'    => \Illuminate\Http\Middleware\SetCacheHeaders::class,
        'can'              => \Illuminate\Auth\Middleware\Authorize::class,
        'guest'            => \App\Http\Middleware\RedirectIfAuthenticated::class,
        'password.confirm' => \Illuminate\Auth\Middleware\RequirePassword::class,
        'signed'           => \Illuminate\Routing\Middleware\ValidateSignature::class,
        'throttle'         => \Illuminate\Routing\Middleware\ThrottleRequests::class,
        'verified'         => \Illuminate\Auth\Middleware\EnsureEmailIsVerified::class,
    ];

    // Middleware groups
    protected $middlewareGroups = [
        'web' => [
            \App\Http\Middleware\EncryptCookies::class,
            \Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse::class,
            \Illuminate\Session\Middleware\StartSession::class,
            \Illuminate\View\Middleware\ShareErrorsFromSession::class,
            \App\Http\Middleware\VerifyCsrfToken::class,
            \Illuminate\Routing\Middleware\SubstituteBindings::class,
        ],
        'api' => [
            \Laravel\Sanctum\Http\Middleware\EnsureFrontendRequestsAreStateful::class,
            \Illuminate\Routing\Middleware\ThrottleRequests::class.':api',
            \Illuminate\Routing\Middleware\SubstituteBindings::class,
        ],
    ];
}

// --- Custom Middleware ---
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class LogRequests
{
    public function handle(Request $request, Closure $next): Response
    {
        $start = microtime(true);

        $response = $next($request);

        $duration = (microtime(true) - $start) * 1000;
        \Log::info('Request', [
            'method' => $request->method(),
            'path' => $request->path(),
            'duration' => round($duration, 2) . 'ms',
            'status' => $response->getStatusCode(),
        ]);

        return $response;
    }
}

// --- Using Middleware in Routes ---
Route::middleware(['auth', 'verified'])->group(function () {
    Route::resource('posts', PostController::class);
    Route::get('/dashboard', [DashboardController::class, 'index']);
});

Route::middleware('throttle:60,1')->group(function () {
    Route::get('/api/users', [UserController::class, 'index']);
});

// --- Authorization: Policies ---
// php artisan make:policy PostPolicy --model=Post
namespace App\Policies;

use App\Models\User;
use App\Models\Post;

class PostPolicy
{
    public function viewAny(User $user): bool
    {
        return true;  // All authenticated users can list posts
    }

    public function view(User $user, Post $post): bool
    {
        return $user->id === $post->user_id || $user->isAdmin();
    }

    public function create(User $user): bool
    {
        return $user->hasVerifiedEmail();
    }

    public function update(User $user, Post $post): bool
    {
        return $user->id === $post->user_id;
    }

    public function delete(User $user, Post $post): bool
    {
        return $user->id === $post->user_id || $user->isAdmin();
    }
}

// Using policies in controllers
class PostController extends Controller
{
    public function update(Request $request, Post $post)
    {
        $this->authorize('update', $post);  // Throws 403 if unauthorized
        // ... update logic
    }
}

// In Blade:
// @can('update', $post)
//     <button>Edit</button>
// @endcan

// --- Authorization: Gates ---
// In AppServiceProvider:
Gate::define('export-reports', function (User $user) {
    return $user->role === 'admin' || $user->role === 'manager';
});

// Usage:
// Gate::allows('export-reports')
// $request->user()->can('export-reports')

// --- Sanctum (API Token Auth) ---
// Configuration: Already set up in Laravel 10+
// User model must use: Laravel\Sanctum\HasApiTokens

// Creating tokens
$token = $user->createToken('api-token', ['read', 'write'])->plainTextToken;

// Verifying token abilities
if ($user->tokenCan('read')) {
    // Can read resources
}

// Protecting routes
Route::middleware('auth:sanctum')->get('/user', function (Request $request) {
    return $request->user();
});
```

## Common Mistakes

```php
<?php

// WRONG: Middleware in wrong kernel group
// Middleware that needs session state added to 'api' group
protected $middlewareGroups = [
    'api' => [
        \App\Http\Middleware\StartSession::class,  // Sessions in API group!
        // ...
    ],
];

// CORRECT: API middleware group should be stateless
protected $middlewareGroups = [
    'api' => [
        \Laravel\Sanctum\Http\Middleware\EnsureFrontendRequestsAreStateful::class,
        'throttle:api',
        \Illuminate\Routing\Middleware\SubstituteBindings::class,
    ],
];


// WRONG: Not authorizing in FormRequest
class UpdatePostRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;  // Always authorizes!
    }
}

// CORRECT: Authorize in FormRequest
class UpdatePostRequest extends FormRequest
{
    public function authorize(): bool
    {
        return $this->user()->can('update', $this->route('post'));
    }
}


// WRONG: Missing Sanctum token abilities
$token = $user->createToken('api-token');  // No ability restrictions

// CORRECT: Specify abilities
$token = $user->createToken('api-token', ['read', 'write']);
```

## Gotchas
- **Middleware ordering**: Middleware runs in the order defined. `auth` middleware must come before `can` middleware (auth sets the user, can checks authorization).
- **Policy auto-discovery**: Laravel auto-discovers policies if the model and policy follow naming conventions (`User` → `UserPolicy`). Register manually in `AuthServiceProvider` for non-standard names.
- **Rate limiting auth endpoints**: Login endpoints should be rate-limited separately. Use `throttle:5,1` on login to prevent brute force attacks.
- **Sanctum SPA vs API**: Sanctum uses cookie-based session auth for SPAs (stateful) and token-based auth for APIs (stateless). Configure `SANCTUM_STATEFUL_DOMAINS` for SPA auth.
- **Authorization in views**: `@can` silently returns false for unauthenticated users. Use `@guest` to check before `@can` if you need different behavior for guests.
- **Middleware parameters**: Middleware can accept parameters: `throttle:60,1` means 60 requests per minute. Multiple parameters are comma-separated.
- **Route model binding**: Route model binding resolves models automatically. Use `$this->authorize('update', $post)` where `$post` is already the resolved model, not just an ID.

## Related
- php/web/laravel-basics.md
- php/web/laravel-eloquent.md
- php/web/laravel-testing.md
