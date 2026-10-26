"""Tine evidenta clientilor conectati si le trimite mesaje."""
import json

from fastapi import WebSocket


def fingerprint(payload: dict) -> str:
    """O 'amprenta' a starii, fara ora serverului (care se schimba mereu)."""
    return json.dumps({k: v for k, v in payload.items() if k != "server_time"}, sort_keys=True)


class ConnectionManager:
    def __init__(self) -> None:
        self.clients: set[WebSocket] = set()
        self.last_fingerprint: str | None = None   # ultima stare trimisa tuturor

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.clients.discard(ws)

    async def send(self, ws: WebSocket, payload: dict) -> None:
        await ws.send_text(json.dumps(payload))

    async def broadcast(self, payload: dict) -> None:
        self.last_fingerprint = fingerprint(payload)
        msg = json.dumps(payload)
        for ws in list(self.clients):
            try:
                await ws.send_text(msg)
            except Exception:
                self.clients.discard(ws)


manager = ConnectionManager()
