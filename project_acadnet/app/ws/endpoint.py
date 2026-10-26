"""Endpoint-ul WebSocket: primeste comenzi, le executa, difuzeaza starea."""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services import active, attempts, timer
from app.services.errors import CmdError
from app.state import snapshot
from app.ws.manager import manager

router = APIRouter()

# Comanda primita -> functia care o executa. O comanda noua se adauga aici.
COMMANDS = {
    "set_proba": active.set_proba,
    "set_team": active.set_team,
    "start": timer.start,
    "finish": timer.finish,    
    "reset": timer.reset,
    "save": attempts.save,
    "delete_attempt": attempts.delete_attempt,
    
}


def handle(cmd: dict) -> None:
    action = cmd.get("action")
    handler = COMMANDS.get(action) if isinstance(action, str) else None
    if handler is None:
        raise CmdError("Comandă necunoscută.")
    handler(cmd)


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await manager.send(ws, snapshot())  # stare initiala la conectare
    try:
        while True:
            raw = await ws.receive_text()
            try:
                cmd = json.loads(raw)
                if not isinstance(cmd, dict):
                    raise CmdError("Comandă invalidă.")
                handle(cmd)
            except json.JSONDecodeError:
                continue
            except CmdError as err:
                await manager.send(ws, {"type": "error", "message": str(err)})
                continue
            await manager.broadcast(snapshot())
    except WebSocketDisconnect:
        manager.disconnect(ws)
