---
id: "python-web-django-basics"
title: "Django Models, Views, and URL Routing"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["django", "models", "views", "orm", "urls", "admin", "mtv"]
version: "3.10+"
retrieval_hint: "Django model view URL routing ORM admin template MTV pattern"
last_verified: "2026-05-24"
confidence: "high"
---

# Django Models, Views, and URL Routing

## When to Use
- Full-featured web applications with admin panel, auth, ORM out of the box
- Content-heavy sites needing server-side rendering (blogs, CMS, e-commerce)
- Projects needing a battle-tested ORM with migrations, signals, and middleware
- Rapid prototyping with Django's built-in admin and auth system

## Standard Pattern

```python
# --- myapp/models.py ---
from django.db import models
from django.utils import timezone


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    author = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="articles")
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["published", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.title


# --- myapp/views.py ---
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView
import json


# Function-based view
def article_list(request):
    articles = Article.objects.filter(published=True).select_related("author")[:20]
    return JsonResponse({
        "articles": list(articles.values("id", "title", "slug", "author__username")),
    })


# Class-based view
class ArticleDetailView(View):
    def get(self, request, slug: str):
        article = get_object_or_404(Article, slug=slug, published=True)
        return JsonResponse({
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "author": article.author.username,
        })

    def post(self, request, slug: str):
        data = json.loads(request.body)
        article = get_object_or_404(Article, slug=slug)
        article.content = data.get("content", article.content)
        article.save()
        return JsonResponse({"status": "updated"})


# Generic view (simplest for common patterns)
class ArticleListView(ListView):
    model = Article
    queryset = Article.objects.filter(published=True).select_related("author")
    paginate_by = 20


# --- myapp/urls.py ---
from django.urls import path
from myapp import views

urlpatterns = [
    path("articles/", views.article_list, name="article-list"),
    path("articles/<slug:slug>/", views.ArticleDetailView.as_view(), name="article-detail"),
]


# --- myproject/urls.py ---
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("myapp.urls")),
]


# --- myapp/admin.py ---
from django.contrib import admin
from myapp.models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "published", "created_at"]
    list_filter = ["published", "created_at"]
    search_fields = ["title", "content"]
    prepopulated_fields = {"slug": ("title",)}
```

## Common Mistakes

```python
# WRONG: N+1 query — accessing related objects in a loop
articles = Article.objects.all()
for article in articles:
    print(article.author.username)  # Separate query per article!

# CORRECT: Use select_related for ForeignKey/OneToOne
articles = Article.objects.select_related("author").all()
for article in articles:
    print(article.author.username)  # Single JOIN query

# WRONG: Using .all() then filtering in Python
users = User.objects.all()
active = [u for u in users if u.is_active]  # Fetches ALL users from DB

# CORRECT: Filter at the database level
active = User.objects.filter(is_active=True)

# WRONG: Saving with update() without filtering
Article.objects.update(published=True)  # Updates ALL rows!

# CORRECT: Always filter before bulk update
Article.objects.filter(author=user).update(published=True)
```

## Gotchas
- `select_related` does SQL JOIN (ForeignKey, OneToOne); `prefetch_related` does separate queries (ManyToMany, reverse FK)
- Django's ORM is lazy — querysets aren't evaluated until iterated, sliced, or converted to list
- `get_object_or_404()` raises `Http404`, not `ObjectDoesNotExist`
- Use `models.Index` in `Meta.indexes` for composite indexes; `db_index=True` for single-column
- `auto_now=True` on DateTimeField updates on every `.save()` — use `auto_now_add=True` for creation only
- Django admin is powerful but not meant for public-facing interfaces
- Always use `related_name` on ForeignKey for reverse access clarity

## Related
- python/db/sqlalchemy-2.0/models.md
- python/web/flask/basics.md
- python/web/fastapi/basics.md
