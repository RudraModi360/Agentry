"""
Configuration and settings for the backend.
"""
import os
from pathlib import Path

# Directory paths
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
UI_DIR = PROJECT_ROOT / "ui"

# Database path (keep in ui/ for backward compatibility)
DB_PATH = str(UI_DIR / "scratchy_users.db")

# Static file directories
ASSETS_DIR = str(UI_DIR / "assets")
MEDIA_DIR = str(UI_DIR / "media")
CSS_DIR = str(UI_DIR / "css")
JS_DIR = str(UI_DIR / "js")

# Ensure media directory exists
os.makedirs(MEDIA_DIR, exist_ok=True)

# CORS settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]
# Add origins from environment if present
env_origins = os.environ.get("CORS_ORIGINS")
if env_origins:
    CORS_ORIGINS.extend(env_origins.split(","))

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Password hashing salt (in production, use per-user salts)
PASSWORD_SALT = "scratchy_salt_2024"
