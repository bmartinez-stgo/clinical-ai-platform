import time
from typing import Any, Dict, List

import jwt
from fastapi import HTTPException, status



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
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=issuer,
            audience=audience,
        )
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
