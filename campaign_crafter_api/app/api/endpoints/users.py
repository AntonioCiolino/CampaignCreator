from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, orm_models # Assuming these are the correct imports
from app.db import get_db # Assuming this is the correct import for db session

router = APIRouter()

@router.post("/", response_model=models.User, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user: models.UserCreate, db: Session = Depends(get_db)):
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.get("/", response_model=List[models.User])
def read_users_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=models.User)
def read_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=models.User)
def update_user_endpoint(user_id: int, user: models.UserUpdate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to update")

    # If email is being updated, check if the new email is already taken by another user
    if user.email:
        existing_user_with_new_email = crud.get_user_by_email(db, email=user.email)
        if existing_user_with_new_email and existing_user_with_new_email.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New email already registered by another user")

    updated_user = crud.update_user(db=db, user_id=user_id, user_update=user)
    if updated_user is None: # Should ideally be caught by the get_user check, but as a safeguard
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after attempting update")
    return updated_user

@router.delete("/{user_id}", response_model=models.User) # Or return a success message/status
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    db_user_to_delete = crud.delete_user(db, user_id=user_id)
    if db_user_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found to delete")
    # The crud.delete_user returns the deleted user object, which is fine for response_model=models.User
    # Alternatively, could return a {detail: "User deleted"} or just HTTP 204 No Content.
    # For now, returning the deleted user object as per current crud setup.
    return db_user_to_delete
