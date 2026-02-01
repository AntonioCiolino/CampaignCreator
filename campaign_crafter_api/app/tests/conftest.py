"""
Shared pytest fixtures for Campaign Crafter API tests.
"""
import pytest
import pytest_asyncio
from typing import Generator, AsyncGenerator, Optional
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db
from app.orm_models import User as ORMUser
from app.models import User as PydanticUser
from app.crud import get_password_hash
from app.services.auth_service import get_current_active_user

# In-memory SQLite database for testing with StaticPool for connection reuse
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # Use StaticPool for in-memory SQLite
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a database session for tests."""
    # Create tables before each test
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after each test
        Base.metadata.drop_all(bind=engine)


def override_get_db(db_session_fixture: Session):
    """Create a dependency override that uses the test session."""
    def _override():
        try:
            yield db_session_fixture
        finally:
            pass  # Don't close - the fixture handles that
    return _override


@pytest.fixture(autouse=True)
def setup_test_database(db_session: Session):
    """Set up database override for each test."""
    # Override the get_db dependency to use our test session
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    # Clean up override
    app.dependency_overrides.pop(get_db, None)


def create_test_user_in_db(
    db: Session,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpassword123",
    is_superuser: bool = False,
    disabled: bool = False
) -> ORMUser:
    """Helper to create a user directly in the database."""
    hashed_password = get_password_hash(password)
    db_user = ORMUser(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_superuser=is_superuser,
        disabled=disabled
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@pytest.fixture
def test_user(db_session: Session) -> ORMUser:
    """Create a standard test user."""
    return create_test_user_in_db(db_session)


@pytest.fixture
def test_superuser(db_session: Session) -> ORMUser:
    """Create a superuser for tests."""
    return create_test_user_in_db(
        db_session,
        username="admin",
        email="admin@example.com",
        password="adminpassword123",
        is_superuser=True
    )


@pytest.fixture
def another_user(db_session: Session) -> ORMUser:
    """Create another user for multi-user tests."""
    return create_test_user_in_db(
        db_session,
        username="anotheruser",
        email="another@example.com",
        password="anotherpassword123"
    )


def get_pydantic_user_from_orm(orm_user: ORMUser) -> PydanticUser:
    """Convert ORM user to Pydantic model."""
    return PydanticUser(
        id=orm_user.id,
        username=orm_user.username,
        email=orm_user.email,
        full_name=orm_user.full_name,
        disabled=orm_user.disabled,
        is_superuser=orm_user.is_superuser,
        openai_api_key_provided=orm_user.openai_api_key_provided,
        sd_api_key_provided=orm_user.sd_api_key_provided,
        sd_engine_preference=orm_user.sd_engine_preference,
        gemini_api_key_provided=orm_user.gemini_api_key_provided,
        other_llm_api_key_provided=orm_user.other_llm_api_key_provided,
        avatar_url=orm_user.avatar_url
    )


@pytest.fixture
def current_active_user_override(test_user: ORMUser) -> Generator[PydanticUser, None, None]:
    """Override get_current_active_user dependency with test user."""
    pydantic_user = get_pydantic_user_from_orm(test_user)
    app.dependency_overrides[get_current_active_user] = lambda: pydantic_user
    yield pydantic_user
    app.dependency_overrides.pop(get_current_active_user, None)


@pytest.fixture
def superuser_override(test_superuser: ORMUser) -> Generator[PydanticUser, None, None]:
    """Override get_current_active_user dependency with superuser."""
    pydantic_user = get_pydantic_user_from_orm(test_superuser)
    app.dependency_overrides[get_current_active_user] = lambda: pydantic_user
    yield pydantic_user
    app.dependency_overrides.pop(get_current_active_user, None)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for API tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def get_auth_headers(
    client: AsyncClient,
    db: Session,
    username: str,
    password: str,
    email: Optional[str] = None,
    is_superuser: bool = False
) -> dict:
    """Get authentication headers for a user."""
    # Ensure user exists
    user = db.query(ORMUser).filter(ORMUser.username == username).first()
    if not user:
        create_test_user_in_db(
            db,
            username=username,
            email=email or f"{username}@example.com",
            password=password,
            is_superuser=is_superuser
        )
    
    login_data = {"username": username, "password": password}
    response = await client.post("/api/v1/auth/token", data=login_data)
    
    if response.status_code != 200:
        raise Exception(f"Failed to get token: {response.text}")
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def user_auth_headers(async_client: AsyncClient, db_session: Session, test_user: ORMUser) -> dict:
    """Get auth headers for the test user."""
    return await get_auth_headers(
        async_client, db_session, 
        username="testuser", 
        password="testpassword123"
    )


@pytest_asyncio.fixture
async def superuser_auth_headers(async_client: AsyncClient, db_session: Session, test_superuser: ORMUser) -> dict:
    """Get auth headers for the superuser."""
    return await get_auth_headers(
        async_client, db_session,
        username="admin",
        password="adminpassword123",
        is_superuser=True
    )
