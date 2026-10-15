"""Endpoints for registering, logging in and checking who you are."""
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.schemas import Token, UserCreate, UserOut
from app.security import (
    DUMMY_HASH,
    check_login_allowed,
    clear_failed_logins,
    create_access_token,
    get_current_user,
    hash_password,
    record_failed_login,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db=Depends(get_db)):
    try:
        cursor = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (user.username, hash_password(user.password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    
    return {"id": cursor.lastrowid, "username": user.username, "role": "user"}


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    check_login_allowed(form.username)

    row = db.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (form.username,)
    ).fetchone()

    
    password_ok = verify_password(form.password, row["password_hash"] if row else DUMMY_HASH)

    if row is None or not password_ok:
        record_failed_login(form.username)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clear_failed_logins(form.username)
    return {"access_token": create_access_token(row["id"]), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def read_me(user: dict = Depends(get_current_user)):
    return user