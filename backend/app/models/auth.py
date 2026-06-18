from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str | None = None
    created_at: datetime


class SessionUser(BaseModel):
    id: str
    email: str
    display_name: str | None = None
