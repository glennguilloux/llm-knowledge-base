---
id: "anti-patterns-perf-n-plus-one"
title: "Performance Anti-Pattern: N+1 Query Problem"
language: "multi"
category: "anti-patterns"
tags: ["antipatterns", "performance", "n-plus-one", "orm", "database", "eager-loading"]
version: "n/a"
retrieval_hint: "N+1 queries ORM eager loading lazy loading SQLAlchemy Django Hibernate TypeORM join"
last_verified: "2026-05-24"
confidence: "high"
---

# Performance Anti-Pattern: N+1 Query Problem

## When to Use
- Reviewing ORM-heavy codebases for hidden performance issues
- Debugging slow page loads that query the database hundreds of times
- Training LLMs to write efficient database access patterns
- Onboarding developers on ORM performance pitfalls

## Standard Pattern

```python
# WRONG: N+1 queries in Django (1 query for authors + N queries for books)
authors = Author.objects.all()          # SELECT * FROM authors
for author in authors:
    print(author.book.title)            # SELECT * FROM books WHERE author_id = ? (N times!)

# CORRECT: Use select_related for ForeignKey/OneToOne (JOIN in single query)
authors = Author.objects.select_related('book').all()
for author in authors:
    print(author.book.title)            # No extra queries

# CORRECT: Use prefetch_related for reverse/M2M (separate query, joined in Python)
authors = Author.objects.prefetch_related('books').all()
for author in authors:
    for book in author.books.all():     # No extra queries — prefetched
        print(book.title)
```

```python
# WRONG: N+1 in SQLAlchemy
authors = session.query(Author).all()
for author in authors:
    print(author.books)  # Lazy load triggers N queries

# CORRECT: Eager loading with joinedload (single JOIN query)
from sqlalchemy.orm import joinedload, subqueryload

authors = session.query(Author).options(joinedload(Author.books)).all()
for author in authors:
    print(author.books)  # Already loaded

# CORRECT: subqueryload (two queries: one for authors, one for all books)
authors = session.query(Author).options(subqueryload(Author.books)).all()
```

```java
// WRONG: N+1 in Hibernate
@Entity
public class Author {
    @OneToMany(fetch = FetchType.LAZY)  // Default — triggers N queries
    private List<Book> books;
}

List<Author> authors = session.createQuery("FROM Author", Author.class).list();
for (Author a : authors) {
    a.getBooks().size();  // N additional SELECTs
}

// CORRECT: JOIN FETCH in JPQL (single query)
List<Author> authors = session.createQuery(
    "SELECT a FROM Author a JOIN FETCH a.books", Author.class
).list();

// CORRECT: EntityGraph (JPA)
@Entity
@NamedEntityGraph(name = "author-with-books",
    attributeNodes = @NamedAttributeNode("books"))
public class Author { ... }

// Usage
EntityGraph<?> graph = em.getEntityGraph("author-with-books");
List<Author> authors = em.createQuery("SELECT a FROM Author a", Author.class)
    .setHint("javax.persistence.fetchgraph", graph)
    .getResultList();
```

```typescript
// WRONG: N+1 in TypeORM
const authors = await authorRepo.find();
for (const author of authors) {
    author.books = await bookRepo.find({ where: { authorId: author.id } });
}

// CORRECT: Eager relations or joins
const authors = await authorRepo.find({
    relations: ["books"],
});

// CORRECT: QueryBuilder with leftJoinAndSelect
const authors = await authorRepo.createQueryBuilder("author")
    .leftJoinAndSelect("author.books", "book")
    .getMany();
```

```javascript
// WRONG: N+1 in Sequelize
const authors = await Author.findAll();
for (const author of authors) {
    author.books = await author.getBooks();  // N queries
}

// CORRECT: Eager loading
const authors = await Author.findAll({
    include: [{ model: Book, as: 'books' }]
});
```

## Common Mistakes
The N+1 query problem is the most common ORM performance anti-pattern. It occurs when code fetches a list of parent records (1 query) then lazily accesses a related collection on each parent (N queries). On a list of 1000 authors, this generates 1001 database round-trips instead of 1-2. The problem is invisible during development with small datasets but causes catastrophic slowdowns in production. Most ORMs default to lazy loading, making N+1 the path of least resistance. Detection requires query logging — the symptom is many identical queries with different WHERE clause values.

## Gotchas
- `select_related` (Django) does a SQL JOIN — use for ForeignKey/OneToOne. `prefetch_related` does a separate query — use for M2M/reverse relations
- `joinedload` (SQLAlchemy) can cause cartesian products with multiple collections — use `subqueryload` for multiple one-to-many joins
- Eager loading on deep chains (A→B→C→D) can generate massive JOINs — consider breaking into multiple queries
- `prefetch_related` with filtering (`Prefetch` object) is powerful but the queryset must not be evaluated before the prefetch
- N+1 in serializers (DRF) is common — use `SerializerMethodField` with `select_related` or use `django-rest-framework-batch`
- GraphQL resolvers are N+1 magnets — use DataLoader pattern (batch + cache per request)
- Test with `django.test.utils.override_settings(DEBUG=True)` and check `len(connection.queries)` to catch N+1 early
- Bullet Train gem (Ruby) and n_plus_one_control gem detect N+1 in test suites automatically

## Related
- anti-patterns/performance-antipatterns.md
- performance/n-plus-one-prevention.md
- anti-patterns/perf-unindexed-queries.md
