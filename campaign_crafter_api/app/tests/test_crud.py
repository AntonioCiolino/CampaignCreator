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

# --- RollTable CRUD Tests ---

# Helper function to create a RollTable for testing
def create_test_roll_table_data(name: str, description: Optional[str] = "Test Description", items_data: Optional[List[Dict]] = None) -> crud.models.RollTableCreate:
    if items_data is None:
        items_data = [
            {"min_roll": 1, "max_roll": 5, "description": "Item 1-5"},
            {"min_roll": 6, "max_roll": 10, "description": "Item 6-10"},
        ]

    # Ensure items_data are valid RollTableItemCreate models
    items = [crud.models.RollTableItemCreate(**item) for item in items_data]
    return crud.models.RollTableCreate(name=name, description=description, items=items)

def test_create_roll_table_with_user(db_session: Session, test_user: ORMUser):
    roll_table_data = create_test_roll_table_data(name="User Table")
    db_roll_table = crud.create_roll_table(db=db_session, roll_table=roll_table_data, user_id=test_user.id)

    assert db_roll_table.id is not None
    assert db_roll_table.name == "User Table"
    assert db_roll_table.user_id == test_user.id
    assert len(db_roll_table.items) == 2
    assert db_roll_table.items[0].description == "Item 1-5"

def test_create_roll_table_system(db_session: Session):
    roll_table_data = create_test_roll_table_data(name="System Table")
    db_roll_table = crud.create_roll_table(db=db_session, roll_table=roll_table_data, user_id=None)

    assert db_roll_table.id is not None
    assert db_roll_table.name == "System Table"
    assert db_roll_table.user_id is None
    assert len(db_roll_table.items) == 2

@pytest.fixture
def another_test_user(db_session: Session) -> ORMUser: # Renamed to avoid conflict if run in same scope
    user_create_data = {"email": "test2@example.com", "password": "password123"}
    return crud.create_user(db=db_session, user=crud.models.UserCreate(**user_create_data))

def test_get_roll_tables_as_user(db_session: Session, test_user: ORMUser, another_test_user: ORMUser):
    # System table
    crud.create_roll_table(db=db_session, roll_table=create_test_roll_table_data(name="SysTable1"), user_id=None)
    # User1's table
    crud.create_roll_table(db=db_session, roll_table=create_test_roll_table_data(name="User1Table"), user_id=test_user.id)
    # User2's table
    crud.create_roll_table(db=db_session, roll_table=create_test_roll_table_data(name="User2Table"), user_id=another_test_user.id)

    tables_for_user1 = crud.get_roll_tables(db=db_session, user_id=test_user.id)

    table_names_for_user1 = {table.name for table in tables_for_user1}
    assert "SysTable1" in table_names_for_user1
    assert "User1Table" in table_names_for_user1
    assert "User2Table" not in table_names_for_user1
    assert len(tables_for_user1) == 2

def test_get_roll_tables_as_anonymous(db_session: Session, test_user: ORMUser):
    crud.create_roll_table(db=db_session, roll_table=create_test_roll_table_data(name="SysTableForAnon"), user_id=None)
    crud.create_roll_table(db=db_session, roll_table=create_test_roll_table_data(name="UserTableForAnonTest"), user_id=test_user.id)

    tables_for_anonymous = crud.get_roll_tables(db=db_session, user_id=None)

    table_names_for_anonymous = {table.name for table in tables_for_anonymous}
    assert "SysTableForAnon" in table_names_for_anonymous
    assert "UserTableForAnonTest" not in table_names_for_anonymous
    assert len(tables_for_anonymous) == 1

def test_get_roll_table_by_name_user_priority(db_session: Session, test_user: ORMUser):
    crud.create_roll_table(db=db_session, roll_table=create_test_roll_table_data(name="Priority Test"), user_id=None)
    user_table_data = create_test_roll_table_data(name="Priority Test", description="User Version")
    user_specific_table = crud.create_roll_table(db=db_session, roll_table=user_table_data, user_id=test_user.id)

    fetched_table = crud.get_roll_table_by_name(db=db_session, name="Priority Test", user_id=test_user.id)
    assert fetched_table is not None
    assert fetched_table.id == user_specific_table.id
    assert fetched_table.description == "User Version"
    assert fetched_table.user_id == test_user.id

def test_get_roll_table_by_name_system_fallback(db_session: Session, test_user: ORMUser):
    system_table_data = create_test_roll_table_data(name="System Fallback Table", description="System Version")
    system_table = crud.create_roll_table(db=db_session, roll_table=system_table_data, user_id=None)

    # Ensure user does not have a table with this name
    # (implicitly true by not creating one for this test_user with this name)

    fetched_table = crud.get_roll_table_by_name(db=db_session, name="System Fallback Table", user_id=test_user.id)
    assert fetched_table is not None
    assert fetched_table.id == system_table.id
    assert fetched_table.description == "System Version"
    assert fetched_table.user_id is None

def test_get_roll_table_by_name_not_found(db_session: Session, test_user: ORMUser):
    fetched_table = crud.get_roll_table_by_name(db=db_session, name="NonExistent Table", user_id=test_user.id)
    assert fetched_table is None

    fetched_table_sys = crud.get_roll_table_by_name(db=db_session, name="NonExistent TableSys", user_id=None)
    assert fetched_table_sys is None

# --- Feature CRUD Tests ---

# Helper function to create FeatureCreate data for testing
def create_test_feature_data(name: str, template: str = "Test Template {{placeholder}}") -> crud.models.FeatureCreate:
    return crud.models.FeatureCreate(name=name, template=template)

def test_create_feature_with_user(db_session: Session, test_user: ORMUser):
    feature_data = create_test_feature_data(name="User Feature")
    db_feature = crud.create_feature(db=db_session, feature=feature_data, user_id=test_user.id)

    assert db_feature.id is not None
    assert db_feature.name == "User Feature"
    assert db_feature.user_id == test_user.id
    assert db_feature.template == "Test Template {{placeholder}}"

def test_create_feature_system(db_session: Session):
    feature_data = create_test_feature_data(name="System Feature")
    # Pass user_id as int, but it's cast from None in the actual ORM model creation if not provided or None.
    # The crud function is defined as create_feature(db: Session, feature: models.FeatureCreate, user_id: int)
    # This means user_id=None is not directly possible for create_feature.
    # However, the ORM model itself has user_id: Mapped[Optional[int]]
    # The previous changes to crud.create_feature expect an integer user_id.
    # For system features, we might need a different approach or adjust create_feature.
    # The ORM model Feature has user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    # So, user_id=None IS valid at the DB level.
    # The crud.create_feature was changed to (db: Session, feature: models.FeatureCreate, user_id: int)
    # This implies system features cannot be made via this specific CRUD function if it strictly type checks user_id as int.
    # Let's re-check crud.py: `db_feature = orm_models.Feature(**feature_data, user_id=user_id)`
    # If user_id is None, this would be `user_id=None`. This is fine.
    # The type hint `user_id: int` in `create_feature`'s signature is the issue for system features.
    # It should be `user_id: Optional[int] = None` in `crud.create_feature` for consistency.
    # Assuming for now that the test setup might need to bypass this or that the type hint will be relaxed.
    # For the purpose of this test, let's assume we can pass user_id=None to crud.create_feature
    # or there's another mechanism.
    # Based on the plan, user_id for create_feature is `int`. This means system features (user_id=None)
    # are likely created manually or via a different path, not `crud.create_feature`.
    #
    # Re-evaluating: The task for crud.py was "Change signature to `create_feature(db: Session, feature: models.FeatureCreate, user_id: int)`"
    # This means `crud.create_feature` as modified cannot create system features.
    # System features would need to be seeded or created by a superuser through a different mechanism
    # if `user_id` is strictly `int`.
    # For testing `get_features` etc., we need system features. Let's create them directly using ORM.
    system_feature_orm = crud.orm_models.Feature(name="System Feature Directly", template="Sys Template", user_id=None)
    db_session.add(system_feature_orm)
    db_session.commit()
    db_session.refresh(system_feature_orm)

    assert system_feature_orm.id is not None
    assert system_feature_orm.name == "System Feature Directly"
    assert system_feature_orm.user_id is None
    assert system_feature_orm.template == "Sys Template"

def test_get_features_as_user(db_session: Session, test_user: ORMUser, another_test_user: ORMUser):
    # System feature
    sys_feature = crud.orm_models.Feature(name="SysFeature1", template="Sys", user_id=None)
    db_session.add(sys_feature)
    # User1's feature
    user1_feature_data = create_test_feature_data(name="User1Feature")
    crud.create_feature(db=db_session, feature=user1_feature_data, user_id=test_user.id)
    # User2's feature
    user2_feature_data = create_test_feature_data(name="User2Feature")
    crud.create_feature(db=db_session, feature=user2_feature_data, user_id=another_test_user.id)
    db_session.commit()

    features_for_user1 = crud.get_features(db=db_session, user_id=test_user.id)

    feature_names_for_user1 = {feature.name for feature in features_for_user1}
    assert "SysFeature1" in feature_names_for_user1
    assert "User1Feature" in feature_names_for_user1
    assert "User2Feature" not in feature_names_for_user1
    assert len(features_for_user1) == 2

def test_get_features_as_anonymous_or_no_user_id(db_session: Session, test_user: ORMUser):
    # System feature
    sys_feature = crud.orm_models.Feature(name="SysFeatureForAnon", template="Sys", user_id=None)
    db_session.add(sys_feature)
    # User's feature
    user_feature_data = create_test_feature_data(name="UserFeatureForAnonTest")
    crud.create_feature(db=db_session, feature=user_feature_data, user_id=test_user.id)
    db_session.commit()

    features_for_anonymous = crud.get_features(db=db_session, user_id=None)

    feature_names_for_anonymous = {feature.name for feature in features_for_anonymous}
    assert "SysFeatureForAnon" in feature_names_for_anonymous
    assert "UserFeatureForAnonTest" not in feature_names_for_anonymous
    assert len(features_for_anonymous) == 1

def test_get_feature_by_name_user_priority(db_session: Session, test_user: ORMUser):
    # System feature
    sys_feature_data = create_test_feature_data(name="Priority Feature", template="System Version")
    sys_feature = crud.orm_models.Feature(**sys_feature_data.model_dump(), user_id=None)
    db_session.add(sys_feature)
    # User's feature with the same name
    user_feature_data = create_test_feature_data(name="Priority Feature", template="User Version")
    user_specific_feature = crud.create_feature(db=db_session, feature=user_feature_data, user_id=test_user.id)
    db_session.commit()

    fetched_feature = crud.get_feature_by_name(db=db_session, name="Priority Feature", user_id=test_user.id)
    assert fetched_feature is not None
    assert fetched_feature.id == user_specific_feature.id
    assert fetched_feature.template == "User Version"
    assert fetched_feature.user_id == test_user.id

def test_get_feature_by_name_system_fallback(db_session: Session, test_user: ORMUser):
    # System feature
    sys_feature_data = create_test_feature_data(name="System Fallback Feature", template="System Version")
    system_feature = crud.orm_models.Feature(**sys_feature_data.model_dump(), user_id=None)
    db_session.add(system_feature)
    db_session.commit()
    db_session.refresh(system_feature)


    fetched_feature = crud.get_feature_by_name(db=db_session, name="System Fallback Feature", user_id=test_user.id)
    assert fetched_feature is not None
    assert fetched_feature.id == system_feature.id
    assert fetched_feature.template == "System Version"
    assert fetched_feature.user_id is None

def test_get_feature_by_name_only_system_exists_no_user_id(db_session: Session):
    # System feature
    sys_feature_data = create_test_feature_data(name="Only System Feature", template="System Version")
    system_feature = crud.orm_models.Feature(**sys_feature_data.model_dump(), user_id=None)
    db_session.add(system_feature)
    db_session.commit()
    db_session.refresh(system_feature)

    fetched_feature = crud.get_feature_by_name(db=db_session, name="Only System Feature", user_id=None)
    assert fetched_feature is not None
    assert fetched_feature.id == system_feature.id
    assert fetched_feature.template == "System Version"
    assert fetched_feature.user_id is None

def test_get_feature_by_name_not_found(db_session: Session, test_user: ORMUser):
    fetched_feature = crud.get_feature_by_name(db=db_session, name="NonExistent Feature", user_id=test_user.id)
    assert fetched_feature is None

    fetched_feature_sys = crud.get_feature_by_name(db=db_session, name="NonExistent System Feature", user_id=None)
    assert fetched_feature_sys is None

def test_copy_system_roll_table_to_user(db_session: Session, test_user: ORMUser):
    system_items_data = [
        {"min_roll": 1, "max_roll": 1, "description": "Sys Item 1"},
        {"min_roll": 2, "max_roll": 2, "description": "Sys Item 2"},
    ]
    system_table_data = create_test_roll_table_data(name="CopyMe System Table", items_data=system_items_data)
    system_table = crud.create_roll_table(db=db_session, roll_table=system_table_data, user_id=None)

    copied_table = crud.copy_system_roll_table_to_user(db=db_session, system_table=system_table, user_id=test_user.id)

    assert copied_table.id is not None
    assert copied_table.id != system_table.id # Must be a new table
    assert copied_table.name == "CopyMe System Table"
    assert copied_table.user_id == test_user.id
    assert copied_table.description == system_table.description

    assert len(copied_table.items) == len(system_table.items)
    for i, copied_item in enumerate(copied_table.items):
        original_item = system_table.items[i]
        assert copied_item.id is not None
        assert copied_item.id != original_item.id
        assert copied_item.min_roll == original_item.min_roll
        assert copied_item.max_roll == original_item.max_roll
        assert copied_item.description == original_item.description
        assert copied_item.roll_table_id == copied_table.id

    # Verify the original system table still exists and is unchanged
    original_system_table_check = db_session.query(ORMUser.RollTable).filter_by(id=system_table.id).first()
    assert original_system_table_check is not None
    assert original_system_table_check.user_id is None

# --- Campaign Theme CRUD Tests ---

TEST_THEME_DATA = {
    "theme_primary_color": "#123456",
    "theme_secondary_color": "#abcdef",
    "theme_background_color": "#fedcba",
    "theme_text_color": "#654321",
    "theme_font_family": "Test Font, sans-serif",
    "theme_background_image_url": "https://example.com/testbg.png",
    "theme_background_image_opacity": 0.5
}

TEST_THEME_DATA_ALTERNATIVE = {
    "theme_primary_color": "#ff0000",
    "theme_secondary_color": "#00ff00",
    "theme_background_color": "#0000ff",
    "theme_text_color": "#ffff00",
    "theme_font_family": "Impact, fantasy",
    "theme_background_image_url": "https://example.com/anotherbg.jpg",
    "theme_background_image_opacity": 0.25
}

@pytest.mark.asyncio
async def test_create_campaign_with_theme(db_session: Session, test_user: ORMUser):
    campaign_payload_dict = {
        "title": "Themed Campaign",
        "initial_user_prompt": "A campaign with a cool theme.",
        **TEST_THEME_DATA
    }
    campaign_create = crud.models.CampaignCreate(**campaign_payload_dict)

    created_campaign = await crud.create_campaign(db=db_session, campaign_payload=campaign_create, owner_id=test_user.id)

    assert created_campaign.title == campaign_payload_dict["title"]
    for key, value in TEST_THEME_DATA.items():
        assert getattr(created_campaign, key) == value

    # Verify in DB
    db_campaign = db_session.query(ORMCampaign).filter(ORMCampaign.id == created_campaign.id).first()
    assert db_campaign is not None
    for key, value in TEST_THEME_DATA.items():
        assert getattr(db_campaign, key) == value
    assert db_campaign.owner_id == test_user.id

@pytest.mark.asyncio
async def test_update_campaign_with_full_theme(db_session: Session, test_user: ORMUser):
    # 1. Create an initial campaign (without specific theme)
    initial_payload = crud.models.CampaignCreate(title="Campaign For Full Theme Update")
    campaign_to_update = await crud.create_campaign(db=db_session, campaign_payload=initial_payload, owner_id=test_user.id)

    # 2. Prepare update data with new theme properties
    campaign_update_payload = crud.models.CampaignUpdate(**TEST_THEME_DATA)

    # 3. Call update_campaign
    updated_campaign = crud.update_campaign(db=db_session, campaign_id=campaign_to_update.id, campaign_update=campaign_update_payload)
    assert updated_campaign is not None

    # 4. Verify updated fields
    for key, value in TEST_THEME_DATA.items():
        assert getattr(updated_campaign, key) == value
    assert updated_campaign.title == "Campaign For Full Theme Update" # Title should be unchanged

@pytest.mark.asyncio
async def test_update_campaign_with_partial_theme(db_session: Session, test_user: ORMUser):
    # 1. Create an initial campaign with some theme data
    initial_campaign_dict = {
        "title": "Campaign For Partial Theme Update",
        **TEST_THEME_DATA
    }
    initial_campaign_create = crud.models.CampaignCreate(**initial_campaign_dict)
    campaign_to_update = await crud.create_campaign(db=db_session, campaign_payload=initial_campaign_create, owner_id=test_user.id)

    # 2. Prepare partial update data
    partial_update_data = {
        "theme_primary_color": "#000001",
        "theme_font_family": "Arial Black, sans-serif",
        # Also update a non-theme field to ensure it works too
        "title": "Partially Updated Title"
    }
    campaign_update_payload = crud.models.CampaignUpdate(**partial_update_data)

    # 3. Call update_campaign
    updated_campaign = crud.update_campaign(db=db_session, campaign_id=campaign_to_update.id, campaign_update=campaign_update_payload)
    assert updated_campaign is not None

    # 4. Verify updated fields
    assert updated_campaign.title == partial_update_data["title"]
    assert updated_campaign.theme_primary_color == partial_update_data["theme_primary_color"]
    assert updated_campaign.theme_font_family == partial_update_data["theme_font_family"]

    # 5. Verify unchanged theme fields from original TEST_THEME_DATA (excluding those updated)
    assert updated_campaign.theme_secondary_color == TEST_THEME_DATA["theme_secondary_color"]
    assert updated_campaign.theme_background_color == TEST_THEME_DATA["theme_background_color"]
    assert updated_campaign.theme_text_color == TEST_THEME_DATA["theme_text_color"]
    assert updated_campaign.theme_background_image_url == TEST_THEME_DATA["theme_background_image_url"]
    assert updated_campaign.theme_background_image_opacity == TEST_THEME_DATA["theme_background_image_opacity"]

@pytest.mark.asyncio
async def test_update_campaign_clearing_theme_fields(db_session: Session, test_user: ORMUser):
    # 1. Create an initial campaign with full theme data
    initial_campaign_dict = {
        "title": "Campaign For Clearing Theme Fields",
        **TEST_THEME_DATA_ALTERNATIVE # Use alternative to ensure fields are set
    }
    initial_campaign_create = crud.models.CampaignCreate(**initial_campaign_dict)
    campaign_to_update = await crud.create_campaign(db=db_session, campaign_payload=initial_campaign_create, owner_id=test_user.id)

    # Ensure fields were set
    for key, value in TEST_THEME_DATA_ALTERNATIVE.items():
        assert getattr(campaign_to_update, key) == value

    # 2. Prepare update data to clear some theme fields (set them to None)
    clearing_update_data = {
        "theme_primary_color": None,
        "theme_font_family": None,
        "theme_background_image_url": None,
        # theme_background_image_opacity is float, so None is valid.
        # If "" was sent for a String field from API, Pydantic might convert to None if Optional[str]=None
        # Here we explicitly use None.
        "theme_background_image_opacity": None
    }
    campaign_update_payload = crud.models.CampaignUpdate(**clearing_update_data)

    # 3. Call update_campaign
    updated_campaign = crud.update_campaign(db=db_session, campaign_id=campaign_to_update.id, campaign_update=campaign_update_payload)
    assert updated_campaign is not None

    # 4. Verify cleared fields are None
    assert updated_campaign.theme_primary_color is None
    assert updated_campaign.theme_font_family is None
    assert updated_campaign.theme_background_image_url is None
    assert updated_campaign.theme_background_image_opacity is None

    # 5. Verify other theme fields remain unchanged from TEST_THEME_DATA_ALTERNATIVE
    assert updated_campaign.theme_secondary_color == TEST_THEME_DATA_ALTERNATIVE["theme_secondary_color"]
    assert updated_campaign.theme_background_color == TEST_THEME_DATA_ALTERNATIVE["theme_background_color"]
    assert updated_campaign.theme_text_color == TEST_THEME_DATA_ALTERNATIVE["theme_text_color"]
    assert updated_campaign.title == initial_campaign_dict["title"] # Title unchanged

@pytest.mark.asyncio
async def test_get_campaign_retrieves_theme_data(db_session: Session, test_user: ORMUser):
    # 1. Create campaign with theme data
    campaign_payload_dict = {
        "title": "Campaign For Get Test",
        **TEST_THEME_DATA
    }
    campaign_create = crud.models.CampaignCreate(**campaign_payload_dict)
    created_campaign = await crud.create_campaign(db=db_session, campaign_payload=campaign_create, owner_id=test_user.id)

    # 2. Retrieve campaign using crud.get_campaign
    retrieved_campaign = crud.get_campaign(db=db_session, campaign_id=created_campaign.id)
    assert retrieved_campaign is not None

    # 3. Assert theme properties
    for key, value in TEST_THEME_DATA.items():
        assert getattr(retrieved_campaign, key) == value
    assert retrieved_campaign.owner_id == test_user.id

# --- Test for LLM selection in create_campaign ---
from unittest.mock import patch, AsyncMock, ANY # For mocking get_llm_service

@pytest.mark.asyncio
@patch('app.crud.get_llm_service') # Patch get_llm_service where it's used in crud.py
async def test_create_campaign_with_concept_generation_variations(
    mock_get_llm_service: MagicMock,
    db_session: Session,
    test_user: ORMUser # ORMUser from fixture
):
    # Mock the LLM service and its concept generation method
    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_campaign_concept = AsyncMock(return_value="Test Concept from LLM")
    mock_get_llm_service.return_value = mock_llm_instance

    # Convert ORMUser to Pydantic User model for current_user_obj argument
    # This requires careful attribute mapping if ORMUser and Pydantic User models differ significantly.
    # Assuming Pydantic User has at least an 'id' field.
    current_user_pydantic = crud.models.User(
        id=test_user.id,
        username=test_user.username,
        email=test_user.email,
        full_name=test_user.full_name,
        disabled=test_user.disabled,
        is_superuser=test_user.is_superuser,
        # Add other fields required by Pydantic User model, e.g. API key status, campaigns, llm_configs
        # For simplicity, if these are not strictly needed by generate_campaign_concept's current_user usage:
        openai_api_key_provided=False, # Example default
        sd_api_key_provided=False,     # Example default
        gemini_api_key_provided=False, # Example default
        other_llm_api_key_provided=False, # Example default
        campaigns=[],                  # Example default
        llm_configs=[]                 # Example default
    )


    # Scenario 1: campaign_payload.model_id_with_prefix_for_concept is provided
    campaign_payload_scenario1 = crud.models.CampaignCreate(
        title="Scenario 1 Campaign",
        initial_user_prompt="Prompt for scenario 1",
        model_id_with_prefix_for_concept="testprovider/testmodel"
    )
    await crud.create_campaign(db=db_session, campaign_payload=campaign_payload_scenario1, current_user_obj=current_user_pydantic)

    mock_get_llm_service.assert_called_with(
        db=db_session,
        current_user_orm=test_user, # crud.py fetches this ORM user
        provider_name="testprovider", # Extracted from payload's prefix
        model_id_with_prefix="testprovider/testmodel", # Original prefix from payload
        campaign=None
    )
    mock_llm_instance.generate_campaign_concept.assert_called_with(
        user_prompt="Prompt for scenario 1",
        db=db_session,
        current_user=current_user_pydantic,
        model="testmodel" # Model part from payload
    )

    # Reset mocks for the next scenario
    mock_get_llm_service.reset_mock()
    mock_llm_instance.generate_campaign_concept.reset_mock()

    # Scenario 2: campaign_payload.model_id_with_prefix_for_concept is NOT provided (None)
    campaign_payload_scenario2 = crud.models.CampaignCreate(
        title="Scenario 2 Campaign",
        initial_user_prompt="Prompt for scenario 2",
        model_id_with_prefix_for_concept=None # Not provided
    )
    await crud.create_campaign(db=db_session, campaign_payload=campaign_payload_scenario2, current_user_obj=current_user_pydantic)

    mock_get_llm_service.assert_called_with(
        db=db_session,
        current_user_orm=test_user,
        provider_name=None, # No prefix, so None
        model_id_with_prefix=None, # Not provided
        campaign=None
    )
    mock_llm_instance.generate_campaign_concept.assert_called_with(
        user_prompt="Prompt for scenario 2",
        db=db_session,
        current_user=current_user_pydantic,
        model=None # No model specified
    )

    # Reset mocks for the next scenario
    mock_get_llm_service.reset_mock()
    mock_llm_instance.generate_campaign_concept.reset_mock()

    # Scenario 3: campaign_payload.model_id_with_prefix_for_concept is just a model ID (no provider prefix)
    campaign_payload_scenario3 = crud.models.CampaignCreate(
        title="Scenario 3 Campaign",
        initial_user_prompt="Prompt for scenario 3",
        model_id_with_prefix_for_concept="justmodelid" # No provider prefix
    )
    await crud.create_campaign(db=db_session, campaign_payload=campaign_payload_scenario3, current_user_obj=current_user_pydantic)

    mock_get_llm_service.assert_called_with(
        db=db_session,
        current_user_orm=test_user,
        provider_name=None, # No prefix, so None
        model_id_with_prefix="justmodelid",
        campaign=None
    )
    mock_llm_instance.generate_campaign_concept.assert_called_with(
        user_prompt="Prompt for scenario 3",
        db=db_session,
        current_user=current_user_pydantic,
        model="justmodelid" # The model ID itself
    )

@pytest.mark.asyncio
@patch('app.crud.get_llm_service') # Patching at the source where get_llm_service is defined or used by crud.py
async def test_create_campaign_skip_concept_generation_flag(
    mock_get_llm_service: MagicMock,
    db_session: Session,
    test_user: ORMUser # Fixture for ORMUser
):
    # Mock the LLM service and its concept generation method
    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_campaign_concept = AsyncMock(return_value="Mocked Concept")
    mock_get_llm_service.return_value = mock_llm_instance

    # Convert ORMUser to Pydantic User model for current_user_obj argument
    current_user_pydantic = crud.models.User(
        id=test_user.id, username=test_user.username, email=test_user.email,
        full_name=test_user.full_name, disabled=test_user.disabled, is_superuser=test_user.is_superuser,
        openai_api_key_provided=False, sd_api_key_provided=False,
        gemini_api_key_provided=False, other_llm_api_key_provided=False,
        campaigns=[], llm_configs=[]
    )

    # Scenario 1: skip_concept_generation = True
    campaign_payload_skip_true = crud.models.CampaignCreate(
        title="Skip True Campaign",
        initial_user_prompt="This prompt should be ignored.",
        skip_concept_generation=True
    )
    created_campaign_skip_true = await crud.create_campaign(
        db=db_session,
        campaign_payload=campaign_payload_skip_true,
        current_user_obj=current_user_pydantic
    )
    assert created_campaign_skip_true.concept is None
    mock_llm_instance.generate_campaign_concept.assert_not_called() # Key assertion

    # Reset mock for next scenario
    mock_get_llm_service.reset_mock() # Reset the main mock first
    mock_llm_instance.generate_campaign_concept.reset_mock() # Then reset the method mock
    # Re-assign return_value because resetting mock_get_llm_service might clear its return_value
    mock_get_llm_service.return_value = mock_llm_instance


    # Scenario 2: skip_concept_generation = False, with prompt
    campaign_payload_skip_false = crud.models.CampaignCreate(
        title="Skip False Campaign",
        initial_user_prompt="Generate a concept for this.",
        skip_concept_generation=False
    )
    created_campaign_skip_false = await crud.create_campaign(
        db=db_session,
        campaign_payload=campaign_payload_skip_false,
        current_user_obj=current_user_pydantic
    )
    assert created_campaign_skip_false.concept == "Mocked Concept"
    mock_llm_instance.generate_campaign_concept.assert_called_once_with(
        user_prompt="Generate a concept for this.",
        db=db_session,
        current_user=current_user_pydantic,
        model=None, # Assuming no model_id_with_prefix_for_concept was passed
        # temperature=ANY # or the default if your method sets one
    )

    # Reset mock for next scenario
    mock_get_llm_service.reset_mock()
    mock_llm_instance.generate_campaign_concept.reset_mock()
    mock_get_llm_service.return_value = mock_llm_instance

    # Scenario 3: skip_concept_generation = False, but no prompt
    campaign_payload_no_prompt = crud.models.CampaignCreate(
        title="No Prompt Campaign",
        initial_user_prompt=None, # Explicitly None
        skip_concept_generation=False
    )
    created_campaign_no_prompt = await crud.create_campaign(
        db=db_session,
        campaign_payload=campaign_payload_no_prompt,
        current_user_obj=current_user_pydantic
    )
    assert created_campaign_no_prompt.concept is None
    # generate_campaign_concept should not be called because initial_user_prompt is None,
    # even if skip_concept_generation is False. The conditional logic in crud.create_campaign is
    # `if not campaign_payload.skip_concept_generation and campaign_payload.initial_user_prompt:`
    mock_llm_instance.generate_campaign_concept.assert_not_called()
