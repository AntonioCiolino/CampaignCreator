from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models
from app.core.security import decode_access_token, oauth2_scheme
from app.db import get_db
from jose import JWTError # Import JWTError

# Assuming verify_password is in crud.py as confirmed earlier

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> models.User: # Return Pydantic model
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception

        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    db_user_orm = crud.get_user_by_username(db, username=username)

    if db_user_orm is None:
        raise credentials_exception

    user_pydantic = models.User.from_orm(db_user_orm)
    return user_pydantic

async def get_current_active_user(
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.User:
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_active_superuser(
    current_user: Annotated[models.User, Depends(get_current_active_user)]
) -> models.User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """
    Authenticates a user.

    Args:
        db: SQLAlchemy session.
        username: The username to authenticate.
        password: The password to verify.

    Returns:
        The authenticated user object (Pydantic model) if successful, else None.
    """
    db_user = crud.get_user_by_username(db, username=username)
    if not db_user:
        return None
    if db_user.disabled: # Check if the user is disabled
        return None
    if not crud.verify_password(password, db_user.hashed_password):
        return None

    # If authentication is successful, return the Pydantic model of the user
    # This ensures that the response (if this function's output is directly used in an API)
    # conforms to the User Pydantic model.
    return models.User.from_orm(db_user)
