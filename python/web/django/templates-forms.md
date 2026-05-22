---
id: "python-web-django-templates-forms"
title: "Django Templates and Forms"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["django", "templates", "forms", "template-tags", "filters", "validation", "crispy"]
version: "3.10+"
retrieval_hint: "Django templates inheritance context processors forms validation crispy form rendering"
last_verified: "2026-05-22"
confidence: "high"
---

# Django Templates and Forms

## When to Use
- Rendering HTML pages with dynamic data
- Building form-based user interfaces with validation
- Reusing template components across pages
- Processing user input with Django's form system
- Customizing form rendering with crispy-forms

## Standard Pattern

```python
# --- Template inheritance ---
# templates/base.html
"""
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}My Site{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
    {% block extra_head %}{% endblock %}
</head>
<body>
    {% include 'partials/navbar.html' %}
    <main>
        {% block content %}{% endblock %}
    </main>
    {% include 'partials/footer.html' %}
    {% block extra_js %}{% endblock %}
</body>
</html>
"""

# templates/articles/list.html
"""
{% extends 'base.html' %}
{% load humanize %}

{% block title %}Articles{% endblock %}

{% block content %}
<h1>Articles ({{ articles|length }})</h1>
{% for article in articles %}
    <article>
        <h2><a href="{% url 'articles:detail' pk=article.pk %}">{{ article.title }}</a></h2>
        <p>{{ article.content|truncatewords:50 }}</p>
        <time>{{ article.created_at|naturaltime }}</time>
    </article>
{% empty %}
    <p>No articles found.</p>
{% endfor %}

{% include 'partials/pagination.html' %}
{% endblock %}
"""
```

```python
# --- Context processors ---
# myapp/context_processors.py
from django.conf import settings


def site_settings(request):
    return {
        "site_name": settings.SITE_NAME,
        "analytics_id": settings.ANALYTICS_ID,
        "is_maintenance": settings.MAINTENANCE_MODE,
    }

# settings.py — add to TEMPLATES context_processors
TEMPLATES = [{
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "myapp.context_processors.site_settings",
        ],
    },
}]
```

```python
# --- Django Forms ---
from django import forms
from django.core.exceptions import ValidationError
from myapp.models import Article


class ArticleForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        help_text="Comma-separated tags",
    )

    class Meta:
        model = Article
        fields = ["title", "content", "published"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Article title"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 10}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"]
        if Article.objects.filter(title=title).exists():
            raise ValidationError("An article with this title already exists.")
        return title

    def clean_tags_input(self):
        tags_text = self.cleaned_data.get("tags_input", "")
        return [t.strip() for t in tags_text.split(",") if t.strip()]

    def save(self, commit=True):
        article = super().save(commit=commit)
        if commit:
            for tag_name in self.cleaned_data["tags_input"]:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                article.tags.add(tag)
        return article


# Using the form in a view
def article_create(request):
    if request.method == "POST":
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save()
            return redirect("articles:detail", pk=article.pk)
    else:
        form = ArticleForm()
    return render(request, "articles/create.html", {"form": form})
```

```python
# --- Crispy Forms ---
# pip install django-crispy-forms crispy-bootstrap5

# settings.py
INSTALLED_APPS += ["crispy_forms", "crispy_bootstrap5"]
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# templates/articles/create.html
"""
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block content %}
<h1>Create Article</h1>
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form|crispy }}
    <button type="submit" class="btn btn-primary">Create</button>
</form>
{% endblock %}
"""
```

```python
# --- Formset for multiple objects ---
from django.forms import formset_factory

TagFormSet = formset_factory(ArticleForm, extra=3)

def create_multiple_articles(request):
    if request.method == "POST":
        formset = TagFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:
                    form.save()
            return redirect("articles:list")
    else:
        formset = TagFormSet()
    return render(request, "articles/create_multiple.html", {"formset": formset})
```

## Common Mistakes

```python
# WRONG: Forgetting {% csrf_token %} in POST forms
<form method="post">
    {{ form.as_p }}
    <button type="submit">Save</button>
</form>
# Results in 403 Forbidden on submission

# CORRECT: Always include CSRF token in POST forms
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Save</button>
</form>
```

```python
# WRONG: Not checking form.is_valid() before accessing cleaned_data
def create_article(request):
    form = ArticleForm(request.POST)
    article = form.save()  # May fail with invalid data

# CORRECT: Always validate before saving
def create_article(request):
    form = ArticleForm(request.POST)
    if form.is_valid():
        article = form.save()
    else:
        return render(request, "articles/create.html", {"form": form})
```

```python
# WRONG: Using {{ form.as_p }} without custom styling
# Renders plain HTML inputs with no CSS classes

# CORRECT: Use crispy forms or manual widget attrs
{{ form|crispy }}
# Or specify widgets in Meta class with attrs
```

```python
# WRONG: Hardcoding template paths in every view
return render(request, "myapp/templates/articles/create.html", {...})

# CORRECT: Use consistent template naming convention
return render(request, "articles/create.html", {...})
```

## Gotchas
- `{% csrf_token %}` is required for all POST/PUT/DELETE forms; missing it causes 403 Forbidden
- `form.as_p`, `form.as_table`, `form.as_ul` are quick rendering methods but don't support custom CSS classes
- `cleaned_data` is only available after `is_valid()` returns True
- Custom `clean_<field>` methods run after field-level validation; `clean()` runs after all field cleaning
- `formset_factory` creates a form for each extra + initial form; use `extra=0` for editing existing objects
- `{% load static %}` is required in every template that uses `{% static %}`
- `{% extends %}` must be the first tag in the template (no whitespace before it)
- Template variable lookup tries dictionary, attribute, list-index, then method-call — if all fail, fails silently

## Related
- python/web/django/basics.md
- python/web/django/views-urls.md
- python/web/django/admin-customization.md
