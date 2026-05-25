---
id: "python-stdlib-metaclasses"
title: "Metaclasses and Class Creation"
language: "python"
category: "stdlib"
tags: ["metaclass", "type", "class-creation", "init_subclass", "new", "init"]
version: "3.10+"
retrieval_hint: "metaclass type class creation init_subclass new init"
last_verified: "2026-05-24"
confidence: "high"
---

# Metaclasses and Class Creation

## When to Use
- Registering subclasses automatically (plugin patterns)
- Enforcing interface/attribute constraints on classes
- Modifying class attributes at class creation time
- Most of the time, you do NOT need metaclasses — prefer `__init_subclass__` or class decorators

## Standard Pattern

```python
from typing import Any


# --- Normal class creation basics ---

# type() with 3 arguments creates a new class dynamically
# type(name, bases, namespace)

def greet(self) -> str:
    return f"Hello from {self.__class__.__name__}"

MyClass = type("MyClass", (object,), {"greet": greet, "x": 42})
obj = MyClass()
print(obj.greet())  # "Hello from MyClass"


# --- __init_subclass__ (preferred over metaclasses for most use cases) ---

class Plugin:
    """Base class that registers all subclasses."""
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, plugin_name: str = "", **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if plugin_name:
            cls._registry[plugin_name] = cls
            cls.plugin_name = plugin_name

class JsonPlugin(Plugin, plugin_name="json"):
    def serialize(self, data: object) -> str:
        import json
        return json.dumps(data)

class YamlPlugin(Plugin, plugin_name="yaml"):
    def serialize(self, data: object) -> str:
        import yaml
        return yaml.dump(data)

# Access registered plugins
print(Plugin._registry)
# {"json": JsonPlugin, "yaml": YamlPlugin}
plugin_cls = Plugin._registry.get("json")


# --- Metaclass (when you truly need one) ---

class SingletonMeta(type):
    """Metaclass that ensures only one instance per class."""
    _instances: dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    def __init__(self, url: str = "sqlite:///db.sqlite") -> None:
        self.url = url

db1 = Database("postgresql://localhost/mydb")
db2 = Database("mysql://localhost/other")
assert db1 is db2  # True — same instance
print(db1.url)  # "postgresql://localhost/mydb"


# --- __new__ vs __init__ in metaclasses ---

class ValidateFieldsMeta(type):
    """Metaclass that ensures all annotated fields have defaults."""
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> type:
        annotations = namespace.get("__annotations__", {})
        for field_name, field_type in annotations.items():
            if field_name not in namespace:
                # No default value for annotated field
                if not hasattr(field_name, "_field"):
                    raise TypeError(
                        f"Class {name}: field '{field_name}' annotated as "
                        f"{field_type} but has no default value"
                    )
        cls = super().__new__(mcs, name, bases, namespace)
        return cls

    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
    ) -> None:
        super().__init__(name, bases, namespace)  # Post-processing

class Validated(metaclass=ValidateFieldsMeta):
    name: str = "default"   # OK: has default
    count: int = 0          # OK: has default


# --- __init_subclass__ is usually enough ---

class RegisteredService:
    """Use __init_subclass__ instead of metaclass when possible."""
    _services: dict[str, type] = {}

    def __init_subclass__(cls, service_name: str = "", **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        name = service_name or cls.__name__.lower()
        cls._services[name] = cls

    @classmethod
    def get_service(cls, name: str) -> type | None:
        return cls._services.get(name)

class EmailService(RegisteredService, service_name="email"):
    pass

class SmsService(RegisteredService, service_name="sms"):
    pass
```

## Common Mistakes

```python
# WRONG: Confusing __new__ and __init__ in a metaclass
class BadMeta(type):
    def __new__(mcs, name, bases, ns):
        # Trying to modify cls here — but cls doesn't exist yet!
        cls.some_attr = "value"  # AttributeError!
        return super().__new__(mcs, name, bases, ns)

# CORRECT: __new__ creates the class, __init__ initializes it
class GoodMeta(type):
    def __new__(mcs, name, bases, ns):
        cls = super().__new__(mcs, name, bases, ns)
        return cls  # Must return the class

    def __init__(cls, name, bases, ns):
        super().__init__(name, bases, ns)
        cls.added_by_meta = "value"  # Now cls exists

# WRONG: Using metaclass when class decorator would work
class Bad(metaclass=SomeMeta):  # Overkill
    pass

# CORRECT: Class decorator is simpler
def register(cls):
    registry.append(cls)
    return cls

@register
class Good:
    pass

# WRONG: Not calling super().__init_subclass__
class Base:
    def __init_subclass__(cls, **kwargs):
        pass  # Didn't call super() — breaks multiple inheritance

class Child(Base):
    pass

# CORRECT: Always call super().__init_subclass__
class Base:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)  # Important!
        cls.registered = True

# WRONG: Forgetting that type.__call__ invokes both __new__ and __init__
class MyClass:
    def __new__(cls, *args, **kwargs):
        print("__new__")
        return super().__new__(cls)
    def __init__(self, x=0):
        print("__init__")

# When you call MyClass(42), Python calls type.__call__(MyClass, 42)
# which calls MyClass.__new__(MyClass, 42) then MyClass.__init__(obj, 42)
```

## Gotchas
- `__new__` creates the class object; `__init__` initializes it. In metaclasses, both receive the class name, bases, and namespace
- 99% of the time, `__init_subclass__` is a simpler alternative to metaclasses
- Metaclasses propagate to subclasses — if `A` uses metaclass `M`, all subclasses of `A` also use `M`
- Multiple inheritance with different metaclasses causes a `TypeError` unless one is a subclass of the other
- `type.__call__` orchestrates `__new__` then `__init__` — this is what `MyClass()` actually invokes
- `abc.ABCMeta` is a metaclass — `class MyABC(ABC)` uses it. Don't combine with another metaclass unless you subclass `ABCMeta`
- Metaclass `__new__` must return a class object; `__init__` should not return anything
- Enums use their own metaclass (`EnumMeta`) — you cannot easily combine Enum with other metaclasses

## Related
- python/stdlib/decorators.md
- python/stdlib/class-methods-static.md
- python/stdlib/typing-advanced.md
