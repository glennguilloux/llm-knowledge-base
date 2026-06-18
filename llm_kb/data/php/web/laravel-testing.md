---
id: "php-web-laravel-testing"
title: "Laravel Testing: PHPUnit, HTTP Tests, Factories, Mocking"
language: "php"
category: "web"
tags: ["php", "laravel", "testing", "phpunit", "factories", "mocking"]
version: "10.x+"
retrieval_hint: "php laravel testing phpunit HTTP tests factories seeding mocking"
last_verified: "2026-05-24"
confidence: "high"
---

# Laravel Testing: PHPUnit, HTTP Tests, Factories, Mocking

## When to Use
- Writing tests for Laravel applications
- Testing HTTP endpoints and API responses
- Creating test data with factories
- Mocking Laravel facades and services

## Standard Pattern

```php
<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use App\Models\Post;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;

// --- HTTP Test with RefreshDatabase ---
class PostApiTest extends TestCase
{
    use RefreshDatabase, WithFaker;

    // --- Model Factory (definition) ---
    // database/factories/PostFactory.php
    // class PostFactory extends Factory
    // {
    //     public function definition(): array
    //     {
    //         return [
    //             'title' => fake()->sentence(),
    //             'content' => fake()->paragraphs(3, true),
    //             'is_published' => fake()->boolean(),
    //         ];
    //     }
    // }

    protected function setUp(): void
    {
        parent::setUp();
        // Additional setup before each test
    }

    // --- Basic HTTP Test ---
    public function test_can_list_posts(): void
    {
        Post::factory()->count(3)->create();

        $response = $this->getJson('/api/posts');

        $response->assertStatus(200)
                 ->assertJsonCount(3, 'data');
    }

    // --- Authenticated Request ---
    public function test_can_create_post_as_authenticated_user(): void
    {
        $user = User::factory()->create();
        $postData = [
            'title' => 'Test Post',
            'content' => 'Test content here...',
        ];

        $response = $this
            ->actingAs($user, 'sanctum')
            ->postJson('/api/posts', $postData);

        $response->assertStatus(201)
                 ->assertJson([
                     'data' => [
                         'title' => 'Test Post',
                     ],
                 ]);

        $this->assertDatabaseHas('posts', [
            'title' => 'Test Post',
            'user_id' => $user->id,
        ]);
    }

    // --- Authentication Test ---
    public function test_unauthenticated_user_cannot_create_post(): void
    {
        $response = $this->postJson('/api/posts', [
            'title' => 'Test',
        ]);

        $response->assertStatus(401);
    }

    // --- Validation Test ---
    public function test_post_creation_requires_title(): void
    {
        $user = User::factory()->create();

        $response = $this
            ->actingAs($user, 'sanctum')
            ->postJson('/api/posts', [
                'content' => 'Missing title',
            ]);

        $response->assertStatus(422)
                 ->assertJsonValidationErrors(['title']);
    }

    // --- Model Factory States ---
    public function test_can_filter_published_posts(): void
    {
        Post::factory()->count(2)->published()->create();
        Post::factory()->count(3)->draft()->create();

        $response = $this->getJson('/api/posts?filter=published');

        $response->assertJsonCount(2, 'data');
    }

    // --- Mocking Services ---
    public function test_sends_welcome_email_on_registration(): void
    {
        Mail::fake();

        $response = $this->postJson('/api/register', [
            'name' => 'New User',
            'email' => 'new@example.com',
            'password' => 'password123',
        ]);

        $response->assertStatus(201);

        Mail::assertSent(WelcomeMail::class, function ($mail) {
            return $mail->hasTo('new@example.com');
        });
    }

    // --- Queue Assertions ---
    public function test_dispatches_processing_job(): void
    {
        Bus::fake();

        $post = Post::factory()->create();

        Bus::assertDispatched(ProcessPostJob::class, function ($job) use ($post) {
            return $job->post->id === $post->id;
        });
    }

    // --- Event Assertions ---
    public function test_fires_post_created_event(): void
    {
        Event::fake();

        $post = Post::factory()->create();

        Event::assertDispatched(PostCreated::class);
    }
}
```

## Common Mistakes

```php
<?php

// WRONG: Not using RefreshDatabase between tests
class UserTest extends TestCase
{
    // No RefreshDatabase trait!
    // Tests leak data between each other

    public function test_create_user(): void
    {
        User::factory()->create(['email' => 'test@test.com']);
        $this->assertDatabaseCount('users', 1);
    }

    public function test_another_test(): void
    {
        // This test sees the user created above!
        $this->assertDatabaseCount('users', 1);  // Fails if second test runs first
    }
}

// CORRECT: Use RefreshDatabase
use RefreshDatabase;

// Or DatabaseTransactions for faster tests (rollback, not truncate)
use DatabaseTransactions;


// WRONG: Testing implementation details
class PostTest extends TestCase
{
    public function test_post_created(): void
    {
        $post = Post::factory()->create();
        // Testing that a specific method was called (too coupled)
        $this->assertTrue($post->wasRecentlyCreated);
    }
}

// CORRECT: Test behavior, not implementation
public function test_post_appears_in_listings(): void
{
    $post = Post::factory()->published()->create();
    $response = $this->getJson('/api/posts');
    $response->assertJsonFragment(['id' => $post->id]);
}


// WRONG: HTTP tests without assertions
class PostTest extends TestCase
{
    public function test_get_posts(): void
    {
        $response = $this->get('/api/posts');
        // No assertions! Test passes even if endpoint fails
    }
}

// CORRECT: Always assert
public function test_get_posts(): void
{
    $response = $this->getJson('/api/posts');
    $response->assertStatus(200);
}


// WRONG: Creating factories in setUp and sharing state
class PostTest extends TestCase
{
    private Post $post;

    protected function setUp(): void
    {
        parent::setUp();
        $this->post = Post::factory()->create();  // Shared mutable state!
    }
}

// CORRECT: Create data per test or use lazy properties
```

## Gotchas
- **In-memory SQLite vs production MySQL**: `RefreshDatabase` with in-memory SQLite behaves differently from MySQL. Some features (JSON, full-text, some constraint types) aren't supported the same way. Use `RefreshDatabase` with `DB_CONNECTION=mysql_test` for parity.
- **Test environment config**: Laravel sets `APP_ENV=testing` and `APP_KEY` automatically. Database config uses `phpunit.xml` `<env>` settings. Cache, session, and queue drivers default to `array` in tests.
- **Parallel testing**: Laravel 10+ supports parallel testing. Each process gets its own database (using `--parallel` flag). Ensure tests don't depend on shared state.
- **HTTP test methods**: `get()` follows redirects; `getJson()` does not. `post()` sends URL-encoded form data; `postJson()` sends JSON. Choose the right method.
- **Factory `sequence()`**: Use `Factory::sequence()` for alternating states: `Post::factory()->count(3)->sequence(fn => ['is_published' => true], fn => ['is_published' => false])->create()`.
- **DatabaseTransactions vs RefreshDatabase**: `DatabaseTransactions` wraps each test in a transaction (faster but misses side effects like auto-increment). `RefreshDatabase` truncates all tables (slower but cleaner).
- **Mail/Event/Queue faking**: `Mail::fake()` globally fakes all mail. `Queue::fake()` globally fakes all jobs. Use `Bus::fake()` for specific buses. Always call `::assertNothingSent()` in negative tests.

## Related
- php/web/laravel-basics.md
- php/testing/phpunit.md
- php/web/laravel-eloquent.md
