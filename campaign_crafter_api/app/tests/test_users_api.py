import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models import UserCreate, UserUpdate
from app.orm_models import User as ORMUser
from app.crud import get_password_hash

# --- Test User Creation (Superuser Protected) ---

@pytest.mark.asyncio
async def test_create_user_success_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict):
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "full_name": "New User",
        "is_superuser": False
    }
    response = await async_client.post("/api/v1/users/", json=user_data, headers=superuser_auth_headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_create_user_duplicate_email_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict):
    user_data1 = {
        "username": "user1",
        "email": "duplicate@example.com",
        "password": "password123"
    }
    response1 = await async_client.post("/api/v1/users/", json=user_data1, headers=superuser_auth_headers)
    assert response1.status_code == 201

    user_data2 = {
        "username": "user2",
        "email": "duplicate@example.com",
        "password": "password456"
    }
    response2 = await async_client.post("/api/v1/users/", json=user_data2, headers=superuser_auth_headers)
    assert response2.status_code == 400
    assert "Email already registered" in response2.json()["detail"]

@pytest.mark.asyncio
async def test_create_user_duplicate_username_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict):
    user_data1 = {
        "username": "duplicateuser",
        "email": "user1@example.com",
        "password": "password123"
    }
    response1 = await async_client.post("/api/v1/users/", json=user_data1, headers=superuser_auth_headers)
    assert response1.status_code == 201

    user_data2 = {
        "username": "duplicateuser",
        "email": "user2@example.com",
        "password": "password456"
    }
    response2 = await async_client.post("/api/v1/users/", json=user_data2, headers=superuser_auth_headers)
    assert response2.status_code == 400
    assert "Username already registered" in response2.json()["detail"]

@pytest.mark.asyncio
async def test_create_user_missing_fields(async_client: AsyncClient, superuser_auth_headers: dict):
    response = await async_client.post("/api/v1/users/", json={"email": "test@example.com"}, headers=superuser_auth_headers)
    assert response.status_code == 422

# --- Test List Users (Superuser Protected) ---

@pytest.mark.asyncio
async def test_read_users_empty_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict):
    response = await async_client.get("/api/v1/users/", headers=superuser_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_read_users_with_data_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, db_session: Session):
    # Create test users
    for i in range(3):
        user = ORMUser(
            username=f"testuser{i}",
            email=f"test{i}@example.com",
            hashed_password=get_password_hash("password"),
            disabled=False,
            is_superuser=False
        )
        db_session.add(user)
    db_session.commit()

    response = await async_client.get("/api/v1/users/", headers=superuser_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3

@pytest.mark.asyncio
async def test_read_users_pagination_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, db_session: Session):
    # Create test users
    for i in range(5):
        user = ORMUser(
            username=f"paginuser{i}",
            email=f"pagin{i}@example.com",
            hashed_password=get_password_hash("password"),
            disabled=False,
            is_superuser=False
        )
        db_session.add(user)
    db_session.commit()

    response = await async_client.get("/api/v1/users/?skip=0&limit=2", headers=superuser_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

# --- Test Get Single User (Superuser Protected) ---

@pytest.mark.asyncio
async def test_read_user_success_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, test_user: ORMUser):
    response = await async_client.get(f"/api/v1/users/{test_user.id}", headers=superuser_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username

@pytest.mark.asyncio
async def test_read_user_not_found_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict):
    response = await async_client.get("/api/v1/users/99999", headers=superuser_auth_headers)
    assert response.status_code == 404

# --- Test Update User (Superuser Protected) ---

@pytest.mark.asyncio
async def test_update_user_success_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, test_user: ORMUser):
    update_data = {"full_name": "Updated Name"}
    response = await async_client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=superuser_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"

@pytest.mark.asyncio
async def test_update_user_password_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, test_user: ORMUser):
    update_data = {"password": "newpassword123"}
    response = await async_client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=superuser_auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_update_user_email_conflict_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, test_user: ORMUser, another_user: ORMUser):
    update_data = {"email": another_user.email}
    response = await async_client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=superuser_auth_headers)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_update_user_username_conflict_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, test_user: ORMUser, another_user: ORMUser):
    update_data = {"username": another_user.username}
    response = await async_client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=superuser_auth_headers)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_update_user_not_found_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict):
    update_data = {"full_name": "New Name"}
    response = await async_client.put("/api/v1/users/99999", json=update_data, headers=superuser_auth_headers)
    assert response.status_code == 404

# --- Test Delete User (Superuser Protected) ---

@pytest.mark.asyncio
async def test_delete_user_success_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, test_user: ORMUser):
    response = await async_client.delete(f"/api/v1/users/{test_user.id}", headers=superuser_auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_user_not_found_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict):
    response = await async_client.delete("/api/v1/users/99999", headers=superuser_auth_headers)
    assert response.status_code == 404

# --- Test Superuser Flag ---

@pytest.mark.asyncio
async def test_create_user_as_superuser_explicitly_superuser_flag(async_client: AsyncClient, superuser_auth_headers: dict):
    user_data = {
        "username": "newsuperuser",
        "email": "super@example.com",
        "password": "password123",
        "is_superuser": True
    }
    response = await async_client.post("/api/v1/users/", json=user_data, headers=superuser_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["is_superuser"] is True

@pytest.mark.asyncio
async def test_update_user_to_superuser_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, test_user: ORMUser):
    update_data = {"is_superuser": True}
    response = await async_client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=superuser_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_superuser"] is True

@pytest.mark.asyncio
async def test_update_user_disabled_status_as_superuser(async_client: AsyncClient, superuser_auth_headers: dict, test_user: ORMUser):
    update_data = {"disabled": True}
    response = await async_client.put(f"/api/v1/users/{test_user.id}", json=update_data, headers=superuser_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["disabled"] is True

# --- Test Login ---

@pytest.mark.asyncio
async def test_login_for_access_token_success(async_client: AsyncClient, test_user: ORMUser):
    login_data = {"username": test_user.username, "password": "testpassword123"}
    response = await async_client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_for_access_token_incorrect_username(async_client: AsyncClient):
    login_data = {"username": "nonexistent", "password": "password"}
    response = await async_client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_for_access_token_incorrect_password(async_client: AsyncClient, test_user: ORMUser):
    login_data = {"username": test_user.username, "password": "wrongpassword"}
    response = await async_client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_for_access_token_disabled_user(async_client: AsyncClient, db_session: Session):
    disabled_user = ORMUser(
        username="disableduser",
        email="disabled@example.com",
        hashed_password=get_password_hash("password"),
        disabled=True,
        is_superuser=False
    )
    db_session.add(disabled_user)
    db_session.commit()

    login_data = {"username": "disableduser", "password": "password"}
    response = await async_client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code in [400, 401]  # Either is acceptable for disabled user

# --- Test Authorization ---

@pytest.mark.asyncio
async def test_read_users_no_token(async_client: AsyncClient):
    response = await async_client.get("/api/v1/users/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_read_users_invalid_token(async_client: AsyncClient):
    headers = {"Authorization": "Bearer invalidtoken"}
    response = await async_client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_read_users_as_normal_user_forbidden(async_client: AsyncClient, user_auth_headers: dict):
    response = await async_client.get("/api/v1/users/", headers=user_auth_headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_read_users_as_superuser_explicit_protection_test(async_client: AsyncClient, superuser_auth_headers: dict):
    response = await async_client.get("/api/v1/users/", headers=superuser_auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_access_with_disabled_user(async_client: AsyncClient, db_session: Session):
    disabled_user = ORMUser(
        username="disabledaccess",
        email="disabledaccess@example.com",
        hashed_password=get_password_hash("password"),
        disabled=True,
        is_superuser=False
    )
    db_session.add(disabled_user)
    db_session.commit()

    login_data = {"username": "disabledaccess", "password": "password"}
    response = await async_client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code in [400, 401]  # Either is acceptable for disabled user
