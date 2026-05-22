---
id: "go-stdlib-viper-config"
title: "Go Configuration with Viper"
language: "go"
category: "stdlib"
subcategory: "configuration"
tags: ["go", "viper", "config", "env", "yaml", "toml", "settings"]
version: "1.21+"
retrieval_hint: "Go Viper configuration YAML TOML environment variables settings"
last_verified: "2026-05-22"
confidence: "high"
---

# Go Configuration with Viper

## When to Use
- Application configuration from multiple sources (files, env vars, flags)
- Supporting multiple config formats (YAML, TOML, JSON, env)
- Environment-specific configuration (dev, staging, prod)
- Type-safe configuration with defaults

## Standard Pattern

```go
package config

import (
    "fmt"
    "strings"

    "github.com/spf13/viper"
)

type Config struct {
    Server   ServerConfig
    Database DatabaseConfig
    Redis    RedisConfig
    Log      LogConfig
}

type ServerConfig struct {
    Host string
    Port int
}

type DatabaseConfig struct {
    URL        string
    MaxConns   int
    IdleConns  int
}

type RedisConfig struct {
    URL string
}

type LogConfig struct {
    Level  string
    Format string
}

func Load() (*Config, error) {
    v := viper.New()

    // Defaults
    v.SetDefault("server.host", "0.0.0.0")
    v.SetDefault("server.port", 8080)
    v.SetDefault("database.maxconns", 25)
    v.SetDefault("database.idleconns", 10)
    v.SetDefault("log.level", "info")
    v.SetDefault("log.format", "json")

    // Config file
    v.SetConfigName("config")
    v.SetConfigType("yaml")
    v.AddConfigPath(".")
    v.AddConfigPath("/etc/myapp")
    v.AddConfigPath("$HOME/.myapp")

    if err := v.ReadInConfig(); err != nil {
        if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
            return nil, fmt.Errorf("read config: %w", err)
        }
    }

    // Environment variables
    v.SetEnvPrefix("MYAPP")
    v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
    v.AutomaticEnv()  // MYAPP_SERVER_PORT, MYAPP_DATABASE_URL, etc.

    // Command-line flags
    v.BindPFlag("server.port", flag.Lookup("port"))

    // Unmarshal
    var cfg Config
    if err := v.Unmarshal(&cfg); err != nil {
        return nil, fmt.Errorf("unmarshal config: %w", err)
    }

    return &cfg, nil
}

// --- Usage ---
func main() {
    cfg, err := config.Load()
    if err != nil {
        log.Fatalf("Load config: %v", err)
    }

    addr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)
    log.Printf("Starting on %s", addr)
}
```

## Common Mistakes

```go
// WRONG: Hardcoding configuration
const port = 8080
const dbURL = "postgres://localhost/mydb"

// CORRECT: Load from config with defaults
v.SetDefault("server.port", 8080)
port := v.GetInt("server.port")

// WRONG: Not handling missing config file
v.ReadInConfig()  // Panics if file not found

// CORRECT: Handle ConfigFileNotFoundError
if err := v.ReadInConfig(); err != nil {
    if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
        return err  // Real error, not just "file not found"
    }
}

// WRONG: Using wrong env var format
v.SetEnvPrefix("MYAPP")
// Expects MYAPP_SERVER.PORT (invalid env var name!)

// CORRECT: Set env key replacer
v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
// Now expects MYAPP_SERVER_PORT
```

## Gotchas
- `v.SetEnvPrefix("APP")` means env vars start with `APP_` (uppercase)
- `v.AutomaticEnv()` automatically reads environment variables matching config keys
- `v.BindPFlag()` connects command-line flags to config keys
- Config precedence: flag > env > config file > default
- `v.Unmarshal()` maps config to struct using `mapstructure` tags (or matching field names)
- Use `v.WatchConfig()` for live config reloading (with `fsnotify`)
- `v.SetConfigType()` is required when using `v.ReadConfig(reader)`
- YAML config files don't need the prefix: `server.port` in code, `server: port:` in YAML

## Related
- go/stdlib/modules.md
- go/web/http-server.md
- go/stdlib/error-handling.md
