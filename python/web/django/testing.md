---
id: "python-web-django-testing"
title: "Django Testing: TestCase, Client, Fixtures, Factory Boy"
language: "python"
category: "web"
subcategory: "testing"
tags: ["django", "testing", "testcase", "client", "fixtures", "factory-boy", "api-testing"]
version: "3.10+"
retrieval_hint: "Django testing TestCase Client fixtures factory_boy test database transaction APIClient"
last_verified: "2026-05-22"
confidence: "high"
---

# Django Testing: TestCase, Client, Fixtures, Factory Boy

## When to Use
- Writing unit and integration tests for Django apps
- Testing views, forms, and model logic
- Testing API endpoints with DRF's APIClient
- Creating test data with fixtures or factories
- Verifying database state in tests

## Standard Pattern

```python
# --- Basic TestCase ---
from django.test import TestCase, Client
from django.urls import reverse
from myapp.models import Article, Author


class ArticleModelTest(TestCase):
    def test_article_str(self):
        author = Author.objects.create(name="Alice")
        article = Article.objects.create(title="Test Article", author=author)
        self.assertEqual(str(article), "Test Article")

    def test_published_manager(self):
        author = Author.objects.create(name="Alice")
        Article.objects.create(title="Draft", author=author, status="draft")
        Article.objects.create(title="Published", author=author, status="published")
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.published.count(), 1)


# --- Testing views with Client ---
class ArticleViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = Author.objects.create(name="Alice")
        self.article = Article.objects.create(
            title="Test Article",
            author=self.author,
            status="published",
        )

    def test_article_list(self):
        response = self.client.get(reverse("articles:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Article")

    def test_article_detail(self):
        response = self.client.get(reverse("articles:detail", kwargs={"pk": self.article.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)

    def test_article_create_requires_auth(self):
        response = self.client.post(reverse("articles:create"), {"title": "New"})
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_article_create_authenticated(self):
        self.client.force_login(self.author.user)
        response = self.client.post(
            reverse("articles:create"),
            {"title": "New Article", "content": "Content here"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Article.objects.filter(title="New Article").exists())
```

```python
# --- Factory Boy ---
# pip install factory-boy
import factory
from myapp.models import Article, Author, Tag


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author

    name = factory.Sequence(lambda n: f"Author {n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.name.lower().replace(' ', '.')}@example.com")


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f"tag-{n}")


class ArticleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Article

    title = factory.Sequence(lambda n: f"Article {n}")
    content = factory.Faker("paragraph", nb_sentences=5)
    author = factory.SubFactory(AuthorFactory)
    status = "published"

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


# Using factories in tests
class ArticleAPITest(TestCase):
    def test_list_articles(self):
        articles = ArticleFactory.create_batch(5)
        response = self.client.get(reverse("articles:api-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 5)

    def test_filter_by_author(self):
        author = AuthorFactory()
        ArticleFactory(author=author)
        ArticleFactory()  # Different author
        response = self.client.get(reverse("articles:api-list"), {"author": author.pk})
        self.assertEqual(len(response.json()["results"]), 1)
```

```python
# --- Testing DRF APIs ---
from rest_framework.test import APIClient, APITestCase
from rest_framework import status


class ArticleAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = AuthorFactory()
        self.article = ArticleFactory(author=self.author)
        self.client.force_authenticate(user=self.author.user)

    def test_create_article(self):
        data = {"title": "API Article", "content": "Content", "author": self.author.pk}
        response = self.client.post(reverse("article-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "API Article")

    def test_update_article(self):
        data = {"title": "Updated Title"}
        response = self.client.patch(
            reverse("article-detail", kwargs={"pk": self.article.pk}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Updated Title")

    def test_delete_article(self):
        response = self.client.delete(
            reverse("article-detail", kwargs={"pk": self.article.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(pk=self.article.pk).exists())

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("article-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
```

```python
# --- Fixtures ---
# myapp/fixtures/initial_data.json
# Generate with: python manage.py dumpdata myapp --indent 2 > myapp/fixtures/initial_data.json

class ArticleFixtureTest(TestCase):
    fixtures = ["initial_data.json"]

    def test_fixture_loaded(self):
        self.assertGreater(Article.objects.count(), 0)
```

## Common Mistakes

```python
# WRONG: Not using TestCase's transaction isolation
class ArticleTest(TestCase):
    def test_create(self):
        Article.objects.create(title="Test")
        # Article persists in DB — may affect other tests!

# CORRECT: TestCase wraps each test in a transaction that rolls back
# (TestCase does this automatically; TransactionTestCase does NOT)
class ArticleTest(TestCase):
    def test_create(self):
        Article.objects.create(title="Test")
        # Automatically rolled back after test
```

```python
# WRONG: Hardcoding IDs in tests
def test_article_detail(self):
    response = self.client.get("/articles/1/")  # Breaks if ID changes

# CORRECT: Use reverse() with actual object IDs
def test_article_detail(self):
    article = ArticleFactory()
    response = self.client.get(reverse("articles:detail", kwargs={"pk": article.pk}))
```

```python
# WRONG: Not testing edge cases
def test_search(self):
    response = self.client.get(reverse("articles:list"), {"q": "test"})
    self.assertEqual(response.status_code, 200)

# CORRECT: Test empty queries, special characters, and missing params
def test_search(self):
    # Normal search
    response = self.client.get(reverse("articles:list"), {"q": "test"})
    self.assertEqual(response.status_code, 200)

    # Empty search
    response = self.client.get(reverse("articles:list"), {"q": ""})
    self.assertEqual(response.status_code, 200)

    # Special characters
    response = self.client.get(reverse("articles:list"), {"q": "<script>alert('xss')</script>"})
    self.assertEqual(response.status_code, 200)
```

```python
# WRONG: Using assertEqual for floating point comparisons
def test_average_rating(self):
    avg = article.average_rating
    self.assertEqual(avg, 4.333333)  # Fails due to float precision

# CORRECT: Use assertAlmostEqual for floats
def test_average_rating(self):
    avg = article.average_rating
    self.assertAlmostEqual(avg, 4.333, places=3)
```

## Gotchas
- `TestCase` wraps each test in a database transaction; `TransactionTestCase` does not (use for testing transaction behavior)
- `Client` simulates a browser; use `APIClient` for DRF API testing
- `force_login()` bypasses authentication; `force_authenticate()` is the DRF equivalent
- `fixtures` are loaded once per TestCase class, not per test method
- `assertContains` checks both status code and response content; `assertNotContains` checks absence
- `setUp` runs before every test method; `setUpTestData` runs once for the entire class (faster for read-only data)
- Factory Boy's `SubFactory` creates related objects; `LazyAttribute` computes values from other fields
- `@factory.post_generation` handles ManyToMany relationships after object creation

## Related
- python/web/django/basics.md
- python/web/django/rest-framework.md
- python/testing/http-testing.md
