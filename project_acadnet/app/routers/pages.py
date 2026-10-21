"""Paginile HTML servite de server."""
from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

from app.config import STATIC_DIR

router = APIRouter()


@router.get("/")
def root():
    return RedirectResponse("/display")


@router.get("/display")
def display():
    return FileResponse(STATIC_DIR / "display.html")


@router.get("/leaderboard")
def leaderboard():
    return FileResponse(STATIC_DIR / "leaderboard.html")


@router.get("/arbitru")
def arbitru():
    return FileResponse(STATIC_DIR / "arbitru.html")
