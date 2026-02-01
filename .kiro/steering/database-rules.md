# Database Rules - Campaign Crafter API

## Environment Setup

| Environment | Database | Hosting |
|-------------|----------|---------|
| Development | SQLite (local file or in-memory) | Local |
| Testing | SQLite in-memory with StaticPool | Local |
| Production | PostgreSQL | Render (backed by Supabase) |

## Database Agnostic Code (Critical)

This project uses SQLite for development and PostgreSQL for production. All database code MUST work with both.

### DO NOT USE

- `JSONB` type or PostgreSQL-specific casts (`.cast(JSONB)`)
- PostgreSQL-specific operators (`@>`, `->`, `->>` in raw SQL)
- `::jsonb` casts in SQLAlchemy queries

### DO USE

- SQLAlchemy's `JSON` type (works with both SQLite and PostgreSQL)
- Python-side filtering for JSON field queries
- Database-agnostic SQLAlchemy ORM methods

### Example - JSON Field Queries

```python
# BAD - PostgreSQL only
from sqlalchemy.dialects.postgresql import JSONB
db.query(Model).filter(Model.json_field.cast(JSONB).contains('["value"]'))

# GOOD - Database agnostic
results = db.query(Model).filter(Model.category == "SomeCategory").all()
for item in results:
    if item.json_field and "value" in item.json_field:
        return item
```

## ORM Models

Located in `app/orm_models.py`. Key patterns:

- Integer primary keys (this project uses Integer, not UUID)
- JSON columns for flexible data (lists, dicts)
- Relationships with `back_populates`
- `cascade="all, delete-orphan"` for owned collections

## Migrations

```bash
# Create migration
alembic revision -m "description" --autogenerate

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Session Management

Use the `get_db` dependency:

```python
from app.db import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

@router.get("/items")
def get_items(db: Session = Depends(get_db)):
    return db.query(Model).all()
```


## Production Database

- **Provider**: Render PostgreSQL (managed)
- **Backing**: Supabase
- **Connection**: Via `DATABASE_URL` environment variable
- **SSL**: Required for production connections

### Connection String Format
```
postgresql://user:password@host:port/database?sslmode=require
```

## Testing Strategy

Tests use SQLite in-memory with `StaticPool` for connection reuse:

```python
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
```

This ensures tests are fast and isolated while the production code remains PostgreSQL-compatible.
