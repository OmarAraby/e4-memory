---
tags: [pattern, architecture, reference]
created: {{date}}
---

# Repository Pattern

> Example knowledge note — replace/extend with your own.

## Problem
Business logic gets tangled with data-access code, making it hard to test and swap databases.

## Solution
Introduce a repository layer that abstracts persistence behind an interface. Services depend on the interface, not the concrete database.

```python
# Interface
class UserRepository(Protocol):
    def get_by_id(self, user_id: str) -> User | None: ...
    def save(self, user: User) -> None: ...

# Concrete (Postgres)
class PostgresUserRepository:
    def __init__(self, session): self.session = session
    def get_by_id(self, user_id): ...
    def save(self, user): ...

# Service depends on the abstraction
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
```

## When to use
- You expect to swap data stores
- You want to unit-test services without a real database
- Data access is non-trivial

## When NOT to use
- Tiny CRUD apps (adds ceremony for little gain)
- When your ORM already provides clean abstraction you're happy with

## See also
- [[dependency-injection]]
- [[unit-of-work-pattern]]
