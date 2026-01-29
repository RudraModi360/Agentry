"""
Authentication data models.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional

__all__ = [
    "UserCredentials", 
    "UserRegistration", 
    "UserProfileUpdate", 
    "PasswordChange",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "SmtpConfig"
]


class UserCredentials(BaseModel):
    username: str
    password: str


class UserRegistration(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str


class SmtpConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
