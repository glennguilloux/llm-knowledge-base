---
id: "php-stdlib-composer"
title: "Composer: Dependency Management and Autoloading"
language: "php"
category: "stdlib"
tags: ["php", "composer", "autoload", "psr-4", "dependencies"]
version: "2.x+"
retrieval_hint: "php composer install autoload PSR-4 version constraints scripts"
last_verified: "2026-05-24"
confidence: "high"
---

# Composer: Dependency Management and Autoloading

## When to Use
- Managing PHP package dependencies
- Setting up autoloading for PHP projects
- Creating reusable PHP packages with PSR-4
- Running scripts during build/deploy

## Standard Pattern

```php
<?php
// --- composer.json — Project Definition ---
{
    "name": "myorg/myapp",
    "description": "My PHP application",
    "type": "project",
    "require": {
        "php": ">=8.1",
        "laravel/framework": "^10.0",
        "guzzlehttp/guzzle": "^7.0",
        "monolog/monolog": "^3.0"
    },
    "require-dev": {
        "phpunit/phpunit": "^10.0",
        "mockery/mockery": "^1.5",
        "laravel/sail": "^1.0"
    },
    "autoload": {
        "psr-4": {
            "App\\": "app/",
            "Database\\Factories\\": "database/factories/",
            "Database\\Seeders\\": "database/seeders/"
        },
        "files": [
            "app/Helpers/functions.php"
        ]
    },
    "autoload-dev": {
        "psr-4": {
            "Tests\\": "tests/"
        }
    },
    "scripts": {
        "post-autoload-dump": [
            "Illuminate\\Foundation\\ComposerScripts::postAutoloadDump",
            "@php artisan package:discover --ansi"
        ],
        "post-update-cmd": [
            "@php artisan optimize"
        ],
        "test": "phpunit",
        "cs-fix": "php-cs-fixer fix"
    },
    "config": {
        "optimize-autoloader": true,
        "sort-packages": true,
        "preferred-install": "dist"
    },
    "extra": {
        "laravel": {
            "dont-discover": []
        }
    }
}

// --- Basic Composer Commands ---
// # Install from lock file (production)
// $ composer install --no-dev --optimize-autoloader
//
// # Add a package
// $ composer require guzzlehttp/guzzle:^7.0
//
// # Add a dev dependency
// $ composer require --dev phpunit/phpunit:^10.0
//
// # Update a single package
// $ composer update laravel/framework
//
// # Update all packages (use with caution)
// $ composer update
//
// # Show outdated packages
// $ composer outdated --direct
//
// # Validate composer.json
// $ composer validate

// --- Custom Autoloading (PSR-4) ---
// File: src/MyService.php
namespace App\Services;

class MyService
{
    public function process(): string
    {
        return "Processing...";
    }
}

// Usage (autoloaded automatically)
// $service = new App\Services\MyService();

// --- Version Constraints ---
// Exact version: "1.0.0"
// Caret (recommended): "^1.2" = >=1.2, <2.0
// Tilde: "~1.2" = >=1.2, <1.3
// Wildcard: "1.*"
// OR: "^1.0 || ^2.0"
// Stability: "monolog/monolog": "^2.0@beta"
```

## Common Mistakes

```php
// WRONG: Committing vendor/ directory
// vendor/ contains hundreds of MB of third-party code
// Should be in .gitignore and installed at deploy time

# CORRECT: .gitignore
/vendor/
/node_modules/
.env
.phpunit.result.cache


// WRONG: Missing composer.lock in version control
// Different team members get different dependency versions
// Production installs different versions than development

// CORRECT: Always commit composer.lock
// $ git add composer.lock && git commit -m "Add composer.lock"
// Then install: composer install (respects lock file)
// Update: composer update (writes new lock file)


// WRONG: Wrong version constraint operator
{
    "require": {
        "guzzlehttp/guzzle": "7.0"  // Means exactly 7.0 (not >=7.0)!
    }
}

// CORRECT: Use ^ for compatible versions
{
    "require": {
        "guzzlehttp/guzzle": "^7.0"  // Means >=7.0, <8.0
    }
}


// WRONG: Not using --no-dev in production
$ composer install  # Includes dev dependencies in production!

// CORRECT: Production install
$ composer install --no-dev --optimize-autoloader
// --no-dev: skip require-dev
// --optimize-autoloader: generate classmap for faster loading


// WRONG: Registering autoload manually
require_once __DIR__ . '/src/MyService.php';
require_once __DIR__ . '/src/MyHelper.php';

// CORRECT: Use Composer autoload
require_once __DIR__ . '/vendor/autoload.php';
```

## Gotchas
- **Autoloader optimization**: In production, run `composer dump-autoload -o` to generate an optimized classmap. This is faster than PSR-4 directory scanning at runtime.
- **Platform requirements**: Use `"php": ">=8.1"` and `"ext-json": "*"` to ensure the runtime environment has required extensions. Composer checks these at install time.
- **Abandoned packages**: Run `composer outdated` regularly. Composer warns about abandoned packages that suggest replacements.
- **Composer.lock mismatch**: If `composer.lock` is out of sync with `composer.json`, Composer will warn. Run `composer install` instead of `composer update` to respect the lock file.
- **Memory limit**: Large dependency trees can exhaust memory. Use `COMPOSER_MEMORY_LIMIT=-1` to disable the memory limit during `composer update`.
- **Prefer-dist vs prefer-source**: `preferred-install: "dist"` downloads zip archives (faster). `"source"` clones from git (slower but allows patches). Use `"dist"` in CI.
- **Scripts in CI**: Composer scripts run in the context of the project. Ensure `post-install-cmd` scripts don't require environment not yet configured in CI.

## Related
- php/stdlib/basics.md
- php/web/laravel-basics.md
