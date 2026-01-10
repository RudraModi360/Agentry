"""
Static page routes (HTML pages).
"""
import os
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from backend.config import UI_DIR

router = APIRouter()


def safe_file_response(filename: str):
    """Return file if exists, otherwise return JSON placeholder."""
    filepath = os.path.join(UI_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    return JSONResponse({"message": f"UI file '{filename}' not yet created. API is working.", "file": filename})


@router.get("/")
async def landing_page():
    return safe_file_response("index.html")


@router.get("/login")
@router.get("/login.html")
async def login_page():
    return safe_file_response("login.html")


@router.get("/chat")
@router.get("/chat.html")
async def chat_page():
    return safe_file_response("chat.html")


@router.get("/setup")
@router.get("/setup.html")
async def setup_page():
    return safe_file_response("setup.html")


@router.get("/orb")
@router.get("/orb.html")
async def orb_page():
    return safe_file_response("orb.html")
