from typing import Optional

from app.core.config import get_settings
from app.core.security import verify_password

settings = get_settings()


def authenticate_user(username: str, password: str) -> Optional[dict]:
    for user in settings.auth_users:
        if user["username"] != username:
            continue
        if verify_password(password, user["password"]):
            return user
    return None
