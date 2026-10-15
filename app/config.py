import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "tickets.db")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-key-change-me-in-production-0000")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))

MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_SECONDS = int(os.getenv("LOCKOUT_SECONDS", "300"))