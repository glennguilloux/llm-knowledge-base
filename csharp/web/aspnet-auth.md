---
id: "csharp-web-aspnet-auth"
title: "ASP.NET Core JWT Authentication and Authorization"
language: "csharp"
category: "web"
subcategory: "api-framework"
tags: ["csharp", "dotnet", "aspnet", "jwt", "authentication", "authorization", "bearer", "claims"]
version: "8.0+"
retrieval_hint: "ASP.NET JWT bearer authentication authorization policy claims roles token"
last_verified: "2026-05-24"
confidence: "high"
---

# ASP.NET Core JWT Authentication and Authorization

## When to Use
- Stateless API authentication with JWT tokens
- Role-based or claim-based access control
- Single sign-on (SSO) with external identity providers
- Microservice-to-microservice authentication

## Standard Pattern

```csharp
// Program.cs — full JWT auth setup
using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;

var builder = WebApplication.CreateBuilder(args);

// JWT configuration
builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = builder.Configuration["Jwt:Issuer"],
        ValidAudience = builder.Configuration["Jwt:Audience"],
        IssuerSigningKey = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!)),
        ClockSkew = TimeSpan.FromMinutes(1),  // Default is 5 min — too generous
    };
});

// Authorization policies
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy =>
        policy.RequireRole("Admin"));

    options.AddPolicy("CanManageUsers", policy =>
        policy.RequireClaim("permission", "users.manage"));

    options.AddPolicy("MinimumAge", policy =>
        policy.Requirements.Add(new MinimumAgeRequirement(18)));
});

builder.Services.AddScoped<IAuthorizationHandler, MinimumAgeHandler>();

var app = builder.Build();
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
app.Run();
```

## Token Generation

```csharp
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using Microsoft.IdentityModel.Tokens;

public class TokenService
{
    private readonly IConfiguration _config;

    public TokenService(IConfiguration config) => _config = config;

    public string GenerateToken(ApplicationUser user, IList<string> roles)
    {
        var claims = new List<Claim>
        {
            new(ClaimTypes.NameIdentifier, user.Id),
            new(ClaimTypes.Email, user.Email!),
            new(ClaimTypes.Name, user.UserName!),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
        };

        foreach (var role in roles)
            claims.Add(new Claim(ClaimTypes.Role, role));

        var key = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(_config["Jwt:Key"]!));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _config["Jwt:Issuer"],
            audience: _config["Jwt:Audience"],
            claims: claims,
            expires: DateTime.UtcNow.AddHours(1),
            signingCredentials: creds);

        return new JwtSecurityTokenHandler().WriteToken(token);
    }
}
```

## Controller with Authorization

```csharp
[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    [Authorize(Roles = "Admin")]
    [HttpGet("admin-only")]
    public IActionResult AdminEndpoint() => Ok("Admin content");

    [Authorize(Policy = "CanManageUsers")]
    [HttpGet("manage")]
    public IActionResult ManageUsers() => Ok("User management");

    [Authorize]
    [HttpGet("me")]
    public IActionResult GetCurrentUser()
    {
        var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
        return Ok(new { UserId = userId });
    }
}
```

## Custom Authorization Requirement

```csharp
using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;

public class MinimumAgeRequirement : IAuthorizationRequirement
{
    public int MinimumAge { get; }
    public MinimumAgeRequirement(int minimumAge) => MinimumAge = minimumAge;
}

public class MinimumAgeHandler : AuthorizationHandler<MinimumAgeRequirement>
{
    protected override Task HandleRequirementAsync(
        AuthorizationHandlerContext context, MinimumAgeRequirement requirement)
    {
        var dobClaim = context.User.FindFirst(ClaimTypes.DateOfBirth);
        if (dobClaim is null)
        {
            context.Fail(new AuthorizationFailureReason(this, "Date of birth claim missing"));
            return Task.CompletedTask;
        }

        var dob = DateTime.Parse(dobClaim.Value);
        var age = DateTime.Today.Year - dob.Year;
        if (dob > DateTime.Today.AddYears(-age)) age--;
        if (age >= requirement.MinimumAge)
            context.Succeed(requirement);

        return Task.CompletedTask;
    }
}
```

## Common Mistakes

```csharp
// WRONG: Missing ValidateIssuerSigningKey — any JWT with correct issuer is accepted
TokenValidationParameters = new TokenValidationParameters
{
    ValidateIssuer = true,
    ValidateAudience = true,
    // ValidateIssuerSigningKey defaults to false!
}

// CORRECT: Always validate the signing key
TokenValidationParameters = new TokenValidationParameters
{
    ValidateIssuer = true,
    ValidateAudience = true,
    ValidateIssuerSigningKey = true,
    IssuerSigningKey = new SymmetricSecurityKey(
        Encoding.UTF8.GetBytes(key)),
}
```

```csharp
// WRONG: Storing JWT secret in code or appsettings.json checked into git
public static class Config
{
    public const string JwtKey = "super-secret-key-12345";
}

// CORRECT: Use environment variables or secret manager
builder.Configuration["Jwt:Key"]  // From env var, Azure Key Vault, or dotnet user-secrets
```

```csharp
// WRONG: Using [Authorize] without UseAuthentication middleware
app.UseAuthorization();  // No UseAuthentication — claims never populated
app.MapControllers();

// CORRECT: Authentication before Authorization
app.UseAuthentication();
app.UseAuthorization();
app.MapControllers();
```

## Gotchas
- Default `ClockSkew` is 5 minutes — tokens appear valid after expiration; set to 1 minute for tighter security
- `[Authorize]` without parameters requires any authenticated user; `[AllowAnonymous]` overrides it
- `User.FindFirstValue(ClaimTypes.NameIdentifier)` returns null if the claim doesn't exist — always null-check
- JWT tokens are stateless — you cannot revoke them without a token blacklist (use short expiry + refresh tokens)
- Roles in claims are case-sensitive: `"Admin"` ≠ `"admin"` — normalize at token creation
- `[Authorize(Policy = "...")]` fails at runtime (not compile-time) if the policy name is misspelled
- `AddJwtBearer` must be called before `Build()` — adding after has no effect
- Token validation happens once per request; changing token validation parameters requires restarting the app

## Related
- csharp/web/aspnet-basics.md
- csharp/web/aspnet-middleware.md
- crypto/jwt-tokens.md
