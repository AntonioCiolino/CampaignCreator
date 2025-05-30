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
        response = await ac.get("/api/v1/campaigns/") # Adjusted path
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_list_campaigns_with_data():
    # Add a campaign to the test database
    db = TestingSessionLocal()
    # For Campaign ORM model, ensure all required fields from the latest models.py are present
    # Based on previous steps, Campaign ORM model has: id, title, initial_user_prompt, concept, toc, homebrewery_export, owner_id
    # The test Campaign model used here for setup might need to be updated if it causes issues with the actual ORM model.
    # For now, assuming title and owner_id are sufficient for pre-populating,
    # and other fields are nullable or have defaults.
    test_campaign = Campaign(title="Test Campaign 1", owner_id=1) # owner_id is placeholder
    db.add(test_campaign)
    db.commit()
    db.refresh(test_campaign)
    campaign_id = test_campaign.id # Get the id for the path
    db.close()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/campaigns/") # Adjusted path

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["title"] == "Test Campaign 1"
    assert response_data[0]["id"] == campaign_id
    # Asserting based on the Campaign model from models.py which includes these fields
    assert "initial_user_prompt" in response_data[0]
    assert "concept" in response_data[0]
    assert "toc" in response_data[0]
    assert "homebrewery_export" in response_data[0]

@pytest.mark.asyncio
async def test_create_campaign_full_data():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "title": "My Super Campaign",
            "initial_user_prompt": "A world of dragons and magic.",
            "model_id_with_prefix_for_concept": "openai/gpt-3.5-turbo" # Example model
        }
        response = await ac.post("/api/v1/campaigns/", json=payload)

    assert response.status_code == 200, response.text # Include response text on failure
    data = response.json()
    assert data["title"] == "My Super Campaign"
    assert data["initial_user_prompt"] == "A world of dragons and magic."
    assert "id" in data
    assert "owner_id" in data # Default owner_id = 1 from endpoint
    assert "concept" in data # Can be None or str
    assert data["toc"] is None # Should be None initially
    assert data["homebrewery_export"] is None # Should be None initially
    # If LLMs are not actually called in test env, concept might be None.
    # If concept generation is mocked, assert specific mock output.

@pytest.mark.asyncio
async def test_create_campaign_no_model_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "title": "Simple Adventure",
            "initial_user_prompt": "A quiet village with a dark secret."
            # model_id_with_prefix_for_concept is omitted
        }
        response = await ac.post("/api/v1/campaigns/", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Simple Adventure"
    assert data["initial_user_prompt"] == "A quiet village with a dark secret."
    assert "id" in data
    assert "owner_id" in data
    assert "concept" in data # Concept generation might be attempted with a default model or skipped
    assert data["toc"] is None
    assert data["homebrewery_export"] is None

@pytest.mark.asyncio
async def test_create_campaign_only_title():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "title": "The Lone Artifact"
            # initial_user_prompt is omitted
            # model_id_with_prefix_for_concept is omitted
        }
        response = await ac.post("/api/v1/campaigns/", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "The Lone Artifact"
    assert data["initial_user_prompt"] is None
    assert "id" in data
    assert "owner_id" in data
    # Concept should be None as no prompt was provided for generation
    assert data["concept"] is None
    assert data["toc"] is None
    assert data["homebrewery_export"] is None

# If you have a main.py that runs uvicorn, you might need to adjust how 'app' is imported or accessed.
# For example, if app is created inside a function in main.py, you might need:
# from app.main import get_application
# app = get_application()
# Ensure your conftest.py or test setup handles any necessary async setup if needed.
