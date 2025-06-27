from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models # Standardized import
from app.db import get_db # Standardized import
from app.services.auth_service import get_current_active_superuser, get_current_active_user # Standardized import
from app.services.image_generation_service import ImageGenerationService # Added import

router = APIRouter()

# Order matters for /me vs /{user_id} if /me could be misinterpreted as a user_id.
# Placing /me first ensures it's matched correctly.
@router.get("/me", response_model=models.User)
async def read_users_me(
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    """
    Get current logged-in user.
    """
    return current_user

@router.put("/me/keys", response_model=models.User)
def update_my_api_keys(
    api_keys_in: models.UserAPIKeyUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)]
):
    # Assuming current_user from get_current_active_user is an ORM model instance
    # or a Pydantic model that has the user's ID.
    # We need the ORM model of the user to pass to the CRUD function.
    db_user = crud.get_user(db, user_id=current_user.id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_user_orm = crud.update_user_api_keys(db=db, db_user=db_user, api_keys_in=api_keys_in)

    # Construct the response model. This might require converting updated_user_orm
    # to include the dynamically generated *_api_key_provided fields.
    # The crud.update_user_api_keys should ideally return an ORM object that,
    # when converted by FastAPI to models.User, correctly populates these.
    return updated_user_orm

# The old /me/files endpoint has been removed.
# It will be replaced by /campaigns/{campaign_id}/files in campaigns.py.

@router.post("/", response_model=models.User, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user: models.UserCreate,
    db: Annotated[Session, Depends(get_db)],
    current_admin_user: Annotated[models.User, Depends(get_current_active_superuser)]
):
    # Check for existing email
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Check for existing username
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    return crud.create_user(db=db, user=user)

@router.get("/", response_model=List[models.User])
def read_users_endpoint(
    db: Annotated[Session, Depends(get_db)],
    current_admin_user: Annotated[models.User, Depends(get_current_active_superuser)],
    skip: int = 0,
    limit: int = 100
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=models.User)
def read_user_endpoint(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin_user: Annotated[models.User, Depends(get_current_active_superuser)]
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=models.User)
def update_user_endpoint(
    user_id: int,
    user_in: models.UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[models.User, Depends(get_current_active_user)] # Changed dependency
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to update")

    # Check if the current user is the one being updated or is a superuser
    if db_user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")

    # If email is being updated, check if the new email is already taken by another user
    if user_in.email and user_in.email != db_user.email: # check if email is actually changing
        existing_user_with_new_email = crud.get_user_by_email(db, email=user_in.email)
        if existing_user_with_new_email and existing_user_with_new_email.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email already registered by another user")

    # If username is being updated, check if the new username is already taken
    if user_in.username and user_in.username != db_user.username: # check if username is actually changing
        existing_user_with_new_username = crud.get_user_by_username(db, username=user_in.username)
        if existing_user_with_new_username and existing_user_with_new_username.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New username already registered by another user")

    # The crud.update_user function handles password hashing and selective updates
    # based on user_in fields that are not None.
    updated_user = crud.update_user(db=db, db_user=db_user, user_in=user_in)
    return updated_user

@router.delete("/{user_id}", response_model=models.User)
def delete_user_endpoint(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_admin_user: Annotated[models.User, Depends(get_current_active_superuser)]
):
    db_user_to_delete = crud.get_user(db, user_id=user_id) # Fetch first
    if db_user_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to delete")

    # crud.delete_user returns the deleted user object or None if not found (already checked)
    deleted_user_orm = crud.delete_user(db, user_id=user_id)
    return deleted_user_orm # FastAPI will convert this to the response_model
