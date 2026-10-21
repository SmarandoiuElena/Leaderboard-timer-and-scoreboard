"""Timerul: start / pauza / reset. Nu stie nimic despre WebSocket sau HTTP."""
import time

from app.services.errors import CmdError
from app.state import state


def elapsed() -> float:
    t = state["timer"]
    e = t["elapsed_before_pause"]
    if t["state"] == "running":
        e += time.time() - t["start"]
    return max(0.0, e)


def reset_timer() -> None:
    t = state["timer"]
    t["state"] = "stopped"
    t["elapsed_before_pause"] = 0.0


def start(cmd: dict) -> None:
    t = state["timer"]
    if state["active"]["team_id"] is None:
        raise CmdError("Alege o echipă înainte de start.")
    if t["state"] != "running":
        if t["state"] == "stopped":
            t["elapsed_before_pause"] = 0.0
        t["start"] = time.time()
        t["state"] = "running"


def pause(cmd: dict) -> None:
    t = state["timer"]
    if t["state"] == "running":
        t["elapsed_before_pause"] += time.time() - t["start"]
        t["state"] = "paused"


def reset(cmd: dict) -> None:
    reset_timer()
