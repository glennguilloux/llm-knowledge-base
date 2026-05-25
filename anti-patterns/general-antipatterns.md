---
id: "anti-patterns-general"
title: "General Software Anti-Patterns"
language: "multi"
category: "anti-patterns"
subcategory: "general"
tags: ["anti-pattern", "premature-optimization", "cargo-cult", "over-abstraction", "design"]
version: ""
retrieval_hint: "General anti-pattern premature optimization cargo cult over-abstraction complexity"
last_verified: "2026-05-24"
confidence: "high"
---

# General Software Anti-Patterns

## When to Use
- Code review: identifying common design mistakes
- Architecture discussions: avoiding unnecessary complexity
- Refactoring: simplifying over-engineered code
- Mentoring junior developers

## Standard Pattern

See Common Mistakes below for WRONG/CORRECT code pairs.

## Common Mistakes

```python
# WRONG: Premature optimization
def get_users():
    # Complex caching layer before knowing if there's a performance problem
    cache_key = f"users:{hash(str(filters))}"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    # ... actual query ...
    redis.setex(cache_key, 300, json.dumps(result))
    return result

# CORRECT: Measure first, optimize later
def get_users():
    # Simple implementation — optimize when profiling shows it's needed
    return db.query(User).filter(filters).all()

# WRONG: Cargo cult programming
def process(data):
    # "I saw this pattern in a blog post"
    factory = AbstractFactoryBuilder.create(StrategyPattern.INSTANCE)
    result = factory.process(data)  # Unnecessary abstraction
    return result

# CORRECT: Simple, direct solution
def process(data):
    return [transform(item) for item in data if item.is_valid]

# WRONG: Over-abstraction
class DataProcessorInterface(ABC):
    @abstractmethod
    def process(self, data): pass

class CsvProcessor(DataProcessorInterface):
    def process(self, data): return parse_csv(data)

class JsonProcessor(DataProcessorInterface):
    def process(self, data): return parse_json(data)

# Only one implementation exists!

# CORRECT: YAGNI — abstract when you have 3+ implementations
def process_data(data, format):
    if format == "csv":
        return parse_csv(data)
    return parse_json(data)

# WRONG: God class
class UserService:
    def create_user(self): ...
    def send_email(self): ...
    def generate_report(self): ...
    def process_payment(self): ...
    def export_csv(self): ...
    # 2000 lines, 15 responsibilities

# CORRECT: Single responsibility
class UserService:
    def create_user(self): ...

class EmailService:
    def send_welcome(self): ...

class ReportService:
    def generate(self): ...
```

## Gotchas
- **Premature optimization**: Profile first, optimize bottlenecks, not assumptions
- **Cargo cult**: Don't copy patterns without understanding why they exist
- **Over-abstraction**: Wait for 3 similar implementations before abstracting
- **God class**: If a class has >5 responsibilities, split it
- **Magic numbers**: Use named constants instead of unexplained values
- **Copy-paste**: If you're copying code, extract a function
- **Speculative generality**: Build for today's requirements, not hypothetical future ones
- **Dependency hell**: Minimize external dependencies — each one is a maintenance burden

## Related
- anti-patterns/python-antipatterns.md
- anti-patterns/java-antipatterns.md
- patterns/feature-flags.md
