from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict

from campaign_crafter_api.app.main import app # Main FastAPI app
from campaign_crafter_api.app.core.config import settings
from campaign_crafter_api.app.models import User as PydanticUser # Pydantic model for response
from campaign_crafter_api.app.orm_models import User as ORMUser
from campaign_crafter_api.app.core.security import decrypt_key, encrypt_key # Added encrypt_key
from campaign_crafter_api.app.tests.utils.user import create_random_user, authentication_token_from_username
from campaign_crafter_api.app.tests.utils.utils import random_lower_string

client = TestClient(app)

def test_update_user_api_keys_set_both(
    db: Session
) -> None:
    created_user = create_random_user(db)
    user_token_headers = authentication_token_from_username(
        username=created_user.username, client=client, db=db
    )

    new_openai_key = f"sk-{random_lower_string(32)}"
    new_sd_key = f"sd-{random_lower_string(32)}"

    response = client.put(
        f"{settings.API_V1_STR}/users/me/keys",
        headers=user_token_headers,
        json={"openai_api_key": new_openai_key, "sd_api_key": new_sd_key},
    )
    assert response.status_code == 200
    updated_user_data = response.json()

    assert updated_user_data["openai_api_key_provided"] is True
    assert updated_user_data["sd_api_key_provided"] is True

    db.refresh(created_user) # Refresh ORM user from DB
    assert created_user.encrypted_openai_api_key is not None
    assert decrypt_key(created_user.encrypted_openai_api_key) == new_openai_key
    assert created_user.encrypted_sd_api_key is not None
    assert decrypt_key(created_user.encrypted_sd_api_key) == new_sd_key

def test_update_user_api_keys_set_one_clear_one(
    db: Session
) -> None:
    # First, set both keys
    user_orm = create_random_user(db)
    initial_openai_key = f"sk-initial-{random_lower_string(16)}"
    initial_sd_key = f"sd-initial-{random_lower_string(16)}"
    user_orm.encrypted_openai_api_key = encrypt_key(initial_openai_key)
    user_orm.encrypted_sd_api_key = encrypt_key(initial_sd_key)
    db.commit()
    db.refresh(user_orm)

    user_token_headers = authentication_token_from_username(
        username=user_orm.username, client=client, db=db
    )

    new_openai_key = f"sk-updated-{random_lower_string(16)}"
    # To clear SD key, send empty string or null (backend UserAPIKeyUpdate model definition and endpoint logic handles this)
    # The UserAPIKeyUpdate Pydantic model allows Optional[str] = None
    # The endpoint logic treats "" as clear.

    response = client.put(
        f"{settings.API_V1_STR}/users/me/keys",
        headers=user_token_headers,
        json={"openai_api_key": new_openai_key, "sd_api_key": ""}, # Clear SD key
    )
    assert response.status_code == 200
    updated_user_data = response.json()

    assert updated_user_data["openai_api_key_provided"] is True
    assert updated_user_data["sd_api_key_provided"] is False # Should be false after clearing

    db.refresh(user_orm)
    assert user_orm.encrypted_openai_api_key is not None
    assert decrypt_key(user_orm.encrypted_openai_api_key) == new_openai_key
    assert user_orm.encrypted_sd_api_key is None # Should be cleared in DB

def test_update_user_api_keys_no_payload(
    db: Session
) -> None:
    # Set initial keys
    user_orm = create_random_user(db)
    initial_openai_key = f"sk-initial-{random_lower_string(16)}"
    user_orm.encrypted_openai_api_key = encrypt_key(initial_openai_key)
    db.commit()
    db.refresh(user_orm)

    user_token_headers = authentication_token_from_username(
        username=user_orm.username, client=client, db=db
    )

    # Sending empty JSON means no change for any key as per current UserAPIKeyUpdate model (all fields Optional)
    # and endpoint logic (if key is not in payload, it's not updated).
    response = client.put(
        f"{settings.API_V1_STR}/users/me/keys",
        headers=user_token_headers,
        json={}, # Empty payload
    )
    assert response.status_code == 200
    updated_user_data = response.json()

    assert updated_user_data["openai_api_key_provided"] is True # Should remain true
    assert updated_user_data["sd_api_key_provided"] is False # Was never set, so should remain false

    db.refresh(user_orm)
    assert user_orm.encrypted_openai_api_key is not None # Check it wasn't cleared
    assert decrypt_key(user_orm.encrypted_openai_api_key) == initial_openai_key
    assert user_orm.encrypted_sd_api_key is None

def test_update_user_api_keys_unauthenticated(
    db: Session # db fixture might not be strictly necessary if no DB interaction before auth check
) -> None:
    response = client.put(
        f"{settings.API_V1_STR}/users/me/keys",
        json={"openai_api_key": "some_key"},
    )
    assert response.status_code == 401 # Expect 401 if no token is provided
                                       # If using OAuth2PasswordBearer, it should be 401.
                                       # If a different scheme makes it 403, adjust.
                                       # Current deps.get_current_active_user raises 401.
