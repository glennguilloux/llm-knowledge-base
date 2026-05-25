---
id: "python-web-django-admin-customization"
title: "Django Admin Customization"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["django", "admin", "customization", "list-display", "inlines", "actions", "fieldsets"]
version: "3.10+"
retrieval_hint: "Django admin customization list_display list_filter search_fields inline models admin actions readonly_fields fieldsets"
last_verified: "2026-05-24"
confidence: "high"
---

# Django Admin Customization

## When to Use
- Building internal admin interfaces for content management
- Customizing the Django admin for non-technical users
- Adding bulk actions for managing data
- Creating inline editing for related models
- Restricting admin access with permissions

## Standard Pattern

```python
# --- Basic admin customization ---
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from myapp.models import Article, Author, Tag, Comment


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "status", "created_at", "view_count"]
    list_filter = ["status", "created_at", "author"]
    search_fields = ["title", "content", "author__name"]
    list_editable = ["status"]
    list_per_page = 25
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    # Fieldsets for organized edit form
    fieldsets = (
        (None, {"fields": ("title", "slug", "author")}),
        ("Content", {"fields": ("content", "excerpt", "featured_image")}),
        ("Publishing", {"fields": ("status", "published_at", "tags")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )

    # Readonly fields
    readonly_fields = ["view_count", "created_at", "updated_at"]

    # Prepopulated fields
    prepopulated_fields = {"slug": ("title",)}

    # Raw ID fields for large foreign key tables
    raw_id_fields = ["author"]

    # Filter horizontal for ManyToMany
    filter_horizontal = ["tags"]

    # Custom display methods
    @admin.display(description="Views")
    def view_count(self, obj):
        return obj.views.count()

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        colors = {"draft": "gray", "published": "green", "archived": "orange"}
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:4px;">{}</span>',
            colors.get(obj.status, "gray"),
            obj.status,
        )
```

```python
# --- Inline models ---
class CommentInline(admin.TabularInline):  # or admin.StackedInline
    model = Comment
    extra = 1  # Number of empty forms to show
    fields = ["author_name", "content", "created_at"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    inlines = [CommentInline]
    ...


# --- Nested inlines (requires django-nested-admin or similar) ---
# pip install django-nested-admin
```

```python
# --- Admin actions ---
@admin.action(description="Publish selected articles")
def publish_articles(modeladmin, request, queryset):
    updated = queryset.update(status="published")
    modeladmin.message_user(request, f"{updated} articles published.")


@admin.action(description="Archive selected articles")
def archive_articles(modeladmin, request, queryset):
    queryset.update(status="archived")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    actions = [publish_articles, archive_articles]
    ...
```

```python
# --- Custom admin views ---
from django.http import HttpResponseRedirect
from django.urls import path


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("stats/", self.admin_site.admin_view(self.stats_view)),
        ]
        return custom_urls + urls

    def stats_view(self, request):
        from django.shortcuts import render
        stats = {
            "total": Article.objects.count(),
            "published": Article.objects.filter(status="published").count(),
        }
        return render(request, "admin/article_stats.html", {"stats": stats})
```

```python
# --- Registering models with custom admin site ---
from django.contrib.admin import AdminSite


class MyAdminSite(AdminSite):
    site_header = "My App Administration"
    site_title = "My App Admin"
    index_title = "Dashboard"


admin_site = MyAdminSite(name="myadmin")
admin_site.register(Article, ArticleAdmin)

# urls.py
urlpatterns = [
    path("admin/", admin_site.urls),
]
```

## Common Mistakes

```python
# WRONG: Using list_display with a method that doesn't exist
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "get_author_name"]  # No such method defined!

# CORRECT: Define the method and use @admin.display decorator
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "author_name"]

    @admin.display(description="Author")
    def author_name(self, obj):
        return obj.author.name
```

```python
# WRONG: Not using raw_id_fields for large FK tables
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "author"]
    # author dropdown loads ALL users — slow with 10k+ users

# CORRECT: Use raw_id_fields for large foreign key lookups
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "author"]
    raw_id_fields = ["author"]  # Shows a text input with a lookup popup
```

```python
# WRONG: Forgetting to register admin actions
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    actions = []  # No actions — users can't do bulk operations

# CORRECT: Define and register actions
@admin.action(description="Publish selected")
def publish_selected(modeladmin, request, queryset):
    queryset.update(status="published")

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    actions = [publish_selected]
```

```python
# WRONG: Making sensitive fields editable in list_display
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "password"]  # password exposed!

# CORRECT: Only expose safe fields in list_display
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "is_active"]
    readonly_fields = ["password"]
```

## Gotchas
- `list_editable` fields must also appear in `list_display`
- `prepopulated_fields` only works with `SlugField`; the source fields must be in the same fieldset
- `filter_horizontal` and `filter_vertical` are for ManyToManyField only
- `raw_id_fields` shows a lookup popup — useful when the FK table has thousands of rows
- `@admin.display(description="...")` replaces the old `short_description` attribute
- `admin.site.register(Model, ModelAdmin)` can only register once; use `@admin.register(Model)` decorator instead
- `readonly_fields` still appear in detail view but can't be edited; they don't prevent programmatic changes
- `date_hierarchy` adds date-based navigation links above the list; requires an indexed DateField

## Related
- python/web/django/basics.md
- python/web/django/orm-queries.md
- python/web/django/testing.md
