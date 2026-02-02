import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app import crud, models, orm_models

# Helper function to create features in DB
def create_db_feature(db: Session, name: str, template: str = "Default template", user_id: int = None) -> orm_models.Feature:
    feature_orm = orm_models.Feature(name=name, template=template, user_id=user_id)
    db.add(feature_orm)
    db.commit()
    db.refresh(feature_orm)
    return feature_orm

# Base URL for features
FEATURES_ENDPOINT = "/api/v1/features/"

# --- API Tests ---

# 1. POST /features/ (create_feature)
@pytest.mark.asyncio
async def test_create_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    feature_data = {"name": "My New Feature", "template": "Template {{value}}"}
    response = await async_client.post(FEATURES_ENDPOINT, json=feature_data)
    assert response.status_code == 200  # Endpoint returns 200, not 201
    data = response.json()
    assert data["name"] == feature_data["name"]
    assert data["template"] == feature_data["template"]
    assert data["user_id"] == current_active_user_override.id

@pytest.mark.asyncio
async def test_create_feature_as_user_duplicate_name(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    create_db_feature(db_session, name="Duplicate Name Feature", user_id=current_active_user_override.id)
    feature_data = {"name": "Duplicate Name Feature", "template": "Some template"}
    response = await async_client.post(FEATURES_ENDPOINT, json=feature_data)
    assert response.status_code == 400
    assert "You already have a feature with this name" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_feature_as_user_same_name_as_system(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    create_db_feature(db_session, name="System Feature Name", user_id=None)
    feature_data = {"name": "System Feature Name", "template": "User version of template"}
    response = await async_client.post(FEATURES_ENDPOINT, json=feature_data)
    assert response.status_code == 400
    assert "You already have a feature with this name" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_feature_unauthenticated(async_client: AsyncClient, db_session: Session):
    from app.services.auth_service import get_current_active_user
    from app.main import app
    app.dependency_overrides.pop(get_current_active_user, None)
    feature_data = {"name": "Unauth Feature", "template": "Template"}
    response = await async_client.post(FEATURES_ENDPOINT, json=feature_data)
    assert response.status_code == 401

# 2. GET /features/ (read_features)
@pytest.mark.asyncio
async def test_read_features_as_user(async_client: AsyncClient, current_active_user_override: models.User, another_user: orm_models.User, db_session: Session):
    create_db_feature(db_session, name="System Feature Read", user_id=None)
    create_db_feature(db_session, name="User1 Feature Read", user_id=current_active_user_override.id)
    create_db_feature(db_session, name="User2 Feature Read", user_id=another_user.id)

    response = await async_client.get(FEATURES_ENDPOINT)
    assert response.status_code == 200
    data = response.json()
    names = {f["name"] for f in data}
    assert "System Feature Read" in names
    assert "User1 Feature Read" in names
    assert "User2 Feature Read" not in names
    assert len(data) == 2

@pytest.mark.asyncio
async def test_read_features_as_superuser(async_client: AsyncClient, superuser_override: models.User, another_user: orm_models.User, db_session: Session):
    create_db_feature(db_session, name="Sys Feature SU Read", user_id=None)
    create_db_feature(db_session, name="Superuser Feature Read", user_id=superuser_override.id)
    create_db_feature(db_session, name="Other User Feature SU Read", user_id=another_user.id)

    response = await async_client.get(FEATURES_ENDPOINT)
    assert response.status_code == 200
    data = response.json()
    names = {f["name"] for f in data}
    assert "Sys Feature SU Read" in names
    assert "Superuser Feature Read" in names
    assert "Other User Feature SU Read" not in names
    assert len(data) == 2

@pytest.mark.asyncio
async def test_read_features_unauthenticated(async_client: AsyncClient, db_session: Session):
    from app.services.auth_service import get_current_active_user
    from app.main import app
    app.dependency_overrides.pop(get_current_active_user, None)
    response = await async_client.get(FEATURES_ENDPOINT)
    assert response.status_code == 401

# 3. GET /features/{feature_id} (read_one_feature)
@pytest.mark.asyncio
async def test_read_own_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    feature = create_db_feature(db_session, name="My Own Feature", user_id=current_active_user_override.id)
    response = await async_client.get(f"{FEATURES_ENDPOINT}{feature.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Own Feature"
    assert data["id"] == feature.id

@pytest.mark.asyncio
async def test_read_system_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    feature = create_db_feature(db_session, name="Readable System Feature", user_id=None)
    response = await async_client.get(f"{FEATURES_ENDPOINT}{feature.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Readable System Feature"

@pytest.mark.asyncio
async def test_read_other_user_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, another_user: orm_models.User, db_session: Session):
    feature_other_user = create_db_feature(db_session, name="Other User's Secret Feature", user_id=another_user.id)
    response = await async_client.get(f"{FEATURES_ENDPOINT}{feature_other_user.id}")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_read_other_user_feature_as_superuser(async_client: AsyncClient, superuser_override: models.User, another_user: orm_models.User, db_session: Session):
    feature_other_user = create_db_feature(db_session, name="User1's Feature For SU", user_id=another_user.id)
    response = await async_client.get(f"{FEATURES_ENDPOINT}{feature_other_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "User1's Feature For SU"

@pytest.mark.asyncio
async def test_read_nonexistent_feature(async_client: AsyncClient, current_active_user_override: models.User):
    response = await async_client.get(f"{FEATURES_ENDPOINT}99999")
    assert response.status_code == 404

# 4. PUT /features/{feature_id} (update_feature)
@pytest.mark.asyncio
async def test_update_own_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    feature = create_db_feature(db_session, name="Update My Feature", user_id=current_active_user_override.id)
    update_data = {"name": "Updated My Feature Name"}
    response = await async_client.put(f"{FEATURES_ENDPOINT}{feature.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated My Feature Name"
    assert data["id"] == feature.id

@pytest.mark.asyncio
async def test_update_system_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    feature = create_db_feature(db_session, name="Try Update System Feature", user_id=None)
    update_data = {"name": "User Tries Updating System"}
    response = await async_client.put(f"{FEATURES_ENDPOINT}{feature.id}", json=update_data)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_other_user_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, another_user: orm_models.User, db_session: Session):
    feature_other = create_db_feature(db_session, name="Other User Feature To Update", user_id=another_user.id)
    update_data = {"name": "User1 Tries Updating User2"}
    response = await async_client.put(f"{FEATURES_ENDPOINT}{feature_other.id}", json=update_data)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_user_feature_as_superuser(async_client: AsyncClient, superuser_override: models.User, another_user: orm_models.User, db_session: Session):
    feature_user = create_db_feature(db_session, name="User Feature SU Update", user_id=another_user.id)
    update_data = {"name": "Superuser Updated User Feature"}
    response = await async_client.put(f"{FEATURES_ENDPOINT}{feature_user.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Superuser Updated User Feature"

@pytest.mark.asyncio
async def test_update_system_feature_as_superuser(async_client: AsyncClient, superuser_override: models.User, db_session: Session):
    feature_sys = create_db_feature(db_session, name="System Feature SU Update", user_id=None)
    update_data = {"name": "Superuser Updated System Feature"}
    response = await async_client.put(f"{FEATURES_ENDPOINT}{feature_sys.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Superuser Updated System Feature"

@pytest.mark.asyncio
async def test_update_feature_name_conflict_user(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    create_db_feature(db_session, name="Existing Name User", user_id=current_active_user_override.id)
    feature_to_update = create_db_feature(db_session, name="Original Name User", user_id=current_active_user_override.id)
    update_data = {"name": "Existing Name User"}
    response = await async_client.put(f"{FEATURES_ENDPOINT}{feature_to_update.id}", json=update_data)
    assert response.status_code == 400
    assert "Another feature with this name already exists for this user" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_feature_name_conflict_system(async_client: AsyncClient, superuser_override: models.User, db_session: Session):
    create_db_feature(db_session, name="Existing System Name", user_id=None)
    feature_to_update = create_db_feature(db_session, name="Original System Name", user_id=None)
    update_data = {"name": "Existing System Name"}
    response = await async_client.put(f"{FEATURES_ENDPOINT}{feature_to_update.id}", json=update_data)
    assert response.status_code == 400
    assert "Another system feature with this name already exists" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_nonexistent_feature(async_client: AsyncClient, current_active_user_override: models.User):
    update_data = {"name": "Trying to update nothing"}
    response = await async_client.put(f"{FEATURES_ENDPOINT}99999", json=update_data)
    assert response.status_code == 404

# 5. DELETE /features/{feature_id}
@pytest.mark.asyncio
async def test_delete_own_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    feature = create_db_feature(db_session, name="Delete My Feature", user_id=current_active_user_override.id)
    response = await async_client.delete(f"{FEATURES_ENDPOINT}{feature.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Delete My Feature"
    assert crud.get_feature(db_session, feature.id) is None

@pytest.mark.asyncio
async def test_delete_system_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, db_session: Session):
    feature = create_db_feature(db_session, name="Try Delete System Feature", user_id=None)
    response = await async_client.delete(f"{FEATURES_ENDPOINT}{feature.id}")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_other_user_feature_as_user(async_client: AsyncClient, current_active_user_override: models.User, another_user: orm_models.User, db_session: Session):
    feature_other = create_db_feature(db_session, name="Other User Feature To Delete", user_id=another_user.id)
    response = await async_client.delete(f"{FEATURES_ENDPOINT}{feature_other.id}")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_user_feature_as_superuser(async_client: AsyncClient, superuser_override: models.User, another_user: orm_models.User, db_session: Session):
    feature_user = create_db_feature(db_session, name="User Feature SU Delete", user_id=another_user.id)
    response = await async_client.delete(f"{FEATURES_ENDPOINT}{feature_user.id}")
    assert response.status_code == 200
    assert crud.get_feature(db_session, feature_user.id) is None

@pytest.mark.asyncio
async def test_delete_system_feature_as_superuser(async_client: AsyncClient, superuser_override: models.User, db_session: Session):
    feature_sys = create_db_feature(db_session, name="System Feature SU Delete", user_id=None)
    response = await async_client.delete(f"{FEATURES_ENDPOINT}{feature_sys.id}")
    assert response.status_code == 200
    assert crud.get_feature(db_session, feature_sys.id) is None

@pytest.mark.asyncio
async def test_delete_nonexistent_feature(async_client: AsyncClient, current_active_user_override: models.User):
    response = await async_client.delete(f"{FEATURES_ENDPOINT}99999")
    assert response.status_code == 404
