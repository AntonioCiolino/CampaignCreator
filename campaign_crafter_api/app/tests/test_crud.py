import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional, List, Dict, AsyncGenerator

from app.db import Base
from app.orm_models import User as ORMUser, Campaign as ORMCampaign, CampaignSection as ORMCampaignSection
from app.models import CampaignSectionUpdateInput
from app import crud

# In-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
async def test_user(db_session: Session) -> ORMUser:
    user_create_data = {"email": "test@example.com", "password": "password123"}
    # crud.create_user is synchronous
    return crud.create_user(db=db_session, user=crud.models.UserCreate(**user_create_data))

@pytest.fixture
async def test_campaign(db_session: Session, test_user: ORMUser) -> ORMCampaign:
    campaign_create_data = crud.models.CampaignCreate(title="Test Campaign for CRUD")
    # crud.create_campaign is asynchronous
    return await crud.create_campaign(db=db_session, campaign_payload=campaign_create_data, owner_id=test_user.id)

# Helper to directly create a campaign with string TOCs in DB for testing conversion
def create_campaign_with_string_toc_in_db(db: Session, owner_id: int, title: str, display_toc_str: str, homebrewery_toc_str: str) -> ORMCampaign:
    campaign = ORMCampaign(
        title=title,
        owner_id=owner_id,
        display_toc=display_toc_str,
        homebrewery_toc=homebrewery_toc_str
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

# --- Tests for TOC ---
@pytest.mark.asyncio
async def test_get_campaign_converts_string_toc(db_session: Session, test_user: ORMUser):
    # Create campaign directly in DB with string TOCs
    old_display_toc_str = "- Chapter 1\n- Chapter 2"
    old_homebrewery_toc_str = "* Chapter 1\n* Chapter 2"
    db_campaign_direct = create_campaign_with_string_toc_in_db(
        db_session, test_user.id, "Campaign With String TOC", old_display_toc_str, old_homebrewery_toc_str
    )

    # Call crud.get_campaign
    retrieved_campaign = crud.get_campaign(db=db_session, campaign_id=db_campaign_direct.id)

    assert retrieved_campaign is not None
    assert retrieved_campaign.display_toc == [{"title": old_display_toc_str, "type": "unknown"}]
    assert retrieved_campaign.homebrewery_toc == [{"title": old_homebrewery_toc_str, "type": "unknown"}]

@pytest.mark.asyncio
async def test_get_campaign_reads_new_format_toc(db_session: Session, test_campaign: ORMCampaign):
    new_display_toc_data = [{"title": "Section 1", "type": "chapter"}, {"title": "NPC Appendix", "type": "appendix"}]
    new_homebrewery_toc_data = [{"title": "HB Section 1", "type": "main"}, {"title": "HB Appendix A", "type": "extra"}]

    updated_campaign = crud.update_campaign_toc(
        db=db_session,
        campaign_id=test_campaign.id,
        display_toc_content=new_display_toc_data,
        homebrewery_toc_content=new_homebrewery_toc_data
    )
    assert updated_campaign is not None

    retrieved_campaign = crud.get_campaign(db=db_session, campaign_id=test_campaign.id)

    assert retrieved_campaign is not None
    assert retrieved_campaign.display_toc == new_display_toc_data
    assert retrieved_campaign.homebrewery_toc == new_homebrewery_toc_data

@pytest.mark.asyncio
async def test_update_campaign_toc_saves_new_format(db_session: Session, test_campaign: ORMCampaign):
    display_toc_list = [{"title": "New Display TOC Item 1", "type": "generic"}]
    homebrewery_toc_list = [{"title": "New Homebrewery TOC Item 1", "type": "custom"}]

    crud.update_campaign_toc(
        db=db_session,
        campaign_id=test_campaign.id,
        display_toc_content=display_toc_list,
        homebrewery_toc_content=homebrewery_toc_list
    )

    # Fetch directly or via get_campaign to check
    fetched_campaign = db_session.query(ORMCampaign).filter(ORMCampaign.id == test_campaign.id).first()
    assert fetched_campaign is not None
    # SQLAlchemy stores JSON types (like our List[Dict]) and returns them as Python dicts/lists
    assert fetched_campaign.display_toc == display_toc_list
    assert fetched_campaign.homebrewery_toc == homebrewery_toc_list

# --- Tests for CampaignSection.type ---
@pytest.mark.asyncio
async def test_create_section_with_placeholder_content_saves_type(db_session: Session, test_campaign: ORMCampaign):
    section1 = crud.create_section_with_placeholder_content(
        db=db_session, campaign_id=test_campaign.id, title="NPC Section", order=0, type="npc"
    )
    assert section1.type == "npc"

    section2 = crud.create_section_with_placeholder_content(
        db=db_session, campaign_id=test_campaign.id, title="Generic Section", order=1
    )
    assert section2.type == "generic" # Default type

@pytest.mark.asyncio
async def test_create_campaign_section_saves_type(db_session: Session, test_campaign: ORMCampaign):
    section1 = crud.create_campaign_section(
        db=db_session, campaign_id=test_campaign.id, section_title="Location Section", section_content="Content...", section_type="location"
    )
    assert section1.type == "location"

    section2 = crud.create_campaign_section(
        db=db_session, campaign_id=test_campaign.id, section_title="Default Type Section", section_content="More content..."
    )
    assert section2.type == "generic" # Default type

@pytest.mark.asyncio
async def test_update_campaign_section_updates_type(db_session: Session, test_campaign: ORMCampaign):
    # Create an initial section
    initial_section = crud.create_campaign_section(
        db=db_session, campaign_id=test_campaign.id, section_title="Initial Section", section_content="Initial content", section_type="chapter"
    )
    assert initial_section.type == "chapter"

    # Update its type
    update_data_with_type = CampaignSectionUpdateInput(type="main_quest")
    updated_section = crud.update_campaign_section(
        db=db_session, section_id=initial_section.id, campaign_id=test_campaign.id, section_update_data=update_data_with_type
    )
    assert updated_section is not None
    assert updated_section.type == "main_quest"

    # Update content without specifying type
    update_data_no_type = CampaignSectionUpdateInput(content="Updated content here.")
    further_updated_section = crud.update_campaign_section(
        db=db_session, section_id=initial_section.id, campaign_id=test_campaign.id, section_update_data=update_data_no_type
    )
    assert further_updated_section is not None
    assert further_updated_section.content == "Updated content here."
    assert further_updated_section.type == "main_quest" # Type should remain unchanged
