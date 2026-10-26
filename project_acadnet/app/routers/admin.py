"""API-ul paginii de administrare: echipe si incercari (CRUD).
Dupa fiecare modificare trimitem starea noua pe WebSocket, ca timerul si clasamentele sa se actualizeze imediat."""
from fastapi import APIRouter, Body

from app.services import attempts, storage, teams
from app.services.errors import CmdError
from app.state import snapshot
from app.ws.manager import manager

router = APIRouter(prefix="/api")


async def changed() -> None:
    await manager.broadcast(snapshot())


# ---- echipe

@router.get("/teams")
def list_teams():
    return storage.load_teams()


@router.post("/teams", status_code=201)
async def create_team(data: dict = Body(...)):
    team = teams.create(data)
    await changed()
    return team


@router.put("/teams/{team_id}")
async def update_team(team_id: int, data: dict = Body(...)):
    team = teams.update(team_id, data)
    await changed()
    return team


@router.delete("/teams/{team_id}", status_code=204)
async def delete_team(team_id: int):
    teams.delete(team_id)
    await changed()


# ---- incercari (proba = 1 sau 2)

@router.get("/attempts/{proba}")
def list_attempts(proba: int):
    attempts.check_proba(proba)
    return list(reversed(storage.load_attempts(proba)))     # cele mai noi primele


@router.post("/attempts/{proba}", status_code=201)
async def create_attempt(proba: int, data: dict = Body(...)):
    a = attempts.create(proba, data)
    await changed()
    return a


@router.put("/attempts/{proba}/{attempt_id}")
async def update_attempt(proba: int, attempt_id: int, data: dict = Body(...)):
    a = attempts.update(proba, attempt_id, data)
    await changed()
    return a


@router.delete("/attempts/{proba}/{attempt_id}", status_code=204)
async def delete_attempt(proba: int, attempt_id: int):
    attempts.check_proba(proba)
    if not storage.delete_attempt(proba, attempt_id):
        raise CmdError("Încercarea nu există.")
    await changed()
