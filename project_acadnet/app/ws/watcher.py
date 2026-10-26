"""Verifica periodic baza de date. Daca s-a schimbat ceva in afara aplicatiei
(de exemplu o corectura facuta in DB Browser), trimite starea noua tuturor ecranelor."""
import asyncio

from app.state import snapshot
from app.ws.manager import fingerprint, manager

INTERVAL = 2.0   # secunde


def _current() -> str | None:
    try:
        return fingerprint(snapshot())
    except Exception:
        return None       # baza e ocupata o clipa; incercam din nou la urmatoarea runda


async def watch_database() -> None:
    manager.last_fingerprint = _current()          # referinta luata imediat la pornire
    while True:
        await asyncio.sleep(INTERVAL)
        current = _current()
        # diferit de ultima stare trimisa de oricine (aplicatie sau watcher) = schimbare externa
        if current is not None and current != manager.last_fingerprint:
            await manager.broadcast(snapshot())
