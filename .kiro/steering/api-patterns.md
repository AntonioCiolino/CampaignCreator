# API Patterns - Campaign Crafter API

## Project Structure

```
campaign_crafter_api/
├── app/
│   ├── api/endpoints/     # Route handlers
│   ├── core/              # Config, security, seeding
│   ├── services/          # Business logic, LLM integrations
│   ├── crud.py            # Database operations
│   ├── models.py          # Pydantic schemas
│   ├── orm_models.py      # SQLAlchemy models
│   ├── db.py              # Database setup
│   └── main.py            # FastAPI app
├── alembic/               # Migrations
└── requirements.txt
```

## Route Organization

Routes are in `app/api/endpoints/`. Each file is a router:

```python
from fastapi import APIRouter, Depends
router = APIRouter()
```

Included in `main.py` with prefix:
```python
app.include_router(router, prefix="/api/v1/resource", tags=["Resource"])
```

## Pydantic Models (V2)

Located in `app/models.py`. Use V2 syntax:

```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str

class ItemUpdate(BaseModel):
    name: str | None = None

# Serialization
data = item.model_dump(exclude_unset=True)

# Validation
item = ItemCreate.model_validate(data)
```

## CRUD Pattern

All database operations go through `app/crud.py`:

```python
def get_item(db: Session, item_id: int) -> Optional[Model]:
    return db.query(Model).filter(Model.id == item_id).first()

def create_item(db: Session, item: schemas.ItemCreate) -> Model:
    db_item = Model(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

## Authentication

JWT-based auth in `app/core/security.py` and `app/services/auth_service.py`:

```python
from app.services.auth_service import get_current_user
from app import models

@router.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
```

## LLM Service Pattern

Use the factory pattern:

```python
from app.services.llm_factory import get_llm_service

llm_service = get_llm_service(
    db=db,
    current_user_orm=user,
    provider_name="openai",
    model_id_with_prefix="openai/gpt-4"
)
result = await llm_service.generate_text(prompt)
```

## Error Handling

```python
from fastapi import HTTPException

if not item:
    raise HTTPException(status_code=404, detail="Item not found")
```
