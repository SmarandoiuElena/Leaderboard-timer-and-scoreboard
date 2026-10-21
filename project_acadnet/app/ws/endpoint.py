"""Endpoint-ul WebSocket: primeste comenzi, apeleaza serviciile, difuzeaza starea."""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services import scores, timer
from app.state import snapshot
from app.ws.manager import manager

router = APIRouter()

# Comanda primita -> functia care o executa. Comenzi noi se adauga aici.
COMMANDS = {
    "start": timer.start,
    "pause": timer.pause,
    "reset": timer.reset,
    "score": scores.add_score,
}


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await manager.send(ws, snapshot())  # stare initiala la conectare
    try:
        while True:
            try:
                cmd = json.loads(await ws.receive_text())
            except ValueError:
                continue  # mesaj invalid, il ignoram
            handler = COMMANDS.get(cmd.get("action"))
            if handler:
                handler(cmd)
                await manager.broadcast(snapshot())
    except WebSocketDisconnect:
        manager.disconnect(ws)
