"""Paginile HTML servite de server."""
from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.config import STATIC_DIR

router = APIRouter()


def page(name: str) -> FileResponse:
    return FileResponse(STATIC_DIR / name)


@router.get("/")
def index():
    return page("index.html")


@router.get("/timer")
def timer_page():
    return page("timer.html")


@router.get("/arbitru")
def arbitru_page():
    return page("arbitru.html")


@router.get("/clasament1")
def clasament1_page():
    return page("clasament1.html")


@router.get("/clasament2")
def clasament2_page():
    return page("clasament2.html")


@router.get("/admin")
def admin_page():
    return page("admin.html")
