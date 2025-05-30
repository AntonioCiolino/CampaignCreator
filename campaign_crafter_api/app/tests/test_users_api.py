import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession # Renamed to avoid conflict with FastAPI's Session
from typing import Generator, List as TypingList # For fixture typing and List model

from app.main import app
from app.db import Base, get_db
from app.models import UserCreate, UserUpdate # Pydantic models
from app.orm_models import User as ORMUser # SQLAlchemy model
from app.crud import get_password_hash # For testing password update

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency
def override_get_db() -> Generator[SQLAlchemySession, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def create_test_tables_fixture():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# Helper to create a user directly in DB for setup
def create_user_in_db(db: SQLAlchemySession, user_data: dict) -> ORMUser:
    hashed_password = get_password_hash(user_data["password"])
    db_user = ORMUser(
        email=user_data["email"],
        hashed_password=hashed_password,
        full_name=user_data.get("full_name"),
        is_active=user_data.get("is_active", True),
        is_superuser=user_data.get("is_superuser", False)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Test User Creation ---
@pytest.mark.asyncio
async def test_create_user_success():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "is_active": True,
            "is_superuser": False
        }
        response = await ac.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    assert "id" in data
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_create_user_duplicate_email():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        user_data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        # Create first user
        response1 = await ac.post("/api/v1/users/", json=user_data)
        assert response1.status_code == 201

        # Try to create second user with same email
        response2 = await ac.post("/api/v1/users/", json=user_data)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]

@pytest.mark.asyncio
async def test_create_user_missing_fields():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Missing password
        response = await ac.post("/api/v1/users/", json={"email": "test@example.com"})
        assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error

        # Missing email
        response = await ac.post("/api/v1/users/", json={"password": "password123"})
        assert response.status_code == 422

# --- Test List Users ---
@pytest.mark.asyncio
async def test_read_users_empty():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_read_users_with_data():
    db = TestingSessionLocal()
    create_user_in_db(db, {"email": "user1@example.com", "password": "p1"})
    create_user_in_db(db, {"email": "user2@example.com", "password": "p2", "full_name": "User Two"})
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["email"] == "user1@example.com"
    assert data[1]["email"] == "user2@example.com"
    assert data[1]["full_name"] == "User Two"

@pytest.mark.asyncio
async def test_read_users_pagination():
    db = TestingSessionLocal()
    for i in range(5):
        create_user_in_db(db, {"email": f"user{i}@example.com", "password": "p{i}"})
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test limit
        response_limit = await ac.get("/api/v1/users/?limit=2")
        assert response_limit.status_code == 200
        assert len(response_limit.json()) == 2

        # Test skip
        response_skip = await ac.get("/api/v1/users/?skip=2&limit=2")
        assert response_skip.status_code == 200
        data_skip = response_skip.json()
        assert len(data_skip) == 2
        assert data_skip[0]["email"] == "user2@example.com" # 0-indexed, so user2 is at index 2

# --- Test Get User by ID ---
@pytest.mark.asyncio
async def test_read_user_success():
    db = TestingSessionLocal()
    user = create_user_in_db(db, {"email": "getme@example.com", "password": "p1", "full_name": "Get Me"})
    user_id = user.id
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "getme@example.com"
    assert data["full_name"] == "Get Me"

@pytest.mark.asyncio
async def test_read_user_not_found():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/99999") # Non-existent ID
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

# --- Test Update User ---
@pytest.mark.asyncio
async def test_update_user_success():
    db = TestingSessionLocal()
    user = create_user_in_db(db, {"email": "update@example.com", "password": "p1", "full_name": "Original Name"})
    user_id = user.id
    db.close()

    update_payload = {"full_name": "Updated Name", "is_active": False}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(f"/api/v1/users/{user_id}", json=update_payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "update@example.com" # Email not changed
    assert data["full_name"] == "Updated Name"
    assert data["is_active"] is False

@pytest.mark.asyncio
async def test_update_user_password():
    db = TestingSessionLocal()
    user = create_user_in_db(db, {"email": "pwupdate@example.com", "password": "oldpassword"})
    user_id = user.id
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(f"/api/v1/users/{user_id}", json={"password": "newpassword"})
    assert response.status_code == 200

    # Verify password was actually updated by fetching user and checking hash (conceptual)
    # In a real scenario, you might try to "login" or use a verify_password function if exposed/testable
    db = TestingSessionLocal()
    updated_db_user = db.query(ORMUser).filter(ORMUser.id == user_id).first()
    db.close()
    assert updated_db_user is not None
    # This relies on pwd_context from crud.py, ensure it's accessible or mock verification
    from app.crud import verify_password
    assert verify_password("newpassword", updated_db_user.hashed_password)
    assert not verify_password("oldpassword", updated_db_user.hashed_password)

@pytest.mark.asyncio
async def test_update_user_email_conflict():
    db = TestingSessionLocal()
    user1 = create_user_in_db(db, {"email": "user1.conflict@example.com", "password": "p1"})
    user2 = create_user_in_db(db, {"email": "user2.conflict@example.com", "password": "p2"})
    user1_id = user1.id
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Try to update user1's email to user2's email
        response = await ac.put(f"/api/v1/users/{user1_id}", json={"email": "user2.conflict@example.com"})
    assert response.status_code == 400
    assert "New email already registered by another user" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_user_not_found():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put("/api/v1/users/99999", json={"full_name": "Ghost User"})
    assert response.status_code == 404
    assert "User not found to update" in response.json()["detail"]

# --- Test Delete User ---
@pytest.mark.asyncio
async def test_delete_user_success():
    db = TestingSessionLocal()
    user = create_user_in_db(db, {"email": "delete@example.com", "password": "p1"})
    user_id = user.id
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response_delete = await ac.delete(f"/api/v1/users/{user_id}")
    assert response_delete.status_code == 200
    deleted_data = response_delete.json()
    assert deleted_data["id"] == user_id
    assert deleted_data["email"] == "delete@example.com"

    # Verify user is actually deleted
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response_get = await ac.get(f"/api/v1/users/{user_id}")
    assert response_get.status_code == 404

@pytest.mark.asyncio
async def test_delete_user_not_found():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete("/api/v1/users/99999")
    assert response.status_code == 404
    assert "User not found to delete" in response.json()["detail"]

# TODO: Add tests for is_active and is_superuser fields during creation and update
# Example:
@pytest.mark.asyncio
async def test_create_user_superuser():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        user_data = {
            "email": "super@example.com",
            "password": "superpassword",
            "full_name": "Super User",
            "is_active": True,
            "is_superuser": True # Explicitly set
        }
        response = await ac.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "super@example.com"
    assert data["is_superuser"] is True

@pytest.mark.asyncio
async def test_update_user_to_superuser():
    db = TestingSessionLocal()
    user = create_user_in_db(db, {"email": "make_super@example.com", "password": "p1", "is_superuser": False})
    user_id = user.id
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(f"/api/v1/users/{user_id}", json={"is_superuser": True})
    assert response.status_code == 200
    data = response.json()
    assert data["is_superuser"] is True
    assert data["email"] == "make_super@example.com" # ensure other fields not changed
    assert data["full_name"] is None # Assuming it was None initially and not part of update.
```
