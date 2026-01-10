"""
Security utilities: password hashing, token generation.
"""
import hashlib
import uuid
from backend.config import PASSWORD_SALT

__all__ = ["hash_password", "verify_password", "generate_token"]


def hash_password(password: str) -> str:
    """Hash password with salt."""
    return hashlib.sha256(f"{PASSWORD_SALT}{password}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed


def generate_token() -> str:
    """Generate a unique authentication token."""
    return str(uuid.uuid4())
