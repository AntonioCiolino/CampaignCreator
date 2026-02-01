"""
Tests for User Settings API endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.tests.conftest import create_test_user_in_db
from app.orm_models import User as ORMUser
from app.models import User as PydanticUser
from app.core.security import decrypt_key


class TestUserAPIKeys:
    """Tests for user API key management."""

    @pytest.mark.asyncio
    async def test_update_openai_api_key(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        current_active_user_override: PydanticUser
    ):
        """Test setting OpenAI API key."""
        response = await async_client.put(
            "/api/v1/users/me/keys",
            json={"openai_api_key": "sk-test-key-12345"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["openai_api_key_provided"] is True
        
        # Verify key is encrypted in DB
        db_user = db_session.query(ORMUser).filter(
            ORMUser.id == current_active_user_override.id
        ).first()
        assert db_user.encrypted_openai_api_key is not None
        assert decrypt_key(db_user.encrypted_openai_api_key) == "sk-test-key-12345"

    @pytest.mark.asyncio
    async def test_update_sd_api_key(
        self, 
        async_client: AsyncClient,
        current_active_user_override: PydanticUser
    ):
        """Test setting Stable Diffusion API key."""
        response = await async_client.put(
            "/api/v1/users/me/keys",
            json={"sd_api_key": "sd-test-key-67890"}
        )
        
        assert response.status_code == 200
        assert response.json()["sd_api_key_provided"] is True

    @pytest.mark.asyncio
    async def test_update_gemini_api_key(
        self, 
        async_client: AsyncClient,
        current_active_user_override: PydanticUser
    ):
        """Test setting Gemini API key."""
        response = await async_client.put(
            "/api/v1/users/me/keys",
            json={"gemini_api_key": "gemini-test-key"}
        )
        
        assert response.status_code == 200
        assert response.json()["gemini_api_key_provided"] is True

    @pytest.mark.asyncio
    async def test_update_other_llm_api_key(
        self, 
        async_client: AsyncClient,
        current_active_user_override: PydanticUser
    ):
        """Test setting other LLM API key."""
        response = await async_client.put(
            "/api/v1/users/me/keys",
            json={"other_llm_api_key": "other-test-key"}
        )
        
        assert response.status_code == 200
        assert response.json()["other_llm_api_key_provided"] is True

    @pytest.mark.asyncio
    async def test_clear_api_key(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        current_active_user_override: PydanticUser
    ):
        """Test clearing an API key by setting empty string."""
        # First set a key
        await async_client.put(
            "/api/v1/users/me/keys",
            json={"openai_api_key": "sk-test-key"}
        )
        
        # Then clear it
        response = await async_client.put(
            "/api/v1/users/me/keys",
            json={"openai_api_key": ""}
        )
        
        assert response.status_code == 200
        assert response.json()["openai_api_key_provided"] is False

    @pytest.mark.asyncio
    async def test_update_multiple_api_keys(
        self, 
        async_client: AsyncClient,
        current_active_user_override: PydanticUser
    ):
        """Test updating multiple API keys at once."""
        response = await async_client.put(
            "/api/v1/users/me/keys",
            json={
                "openai_api_key": "sk-openai",
                "sd_api_key": "sd-key",
                "gemini_api_key": "gemini-key"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["openai_api_key_provided"] is True
        assert data["sd_api_key_provided"] is True
        assert data["gemini_api_key_provided"] is True


class TestUserProfile:
    """Tests for user profile management."""

    @pytest.mark.asyncio
    async def test_get_current_user(
        self, 
        async_client: AsyncClient,
        current_active_user_override: PydanticUser
    ):
        """Test getting current user profile."""
        response = await async_client.get("/api/v1/users/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == current_active_user_override.id
        assert data["username"] == current_active_user_override.username

    @pytest.mark.asyncio
    async def test_update_user_profile(
        self, 
        async_client: AsyncClient,
        current_active_user_override: PydanticUser
    ):
        """Test updating user profile via /users/{user_id}."""
        user_id = current_active_user_override.id
        response = await async_client.put(
            f"/api/v1/users/{user_id}",
            json={
                "full_name": "Updated Name"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_sd_engine_preference(
        self, 
        async_client: AsyncClient,
        current_active_user_override: PydanticUser
    ):
        """Test updating SD engine preference via /users/{user_id}."""
        user_id = current_active_user_override.id
        response = await async_client.put(
            f"/api/v1/users/{user_id}",
            json={"sd_engine_preference": "stable-diffusion-xl-1024-v1-0"}
        )
        
        assert response.status_code == 200
        assert response.json()["sd_engine_preference"] == "stable-diffusion-xl-1024-v1-0"

    @pytest.mark.asyncio
    async def test_clear_sd_engine_preference(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        current_active_user_override: PydanticUser
    ):
        """Test clearing SD engine preference."""
        user_id = current_active_user_override.id
        
        # First set a preference
        db_user = db_session.query(ORMUser).filter(
            ORMUser.id == current_active_user_override.id
        ).first()
        db_user.sd_engine_preference = "some-engine"
        db_session.commit()
        
        # Then clear it
        response = await async_client.put(
            f"/api/v1/users/{user_id}",
            json={"sd_engine_preference": None}
        )
        
        assert response.status_code == 200


class TestUserManagement:
    """Tests for user management (superuser operations)."""

    @pytest.mark.asyncio
    async def test_create_user_as_superuser(
        self, 
        async_client: AsyncClient,
        superuser_override: PydanticUser
    ):
        """Test creating a new user as superuser."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = await async_client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        superuser_override: PydanticUser
    ):
        """Test creating user with duplicate email fails."""
        create_test_user_in_db(
            db_session, 
            username="existing", 
            email="duplicate@example.com"
        )
        
        response = await async_client.post(
            "/api/v1/users/",
            json={
                "username": "newuser",
                "email": "duplicate@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        superuser_override: PydanticUser
    ):
        """Test creating user with duplicate username fails."""
        create_test_user_in_db(db_session, username="duplicate", email="first@example.com")
        
        response = await async_client.post(
            "/api/v1/users/",
            json={
                "username": "duplicate",
                "email": "second@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_users_as_superuser(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        superuser_override: PydanticUser
    ):
        """Test listing all users as superuser."""
        create_test_user_in_db(db_session, username="user1", email="user1@example.com")
        create_test_user_in_db(db_session, username="user2", email="user2@example.com")
        
        response = await async_client.get("/api/v1/users/")
        
        assert response.status_code == 200
        data = response.json()
        usernames = {u["username"] for u in data}
        assert "user1" in usernames
        assert "user2" in usernames

    @pytest.mark.asyncio
    async def test_list_users_pagination(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        superuser_override: PydanticUser
    ):
        """Test user list pagination."""
        for i in range(5):
            create_test_user_in_db(
                db_session, 
                username=f"pageuser{i}", 
                email=f"page{i}@example.com"
            )
        
        response = await async_client.get("/api/v1/users/?limit=2")
        
        assert response.status_code == 200
        assert len(response.json()) == 2

    @pytest.mark.asyncio
    async def test_get_user_by_id_as_superuser(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        superuser_override: PydanticUser
    ):
        """Test getting user by ID as superuser."""
        user = create_test_user_in_db(
            db_session, 
            username="getuser", 
            email="get@example.com"
        )
        
        response = await async_client.get(f"/api/v1/users/{user.id}")
        
        assert response.status_code == 200
        assert response.json()["username"] == "getuser"

    @pytest.mark.asyncio
    async def test_update_user_as_superuser(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        superuser_override: PydanticUser
    ):
        """Test updating user as superuser."""
        user = create_test_user_in_db(
            db_session, 
            username="updateuser", 
            email="update@example.com"
        )
        
        response = await async_client.put(
            f"/api/v1/users/{user.id}",
            json={"full_name": "Updated by Admin", "disabled": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated by Admin"
        assert data["disabled"] is True

    @pytest.mark.asyncio
    async def test_delete_user_as_superuser(
        self, 
        async_client: AsyncClient, 
        db_session: Session,
        superuser_override: PydanticUser
    ):
        """Test deleting user as superuser."""
        user = create_test_user_in_db(
            db_session, 
            username="deleteuser", 
            email="delete@example.com"
        )
        user_id = user.id
        
        response = await async_client.delete(f"/api/v1/users/{user_id}")
        
        assert response.status_code == 200
        
        # Verify deletion
        deleted = db_session.query(ORMUser).filter(ORMUser.id == user_id).first()
        assert deleted is None


class TestUserAccessControl:
    """Tests for user access control."""

    @pytest.mark.asyncio
    async def test_list_users_forbidden_for_normal_user(
        self, 
        async_client: AsyncClient,
        current_active_user_override: PydanticUser
    ):
        """Test normal user cannot list all users."""
        response = await async_client.get("/api/v1/users/")
        
        # Should be forbidden for non-superuser
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_user_forbidden_for_normal_user(
        self, 
        async_client: AsyncClient,
        current_active_user_override: PydanticUser
    ):
        """Test normal user cannot create users."""
        response = await async_client.post(
            "/api/v1/users/",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, async_client: AsyncClient):
        """Test unauthenticated requests are denied."""
        # Remove any auth overrides
        from app.main import app
        from app.services.auth_service import get_current_active_user
        app.dependency_overrides.pop(get_current_active_user, None)
        
        response = await async_client.get("/api/v1/users/me")
        
        assert response.status_code == 401
