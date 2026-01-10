"""
Authentication data models.
"""
from pydantic import BaseModel

__all__ = ["UserCredentials"]


class UserCredentials(BaseModel):
    username: str
    password: str
