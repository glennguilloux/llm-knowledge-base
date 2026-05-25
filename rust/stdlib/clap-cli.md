---
id: "rust-stdlib-clap-cli"
title: "Rust CLI with clap Argument Parsing"
language: "rust"
category: "stdlib"
subcategory: "cli"
tags: ["rust", "clap", "cli", "args", "subcommand", "derive", "parser"]
version: "1.75+"
retrieval_hint: "Rust clap CLI argument parsing derive subcommand parser options"
last_verified: "2026-05-24"
confidence: "high"
---

# Rust CLI with clap Argument Parsing

## When to Use
- Building command-line tools in Rust
- Parsing arguments with type safety and auto-generated help
- Subcommand-based CLIs (like git, docker)
- Validating input with built-in constraints

## Standard Pattern

```rust
use clap::{Parser, Subcommand, ValueEnum};
use std::path::PathBuf;

#[derive(Parser, Debug)]
#[command(name = "mytool", version, about = "A CLI tool")]
struct Cli {
    /// Enable verbose output
    #[arg(short, long, global = true)]
    verbose: bool,

    /// Config file path
    #[arg(short, long, default_value = "config.yaml")]
    config: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Initialize a new project
    Init {
        /// Project name
        #[arg(short, long)]
        name: String,

        /// Template to use
        #[arg(short, long, value_enum, default_value = "basic")]
        template: Template,
    },

    /// Process data files
    Process {
        /// Input files
        #[arg(required = true)]
        files: Vec<PathBuf>,

        /// Output format
        #[arg(short, long, value_enum, default_value = "json")]
        format: OutputFormat,

        /// Max parallel workers
        #[arg(short, long, default_value = "4")]
        workers: usize,
    },

    /// Start the server
    Serve {
        /// Port to listen on
        #[arg(short, long, default_value = "8080")]
        port: u16,

        /// Bind address
        #[arg(long, default_value = "0.0.0.0")]
        bind: String,
    },
}

#[derive(ValueEnum, Clone, Debug)]
enum Template {
    Basic,
    Full,
    Api,
}

#[derive(ValueEnum, Clone, Debug)]
enum OutputFormat {
    Json,
    Csv,
    Yaml,
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    if cli.verbose {
        println!("Config: {:?}", cli.config);
    }

    match cli.command {
        Commands::Init { name, template } => {
            println!("Initializing {name} with {template:?} template");
            init_project(&name, template)?;
        }
        Commands::Process { files, format, workers } => {
            println!("Processing {} files with {workers} workers", files.len());
            process_files(&files, format, workers)?;
        }
        Commands::Serve { port, bind } => {
            println!("Starting server on {bind}:{port}");
            start_server(&bind, port).await?;
        }
    }

    Ok(())
}
```

## Common Mistakes

```rust
// WRONG: Manual argument parsing
let args: Vec<String> = std::env::args().collect();
let port = args[1].parse::<u16>().unwrap();  // Panics on bad input

// CORRECT: Use clap for type-safe parsing
#[derive(Parser)]
struct Cli {
    #[arg(short, long, default_value = "8080")]
    port: u16,
}

// WRONG: Not providing help text
#[derive(Parser)]
struct Cli {
    #[arg(short, long)]  // No help description!
    port: u16,
}

// CORRECT: Add doc comments for help
#[derive(Parser)]
struct Cli {
    /// Port to listen on
    #[arg(short, long, default_value = "8080")]
    port: u16,
}

// WRONG: Using unwrap on parse
let value = input.parse::<i32>().unwrap();  // Panics on bad input

// CORRECT: Let clap handle validation
#[derive(Parser)]
struct Cli {
    #[arg(value_parser = clap::value_parser!(i32).range(1..=65535))]
    port: i32,
}
```

## Gotchas
- `#[command(subcommand)]` on an enum creates subcommands (like `git commit`, `git push`)
- Doc comments on enum variants become help text for subcommands
- `global = true` makes a flag available in all subcommands
- `value_enum` lets clap parse string to enum variant automatically
- `#[arg(required = true)]` makes positional args mandatory
- `Vec<PathBuf>` accepts multiple positional arguments
- Use `#[command(version)]` to add `--version` flag automatically
- `clap::value_parser!(u16).range(1..=65535)` validates numeric ranges

## Related
- rust/stdlib/error-crates.md
- rust/stdlib/collections.md
- rust/stdlib/serde.md
