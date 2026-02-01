"""
Tests for Authentication API endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
from datetime import timedelta

from app.tests.conftest import create_test_user_in_db
from app.core.security import create_access_token, decode_access_token, create_refresh_token, decode_refresh_token
from app.services.auth_service import authenticate_user
from app.core.config import settings


class TestAuthToken:
    """Tests for /api/v1/auth/token endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, db_session: Session):
        """Test successful login returns access and refresh tokens."""
        create_test_user_in_db(db_session, username="loginuser", password="loginpass123")
        
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "loginuser", "password": "loginpass123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify token is valid
        payload = decode_access_token(data["access_token"])
        assert payload is not None
        assert payload.get("sub") == "loginuser"

    @pytest.mark.asyncio
    async def test_login_wrong_username(self, async_client: AsyncClient, db_session: Session):
        """Test login with non-existent username fails."""
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "nonexistent", "password": "anypassword"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client: AsyncClient, db_session: Session):
        """Test login with wrong password fails."""
        create_test_user_in_db(db_session, username="wrongpassuser", password="correctpass")
        
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "wrongpassuser", "password": "wrongpass"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_disabled_user(self, async_client: AsyncClient, db_session: Session):
        """Test login with disabled user fails."""
        create_test_user_in_db(
            db_session, 
            username="disableduser", 
            password="password123",
            disabled=True
        )
        
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "disableduser", "password": "password123"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, async_client: AsyncClient):
        """Test login with missing fields fails."""
        # Missing password
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "someuser"}
        )
        assert response.status_code == 422

        # Missing username
        response = await async_client.post(
            "/api/v1/auth/token",
            data={"password": "somepass"}
        )
        assert response.status_code == 422


class TestAuthRefresh:
    """Tests for /api/v1/auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, async_client: AsyncClient, db_session: Session):
        """Test successful token refresh."""
        create_test_user_in_db(db_session, username="refreshuser", password="refreshpass")
        
        # First login to get tokens
        login_response = await async_client.post(
            "/api/v1/auth/token",
            data={"username": "refreshuser", "password": "refreshpass"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_user_not_found(self, async_client: AsyncClient, db_session: Session):
        """Test refresh when user no longer exists fails."""
        # Create a valid refresh token for a non-existent user
        refresh_token = create_refresh_token(data={"sub": "deleteduser"})
        
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 401
        assert "User not found" in response.json()["detail"]


class TestTokenSecurity:
    """Tests for JWT token security functions."""

    def test_create_and_decode_access_token(self):
        """Test access token creation and decoding."""
        token = create_access_token(data={"sub": "testuser"})
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload.get("sub") == "testuser"
        assert "exp" in payload

    def test_access_token_custom_expiry(self):
        """Test access token with custom expiry."""
        custom_delta = timedelta(minutes=5)
        token = create_access_token(data={"sub": "testuser"}, expires_delta=custom_delta)
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload.get("sub") == "testuser"

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None."""
        assert decode_access_token("invalid.token.string") is None
        assert decode_access_token("") is None

    def test_decode_expired_token(self):
        """Test decoding expired token returns None."""
        # Create token that expired in the past
        expired_token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(minutes=-1)
        )
        assert decode_access_token(expired_token) is None

    def test_create_and_decode_refresh_token(self):
        """Test refresh token creation and decoding."""
        token = create_refresh_token(data={"sub": "testuser"})
        payload = decode_refresh_token(token)
        
        assert payload is not None
        assert payload.get("sub") == "testuser"


class TestAuthenticateUserService:
    """Tests for authenticate_user service function."""

    def test_authenticate_valid_user(self, db_session: Session):
        """Test authenticating valid user."""
        create_test_user_in_db(db_session, username="authuser", password="authpass123")
        
        user = authenticate_user(db_session, username="authuser", password="authpass123")
        
        assert user is not None
        assert user.username == "authuser"

    def test_authenticate_invalid_username(self, db_session: Session):
        """Test authenticating with invalid username."""
        user = authenticate_user(db_session, username="nonexistent", password="anypass")
        assert user is None

    def test_authenticate_invalid_password(self, db_session: Session):
        """Test authenticating with invalid password."""
        create_test_user_in_db(db_session, username="authuser2", password="correctpass")
        
        user = authenticate_user(db_session, username="authuser2", password="wrongpass")
        assert user is None

    def test_authenticate_disabled_user(self, db_session: Session):
        """Test authenticating disabled user returns None."""
        create_test_user_in_db(
            db_session, 
            username="disabledauth", 
            password="password123",
            disabled=True
        )
        
        user = authenticate_user(db_session, username="disabledauth", password="password123")
        assert user is None
