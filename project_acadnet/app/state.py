"""Starea aplicatiei.

In memorie raman doar lucrurile care nu apartin bazei de date: timerul si
echipa/proba selectate acum. Echipele si incercarile se citesc din baza de date
la fiecare snapshot, deci o modificare facuta in baza de date apare pe ecrane
fara restart.
"""
import time

from app.config import RECENT_LIMIT
from app.services import scoring, storage

state = {
    "timer": {
        "state": "stopped",        # stopped | running | finished
        "start": 0.0,              # ora serverului la ultimul start
        "elapsed_before_pause": 0.0,
    },
    "active": {"proba": 1, "team_id": None},
}


def snapshot() -> dict:
    """Mesajul trimis tuturor clientilor: tot ce au nevoie ca sa se deseneze."""
    teams = storage.load_teams()
    attempts = {p: storage.load_attempts(p) for p in (1, 2)}

    # echipa activa a fost stearsa din baza de date -> o deselectam
    active = state["active"]
    if active["team_id"] is not None and all(t["id"] != active["team_id"] for t in teams):
        active["team_id"] = None

    return {
        "type": "state",
        "server_time": time.time(),
        "timer": state["timer"],
        "active": active,
        "teams": teams,
        "leaderboards": {str(p): scoring.leaderboard(teams, attempts[p]) for p in (1, 2)},
        "attempts": {str(p): list(reversed(attempts[p]))[:RECENT_LIMIT] for p in (1, 2)},
        "counts": {str(p): len(attempts[p]) for p in (1, 2)},
    }
