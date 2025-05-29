import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient


from app.main import app  # Adjust if your FastAPI app instance is named differently or located elsewhere
from app.db import Base, get_db  # Adjust to your actual db setup and get_db dependency
from app.orm_models import Campaign # Import your Campaign ORM model

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
# DATABASE_URL = "sqlite:///./test.db" # Alternative: use a file-based test DB

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread for SQLite
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Pytest fixture to create tables for each test function
@pytest.fixture(autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_list_campaigns_empty_db():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/campaigns/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_list_campaigns_with_data():
    # Add a campaign to the test database
    db = TestingSessionLocal()
    test_campaign = Campaign(title="Test Campaign 1", owner_id=1) # owner_id is placeholder
    db.add(test_campaign)
    db.commit()
    db.refresh(test_campaign)
    campaign_id = test_campaign.id # Get the id for the path
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/campaigns/")
    
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["title"] == "Test Campaign 1"
    assert response_data[0]["id"] == campaign_id
    # Add more assertions if your Campaign model has more fields you want to check
    # For example, if initial_user_prompt, concept etc. are part of the response model
    assert "initial_user_prompt" in response_data[0]
    assert "concept" in response_data[0]


# If you have a main.py that runs uvicorn, you might need to adjust how 'app' is imported or accessed.
# For example, if app is created inside a function in main.py, you might need:
# from app.main import get_application
# app = get_application()
# Ensure your conftest.py or test setup handles any necessary async setup if needed.
