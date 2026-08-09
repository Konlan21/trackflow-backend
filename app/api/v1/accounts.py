"""
Mirrors accounts/urls.py + accounts/views.py:
  POST /auth/signup
  POST /auth/login
  POST /auth/logout
  GET/PUT/PATCH /auth/user/{userID}/profile
  PUT /auth/user/{userID}/profile/password
  DELETE /auth/user/{userID}/profile
"""
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.token_blacklist import BlacklistedToken
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    SignupRequest,
    SignupResponse,
    UserProfileRead,
    UserProfileUpdate,
    PasswordChangeRequest,
    AccountDeleteRequest,
)

router = APIRouter(tags=["user"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    if await user_crud.get_by_email(db, data.email):
        raise HTTPException(status_code=400, detail={"email": ["A user with this email already exists."]})
    if await user_crud.get_by_username(db, data.username):
        raise HTTPException(status_code=400, detail={"username": ["A user with this username already exists."]})

    user = await user_crud.create_user(db, data)
    return SignupResponse.model_validate(user)


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_by_email(db, data.email)
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail={"detail": "Invalid email or password"})

    return LoginResponse(
        access=create_access_token(str(user.id)),
        refresh=create_refresh_token(str(user.id)),
        id=user.id,
        email=user.email,
    )


@router.post("/logout")
async def logout(data: LogoutRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        payload = decode_token(data.refresh)
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail={"detail": "Invalid refresh token"})

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail={"detail": "Invalid refresh token"})

    db.add(BlacklistedToken(jti=payload["jti"], user_id=current_user.id))
    await db.commit()
    return {"message": "User logged out successfully"}


@router.get("/user/{userID}/profile", response_model=UserProfileRead)
async def get_profile(userID: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if userID != current_user.id:
        raise HTTPException(status_code=403, detail={"detail": "You cannot view another user's profile"})
    return UserProfileRead.model_validate(current_user)


@router.put("/user/{userID}/profile", response_model=UserProfileRead)
@router.patch("/user/{userID}/profile", response_model=UserProfileRead)
async def update_profile(
    userID: uuid.UUID,
    data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if userID != current_user.id:
        raise HTTPException(status_code=403, detail={"detail": "You cannot edit another user's profile"})

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return UserProfileRead.model_validate(current_user)


@router.put("/user/{userID}/profile/password")
async def change_password(
    userID: uuid.UUID,
    data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if userID != current_user.id:
        raise HTTPException(status_code=403, detail={"detail": "You cannot change another user's password"})

    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail={"current_password": ["Current password is incorrect"]})

    current_user.hashed_password = hash_password(data.new_password)
    await db.commit()
    return {"message": "Password updated successfully"}


@router.delete("/user/{userID}/profile")
async def delete_account(
    userID: uuid.UUID,
    data: AccountDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if userID != current_user.id:
        raise HTTPException(status_code=403, detail={"detail": "You cannot delete another user's account"})

    if not verify_password(data.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail={"password": ["Password is incorrect"]})

    await db.delete(current_user)
    await db.commit()
    return {"message": "Account deleted successfully"}