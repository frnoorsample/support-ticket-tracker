"""Password hashing, login tokens and login rate limiting."""
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app import config
from app.database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------- Passwords ----------

def hash_password(password: str) -> str:
    """Hash a password with bcrypt. A random salt is generated every time."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))



DUMMY_HASH = hash_password("dummy-password-for-timing")




def create_access_token(user_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=config.TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expires}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> dict:
    """Dependency: reads the token from the request and returns the logged-in user."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credentials_error

    row = db.execute(
        "SELECT id, username, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row is None:
        raise credentials_error
    return dict(row)


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency: only lets admins through."""
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return user




_failed_logins: dict[str, list[float]] = {}


def check_login_allowed(username: str) -> None:
    now = time.time()
    recent = [t for t in _failed_logins.get(username, []) if now - t < config.LOCKOUT_SECONDS]
    _failed_logins[username] = recent
    if len(recent) >= config.MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
        )


def record_failed_login(username: str) -> None:
    _failed_logins.setdefault(username, []).append(time.time())


def clear_failed_logins(username: str) -> None:
    _failed_logins.pop(username, None)