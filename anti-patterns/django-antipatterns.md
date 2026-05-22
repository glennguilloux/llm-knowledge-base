---
id: "antipatterns-django"
title: "Django Anti-Patterns"
language: "python"
category: "anti-patterns"
tags: ["antipatterns", "django", "orm", "views", "common-mistakes"]
version: "n/a"
retrieval_hint: "django common mistakes N+1 select_related prefetch_related fat views raw SQL transactions"
last_verified: "2026-05-22"
confidence: "high"
---

# Django Anti-Patterns

## When to Use
- Reviewing Django code for ORM and view mistakes
- Training small LLMs to avoid frequent Django errors
- Code review checklists for Django applications
- Onboarding developers new to Django ORM patterns

## Standard Pattern

```python
# WRONG: N+1 query — loop creates a query per item
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # Each access triggers a SELECT

# CORRECT: Use select_related for ForeignKey/OneToOne
users = User.objects.select_related("profile").all()
for user in users:
    print(user.profile.bio)  # Single JOIN query

# WRONG: N+1 for ManyToMany / reverse ForeignKey
posts = Post.objects.all()
for post in posts:
    tags = post.tags.all()  # N queries for tags
    comments = post.comments.all()  # N more queries

# CORRECT: Use prefetch_related for M2M / reverse FK
posts = Post.objects.prefetch_related("tags", "comments").all()
for post in posts:
    tags = post.tags.all()  # From prefetch cache
    comments = post.comments.all()  # From prefetch cache

# WRONG: Using .all() when you need a subset
active_users = User.objects.all()  # Fetches everyone
active_users = [u for u in active_users if u.is_active]  # Filters in Python

# CORRECT: Filter at the database level
active_users = User.objects.filter(is_active=True)

# WRONG: Fat view with business logic
def create_order(request):
    data = json.loads(request.body)
    # Validation
    if not data.get("items"):
        return JsonResponse({"error": "No items"}, status=400)
    # Business logic in view
    order = Order.objects.create(user=request.user, total=0)
    for item_data in data["items"]:
        product = Product.objects.get(id=item_data["product_id"])
        if product.stock < item_data["quantity"]:
            order.delete()
            return JsonResponse({"error": "Out of stock"}, status=400)
        OrderItem.objects.create(order=order, product=product, quantity=item_data["quantity"])
        product.stock -= item_data["quantity"]
        product.save()
        order.total += product.price * item_data["quantity"]
    order.save()
    return JsonResponse({"id": order.id})

# CORRECT: Use forms/serializers for validation, services for logic
class OrderForm(forms.Form):
    items = forms.JSONField()

    def clean_items(self):
        items = self.cleaned_data["items"]
        if not items:
            raise ValidationError("No items")
        return items

class OrderService:
    @staticmethod
    def create_order(user, items):
        with transaction.atomic():
            order = Order.objects.create(user=user, total=0)
            for item_data in items:
                product = Product.objects.select_for_update().get(id=item_data["product_id"])
                if product.stock < item_data["quantity"]:
                    raise OutOfStockError(product.name)
                OrderItem.objects.create(order=order, product=product, quantity=item_data["quantity"])
                product.stock -= item_data["quantity"]
                product.save()
                order.total += product.price * item_data["quantity"]
            order.save()
        return order

def create_order(request):
    form = OrderForm(json.loads(request.body))
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    try:
        order = OrderService.create_order(request.user, form.cleaned_data["items"])
        return JsonResponse({"id": order.id})
    except OutOfStockError as e:
        return JsonResponse({"error": str(e)}, status=400)

# WRONG: Raw SQL when ORM can do it
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT * FROM users WHERE email = %s", [email])
row = cursor.fetchone()

# CORRECT: Use the ORM
user = User.objects.get(email=email)

# WRONG: Not using database transactions
def transfer_funds(from_account, to_account, amount):
    from_account.balance -= amount
    from_account.save()
    # If crash here, money is lost
    to_account.balance += amount
    to_account.save()

# CORRECT: Atomic transaction
from django.db import transaction

def transfer_funds(from_account, to_account, amount):
    with transaction.atomic():
        from_account.balance -= amount
        from_account.save()
        to_account.balance += amount
        to_account.save()

# WRONG: Ignoring migration squashing (slow deploys)
# After years of development, 500+ migrations cause slow migrate

# CORRECT: Squash migrations periodically
# python manage.py squashmigrations myapp 0001 0050
# Then delete old migrations and rename squashed one

# WRONG: QuerySet in loop (re-evaluated each iteration)
for category in Category.objects.all():
    products = Product.objects.filter(category=category)  # N queries
    process(category, products)

# CORRECT: Prefetch or batch query
categories = Category.objects.prefetch_related(
    Prefetch("product_set", queryset=Product.objects.filter(is_active=True))
).all()
for category in categories:
    process(category, category.product_set.all())
```

## Common Mistakes
The most damaging Django anti-patterns are N+1 queries (missing `select_related`/`prefetch_related`), fat views with business logic (hard to test, not reusable), and missing database transactions (data corruption on partial failures). Using `.all()` when `.filter()` suffices fetches unnecessary rows. Raw SQL bypasses ORM protections and is harder to maintain.

## Gotchas
- `select_related` does a SQL JOIN — use for ForeignKey/OneToOne; `prefetch_related` does a separate query — use for M2M/reverse FK
- `QuerySet` is lazy — it doesn't hit the DB until evaluated (iterated, sliced, `list()`, `bool()`)
- `.filter()` chains don't add queries — they build one SQL WHERE clause
- `transaction.atomic()` supports nesting — inner failures don't roll back outer
- `select_for_update()` locks rows — prevents race conditions in concurrent writes
- Django signals (`pre_save`, `post_save`) can cause hidden N+1 if they access related objects
- `values()` / `values_list()` return dicts/tuples instead of model instances — less overhead for read-only data

## Related
- python/web/django/basics.md
- python/web/django/orm-queries.md
- python/db/sqlalchemy-2.0/queries.md
- anti-patterns/sql-antipatterns.md
