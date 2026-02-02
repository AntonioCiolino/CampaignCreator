import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app import crud, models, orm_models

# These tests verify the campaign sections and features endpoints work correctly
# More detailed mocking tests exist in test_campaigns_api.py

@pytest.mark.asyncio
async def test_create_campaign_with_sections(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    """Test that we can create a campaign and it has the expected structure"""
    campaign_data = {"title": "Test Campaign with Sections"}
    response = await async_client.post("/api/v1/campaigns/", json=campaign_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Campaign with Sections"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_campaign_sections(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    """Test retrieving sections for a campaign"""
    # Create a campaign
    campaign = await crud.create_campaign(
        db=db_session,
        campaign_payload=models.CampaignCreate(title="Campaign for Sections"),
        current_user_obj=current_active_user_override
    )
    
    # Create a section using correct function signature
    section = crud.create_campaign_section(
        db=db_session,
        campaign_id=campaign.id,
        section_title="Test Section",
        section_content="Test content",
        section_type="chapter"
    )
    
    # Get sections
    response = await async_client.get(f"/api/v1/campaigns/{campaign.id}/sections")
    assert response.status_code == 200
    data = response.json()
    sections = data.get("sections", [])
    assert len(sections) >= 1
    assert any(s["title"] == "Test Section" for s in sections)

@pytest.mark.asyncio
async def test_update_campaign_section(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    """Test updating a campaign section"""
    # Create campaign and section
    campaign = await crud.create_campaign(
        db=db_session,
        campaign_payload=models.CampaignCreate(title="Campaign for Update"),
        current_user_obj=current_active_user_override
    )
    
    section = crud.create_campaign_section(
        db=db_session,
        campaign_id=campaign.id,
        section_title="Original Title",
        section_content="Original content",
        section_type="chapter"
    )
    
    # Update section
    update_data = {"title": "Updated Title", "content": "Updated content"}
    response = await async_client.put(
        f"/api/v1/campaigns/{campaign.id}/sections/{section.id}",
        json=update_data
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Updated Title"
    assert updated["content"] == "Updated content"

@pytest.mark.asyncio
async def test_delete_campaign_section(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    """Test deleting a campaign section"""
    # Create campaign and section
    campaign = await crud.create_campaign(
        db=db_session,
        campaign_payload=models.CampaignCreate(title="Campaign for Delete"),
        current_user_obj=current_active_user_override
    )
    
    section = crud.create_campaign_section(
        db=db_session,
        campaign_id=campaign.id,
        section_title="Section to Delete",
        section_content="Content",
        section_type="chapter"
    )
    
    # Delete section
    response = await async_client.delete(f"/api/v1/campaigns/{campaign.id}/sections/{section.id}")
    assert response.status_code == 200
    
    # Verify it's deleted - get_section requires both section_id and campaign_id
    deleted_section = crud.get_section(db_session, section.id, campaign.id)
    assert deleted_section is None
