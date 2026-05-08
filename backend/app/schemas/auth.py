"""
Authentication schemas for user registration, login, and tokens.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    role_id: Optional[int] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user data in responses."""
    user_id: int
    email: EmailStr
    display_name: str
    role_id: int
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Schema for decoded JWT token data."""
    user_id: Optional[int] = None
    email: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=120)
    email: Optional[EmailStr] = None