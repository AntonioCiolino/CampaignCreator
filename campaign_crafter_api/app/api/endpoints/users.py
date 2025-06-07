from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models # Removed orm_models import as it's not directly used here
from app.db import get_db
from app.services.auth_service import get_current_active_superuser

router = APIRouter()

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
    current_admin_user: Annotated[models.User, Depends(get_current_active_superuser)]
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to update")

    # If email is being updated, check if the new email is already taken by another user
    if user_in.email:
        existing_user_with_new_email = crud.get_user_by_email(db, email=user_in.email)
        if existing_user_with_new_email and existing_user_with_new_email.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email already registered by another user")

    # If username is being updated, check if the new username is already taken
    # (UserUpdate inherits from UserBase which has username)
    if user_in.username:
        existing_user_with_new_username = crud.get_user_by_username(db, username=user_in.username)
        if existing_user_with_new_username and existing_user_with_new_username.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New username already registered by another user")

    updated_user = crud.update_user(db=db, db_user=db_user, user_in=user_in)
    # The crud.update_user now returns the updated user ORM object.
    # FastAPI will automatically convert it to the response_model (models.User)
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
