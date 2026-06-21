---
id: "python-web-flask-blueprints-advanced"
title: "Advanced Flask Blueprint Registration and Composition"
language: "python"
category: "web"
subcategory: "flask"
tags: ["flask", "blueprints", "app-factory", "registration", "nested-blueprints", "url-prefix", "before-request", "composition"]
version: "3.10+"
retrieval_hint: "Flask blueprint registration nested blueprint app factory url_prefix before_request teardown request context composition"
last_verified: "2026-06-20"
confidence: "medium"
---

# Advanced Flask Blueprint Registration and Composition

## When to Use
- Composing a large Flask application from domain packages in an app factory.
- Registering versioned API or admin blueprints with predictable `url_prefix` behavior.
- Sharing blueprint lifecycle hooks without importing the application object.
- Keeping tests isolated by creating a fresh app for each test configuration.
- Splitting a monolithic `routes.py` into nested blueprints while avoiding circular imports.

## Standard Pattern

```python
# app/__init__.py
from flask import Flask

from .api import api_bp
from .api.v1 import api_v1_bp
from .admin import admin_bp


def create_app(config_object: str = "config.DefaultConfig") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Compose nested blueprints before registering the parent.
    api_bp.register_blueprint(api_v1_bp, url_prefix="/v1")

    # Register each top-level blueprint once from the factory.
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app
```

```python
# app/api/__init__.py
from flask import Blueprint, current_app

api_bp = Blueprint("api", __name__)


@api_bp.before_request
def load_api_context() -> None:
    current_app.config["API_ENABLED"]


@api_bp.route("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# app/api/v1/__init__.py
from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__)


@api_v1_bp.route("/items")
def list_items() -> list[str]:
    return ["alpha", "beta"]
```

## Common Mistakes

```python
# WRONG: Registering blueprints at import time before the app config exists.
app = Flask(__name__)
app.register_blueprint(api_bp, url_prefix="/api")

# CORRECT: Register blueprints inside create_app after loading configuration.
def create_app(config_object: str) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.register_blueprint(api_bp, url_prefix="/api")
    return app
```

```python
# WRONG: Reusing the same blueprint name in two packages.
# app/api/__init__.py
api_bp = Blueprint("api", __name__)

# app/admin/__init__.py
api_bp = Blueprint("api", __name__)  # Duplicate name causes registration errors.

# CORRECT: Give each blueprint a unique Python variable and Flask name.
# app/api/__init__.py
api_bp = Blueprint("api", __name__)

# app/admin/__init__.py
admin_bp = Blueprint("admin", __name__)
```

```python
# WRONG: Setting prefixes in both the blueprint and registration call.
api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
app.register_blueprint(api_v1_bp, url_prefix="/api/v1")  # Double prefix.

# CORRECT: Set the prefix in exactly one place.
api_v1_bp = Blueprint("api_v1", __name__)
app.register_blueprint(api_v1_bp, url_prefix="/api/v1")
```

```python
# WRONG: Importing create_app inside a blueprint module.
# app/api/__init__.py
from app import create_app  # Circular import risk.
app = create_app()

# CORRECT: Use current_app inside request handlers and register from the factory.
from flask import Blueprint, current_app

api_bp = Blueprint("api", __name__)

@api_bp.route("/config")
def show_config() -> str:
    return current_app.config["SERVICE_NAME"]
```

## Gotchas
- Blueprint names must be unique across the application; nested blueprints still share the same namespace.
- `url_prefix` passed to `register_blueprint()` overrides a prefix declared on the blueprint itself.
- For nested blueprints, parent `before_request` handlers run before child handlers; `after_request` and `teardown_request` run in the opposite direction.
- Use `current_app` inside blueprint code instead of a global app object so tests can create isolated apps.
- Register blueprints before the first request; registering after `app.test_client()` has started a request context is too late.
- Keep extension initialization in the factory and access extensions through `current_app.extensions` or imported proxies inside blueprint modules.
- Avoid importing route modules from `app/__init__.py` if those modules import the app; register already-created blueprint objects instead.

## Related
- python/web/flask/basics.md
- python/web/flask/blueprints.md
- python/web/fastapi/dependency-injection.md
