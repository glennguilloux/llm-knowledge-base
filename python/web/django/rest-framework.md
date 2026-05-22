---
id: "python-web-django-rest-framework"
title: "Django REST Framework: Serializers, Viewsets, Authentication"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["django", "drf", "rest-framework", "serializers", "viewsets", "authentication", "api"]
version: "3.10+"
retrieval_hint: "Django REST Framework DRF serializers viewsets routers authentication permissions token JWT API"
last_verified: "2026-05-22"
confidence: "high"
---

# Django REST Framework: Serializers, Viewsets, Authentication

## When to Use
- Building RESTful APIs with Django
- Serializing complex model relationships to JSON
- Implementing token or JWT authentication
- Creating CRUD endpoints with minimal boilerplate
- Adding pagination, filtering, and permissions to APIs

## Standard Pattern

```python
# --- Serializers ---
from rest_framework import serializers
from myapp.models import Article, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class ArticleSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), write_only=True, source="tags"
    )

    class Meta:
        model = Article
        fields = [
            "id", "title", "content", "author_name", "tags", "tag_ids",
            "published", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_title(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters.")
        return value

    def validate(self, data):
        if data.get("published") and not data.get("content"):
            raise serializers.ValidationError("Published articles need content.")
        return data


# --- Viewsets and Routers ---
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from myapp.models import Article
from myapp.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related("author").prefetch_related("tags")
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["published", "author"]
    search_fields = ["title", "content"]
    ordering_fields = ["created_at", "title"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            return qs
        return qs.filter(published=True)

    # Custom action: /articles/{pk}/publish/
    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.published = True
        article.save()
        return Response({"status": "published"})

    # Custom action: /articles/my/
    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my(self, request):
        articles = self.queryset.filter(author=request.user)
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)


# --- Router configuration ---
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(r"articles", ArticleViewSet, basename="article")

urlpatterns = [
    path("api/", include(router.urls)),
]

# Generated URLs:
# GET    /api/articles/          -> list
# POST   /api/articles/          -> create
# GET    /api/articles/{pk}/     -> retrieve
# PUT    /api/articles/{pk}/     -> update
# PATCH  /api/articles/{pk}/     -> partial_update
# DELETE /api/articles/{pk}/     -> destroy
# POST   /api/articles/{pk}/publish/ -> publish (custom)
# GET    /api/articles/my/       -> my (custom)
```

```python
# --- Authentication: Token and JWT ---
# settings.py
INSTALLED_APPS = [
    ...
    "rest_framework",
    "rest_framework.authtoken",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# Token login endpoint
from rest_framework.authtoken.views import obtain_auth_token
urlpatterns += [
    path("api/token/", obtain_auth_token),  # POST username/password -> token
]

# JWT with djangorestframework-simplejwt
# pip install djangorestframework-simplejwt
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns += [
    path("api/token/", TokenObtainPairView.as_view()),
    path("api/token/refresh/", TokenRefreshView.as_view()),
]

# Custom JWT claims
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["org_id"] = user.org_id
        return token
```

```python
# --- Permissions ---
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
```

## Common Mistakes

```python
# WRONG: Calling serializer.save() without passing extra fields
serializer = ArticleSerializer(data=request.data)
if serializer.is_valid():
    serializer.save()  # author field is missing!

# CORRECT: Pass extra keyword arguments to save()
serializer = ArticleSerializer(data=request.data)
if serializer.is_valid():
    serializer.save(author=request.user)
```

```python
# WRONG: Using request.data in GET views
def get_articles(request):
    data = request.data  # Empty for GET requests!

# CORRECT: Use request.query_params for GET parameters
def get_articles(request):
    search = request.query_params.get("search", "")
    page = request.query_params.get("page", 1)
```

```python
# WRONG: Returning raw queryset from list action
@action(detail=False)
def featured(self, request):
    return Response(Article.objects.filter(featured=True))  # Not serialized!

# CORRECT: Serialize the queryset before returning
@action(detail=False)
def featured(self, request):
    articles = Article.objects.filter(featured=True)
    serializer = self.get_serializer(articles, many=True)
    return Response(serializer.data)
```

```python
# WRONG: Forgetting to add router URLs
router = DefaultRouter()
router.register(r"articles", ArticleViewSet)
urlpatterns = []  # Router URLs not included!

# CORRECT: Include router URLs
urlpatterns = [
    path("api/", include(router.urls)),
]
```

## Gotchas
- `request.data` works for POST/PUT/PATCH; use `request.query_params` for GET parameters
- `ModelSerializer` auto-generates validators from model fields — custom `validate_<field>` methods run AFTER model validators
- `perform_create()` is the right place to inject the current user or set defaults
- Router-generated URLs use the basename for URL names: `basename="article"` -> `article-list`, `article-detail`
- `TokenAuthentication` creates one token per user on first login; JWT creates stateless tokens with expiration
- `IsAuthenticatedOrReadOnly` allows anonymous GET/HEAD/OPTIONS but requires auth for mutations
- `@action(detail=True)` creates URLs like `/articles/{pk}/action/`; `detail=False` creates `/articles/action/`
- Nested serializers with `many=True` create a list; use `ListSerializer` for custom list behavior

## Related
- python/web/django/basics.md
- python/web/django/views-urls.md
- python/web/django/testing.md
