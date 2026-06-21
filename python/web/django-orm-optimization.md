---
id: "python-web-django-orm-optimization"
title: "Django ORM Optimization: N+1, Bulk Writes, and QueryShape"
language: "python"
category: "web"
subcategory: "database"
tags: ["django", "orm", "optimization", "n-plus-one", "select-related", "prefetch-related", "bulk-update"]
version: "3.10+"
retrieval_hint: "Django ORM optimization N+1 select_related prefetch_related only defer iterator bulk_update bulk_create query count"
last_verified: "2026-05-24"
confidence: "medium"
---

# Django ORM Optimization: N+1, Bulk Writes, and QueryShape

## When to Use
- Reducing N+1 queries in list/detail endpoints that render related objects
- Improving high-traffic Django views without switching to raw SQL
- Batching writes for imports, scheduled jobs, and admin actions
- Streaming large querysets for reports, exports, or backfills
- Keeping querysets lazy while avoiding accidental evaluation in loops

## Standard Pattern

```python
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from myapp.models import Order, OrderItem, Product

User = get_user_model()


def recent_customer_orders(customer_id: int, statuses: list[str]) -> list[dict]:
    """Return recent orders with product details while keeping database queries bounded."""
    product_qs = Product.objects.only("id", "name", "price")

    item_qs = (
        OrderItem.objects
        .select_related("product")
        .prefetch_related(Prefetch("product", queryset=product_qs))
        .only("id", "order_id", "quantity", "unit_price", "product_id")
    )

    orders = (
        Order.objects
        .filter(customer_id=customer_id, status__in=statuses)
        .select_related("customer")
        .prefetch_related(
            Prefetch("order_items", queryset=item_qs, to_attr="items")
        )
        .only("id", "customer_id", "status", "total", "created_at")
        .order_by("-created_at")[:100]
    )

    return [
        {
            "order_id": order.id,
            "customer": order.customer.name,
            "status": order.status,
            "total": order.total,
            "item_count": len(order.items),
            "first_product": order.items[0].product.name if order.items else None,
        }
        for order in orders
    ]


def search_active_products(term: str) -> list[dict]:
    """Build dynamic filters with Q objects and project only needed fields."""
    words = [word for word in term.split() if word]
    query = Q()
    for word in words:
        query &= Q(name__icontains=word) | Q(description__icontains=word)

    return list(
        Product.objects
        .filter(query, active=True)
        .annotate(order_count=Count("order_items"))
        .values("id", "name", "price", "order_count")
        .order_by("-order_count", "name")[:50]
    )


@transaction.atomic
def mark_orders_paid(order_ids: list[int]) -> int:
    """Batch a simple state transition instead of saving each row in Python."""
    return Order.objects.filter(
        id__in=order_ids,
        status="pending",
    ).update(status="paid")


@transaction.atomic
def bulk_refresh_prices(rows: list[dict]) -> None:
    """Batch update known rows; set every changed field explicitly."""
    products = [
        Product(
            id=row["id"],
            price=row["price"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]
    Product.objects.bulk_update(products, fields=["price", "updated_at"], batch_size=500)
```

## Common Mistakes

```python
# WRONG: N+1 query — one extra customer query per order
orders = Order.objects.all()
for order in orders:
    print(order.customer.name)

# CORRECT: select_related joins ForeignKey/OneToOne data in the original query
orders = Order.objects.select_related("customer").all()
for order in orders:
    print(order.customer.name)
```

```python
# WRONG: N+1 query on ManyToMany or reverse ForeignKey
products = Product.objects.all()
for product in products:
    print(list(product.tags.values_list("name", flat=True)))

# CORRECT: prefetch_related loads related rows in a bounded second query
products = Product.objects.prefetch_related("tags").all()
for product in products:
    print(list(product.tags.values_list("name", flat=True)))
```

```python
# WRONG: Filtering in Python after fetching every row
users = User.objects.all()
active = [user for user in users if user.is_active]

# CORRECT: Push the filter to the database
active = User.objects.filter(is_active=True)
```

```python
# WRONG: Saving thousands of rows one at a time
for product in products:
    product.price = product.price * Decimal("1.05")
    product.save()

# CORRECT: Use bulk_update for simple field updates without per-row save()
Product.objects.bulk_update(products, fields=["price"], batch_size=500)
```

```python
# WRONG: Using iterator() as if it reduces the number of queries
orders = Order.objects.filter(customer__orders__isnull=False).iterator()
for order in orders:
    print(order.customer.name)  # Still N+1

# CORRECT: Fix join shape first, then stream the result
orders = Order.objects.select_related("customer").iterator(chunk_size=1000)
for order in orders:
    print(order.customer.name)
```

## Gotchas
- `select_related` uses SQL joins and works best for `ForeignKey` and `OneToOneField`; use `prefetch_related` for `ManyToManyField` and reverse foreign keys
- `prefetch_related(..., to_attr="items")` stores a list on each instance, not a lazily evaluated queryset
- `only()` and `defer()` reduce selected columns but can trigger extra queries when deferred fields are accessed
- QuerySets are lazy, but iteration, `list()`, slicing, `len()`, `bool()`, and serialization evaluate them
- `iterator(chunk_size=...)` reduces Python memory pressure; it does not fix N+1 query patterns by itself
- `bulk_update()` does not call `save()`, model `clean()`, signals, or auto-update fields unless set explicitly
- `update()` and `aggregate()` return counts or dictionaries immediately; they are not lazy querysets
- Verify query count with Django Debug Toolbar, `assertNumQueries`, or logged SQL before optimizing blindly

## Related
- python/web/django/orm-queries.md
- python/web/django/basics.md
- python/web/django/templates-forms.md
