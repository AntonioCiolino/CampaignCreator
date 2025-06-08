import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from typing import Generator, List as TypingList, Optional, Dict

from app.main import app
from app.db import Base, get_db
from app.models import RollTableCreate, RollTableItemCreate, UserCreate, FeatureCreate # Pydantic models
from app.orm_models import User as ORMUser, RollTable as ORMRollTable, RollTableItem as ORMRollTableItem, Feature as ORMFeature # SQLAlchemy models
from app.crud import get_password_hash
from app.crud import create_roll_table as crud_create_roll_table
from app.crud import create_feature as crud_create_feature # For test setup

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

@pytest.fixture(scope="function", autouse=True) # Changed scope to function for cleaner tests
def create_test_tables_fixture():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# --- Helper Functions ---
def create_user_in_db(db: SQLAlchemySession, user_data: dict) -> ORMUser:
    hashed_password = get_password_hash(user_data["password"])
    db_user = ORMUser(
        username=user_data["username"],
        hashed_password=hashed_password,
        email=user_data.get("email", f"{user_data['username']}@example.com"),
        full_name=user_data.get("full_name"),
        disabled=user_data.get("disabled", False),
        is_superuser=user_data.get("is_superuser", False)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

async def get_user_token_headers(client: AsyncClient, db: SQLAlchemySession, username: str, password: str, email: Optional[str] = None, is_superuser: bool = False) -> dict[str, str]:
    user = db.query(ORMUser).filter(ORMUser.username == username).first()
    if not user:
        create_user_in_db(db, {
            "username": username, "password": password, "email": email, "is_superuser": is_superuser
        })

    login_data = {"username": username, "password": password}
    api_prefix = "/api/v1"
    r = await client.post(f"{api_prefix}/auth/token", data=login_data)
    r.raise_for_status() # Ensure login was successful
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

async def get_normal_user_token_headers(client: AsyncClient, db: SQLAlchemySession, username="testuser", password="testpassword") -> dict[str, str]:
    return await get_user_token_headers(client, db, username=username, password=password, email=f"{username}@example.com")

async def get_superuser_token_headers(client: AsyncClient, db: SQLAlchemySession) -> dict[str, str]:
    return await get_user_token_headers(client, db, username="admin", password="changeme", email="admin@example.com", is_superuser=True)


# Helper to create RollTable directly in DB for setup
def create_db_roll_table(db: SQLAlchemySession, name: str, user_id: Optional[int] = None, items_data: Optional[TypingList[Dict]] = None) -> ORMRollTable:
    if items_data is None:
        items_data = [{"min_roll": 1, "max_roll": 10, "description": "Test Item"}]

    pydantic_items = [RollTableItemCreate(**item) for item in items_data]
    roll_table_create = RollTableCreate(name=name, description="Test Desc", items=pydantic_items)

    # Use the CRUD function to ensure consistency, though it means this helper isn't purely DB layer
    return crud_create_roll_table(db=db, roll_table=roll_table_create, user_id=user_id)

# Helper to create Feature directly in DB for setup
def create_db_feature(db: SQLAlchemySession, name: str, template: str, user_id: Optional[int] = None) -> ORMFeature:
    feature_create = FeatureCreate(name=name, template=template)
    # Use the CRUD function for consistency
    return crud_create_feature(db=db, feature=feature_create, user_id=user_id)


@pytest.fixture
async def test_client() -> AsyncClient: # Changed from Generator to direct AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def db_session_for_setup() -> SQLAlchemySession: # For direct DB manipulation in test setup
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Tests for Roll Tables ---

@pytest.mark.asyncio
async def test_api_create_roll_table_authenticated(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="creatoruser")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "creatoruser").first()

    table_data = {
        "name": "My API Table",
        "description": "Created via API",
        "items": [{"min_roll": 1, "max_roll": 100, "description": "API Item"}]
    }
    response = await test_client.post("/api/v1/random-tables/", json=table_data, headers=user_headers)

    assert response.status_code == 200, response.text # Endpoint returns 200 on create
    data = response.json()
    assert data["name"] == "My API Table"
    assert data["user_id"] == user.id
    assert len(data["items"]) == 1
    assert data["items"][0]["description"] == "API Item"

    # Verify in DB
    db_table = db_session_for_setup.query(ORMRollTable).filter(ORMRollTable.name == "My API Table").first()
    assert db_table is not None
    assert db_table.user_id == user.id

@pytest.mark.asyncio
async def test_api_read_roll_tables_authenticated(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="readeruser")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "readeruser").first()

    create_db_roll_table(db_session_for_setup, name="System Table Read Test", user_id=None)
    create_db_roll_table(db_session_for_setup, name="My Table Read Test", user_id=user.id)

    # Create another user and their table, which should not be visible
    other_user = create_user_in_db(db_session_for_setup, {"username": "otherreader", "password": "op"})
    create_db_roll_table(db_session_for_setup, name="Other User Table Read Test", user_id=other_user.id)

    response = await test_client.get("/api/v1/random-tables/", headers=user_headers)
    assert response.status_code == 200, response.text
    data = response.json()

    names = {table["name"] for table in data}
    assert "System Table Read Test" in names
    assert "My Table Read Test" in names
    assert "Other User Table Read Test" not in names # This is key
    assert len(data) == 2


@pytest.mark.asyncio
async def test_api_read_roll_tables_unauthenticated(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user = create_user_in_db(db_session_for_setup, {"username": "owner", "password": "p"})
    create_db_roll_table(db_session_for_setup, name="System Table Unauth Test", user_id=None)
    create_db_roll_table(db_session_for_setup, name="User Table Unauth Test", user_id=user.id)

    response = await test_client.get("/api/v1/random-tables/") # No headers
    assert response.status_code == 200, response.text
    data = response.json()

    names = {table["name"] for table in data}
    assert "System Table Unauth Test" in names
    assert "User Table Unauth Test" not in names
    assert len(data) == 1

@pytest.mark.asyncio
async def test_api_update_roll_table_owner(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="ownerupdateuser")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "ownerupdateuser").first()

    table_to_update = create_db_roll_table(db_session_for_setup, name="Owned Table For Update", user_id=user.id)

    update_data = {"description": "Updated Description by Owner"}
    response = await test_client.put(f"/api/v1/random-tables/{table_to_update.id}", json=update_data, headers=user_headers)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["description"] == "Updated Description by Owner"
    assert data["name"] == "Owned Table For Update" # Name should not change unless specified

@pytest.mark.asyncio
async def test_api_update_roll_table_not_owner(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    owner_user = create_user_in_db(db_session_for_setup, {"username": "actualowner", "password": "p"})
    table_to_update = create_db_roll_table(db_session_for_setup, name="Table Of Actual Owner", user_id=owner_user.id)

    attacker_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="attackeruser")

    update_data = {"description": "Attempted Update by Attacker"}
    response = await test_client.put(f"/api/v1/random-tables/{table_to_update.id}", json=update_data, headers=attacker_headers)

    assert response.status_code == 403, response.text # Forbidden

@pytest.mark.asyncio
async def test_api_update_roll_table_superuser_can_update_others(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    owner_user = create_user_in_db(db_session_for_setup, {"username": "regularowner", "password": "p"})
    table_to_update = create_db_roll_table(db_session_for_setup, name="Table Of Regular Owner", user_id=owner_user.id)

    su_headers = await get_superuser_token_headers(test_client, db_session_for_setup)

    update_data = {"description": "Updated by Superuser"}
    response = await test_client.put(f"/api/v1/random-tables/{table_to_update.id}", json=update_data, headers=su_headers)

    assert response.status_code == 200, response.text
    assert response.json()["description"] == "Updated by Superuser"


@pytest.mark.asyncio
async def test_api_delete_roll_table_owner(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="ownerdeleteuser")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "ownerdeleteuser").first()

    table_to_delete = create_db_roll_table(db_session_for_setup, name="Table To Be Deleted By Owner", user_id=user.id)

    response = await test_client.delete(f"/api/v1/random-tables/{table_to_delete.id}", headers=user_headers)

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Table To Be Deleted By Owner"

    # Verify in DB
    deleted_table_check = db_session_for_setup.query(ORMRollTable).filter(ORMRollTable.id == table_to_delete.id).first()
    assert deleted_table_check is None

@pytest.mark.asyncio
async def test_api_delete_roll_table_not_owner(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    owner_user = create_user_in_db(db_session_for_setup, {"username": "actualownerfordelete", "password": "p"})
    table_to_delete = create_db_roll_table(db_session_for_setup, name="Table Of Actual Owner For Delete", user_id=owner_user.id)

    attacker_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="attackeruserfordelete")

    response = await test_client.delete(f"/api/v1/random-tables/{table_to_delete.id}", headers=attacker_headers)

    assert response.status_code == 403, response.text # Forbidden

@pytest.mark.asyncio
async def test_api_copy_system_tables(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="copieruser")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "copieruser").first()

    create_db_roll_table(db_session_for_setup, name="SysTableToCopy1", user_id=None)
    create_db_roll_table(db_session_for_setup, name="SysTableToCopy2", user_id=None)
    # User already has one table with the same name as a system table
    create_db_roll_table(db_session_for_setup, name="SysTableToCopy1", user_id=user.id, description="User's existing version")

    response = await test_client.post("/api/v1/random-tables/copy-system-tables", headers=user_headers)
    assert response.status_code == 200, response.text
    copied_tables_data = response.json()

    assert len(copied_tables_data) == 1 # Should only copy SysTableToCopy2
    copied_table_names = {t["name"] for t in copied_tables_data}
    assert "SysTableToCopy2" in copied_table_names
    assert "SysTableToCopy1" not in copied_table_names # Because user already had one

    # Verify in DB
    user_tables_after_copy = db_session_for_setup.query(ORMRollTable).filter(ORMRollTable.user_id == user.id).all()
    user_table_names_after_copy = {t.name for t in user_tables_after_copy}

    assert "SysTableToCopy1" in user_table_names_after_copy # The original one
    assert "SysTableToCopy2" in user_table_names_after_copy # The newly copied one
    assert len(user_tables_after_copy) == 2

    # Check that the user's original "SysTableToCopy1" was not overwritten
    original_user_table1 = db_session_for_setup.query(ORMRollTable).filter(ORMRollTable.user_id == user.id, ORMRollTable.name == "SysTableToCopy1").first()
    assert original_user_table1.description == "User's existing version"

    # Call again, should copy no new tables
    response_again = await test_client.post("/api/v1/random-tables/copy-system-tables", headers=user_headers)
    assert response_again.status_code == 200, response_again.text
    assert len(response_again.json()) == 0

# Test for GET specific table (not explicitly in prompt but good to have)
@pytest.mark.asyncio
async def test_api_read_specific_roll_table(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="specificreader")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "specificreader").first()

    # User's own table
    user_table = create_db_roll_table(db_session_for_setup, name="My Specific Table", user_id=user.id)
    # System table
    system_table = create_db_roll_table(db_session_for_setup, name="Specific System Table", user_id=None)

    # Read user's own table
    response_user = await test_client.get(f"/api/v1/random-tables/{user_table.id}", headers=user_headers)
    assert response_user.status_code == 200, response_user.text
    assert response_user.json()["name"] == "My Specific Table"

    # Read system table (should be allowed for any authenticated user, or even unauthenticated depending on endpoint security)
    # Current endpoint for single table does not check ownership, just existence.
    response_system = await test_client.get(f"/api/v1/random-tables/{system_table.id}", headers=user_headers)
    assert response_system.status_code == 200, response_system.text
    assert response_system.json()["name"] == "Specific System Table"

    # Read non-existent table
    response_non_existent = await test_client.get("/api/v1/random-tables/99999", headers=user_headers)
    assert response_non_existent.status_code == 404


# Test for random item endpoint (briefly, as service is tested more deeply)
@pytest.mark.asyncio
async def test_api_get_random_item(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="itemroller")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "itemroller").first()

    # User table with specific name
    create_db_roll_table(db_session_for_setup, name="ItemTestUserTable", user_id=user.id, items_data=[{"min_roll":1, "max_roll":1, "description":"User Only Item"}])
    # System table with different name
    create_db_roll_table(db_session_for_setup, name="ItemTestSystemTable", user_id=None, items_data=[{"min_roll":1, "max_roll":1, "description":"System Only Item"}])
    # System table with same name as user table
    create_db_roll_table(db_session_for_setup, name="ItemTestUserTable", user_id=None, items_data=[{"min_roll":1, "max_roll":1, "description":"System Version of ItemTestUserTable"}])

    # Roll on user's table (user specific version should be prioritized)
    response_user_table = await test_client.get("/api/v1/random-tables/ItemTestUserTable/item", headers=user_headers)
    assert response_user_table.status_code == 200
    assert response_user_table.json()["item"] == "User Only Item"

    # Roll on system table (that user does not own)
    response_system_table = await test_client.get("/api/v1/random-tables/ItemTestSystemTable/item", headers=user_headers)
    assert response_system_table.status_code == 200
    assert response_system_table.json()["item"] == "System Only Item"

    # Unauthenticated user rolls on system table
    response_unauth_system = await test_client.get("/api/v1/random-tables/ItemTestSystemTable/item")
    assert response_unauth_system.status_code == 200
    assert response_unauth_system.json()["item"] == "System Only Item"

    # Unauthenticated user tries to roll on a table name that only exists for a user
    # (should result in system table lookup, which fails, so 404)
    response_unauth_user_only_name = await test_client.get("/api/v1/random-tables/ItemTestUserTable/item") # This table name also exists as system
    assert response_unauth_user_only_name.status_code == 200 # Will get system version
    assert response_unauth_user_only_name.json()["item"] == "System Version of ItemTestUserTable"

    # Test non-existent table
    response_non_existent_item = await test_client.get("/api/v1/random-tables/NonExistentTableForItems/item", headers=user_headers)
    assert response_non_existent_item.status_code == 404
    assert "Table 'NonExistentTableForItems' not found" in response_non_existent_item.json()["detail"]

# TODO: Add tests for superuser update/delete of system tables if that's allowed.
# Current logic: system tables (user_id=None) cannot be updated/deleted by current permission checks
# as they don't have a user_id matching current_user.id, and is_superuser check for these operations
# might need to explicitly allow if user_id is None.
# For now, assuming system tables are protected from modification/deletion via these standard endpoints.

# Test cases for table name conflicts during creation
@pytest.mark.asyncio
async def test_api_create_roll_table_name_conflict_user_and_system(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="conflictuser")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "conflictuser").first()

    # System table
    create_db_roll_table(db_session_for_setup, name="ConflictNameTable", user_id=None)

    # User tries to create table with same name as system table - this should be allowed
    table_data_user = {
        "name": "ConflictNameTable", "description": "User version",
        "items": [{"min_roll": 1, "max_roll": 1, "description": "User item"}]
    }
    response_user = await test_client.post("/api/v1/random-tables/", json=table_data_user, headers=user_headers)
    assert response_user.status_code == 200, response_user.text
    assert response_user.json()["user_id"] == user.id
    assert response_user.json()["description"] == "User version"

    # User tries to create table with same name again - this should fail (user already has one)
    response_user_again = await test_client.post("/api/v1/random-tables/", json=table_data_user, headers=user_headers)
    assert response_user_again.status_code == 400, response_user_again.text # From endpoint check
    assert "Rolltable with this name already exists" in response_user_again.json()["detail"] # or similar from crud check

    # What if a superuser tries to create a SYSTEM table with a name that a USER already has?
    # Current create_roll_table endpoint always assigns current_user.id if authenticated.
    # To create a true system table via API, it might need a dedicated superuser endpoint or flag.
    # The current POST / endpoint will create it for the superuser themselves, not as a system table.
    su_headers = await get_superuser_token_headers(test_client, db_session_for_setup)
    superuser = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "admin").first()
    table_data_su_as_system_attempt = {
        "name": "UserOwnedNameForSystemTest", "description": "Superuser's table, not system",
        "items": [{"min_roll": 1, "max_roll": 1, "description": "SU item"}]
    }
    # First, a normal user creates this table:
    create_db_roll_table(db_session_for_setup, name="UserOwnedNameForSystemTest", user_id=user.id)

    # Superuser attempts to create a table with the same name.
    # It will be assigned to the superuser, not as a system table.
    # Name conflict check in create_roll_table endpoint: "Rolltable with this name already exists"
    # This check is on (name, user_id) OR (name, user_id=None) basis from get_roll_table_by_name.
    # The endpoint's initial check is: `crud.get_roll_table_by_name(db, name=roll_table.name, user_id=current_user.id)`
    # This means a superuser CAN create a table with the same name as a user's table, because it will be for the superuser.
    # And a superuser CAN create a table with the same name as a system table, because it will be for the superuser.
    response_su_create = await test_client.post("/api/v1/random-tables/", json=table_data_su_as_system_attempt, headers=su_headers)
    assert response_su_create.status_code == 200
    assert response_su_create.json()["user_id"] == superuser.id
    assert response_su_create.json()["name"] == "UserOwnedNameForSystemTest"

# TODO: Test updating a user table to a name that conflicts with another of *their own* tables.
# TODO: Test updating a user table to a name that conflicts with a *system* table (should be allowed).
# TODO: Test updating a system table (if allowed, and how name conflicts are handled).


# --- API Tests for Features ---

@pytest.mark.asyncio
async def test_api_create_feature_authenticated(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="featurecreator")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "featurecreator").first()

    feature_data = {"name": "My API Feature", "template": "Template for {name}"}
    response = await test_client.post("/api/v1/features/", json=feature_data, headers=user_headers)

    assert response.status_code == 200, response.text # Endpoint returns 200 on create
    data = response.json()
    assert data["name"] == "My API Feature"
    assert data["user_id"] == user.id
    assert data["template"] == "Template for My API Feature"

    # Verify in DB
    db_feature = db_session_for_setup.query(ORMFeature).filter(ORMFeature.name == "My API Feature").first()
    assert db_feature is not None
    assert db_feature.user_id == user.id

@pytest.mark.asyncio
async def test_api_create_feature_name_conflict_same_user(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="featureconflictuser")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "featureconflictuser").first()

    create_db_feature(db_session_for_setup, name="Conflict Feature", template="Original", user_id=user.id)

    feature_data = {"name": "Conflict Feature", "template": "Attempted duplicate"}
    response = await test_client.post("/api/v1/features/", json=feature_data, headers=user_headers)

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "You already have a feature with this name."

@pytest.mark.asyncio
async def test_api_create_feature_name_conflict_system_override(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="featureoverrideuser")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "featureoverrideuser").first()

    create_db_feature(db_session_for_setup, name="System Feature To Override", template="System Version", user_id=None)

    feature_data = {"name": "System Feature To Override", "template": "User Version"}
    response = await test_client.post("/api/v1/features/", json=feature_data, headers=user_headers)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "System Feature To Override"
    assert data["template"] == "User Version"
    assert data["user_id"] == user.id

    # Verify user has their own version
    user_feature = db_session_for_setup.query(ORMFeature).filter(ORMFeature.name == "System Feature To Override", ORMFeature.user_id == user.id).first()
    assert user_feature is not None
    assert user_feature.template == "User Version"

@pytest.mark.asyncio
async def test_api_read_features_authenticated(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="featurereader")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "featurereader").first()

    create_db_feature(db_session_for_setup, name="SysFeature Read Test", template="Sys", user_id=None)
    create_db_feature(db_session_for_setup, name="MyFeature Read Test", template="User", user_id=user.id)

    other_user = create_user_in_db(db_session_for_setup, {"username": "otherfeaturereader", "password": "op"})
    create_db_feature(db_session_for_setup, name="OtherUserFeature Read Test", template="Other", user_id=other_user.id)

    response = await test_client.get("/api/v1/features/", headers=user_headers)
    assert response.status_code == 200, response.text
    data = response.json()

    names = {f["name"] for f in data}
    assert "SysFeature Read Test" in names
    assert "MyFeature Read Test" in names
    assert "OtherUserFeature Read Test" not in names
    assert len(data) == 2

# test_api_read_features_unauthenticated: Not applicable as endpoint requires auth by default.

@pytest.mark.asyncio
async def test_api_update_feature_owner(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="featureownerupdate")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "featureownerupdate").first()

    feature_to_update = create_db_feature(db_session_for_setup, name="Owned Feature", template="Original Template", user_id=user.id)

    update_data = {"template": "Updated Template by Owner"}
    response = await test_client.put(f"/api/v1/features/{feature_to_update.id}", json=update_data, headers=user_headers)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["template"] == "Updated Template by Owner"

@pytest.mark.asyncio
async def test_api_update_feature_not_owner(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    owner_user = create_user_in_db(db_session_for_setup, {"username": "actualfeatureowner", "password": "p"})
    feature_to_update = create_db_feature(db_session_for_setup, name="Another Owner's Feature", template="Belongs to actualfeatureowner", user_id=owner_user.id)

    attacker_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="featureattacker")

    update_data = {"template": "Attempted Update by Attacker on Feature"}
    response = await test_client.put(f"/api/v1/features/{feature_to_update.id}", json=update_data, headers=attacker_headers)

    assert response.status_code == 403, response.text

@pytest.mark.asyncio
async def test_api_update_feature_admin_can_update_others(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    owner_user = create_user_in_db(db_session_for_setup, {"username": "regularfeatureowner", "password": "p"})
    feature_to_update = create_db_feature(db_session_for_setup, name="Regular User Feature", template="Original", user_id=owner_user.id)

    su_headers = await get_superuser_token_headers(test_client, db_session_for_setup)

    update_data = {"template": "Updated by Superuser Feature"}
    response = await test_client.put(f"/api/v1/features/{feature_to_update.id}", json=update_data, headers=su_headers)

    assert response.status_code == 200, response.text
    assert response.json()["template"] == "Updated by Superuser Feature"

@pytest.mark.asyncio
async def test_api_delete_feature_owner(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    user_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="featureownerdelete")
    user = db_session_for_setup.query(ORMUser).filter(ORMUser.username == "featureownerdelete").first()

    feature_to_delete = create_db_feature(db_session_for_setup, name="Feature To Delete By Owner", template="delete me", user_id=user.id)

    response = await test_client.delete(f"/api/v1/features/{feature_to_delete.id}", headers=user_headers)

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Feature To Delete By Owner"

    # Verify in DB
    deleted_feature_check = db_session_for_setup.query(ORMFeature).filter(ORMFeature.id == feature_to_delete.id).first()
    assert deleted_feature_check is None

@pytest.mark.asyncio
async def test_api_delete_feature_not_owner(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    owner_user = create_user_in_db(db_session_for_setup, {"username": "actualfeatureownerfordelete", "password": "p"})
    feature_to_delete = create_db_feature(db_session_for_setup, name="Actual Owner's Feature For Delete", template="don't delete me", user_id=owner_user.id)

    attacker_headers = await get_normal_user_token_headers(test_client, db_session_for_setup, username="featureattackerfordelete")

    response = await test_client.delete(f"/api/v1/features/{feature_to_delete.id}", headers=attacker_headers)

    assert response.status_code == 403, response.text

@pytest.mark.asyncio
async def test_api_delete_feature_admin_can_delete_others(test_client: AsyncClient, db_session_for_setup: SQLAlchemySession):
    owner_user = create_user_in_db(db_session_for_setup, {"username": "regularfeatureownerfordelete", "password": "p"})
    feature_to_delete = create_db_feature(db_session_for_setup, name="Regular User Feature to be Deleted by Admin", template="admin delete", user_id=owner_user.id)

    su_headers = await get_superuser_token_headers(test_client, db_session_for_setup)

    response = await test_client.delete(f"/api/v1/features/{feature_to_delete.id}", headers=su_headers)

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Regular User Feature to be Deleted by Admin"

    # Verify in DB
    deleted_feature_check = db_session_for_setup.query(ORMFeature).filter(ORMFeature.id == feature_to_delete.id).first()
    assert deleted_feature_check is None
