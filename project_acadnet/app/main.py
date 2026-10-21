from fastapi import FastAPI

from app.routers import pages
from app.ws import endpoint

app = FastAPI()
app.include_router(pages.router)
app.include_router(endpoint.router)
