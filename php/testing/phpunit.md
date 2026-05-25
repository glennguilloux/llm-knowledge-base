---
id: "php-testing-phpunit"
title: "PHPUnit: Test Structure, Assertions, Data Providers, and Mocking"
language: "php"
category: "testing"
tags: ["php", "phpunit", "testing", "assertions", "data-providers", "mocking"]
version: "10.x+"
retrieval_hint: "php PHPUnit setup test structure assertions data providers mocking database testing"
last_verified: "2026-05-24"
confidence: "high"
---

# PHPUnit: Test Structure, Assertions, Data Providers, and Mocking

## When to Use
- Writing unit tests for PHP code
- Testing classes and functions in isolation
- Using data providers for parameterized tests
- Mocking dependencies with PHPUnit's built-in mocking

## Standard Pattern

```php
<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use App\Services\UserService;
use App\Repositories\UserRepository;

class UserServiceTest extends TestCase
{
    private UserRepository $repository;
    private UserService $service;

    protected function setUp(): void
    {
        parent::setUp();
        $this->repository = $this->createMock(UserRepository::class);
        $this->service = new UserService($this->repository);
    }

    public function testFindUserReturnsUserWhenExists(): void
    {
        // Arrange
        $user = ['id' => 1, 'name' => 'Alice', 'email' => 'a@b.com'];
        $this->repository
            ->expects($this->once())
            ->method('findById')
            ->with(1)
            ->willReturn($user);

        // Act
        $result = $this->service->findUser(1);

        // Assert
        $this->assertNotNull($result);
        $this->assertEquals('Alice', $result['name']);
    }

    public function testFindUserReturnsNullWhenNotFound(): void
    {
        $this->repository
            ->method('findById')
            ->willReturn(null);

        $result = $this->service->findUser(999);

        $this->assertNull($result);
    }

    public function testCreateUserValidatesEmail(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Invalid email');

        $this->service->createUser('Alice', 'invalid-email');
    }

    public function testCreateUserHashesPassword(): void
    {
        $this->repository
            ->expects($this->once())
            ->method('create')
            ->with($this->callback(function ($data) {
                return isset($data['password'])
                    && password_verify('secret123', $data['password']);
            }))
            ->willReturn(1);

        $id = $this->service->createUser('Alice', 'a@b.com', 'secret123');
        $this->assertEquals(1, $id);
    }

    /**
     * @dataProvider validEmailProvider
     */
    public function testValidEmailsAreAccepted(string $email): void
    {
        $this->repository->method('create')->willReturn(1);

        $id = $this->service->createUser('Test', $email, 'password123');
        $this->assertGreaterThan(0, $id);
    }

    public static function validEmailProvider(): array
    {
        return [
            'simple email' => ['test@example.com'],
            'with subdomain' => ['test@mail.example.com'],
            'with plus' => ['test+tag@example.com'],
        ];
    }

    /**
     * @dataProvider invalidEmailProvider
     */
    public function testInvalidEmailsAreRejected(string $email): void
    {
        $this->expectException(\InvalidArgumentException::class);

        $this->service->createUser('Test', $email, 'password123');
    }

    public static function invalidEmailProvider(): array
    {
        return [
            'no at sign' => ['testexample.com'],
            'no domain' => ['test@'],
            'empty' => [''],
        ];
    }

    // Common assertions
    public function testCommonAssertions(): void
    {
        $array = ['name' => 'Alice', 'age' => 30];

        $this->assertIsArray($array);
        $this->assertCount(2, $array);
        $this->assertArrayHasKey('name', $array);
        $this->assertContains('Alice', $array);
        $this->assertStringContainsString('lic', 'Alice');
        $this->assertMatchesRegularExpression('/^[A-Z]/', 'Alice');
        $this->assertSame('Alice', $array['name']);  // === comparison
        $this->assertEquals(30, $array['age']);       // == comparison
        $this->assertTrue(true);
        $this->assertFalse(false);
        $this->assertNull(null);
        $this->assertGreaterThan(0, 42);
        $this->assertLessThan(100, 42);
        $this->assertCount(3, [1, 2, 3]);
    }

    // Database testing with transactions
    public function testDatabaseOperations(): void
    {
        // Use RefreshDatabase trait or manual transaction rollback
        $this->repository->method('create')->willReturn(1);
        
        $id = $this->service->createUser('Test', 'test@test.com', 'pass');
        $this->assertGreaterThan(0, $id);
    }
}

// Mocking patterns
class MockingExamplesTest extends TestCase
{
    public function testMockWithReturnMap(): void
    {
        $mock = $this->createMock(UserRepository::class);
        
        $mock->method('findById')
            ->willReturnMap([
                [1, ['id' => 1, 'name' => 'Alice']],
                [2, ['id' => 2, 'name' => 'Bob']],
                [999, null],
            ]);

        $this->assertNotNull($mock->findById(1));
        $this->assertNull($mock->findById(999));
    }

    public function testMockWithCallback(): void
    {
        $mock = $this->createMock(UserRepository::class);
        
        $mock->method('findById')
            ->willReturnCallback(function (int $id) {
                return ['id' => $id, 'name' => "User $id"];
            });

        $this->assertEquals('User 42', $mock->findById(42)['name']);
    }

    public function testMockExpectsExactCallCount(): void
    {
        $mock = $this->createMock(UserRepository::class);
        
        $mock->expects($this->exactly(2))
            ->method('save');

        $mock->save(['name' => 'Alice']);
        $mock->save(['name' => 'Bob']);
    }

    public function testMockThrowsException(): void
    {
        $mock = $this->createMock(UserRepository::class);
        
        $mock->method('findById')
            ->willThrowException(new \RuntimeException('DB error'));

        $this->expectException(\RuntimeException::class);
        $mock->findById(1);
    }
}
```

## Common Mistakes

```php
<?php

// WRONG: Not using setUp() for shared initialization
class BadTest extends TestCase
{
    public function testOne(): void
    {
        $service = new UserService(new UserRepository());  // Repeated in every test
    }
    public function testTwo(): void
    {
        $service = new UserService(new UserRepository());  // Duplicated!
    }
}

// CORRECT: Use setUp() for shared initialization
class GoodTest extends TestCase
{
    private UserService $service;

    protected function setUp(): void
    {
        $this->service = new UserService(new UserRepository());
    }
}

// WRONG: Using assertEquals when assertSame is needed
$this->assertEquals(0, $result);  // Passes for false, null, "0" too (loose ==)

// CORRECT: Use assertSame for strict comparison
$this->assertSame(0, $result);    // Only passes for integer 0 (strict ===)

// WRONG: Not testing error paths
public function testCreateUser(): void
{
    $result = $this->service->createUser('Alice', 'a@b.com', 'pass');
    $this->assertNotNull($result);
    // But what happens with invalid input?
}

// CORRECT: Test both success and failure paths
public function testCreateUserWithInvalidEmail(): void
{
    $this->expectException(\InvalidArgumentException::class);
    $this->service->createUser('Alice', 'invalid', 'pass');
}

// WRONG: Not using data providers for similar tests
public function testEmail1(): void { /* test "a@b.com" */ }
public function testEmail2(): void { /* test "c@d.com" */ }
public function testEmail3(): void { /* test "e@f.com" */ }

// CORRECT: Use @dataProvider for parameterized tests
/**
 * @dataProvider emailProvider
 */
public function testValidEmail(string $email): void { /* test $email */ }

// WRONG: Testing implementation details instead of behavior
// Testing that internal method was called 3 times — brittle!

// CORRECT: Test the observable behavior (return values, side effects)
```

## Gotchas
- `assertSame()` uses `===` (strict). `assertEquals()` uses `==` (loose). Prefer `assertSame()`.
- `setUp()` runs before EACH test method. `tearDown()` runs after EACH test.
- `setUpBeforeClass()` / `tearDownAfterClass()` run once per class (static methods).
- Data providers must be `public static` methods returning arrays of arrays.
- `createMock()` creates a mock where all methods return null/0/false by default.
- `createStub()` is an alias for `createMock()` in PHPUnit 9+.
- `expects($this->once())` verifies the method is called exactly once.
- `expects($this->any())` allows any number of calls (including zero).
- `willReturnMap()` maps different arguments to different return values.
- `willReturnCallback()` lets you compute the return value dynamically.
- For database testing, use transactions that roll back after each test to keep tests isolated.

## Related
- php/stdlib/basics.md
- php/db/pdo.md
- php/web/laravel-basics.md
- php/stdlib/error-handling.md
