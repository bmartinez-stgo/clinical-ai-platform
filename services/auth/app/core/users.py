from typing import Optional

from app.core.config import get_settings

settings = get_settings()



def authenticate_user(username: str, password: str) -> Optional[dict]:
    for user in settings.auth_users:
        if user["username"] == username and user["password"] == password:
            return user
    return None
