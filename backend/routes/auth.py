"""
routes/auth.py

POST /api/v1/auth/register       — create HR user account
POST /api/v1/auth/login          — returns JWT access token
GET  /api/v1/auth/me             — returns current user profile
POST /api/v1/auth/google         — Google OAuth2 sign-in / sign-up
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import httpx

from config import settings
from db.session import get_db
from db.models import HRUser
from services.auth_service import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    # role is hardcoded to "hr" — only admins can elevate roles via separate endpoint


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    existing = await db.execute(select(HRUser).where(HRUser.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = HRUser(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role="hr",  # hardcoded — prevents privilege escalation on self-registration
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(str(user.id), user.email, user.role)
    return TokenOut(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )


@router.post("/login", response_model=TokenOut)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenOut:
    result = await db.execute(select(HRUser).where(HRUser.email == form.username))
    user: HRUser | None = result.scalar_one_or_none()

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token(str(user.id), user.email, user.role)
    return TokenOut(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )


@router.get("/me", response_model=UserOut)
async def me(user: HRUser = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )


class GoogleLoginIn(BaseModel):
    credential: str  # authorization code from OAuth2 popup


@router.post("/google", response_model=TokenOut)
async def google_login(body: GoogleLoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": body.credential,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": "http://localhost:3000/auth/google/callback",
                "grant_type": "authorization_code",
            },
        )
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Google token exchange failed: {token_resp.text}")

    tokens = token_resp.json()
    try:
        info = id_token.verify_oauth2_token(
            tokens["id_token"],
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Google token: {exc}")

    email: str = info["email"]
    full_name: str = info.get("name", email.split("@")[0])

    result = await db.execute(select(HRUser).where(HRUser.email == email))
    user: HRUser | None = result.scalar_one_or_none()

    if not user:
        user = HRUser(
            email=email,
            hashed_password=hash_password(info["sub"]),
            full_name=full_name,
            role="hr",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token(str(user.id), user.email, user.role)
    return TokenOut(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
    )
