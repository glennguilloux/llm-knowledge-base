---
id: "csharp-stdlib-configuration"
title: ".NET Configuration and Options Pattern"
language: "csharp"
category: "stdlib"
subcategory: "configuration"
tags: ["csharp", "dotnet", "configuration", "options", "appsettings", "secrets", "env"]
version: "8.0+"
retrieval_hint: ".NET IConfiguration Options pattern appsettings environment variables user secrets"
last_verified: "2026-05-24"
confidence: "high"
---

# .NET Configuration and Options Pattern

## When to Use
- Reading settings from appsettings.json, environment variables, or Azure Key Vault
- Strongly-typed configuration with validation
- Environment-specific overrides (Development vs Production)
- Secrets management during development (user secrets)

## Standard Pattern

```csharp
// appsettings.json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Database=MyDb;Trusted_Connection=true"
  },
  "Smtp": {
    "Host": "smtp.example.com",
    "Port": 587,
    "EnableSsl": true,
    "Username": "noreply@example.com",
    "Password": ""
  },
  "FeatureFlags": {
    "EnableNewDashboard": false
  }
}
```

```csharp
// Strongly-typed options class
public class SmtpOptions
{
    public const string SectionName = "Smtp";

    [Required]
    public string Host { get; set; } = string.Empty;

    [Range(1, 65535)]
    public int Port { get; set; } = 587;

    public bool EnableSsl { get; set; } = true;

    [Required]
    public string Username { get; set; } = string.Empty;

    [Required]
    public string Password { get; set; } = string.Empty;
}
```

```csharp
// Program.cs — register options with validation
var builder = WebApplication.CreateBuilder(args);

// Method 1: Bind with validation
builder.Services.AddOptions<SmtpOptions>()
    .Bind(builder.Configuration.GetSection(SmtpOptions.SectionName))
    .ValidateDataAnnotations()
    .ValidateOnStart();  // Fail fast at startup, not on first use

// Method 2: Configure with lambda validation
builder.Services.AddOptions<SmtpOptions>()
    .Bind(builder.Configuration.GetSection(SmtpOptions.SectionName))
    .Validate(options => !string.IsNullOrEmpty(options.Host), "Host is required")
    .ValidateOnStart();

// Method 3: Named options (multiple SMTP configs)
builder.Services.AddOptions<SmtpOptions>("Primary")
    .Bind(builder.Configuration.GetSection("Smtp:Primary"));
builder.Services.AddOptions<SmtpOptions>("Secondary")
    .Bind(builder.Configuration.GetSection("Smtp:Secondary"));
```

## Injecting Options

```csharp
// Constructor injection — IOptions<T> (singleton, does NOT pick up changes)
public class EmailService
{
    private readonly SmtpOptions _options;

    public EmailService(IOptions<SmtpOptions> options)
    {
        _options = options.Value;
    }

    public void Send(string to, string subject, string body)
    {
        using var client = new SmtpClient(_options.Host, _options.Port);
        client.EnableSsl = _options.EnableSsl;
        client.Credentials = new NetworkCredential(_options.Username, _options.Password);
        // ...
    }
}

// IOptionsSnapshot<T> — scoped, picks up changes per request (NOT in singletons)
public class DynamicEmailService
{
    private readonly SmtpOptions _options;

    public DynamicEmailService(IOptionsSnapshot<SmtpOptions> options)
    {
        _options = options.Value;
    }
}

// IOptionsMonitor<T> — singleton, notified on change (supports hot reload)
public class LiveEmailService
{
    private readonly IOptionsMonitor<SmtpOptions> _optionsMonitor;

    public LiveEmailService(IOptionsMonitor<SmtpOptions> optionsMonitor)
    {
        _optionsMonitor = optionsMonitor;
        _optionsMonitor.OnChange(options =>
        {
            Console.WriteLine($"SMTP config changed: {options.Host}");
        });
    }

    public SmtpOptions Current => _optionsMonitor.CurrentValue;
}
```

## Environment Configuration

```csharp
// appsettings.Development.json — overrides base values
{
  "Smtp": {
    "Host": "localhost",
    "Port": 1025
  }
}

// Environment variables (highest priority by default)
// ASPNETCORE_ENVIRONMENT=Production
// Smtp__Host=smtp.prod.example.com  (double underscore for nesting)

// User secrets (development only)
// dotnet user-secrets init
// dotnet user-secrets set "Smtp:Password" "real-password-here"
```

## Common Mistakes

```csharp
// WRONG: Accessing configuration directly with magic strings
public class EmailService
{
    private readonly IConfiguration _config;

    public EmailService(IConfiguration config) => _config = config;

    public void Send()
    {
        var host = _config["Smtp:Host"];  // No validation, no type safety
        var port = int.Parse(_config["Smtp:Port"]);  // Throws if missing
    }
}

// CORRECT: Use strongly-typed options with validation
public class EmailService
{
    private readonly SmtpOptions _options;

    public EmailService(IOptions<SmtpOptions> options) => _options = options.Value;
    // Validated at startup — fails fast if misconfigured
}
```

```csharp
// WRONG: Using IOptions<T> in a singleton and it never updates
builder.Services.AddSingleton<LiveEmailService>();  // Captures IOptions<T> at registration
// IOptions<T>.Value is computed once — never changes

// CORRECT: Use IOptionsMonitor<T> for singletons that need live updates
builder.Services.AddSingleton<LiveEmailService>();  // Uses IOptionsMonitor<T>
```

```csharp
// WRONG: IOptionsSnapshot<T> injected into singleton — captures stale value
builder.Services.AddSingleton<EmailService>();  // EmailService uses IOptionsSnapshot<T>
// Snapshot is scoped — singleton captures the first request's value forever

// CORRECT: IOptionsSnapshot<T> must be used in scoped or transient services
builder.Services.AddScoped<EmailService>();  // Scoped service gets fresh options per request
```

## Gotchas
- Configuration priority: appsettings.json < appsettings.{ENV}.json < env vars < command-line args < user secrets
- `IOptions<T>.Value` is lazily computed once and cached — it does NOT pick up config changes
- `IOptionsSnapshot<T>` is scoped — resolves fresh per request but CANNOT be injected into singletons
- `IOptionsMonitor<T>` supports `OnChange` callback and works in singletons — use for hot-reload scenarios
- `ValidateOnStart()` fails the app at startup if options are invalid — without it, the error only surfaces on first injection
- `builder.Configuration.GetSection("X")` returns an empty section (not null) if missing — binding produces default values, not exceptions
- User secrets override appsettings in Development only — in Production, environment variables take that role
- Nested config uses `__` in env vars: `Smtp__Host` maps to `Smtp:Host`

## Related
- csharp/stdlib/dependency-injection.md
- csharp/web/aspnet-basics.md
- csharp/stdlib/background-services.md
