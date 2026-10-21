"""Starea aplicatiei, tinuta in memorie (datele se citesc din CSV o singura data, la pornire).

Orice alt modul citeste/modifica starea doar prin obiectele de aici.
"""
import time

from app.config import RECENT_LIMIT
from app.services import scoring, storage

state = {
    "timer": {
        "state": "stopped",        # stopped | running | paused
        "start": 0.0,              # ora serverului la ultimul start
        "elapsed_before_pause": 0.0,
    },
    "active": {"proba": 1, "team_id": None},
}

teams: list[dict] = storage.load_teams()
attempts: dict[int, list[dict]] = {p: storage.load_attempts(p) for p in (1, 2)}


def team_by_id(team_id):
    return next((t for t in teams if t["id"] == team_id), None)


def snapshot() -> dict:
    """Mesajul trimis tuturor clientilor: tot ce au nevoie ca sa se deseneze."""
    return {
        "type": "state",
        "server_time": time.time(),
        "timer": state["timer"],
        "active": state["active"],
        "teams": teams,
        "leaderboards": {str(p): scoring.leaderboard(teams, attempts[p]) for p in (1, 2)},
        "attempts": {str(p): list(reversed(attempts[p]))[:RECENT_LIMIT] for p in (1, 2)},
        "counts": {str(p): len(attempts[p]) for p in (1, 2)},
    }
