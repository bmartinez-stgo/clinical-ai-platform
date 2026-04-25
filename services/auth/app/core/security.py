import time
from typing import Any, Dict, List

import bcrypt
import jwt
from fastapi import HTTPException, status


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_access_token(
    subject: str,
    roles: List[str],
    secret: str,
    expiration_seconds: int,
    issuer: str,
    audience: str,
) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + expiration_seconds,
        "iss": issuer,
        "aud": audience,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def create_refresh_token(
    subject: str,
    roles: List[str],
    secret: str,
    expiration_seconds: int,
    issuer: str,
    audience: str,
) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "roles": roles,
        "type": "refresh",
        "iat": now,
        "exp": now + expiration_seconds,
        "iss": issuer,
        "aud": audience,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(
    token: str,
    secret: str,
    issuer: str,
    audience: str,
) -> Dict[str, Any]:
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=issuer,
            audience=audience,
        )
        if claims.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid token type",
            )
        return claims
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        ) from exc


def decode_refresh_token(
    token: str,
    secret: str,
    issuer: str,
    audience: str,
) -> Dict[str, Any]:
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=issuer,
            audience=audience,
        )
        if claims.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid token type",
            )
        return claims
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid refresh token",
        ) from exc
