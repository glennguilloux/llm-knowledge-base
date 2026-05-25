---
id: "python-web-flask-basics"
title: "Flask Application Setup and Blueprints"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["flask", "blueprint", "routing", "app-factory", "jinja", "wsgi"]
version: "3.10+"
retrieval_hint: "Flask app factory blueprint routing template Jinja WSGI"
last_verified: "2026-05-24"
confidence: "high"
---

# Flask Application Setup and Blueprints

## When to Use
- Legacy codebases that use Flask (still very common)
- Simple APIs and internal tools where FastAPI is overkill
- Projects needing server-rendered HTML with Jinja2 templates
- Microframework philosophy: minimal dependencies, explicit configuration

## Standard Pattern

```python
# --- app/__init__.py: App Factory Pattern ---
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api")

    return app


# --- app/routes/api.py: Blueprint with routes ---
from flask import Blueprint, jsonify, request, abort

api_bp = Blueprint("api", __name__)


@api_bp.route("/users", methods=["GET"])
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    users = User.query.paginate(page=page, per_page=per_page)
    return jsonify({
        "users": [u.to_dict() for u in users.items],
        "total": users.total,
        "page": page,
    })


@api_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    return jsonify(user.to_dict())


@api_bp.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data or "name" not in data:
        abort(400, description="name is required")
    user = User(name=data["name"], email=data.get("email"))
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


# --- app/templates/base.html: Jinja template ---
# <!DOCTYPE html>
# <html>
# <head><title>{% block title %}My App{% endblock %}</title></head>
# <body>
#   {% block content %}{% endblock %}
# </body>
# </html>

# --- app/templates/users/list.html ---
# {% extends "base.html" %}
# {% block content %}
# <ul>
#   {% for user in users %}
#   <li>{{ user.name }} ({{ user.email }})</li>
#   {% endfor %}
# </ul>
# {% endblock %}

# --- run.py ---
from app import create_app
app = create_app()
# Run: flask --app run.py --debug run
```

## Common Mistakes

```python
# WRONG: Global app object (not testable, not reusable)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
# Can't create different configs for testing

# CORRECT: App factory pattern
def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # ... setup ...
    return app

# WRONG: Importing db/models at module level in routes
from app import db  # Circular import risk
from app.models import User

# CORRECT: Import inside function or use blueprints with lazy imports
@api_bp.route("/users")
def list_users():
    from app.models import User  # Or import at top of blueprint file

# WRONG: Returning raw strings without jsonify
@app.route("/api/data")
def get_data():
    return {"key": "value"}  # Wrong Content-Type (text/html)

# CORRECT: Use jsonify for proper JSON response
@app.route("/api/data")
def get_data():
    return jsonify({"key": "value"})  # application/json
```

## Gotchas
- Flask is synchronous by default — use `async def` routes only with `async` Flask extensions
- `request` is a proxy, not a global — it only works inside request context
- `abort()` raises an HTTP exception; use `make_response` for custom error pages
- Jinja2 auto-escapes HTML by default (`{{ var }}` is safe, `{{ var|safe }}` is not)
- Blueprints are registered with `url_prefix` — routes inside don't include the prefix
- `flask --debug run` enables auto-reload and detailed error pages
- Flask's `app.config` is a dict — use `from_object` or `from_envvar` for config management
- Extensions like SQLAlchemy, Migrate, Login must be initialized with the app (or use `init_app`)

## Related
- python/web/fastapi/basics.md
- python/db/sqlalchemy-2.0/models.md
- python/web/django/basics.md
