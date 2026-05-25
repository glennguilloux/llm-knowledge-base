---
id: "csharp-stdlib-json-serialization"
title: "C# JSON Serialization: System.Text.Json Patterns and Custom Converters"
language: "csharp"
category: "stdlib"
tags: ["csharp", "json", "System.Text.Json", "JsonSerializer", "custom-converters", "nullable"]
version: ".NET 8+"
retrieval_hint: "csharp System.Text.Json JsonSerializer JsonPropertyName custom converters nullable handling deserialization patterns"
last_verified: "2026-05-24"
confidence: "high"
---

# C# JSON Serialization: System.Text.Json Patterns and Custom Converters

## When to Use
- Serializing/deserializing JSON in .NET applications
- Working with REST APIs
- Configuring JSON serialization options
- Creating custom converters for complex types

## Standard Pattern

```csharp
using System;
using System.Text.Json;
using System.Text.Json.Serialization;

// Basic serialization
var user = new User { Id = 1, Name = "Alice", Email = "alice@example.com" };
string json = JsonSerializer.Serialize(user);
// {"Id":1,"Name":"Alice","Email":"alice@example.com"}

// Basic deserialization
var deserialized = JsonSerializer.Deserialize<User>(json);

// Configuration options
var options = new JsonSerializerOptions
{
    PropertyNamingPolicy = JsonNamingPolicy.CamelCase,  // camelCase output
    WriteIndented = true,                                // Pretty print
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,  // Skip nulls
    PropertyNameCaseInsensitive = true,                  // Case-insensitive reading
    ReferenceHandler = ReferenceHandler.Preserve,        // Handle circular references
};

string json = JsonSerializer.Serialize(user, options);
// {
//   "id": 1,
//   "name": "Alice",
//   "email": "alice@example.com"
// }

// Custom property names
public class ApiResponse
{
    [JsonPropertyName("user_id")]
    public int UserId { get; set; }

    [JsonPropertyName("full_name")]
    public string FullName { get; set; } = "";

    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
}

// Ignoring properties
public class User
{
    public int Id { get; set; }
    public string Name { get; set; } = "";

    [JsonIgnore]
    public string PasswordHash { get; set; } = "";  // Never serialized
}

// Nullable handling
public class Config
{
    public string Host { get; set; } = "localhost";
    public int? Port { get; set; }  // Nullable — omitted if null when WhenWritingNull
}

// Custom converter
public class DateOnlyConverter : JsonConverter<DateOnly>
{
    private const string Format = "yyyy-MM-dd";

    public override DateOnly Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        return DateOnly.ParseExact(reader.GetString()!, Format);
    }

    public override void Write(Utf8JsonWriter writer, DateOnly value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value.ToString(Format));
    }
}

// Using custom converter
public class Event
{
    public string Name { get; set; } = "";

    [JsonConverter(typeof(DateOnlyConverter))]
    public DateOnly Date { get; set; }
}

// Or register converter in options
var options = new JsonSerializerOptions();
options.Converters.Add(new DateOnlyConverter());

// Polymorphic serialization
[JsonDerivedType(typeof(Circle), "circle")]
[JsonDerivedType(typeof(Rectangle), "rectangle")]
public abstract class Shape
{
    public string Color { get; set; } = "black";
}

public class Circle : Shape
{
    public double Radius { get; set; }
}

public class Rectangle : Shape
{
    public double Width { get; set; }
    public double Height { get; set; }
}

// Deserializing polymorphic types
var shape = JsonSerializer.Deserialize<Shape>(json);
// Type discriminator in JSON determines which class to create

// JsonDocument for read-only parsing (no deserialization)
using var doc = JsonDocument.Parse(json);
var root = doc.RootElement;
var name = root.GetProperty("name").GetString();
var age = root.GetProperty("age").GetInt32();

// JsonNode for mutable JSON
var node = JsonNode.Parse(json);
node!["name"] = "Bob";
var updated = node.ToJsonString();

// Streaming deserialization (for large JSON)
await foreach (var user in JsonSerializer.DeserializeAsyncEnumerable<User>(stream))
{
    ProcessUser(user);
}
```

## Common Mistakes

```csharp
// WRONG: Using Newtonsoft.Json in new .NET projects
// Newtonsoft.Json is legacy — System.Text.Json is the default in .NET 6+
var json = Newtonsoft.Json.JsonConvert.SerializeObject(user);

// CORRECT: Use System.Text.Json
var json = JsonSerializer.Serialize(user);

// WRONG: Not handling deserialization errors
var user = JsonSerializer.Deserialize<User>(invalidJson);  // Throws JsonException!

// CORRECT: Handle errors
try
{
    var user = JsonSerializer.Deserialize<User>(json);
}
catch (JsonException ex)
{
    Console.WriteLine($"JSON error: {ex.Message}");
}

// WRONG: Not setting PropertyNameCaseInsensitive
// API returns camelCase but C# properties are PascalCase
var user = JsonSerializer.Deserialize<User>(apiResponse);  // All properties null!

// CORRECT: Set case-insensitive option
var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
var user = JsonSerializer.Deserialize<User>(apiResponse, options);

// WRONG: Serializing null values unnecessarily
var json = JsonSerializer.Serialize(new { Name = (string?)null });
// {"Name":null} — wastes bandwidth

// CORRECT: Skip null values
var options = new JsonSerializerOptions
{
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
};
var json = JsonSerializer.Serialize(new { Name = (string?)null }, options);
// {}

// WRONG: Not using [JsonIgnore] for sensitive data
public class User
{
    public string Name { get; set; } = "";
    public string PasswordHash { get; set; } = "";  // Serialized to JSON!
}

// CORRECT: Mark sensitive properties with [JsonIgnore]
public class User
{
    public string Name { get; set; } = "";
    [JsonIgnore]
    public string PasswordHash { get; set; } = "";
}
```

## Gotchas
- `System.Text.Json` is the default in .NET 6+. Use it for new projects.
- `PropertyNameCaseInsensitive = true` is essential for deserializing camelCase JSON from APIs.
- `JsonIgnoreCondition.WhenWritingNull` skips null properties — reduces payload size.
- Custom converters implement `JsonConverter<T>` with `Read()` and `Write()` methods.
- Polymorphic serialization requires `[JsonDerivedType]` attributes on the base class.
- `JsonDocument` is for read-only parsing. `JsonNode` is for mutable JSON.
- `JsonSerializer.DeserializeAsyncEnumerable<T>()` streams large JSON arrays.
- `System.Text.Json` does NOT support `DateTimeOffset` timezone preservation by default.
- Source generators (`JsonSerializerContext`) eliminate runtime reflection for better performance.

## Related
- csharp/stdlib/reflection-attributes.md
- csharp/stdlib/linq-advanced.md
- csharp/web/aspnet-basics.md
