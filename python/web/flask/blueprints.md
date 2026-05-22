---
id: "python-web-flask-blueprints"
title: "Flask Blueprints and App Factory Pattern"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["flask", "blueprint", "factory", "modular", "register", "routes"]
version: "3.10+"
retrieval_hint: "Flask blueprint app factory register url_prefix modular routes"
last_verified: "2026-05-22"
confidence: "high"
---

# Flask Blueprints and App Factory Pattern

## When to Use
- Organizing Flask applications into modular components
- Building reusable components (auth, admin, API versions)
- Testing with different configurations (app factory enables this)
- Large Flask projects that need separation of concerns

## Standard Pattern

```python
# --- app/__init__.py: App Factory ---
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(f"config.{config_name.capitalize()}Config")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.api import api_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)

    return app


# --- app/routes/auth.py: Auth Blueprint ---
from flask import Blueprint, request, jsonify, session
from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()
    if user and user.check_password(data["password"]):
        session["user_id"] = user.id
        return jsonify({"message": "Logged in"})
    return jsonify({"error": "Invalid credentials"}), 401


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out"})


# --- app/routes/api.py: API Blueprint ---
from flask import Blueprint, jsonify, request
from app.models import User, Post

api_bp = Blueprint("api", __name__)


@api_bp.route("/users", methods=["GET"])
def list_users():
    page = request.args.get("page", 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return jsonify({
        "users": [u.to_dict() for u in users.items],
        "total": users.total,
    })


@api_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify(user.to_dict())


# --- app/routes/admin.py: Admin Blueprint ---
from flask import Blueprint, abort
from flask_login import login_required, current_user

admin_bp = Blueprint("admin", __name__)


@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin:
        abort(403)


@admin_bp.route("/stats")
def stats():
    return jsonify({"users": User.query.count(), "posts": Post.query.count()})
```

## Common Mistakes

```python
# WRONG: Importing models at module level (circular import)
# app/routes/api.py
from app.models import User  # May fail if models imports from routes

# CORRECT: Import inside function or at top of blueprint file (after app creation)
@api_bp.route("/users")
def list_users():
    from app.models import User  # Safe inside function
    return jsonify([u.to_dict() for u in User.query.all()])

# WRONG: Using `url_prefix` in both blueprint and registration
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
app.register_blueprint(auth_bp, url_prefix="/api/auth")  # Double prefix!

# CORRECT: Use prefix in one place only
auth_bp = Blueprint("auth", __name__)
app.register_blueprint(auth_bp, url_prefix="/auth")

# WRONG: Not using app factory (hard to test)
app = Flask(__name__)
app.config["TESTING"] = True  # Can't easily change config per test

# CORRECT: App factory enables config injection
def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    return app

# Test: create_app("testing")
```

## Gotchas
- Blueprint names must be unique across the application
- `url_prefix` in `register_blueprint()` overrides the blueprint's own prefix
- Blueprint-level `before_request` hooks only apply to routes in that blueprint
- Templates in `blueprint_folder/templates/` are searched before app templates
- Static files can be served per-blueprint: `Blueprint("bp", __name__, static_folder="static")`
- Use `current_app` inside blueprint routes to access the app context
- Blueprints can be nested (blueprint registering sub-blueprints)
- `app.register_blueprint()` must be called before the first request

## Related
- python/web/flask/basics.md
- python/web/fastapi/basics.md
- python/web/django/basics.md
