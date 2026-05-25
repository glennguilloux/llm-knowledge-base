---
id: "python-web-django-views-urls"
title: "Django Views and URL Routing"
language: "python"
category: "web"
subcategory: "api-framework"
tags: ["django", "views", "urls", "routing", "cbv", "fbv", "path", "reverse"]
version: "3.10+"
retrieval_hint: "Django function views class-based views ListView DetailView URL routing path re_path reverse namespacing"
last_verified: "2026-05-24"
confidence: "high"
---

# Django Views and URL Routing

## When to Use
- Handling HTTP requests and returning responses in Django
- Building CRUD interfaces with class-based views
- Creating RESTful URL patterns with path converters
- Namespacing URLs for reusable apps
- Redirecting and reversing URLs dynamically

## Standard Pattern

```python
# --- Function-based views ---
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from myapp.models import Article


@require_http_methods(["GET"])
def article_list(request):
    """List all published articles."""
    articles = Article.objects.filter(published=True).values("id", "title", "slug")
    return JsonResponse({"articles": list(articles)})


@require_http_methods(["GET", "POST"])
def article_create(request):
    """Create a new article."""
    if request.method == "POST":
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save()
            return JsonResponse({"id": article.id, "title": article.title}, status=201)
        return JsonResponse({"errors": form.errors}, status=400)
    return render(request, "articles/create.html")


# --- Class-based views ---
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin


class ArticleListView(ListView):
    model = Article
    template_name = "articles/list.html"
    context_object_name = "articles"
    paginate_by = 20

    def get_queryset(self):
        return Article.objects.filter(published=True).select_related("author")


class ArticleDetailView(DetailView):
    model = Article
    template_name = "articles/detail.html"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related"] = Article.objects.filter(
            published=True,
            tags__in=self.object.tags.all(),
        ).exclude(pk=self.object.pk)[:5]
        return context


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    fields = ["title", "content", "tags"]
    template_name = "articles/create.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


# Custom class-based view with multiple methods
class ArticleAPIView(View):
    def get(self, request, pk):
        article = get_object_or_404(Article, pk=pk, published=True)
        return JsonResponse({"id": article.id, "title": article.title})

    def put(self, request, pk):
        article = get_object_or_404(Article, pk=pk, author=request.user)
        data = json.loads(request.body)
        article.title = data.get("title", article.title)
        article.content = data.get("content", article.content)
        article.save()
        return JsonResponse({"id": article.id, "title": article.title})

    def delete(self, request, pk):
        article = get_object_or_404(Article, pk=pk, author=request.user)
        article.delete()
        return HttpResponse(status=204)
```

```python
# --- URL routing ---
# myapp/urls.py
from django.urls import path, re_path, include
from myapp import views

app_name = "articles"  # URL namespace

urlpatterns = [
    # Basic path with type converters
    path("", views.ArticleListView.as_view(), name="list"),
    path("create/", views.ArticleCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ArticleDetailView.as_view(), name="detail"),
    path("<slug:slug>/", views.ArticleDetailView.as_view(), name="detail-slug"),

    # re_path for complex patterns
    re_path(
        r"^(?P<year>\d{4})/(?P<month>\d{2})/$",
        views.article_archive,
        name="archive",
    ),

    # Nested includes for API versioning
    path("api/v1/", include("myapp.api_v1_urls")),
]

# project/urls.py
from django.urls import path, include

urlpatterns = [
    path("articles/", include("myapp.urls", namespace="articles")),
    path("accounts/", include("django.contrib.auth.urls")),
]
```

```python
# --- Using reverse() and reverse_lazy ---
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect


# In views (runtime)
def article_redirect(request, pk):
    url = reverse("articles:detail", kwargs={"pk": pk})
    return HttpResponseRedirect(url)

# In class attributes (evaluated at import time)
class ArticleCreateView(CreateView):
    success_url = reverse_lazy("articles:list")

# In templates
# <a href="{% url 'articles:detail' pk=article.pk %}">{{ article.title }}</a>
```

## Common Mistakes

```python
# WRONG: No CSRF protection on POST view
def create_article(request):
    form = ArticleForm(request.POST)
    if form.is_valid():
        form.save()
    return redirect("articles:list")

# CORRECT: Use csrf_exempt only for APIs, or include CSRF token in forms
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Only for API endpoints with token auth
def create_article_api(request):
    ...
```

```python
# WRONG: Hardcoding URLs in views and templates
return HttpResponseRedirect("/articles/123/")
# <a href="/articles/{{ article.pk }}/">

# CORRECT: Use reverse() and {% url %} tag
return HttpResponseRedirect(reverse("articles:detail", kwargs={"pk": 123}))
# <a href="{% url 'articles:detail' pk=article.pk %}">
```

```python
# WRONG: Forgetting to call as_view() in URLconf
urlpatterns = [
    path("", views.ArticleListView),  # Missing as_view()!
]

# CORRECT: Always call as_view() for class-based views
urlpatterns = [
    path("", views.ArticleListView.as_view(), name="list"),
]
```

```python
# WRONG: Using get_object() without handling 404
def article_detail(request, pk):
    article = Article.objects.get(pk=pk)  # Raises Article.DoesNotExist

# CORRECT: Use get_object_or_404 for automatic 404 handling
def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
```

## Gotchas
- `path()` converters (`<int:pk>`, `<slug:slug>`) validate and convert types automatically; `re_path()` gives full regex control
- Class-based views require `.as_view()` in URLconf — forgetting it is a common error
- `reverse_lazy()` is needed in class attributes because `reverse()` requires URL configuration to be loaded
- `LoginRequiredMixin` must come before `View` in the class MRO: `class MyView(LoginRequiredMixin, View)`
- `ListView` automatically paginates with `paginate_by`; access page object via `page_obj` in template
- `DetailView` uses `pk` by default; override with `slug_field` and `slug_url_kwarg`
- `get_queryset()` on CBVs is the place to add `select_related` / `prefetch_related`
- URL namespaces require `app_name` in the included `urls.py` module

## Related
- python/web/django/basics.md
- python/web/django/templates-forms.md
- python/web/django/rest-framework.md
