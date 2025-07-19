from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, crud
from app.services.auth_service import authenticate_user
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token
from app.core.config import settings
from app.db import get_db

router = APIRouter()


@router.post("/token", response_model=models.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    user = authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@router.post("/refresh", response_model=models.Token)
async def refresh_access_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    user = crud.get_user_by_username(db, username=username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}
