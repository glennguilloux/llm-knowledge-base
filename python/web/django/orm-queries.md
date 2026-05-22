---
id: "python-web-django-orm-queries"
title: "Django ORM Queries: Filter, Annotate, Aggregate, Q and F"
language: "python"
category: "web"
subcategory: "database"
tags: ["django", "orm", "queries", "filter", "annotate", "aggregate", "q-objects", "f-expressions"]
version: "3.10+"
retrieval_hint: "Django ORM filter annotate aggregate Q objects F expressions select_related prefetch_related complex queries"
last_verified: "2026-05-22"
confidence: "high"
---

# Django ORM Queries: Filter, Annotate, Aggregate, Q and F

## When to Use
- Building complex database queries without raw SQL
- Annotating querysets with computed values from related models
- Aggregating data for reports and dashboards
- Combining multiple filter conditions dynamically
- Referencing model fields in queries (comparisons, updates)

## Standard Pattern

```python
from django.db.models import (
    Q, F, Count, Sum, Avg, Max, Min, Case, When, Value, CharField
)
from django.db.models.functions import Coalesce, TruncMonth, Concat
from myapp.models import Order, Product, Customer


# --- Basic filtering ---
# Filter with keyword arguments
active_orders = Order.objects.filter(status="active")

# Chaining filters (AND logic)
recent_large = Order.objects.filter(
    created_at__gte="2024-01-01",
    total__gte=100.00,
)

# Exclude
non_cancelled = Order.objects.exclude(status="cancelled")


# --- Q objects for OR/NOT logic ---
from django.db.models import Q

# OR: orders from VIP customers OR orders over $500
vip_or_large = Order.objects.filter(
    Q(customer__is_vip=True) | Q(total__gte=500)
)

# AND + OR combination
complex_query = Order.objects.filter(
    Q(status="active") & (Q(total__gte=100) | Q(customer__is_vip=True))
)

# NOT
not_pending = Order.objects.filter(~Q(status="pending"))

# Dynamic Q building
def build_search_query(search_term: str) -> Q:
    """Build a Q object from user search input."""
    query = Q()
    for word in search_term.split():
        query &= (
            Q(title__icontains=word) |
            Q(description__icontains=word) |
            Q(tags__name__icontains=word)
        )
    return query

results = Product.objects.filter(build_search_query("wireless bluetooth"))


# --- F expressions for field-to-field comparisons ---
from django.db.models import F

# Products where compare_price > price (on sale)
on_sale = Product.objects.filter(compare_price__gt=F("price"))

# Update: increase all prices by 10%
Product.objects.update(price=F("price") * 1.10)

# Annotate with F expression
orders = Order.objects.annotate(
    profit=F("total") - F("cost"),
    margin=F("profit") / F("total") * 100,
)

# F with related fields
orders = Order.objects.annotate(
    customer_email=F("customer__email"),
)


# --- Annotate: adding computed fields ---
from django.db.models import Count, Sum, Avg

# Count orders per customer
customers = Customer.objects.annotate(
    order_count=Count("orders"),
    total_spent=Sum("orders__total"),
    avg_order=Avg("orders__total"),
)

# Filter on annotated values
big_spenders = customers.filter(total_spent__gte=1000)
frequent_buyers = customers.filter(order_count__gte=10)

# Annotate with conditional logic
customers = Customer.objects.annotate(
    high_value=Case(
        When(total_spent__gte=1000, then=Value("premium")),
        When(total_spent__gte=100, then=Value("regular")),
        default=Value("new"),
        output_field=CharField(),
    )
)


# --- Aggregate: database-level calculations ---
from django.db.models import Count, Sum, Avg, Max, Min

# Single aggregate
stats = Order.objects.aggregate(
    total_orders=Count("id"),
    revenue=Sum("total"),
    avg_order=Avg("total"),
    largest_order=Max("total"),
    smallest_order=Min("total"),
)
# stats = {"total_orders": 1234, "revenue": 56789.00, ...}

# Aggregate with filter
active_stats = Order.objects.filter(status="active").aggregate(
    active_revenue=Sum("total"),
)


# --- select_related and prefetch_related ---
# select_related: JOIN for ForeignKey and OneToOneField (single query)
orders = Order.objects.select_related("customer", "shipping_address").all()
# Accessing order.customer.name does NOT trigger a new query

# prefetch_related: separate query for ManyToMany and reverse ForeignKey
customers = Customer.objects.prefetch_related("orders", "tags").all()
# Accessing customer.orders.all() uses the prefetched data

# Nested prefetch
products = Product.objects.prefetch_related(
    "tags",
    "reviews__author",
)

# Prefetch with custom queryset
from django.db.models import Prefetch

customers = Customer.objects.prefetch_related(
    Prefetch(
        "orders",
        queryset=Order.objects.filter(status="active").order_by("-created_at"),
        to_attr="active_orders",  # stores as list, not queryset
    )
)


# --- Complex real-world example: monthly revenue report ---
from django.db.models.functions import TruncMonth

monthly_report = (
    Order.objects
    .filter(status="completed", created_at__year=2024)
    .annotate(month=TruncMonth("created_at"))
    .values("month")
    .annotate(
        order_count=Count("id"),
        revenue=Sum("total"),
        avg_order=Avg("total"),
        unique_customers=Count("customer", distinct=True),
    )
    .order_by("month")
)
# Returns: [{"month": "2024-01-01", "order_count": 150, "revenue": 12345.67, ...}, ...]
```

## Common Mistakes

```python
# WRONG: N+1 query — accessing related objects in a loop
orders = Order.objects.all()
for order in orders:
    print(order.customer.name)  # Triggers a query for EACH order

# CORRECT: Use select_related to JOIN in a single query
orders = Order.objects.select_related("customer").all()
for order in orders:
    print(order.customer.name)  # No additional query
```

```python
# WRONG: Using filter after aggregate (wrong queryset order)
stats = Order.objects.aggregate(total=Sum("total"))
stats.filter(total__gt=1000)  # AttributeError: dict has no filter

# CORRECT: Annotate first, then filter on the annotation
stats = Order.objects.annotate(
    customer_total=Sum("customer__orders__total")
).filter(customer_total__gt=1000)
```

```python
# WRONG: Using | operator for OR queries
orders = Order.objects.filter(status="active") | Order.objects.filter(total__gt=100)
# Works but inefficient — two separate queries combined

# CORRECT: Use Q objects for a single efficient query
orders = Order.objects.filter(
    Q(status="active") | Q(total__gt=100)
)
```

```python
# WRONG: Chaining filter on ManyToMany without prefetch
for product in Product.objects.all():
    tags = product.tags.all()  # N+1 queries
    print(tags)

# CORRECT: Use prefetch_related for ManyToMany and reverse FK
for product in Product.objects.prefetch_related("tags").all():
    tags = product.tags.all()  # Uses prefetched data, no query
    print(tags)
```

## Gotchas
- `select_related` works with ForeignKey and OneToOneField only; use `prefetch_related` for ManyToManyField and reverse ForeignKey
- `filter()` chains are AND logic; use `Q` objects for OR and NOT
- `values()` returns dictionaries, not model instances — you lose access to model methods
- `annotate()` before `values()` annotates per-row; `annotate()` after `values()` groups by the values fields
- `F()` expressions are evaluated in the database, so they avoid race conditions in `update()` calls
- `prefetch_related` caches results on the instance — calling `.all()` again on the same relation returns the cached queryset
- `Count("field", distinct=True)` is needed when joining through related models to avoid counting duplicates
- `aggregate()` returns a dictionary; `annotate()` returns a queryset
- `Q()` objects must come before keyword arguments in `filter()` if mixing them

## Related
- python/web/django/basics.md
- python/db/sqlalchemy-2.0/queries.md
- anti-patterns/sql-antipatterns.md
