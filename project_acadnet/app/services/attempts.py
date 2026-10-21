"""Salvarea si stergerea incercarilor (fiecare operatie rescrie CSV-ul probei)."""
import math
import time

from app.config import CHECKPOINT_POINTS, CHECKPOINTS, SPEED_MAX_P1
from app.services import storage
from app.services.errors import CmdError
from app.services.timer import elapsed, reset_timer
from app.state import attempts, state


def number(cmd: dict, key: str, label: str, hi: float | None = None) -> float:
    raw = cmd.get(key)
    if raw is None or raw == "":
        raise CmdError(f"Completează: {label}.")
    try:
        v = float(raw)
    except (TypeError, ValueError):
        raise CmdError(f"{label}: valoare invalidă.")
    if not math.isfinite(v):
        raise CmdError(f"{label}: valoare invalidă.")
    if v < 0:
        raise CmdError(f"{label} nu poate fi negativ.")
    if hi is not None and v > hi:
        raise CmdError(f"{label} nu poate depăși {hi:g}.")
    return round(v, 2)


def save(cmd: dict) -> None:
    act = state["active"]
    proba = act["proba"]
    if act["team_id"] is None:
        raise CmdError("Alege o echipă.")
    # protectie impotriva scorului trecut la proba/echipa gresita (pagina veche, alt arbitru)
    if cmd.get("proba") != proba or cmd.get("team_id") != act["team_id"]:
        raise CmdError("Proba sau echipa de pe ecran nu mai corespunde cu cea activă. Reîncarcă pagina.")

    a = {
        "id": max((x["id"] for x in attempts[proba]), default=0) + 1,
        "team_id": act["team_id"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    e = elapsed()
    a["time_s"] = round(e, 1) if e > 0 else None

    if proba == 1:
        cps = cmd.get("checkpoints")
        if not isinstance(cps, list) or len(cps) != CHECKPOINTS:
            raise CmdError("Checkpoint-uri invalide.")
        for i, v in enumerate(cps, start=1):
            a[f"cp{i}"] = 1 if v else 0
        a["speed_points"] = number(cmd, "speed_points", "Punctaj viteză", hi=SPEED_MAX_P1)
        a["total"] = sum(a[f"cp{i}"] for i in range(1, CHECKPOINTS + 1)) * CHECKPOINT_POINTS + a["speed_points"]
    else:
        a["control_points"] = number(cmd, "control_points", "Punctaj control")
        a["speed_points"] = number(cmd, "speed_points", "Punctaj viteză (grosime linie)")
        a["total"] = round(a["control_points"] + a["speed_points"], 2)

    new_rows = attempts[proba] + [a]
    storage.save_attempts(proba, new_rows)      # daca scrierea esueaza, memoria ramane neschimbata
    attempts[proba] = new_rows
    reset_timer()


def delete_attempt(cmd: dict) -> None:
    proba, aid = cmd.get("proba"), cmd.get("id")
    if proba not in (1, 2):
        raise CmdError("Probă invalidă.")
    new_rows = [x for x in attempts[proba] if x["id"] != aid]
    if len(new_rows) == len(attempts[proba]):
        raise CmdError("Încercarea nu există.")
    storage.save_attempts(proba, new_rows)
    attempts[proba] = new_rows
