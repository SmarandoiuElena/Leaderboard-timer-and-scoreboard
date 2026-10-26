"""Server de arbitraj Acadnet.
Pornire (din folderul proiectului):  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.routers import admin, pages
from app.services.errors import CmdError
from app.ws import endpoint
from app.ws.watcher import watch_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(watch_database())   # ruleaza cat timp ruleaza serverul
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(pages.router)
app.include_router(admin.router)
app.include_router(endpoint.router)


@app.exception_handler(CmdError)
async def cmd_error_handler(request, err: CmdError):
    """Erorile de validare din API ajung la pagina ca {"detail": mesaj}, cu status 400."""
    return JSONResponse({"detail": str(err)}, status_code=400)
