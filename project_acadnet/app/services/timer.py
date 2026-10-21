"""Logica timerului. Nu stie nimic despre WebSocket sau HTTP."""
import time

from app.state import state


def start(_cmd: dict | None = None) -> None:
    t = state["timer"]
    if t["state"] == "running":
        return
    if t["state"] == "stopped":
        t["elapsed_before_pause"] = 0.0
    t["start"] = time.time()
    t["state"] = "running"


def pause(_cmd: dict | None = None) -> None:
    t = state["timer"]
    if t["state"] != "running":
        return
    t["elapsed_before_pause"] += time.time() - t["start"]
    t["state"] = "paused"


def reset(_cmd: dict | None = None) -> None:
    t = state["timer"]
    t["state"] = "stopped"
    t["elapsed_before_pause"] = 0.0
