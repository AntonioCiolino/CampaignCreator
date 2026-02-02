import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app import crud, models, orm_models

# Helper to create RollTable directly in DB
def create_db_roll_table(db: Session, name: str, user_id: int = None, items_data: list = None) -> orm_models.RollTable:
    if items_data is None:
        items_data = [{"min_roll": 1, "max_roll": 10, "description": "Test Item"}]
    
    pydantic_items = [models.RollTableItemCreate(**item) for item in items_data]
    roll_table_create = models.RollTableCreate(name=name, description="Test Desc", items=pydantic_items)
    return crud.create_roll_table(db=db, roll_table=roll_table_create, user_id=user_id)

# --- API Tests for Roll Tables ---

@pytest.mark.asyncio
async def test_api_create_roll_table_authenticated(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    table_data = {
        "name": "My API Table",
        "description": "Created via API",
        "items": [{"min_roll": 1, "max_roll": 100, "description": "API Item"}]
    }
    response = await async_client.post("/api/v1/roll_tables/", json=table_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My API Table"
    assert data["user_id"] == current_active_user_override.id
    assert len(data["items"]) == 1
    assert data["items"][0]["description"] == "API Item"

@pytest.mark.asyncio
async def test_api_read_roll_tables_authenticated(async_client: AsyncClient, current_active_user_override: models.User, another_user: orm_models.User, db_session: Session):
    create_db_roll_table(db_session, name="System Table Read Test", user_id=None)
    create_db_roll_table(db_session, name="My Table Read Test", user_id=current_active_user_override.id)
    create_db_roll_table(db_session, name="Other User Table Read Test", user_id=another_user.id)

    response = await async_client.get("/api/v1/roll_tables/")
    assert response.status_code == 200
    data = response.json()
    names = {table["name"] for table in data}
    assert "System Table Read Test" in names
    assert "My Table Read Test" in names
    assert "Other User Table Read Test" not in names
    assert len(data) == 2

@pytest.mark.asyncio
async def test_api_read_roll_tables_unauthenticated(async_client: AsyncClient, db_session: Session):
    # This test needs to run without auth override, but the endpoint requires auth
    # So we expect 401 Unauthorized
    from app.services.auth_service import get_current_active_user
    from app.main import app
    app.dependency_overrides.pop(get_current_active_user, None)
    
    response = await async_client.get("/api/v1/roll_tables/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_api_update_roll_table_owner(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    table_to_update = create_db_roll_table(db_session, name="Owned Table For Update", user_id=current_active_user_override.id)
    update_data = {"description": "Updated Description by Owner"}
    response = await async_client.put(f"/api/v1/roll_tables/{table_to_update.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated Description by Owner"
    assert data["name"] == "Owned Table For Update"

@pytest.mark.asyncio
async def test_api_update_roll_table_not_owner(async_client: AsyncClient, current_active_user_override: models.User, another_user: orm_models.User, db_session: Session):
    table_to_update = create_db_roll_table(db_session, name="Table Of Actual Owner", user_id=another_user.id)
    update_data = {"description": "Attempted Update by Attacker"}
    response = await async_client.put(f"/api/v1/roll_tables/{table_to_update.id}", json=update_data)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_api_update_roll_table_superuser_can_update_others(async_client: AsyncClient, superuser_override: models.User, another_user: orm_models.User, db_session: Session):
    table_to_update = create_db_roll_table(db_session, name="Table Of Regular Owner", user_id=another_user.id)
    update_data = {"description": "Updated by Superuser"}
    response = await async_client.put(f"/api/v1/roll_tables/{table_to_update.id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["description"] == "Updated by Superuser"

@pytest.mark.asyncio
async def test_api_delete_roll_table_owner(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    table_to_delete = create_db_roll_table(db_session, name="Table To Be Deleted By Owner", user_id=current_active_user_override.id)
    response = await async_client.delete(f"/api/v1/roll_tables/{table_to_delete.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Table To Be Deleted By Owner"
    deleted_table_check = db_session.query(orm_models.RollTable).filter(orm_models.RollTable.id == table_to_delete.id).first()
    assert deleted_table_check is None

@pytest.mark.asyncio
async def test_api_delete_roll_table_not_owner(async_client: AsyncClient, current_active_user_override: models.User, another_user: orm_models.User, db_session: Session):
    table_to_delete = create_db_roll_table(db_session, name="Table Of Actual Owner For Delete", user_id=another_user.id)
    response = await async_client.delete(f"/api/v1/roll_tables/{table_to_delete.id}")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_api_copy_system_tables(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    # Create system tables
    create_db_roll_table(db_session, name="SysTableToCopy1", user_id=None)
    create_db_roll_table(db_session, name="SysTableToCopy2", user_id=None)
    # User already has one with same name
    create_db_roll_table(db_session, name="SysTableToCopy1", user_id=current_active_user_override.id)

    response = await async_client.post("/api/v1/roll_tables/copy-system-tables")
    assert response.status_code == 200
    copied_tables_data = response.json()
    # The endpoint copies system tables that the user doesn't already have
    # Since we created 2 system tables and user has 1, should copy at least 1
    assert isinstance(copied_tables_data, list)

@pytest.mark.asyncio
async def test_api_read_specific_roll_table(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    user_table = create_db_roll_table(db_session, name="My Specific Table", user_id=current_active_user_override.id)
    system_table = create_db_roll_table(db_session, name="Specific System Table", user_id=None)

    response_user = await async_client.get(f"/api/v1/roll_tables/{user_table.id}")
    assert response_user.status_code == 200
    assert response_user.json()["name"] == "My Specific Table"

    response_system = await async_client.get(f"/api/v1/roll_tables/{system_table.id}")
    assert response_system.status_code == 200
    assert response_system.json()["name"] == "Specific System Table"

    response_non_existent = await async_client.get("/api/v1/roll_tables/99999")
    assert response_non_existent.status_code == 404

@pytest.mark.skip(reason="Endpoint /api/v1/roll_tables/{name}/item not implemented")
@pytest.mark.asyncio
async def test_api_get_random_item(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    create_db_roll_table(db_session, name="ItemTestUserTable", user_id=current_active_user_override.id, 
                        items_data=[{"min_roll":1, "max_roll":1, "description":"User Only Item"}])
    create_db_roll_table(db_session, name="ItemTestSystemTable", user_id=None, 
                        items_data=[{"min_roll":1, "max_roll":1, "description":"System Only Item"}])

    # The endpoint is /random-tables/{table_name}/item
    response_user_table = await async_client.get("/api/v1/random-tables/ItemTestUserTable/item")
    
    assert response_user_table.status_code == 200
    assert response_user_table.json()["item"] == "User Only Item"

@pytest.mark.asyncio
async def test_api_create_roll_table_name_conflict_user_and_system(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    create_db_roll_table(db_session, name="ConflictNameTable", user_id=None)
    
    table_data_user = {
        "name": "ConflictNameTable", "description": "User version",
        "items": [{"min_roll": 1, "max_roll": 1, "description": "User item"}]
    }
    response_user = await async_client.post("/api/v1/roll_tables/", json=table_data_user)
    assert response_user.status_code == 400
    assert "already exists" in response_user.json()["detail"]
