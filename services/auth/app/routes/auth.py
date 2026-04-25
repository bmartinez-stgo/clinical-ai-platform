from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.core.users import authenticate_user

router = APIRouter()
settings = get_settings()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class ValidateResponse(BaseModel):
    active: bool
    subject: str
    expires_at: int
    service: str


def extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing authorization header",
        )
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid authorization header",
        )
    return parts[1]


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
        )

    roles = user.get("roles", [])

    access_token = create_access_token(
        subject=user["username"],
        roles=roles,
        secret=settings.auth_token_secret,
        expiration_seconds=settings.token_expiration_seconds,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    refresh_token = create_refresh_token(
        subject=user["username"],
        roles=roles,
        secret=settings.refresh_token_secret,
        expiration_seconds=settings.refresh_token_expiration_seconds,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.token_expiration_seconds,
        refresh_expires_in=settings.refresh_token_expiration_seconds,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(payload: RefreshRequest):
    claims = decode_refresh_token(
        token=payload.refresh_token,
        secret=settings.refresh_token_secret,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )

    access_token = create_access_token(
        subject=claims["sub"],
        roles=claims.get("roles", []),
        secret=settings.auth_token_secret,
        expiration_seconds=settings.token_expiration_seconds,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )

    return RefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.token_expiration_seconds,
    )


@router.get("/validate", response_model=ValidateResponse)
async def validate(authorization: Optional[str] = Header(default=None)):
    token = extract_bearer_token(authorization)
    claims = decode_access_token(
        token=token,
        secret=settings.auth_token_secret,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )

    return ValidateResponse(
        active=True,
        subject=claims["sub"],
        expires_at=claims["exp"],
        service=settings.app_name,
    )
