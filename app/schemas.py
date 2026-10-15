from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes long")
        return value


class UserOut(BaseModel):
    id: int
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


Priority = Literal["low", "medium", "high"]
Status = Literal["open", "in_progress", "resolved", "closed"]


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    priority: Priority = "medium"


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    priority: Priority | None = None


class StatusUpdate(BaseModel):
    status: Status


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    created_by: int
    created_at: str
    updated_at: str