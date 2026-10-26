"""Incercarile: salvare de la arbitru, plus adaugare / editare / stergere din pagina de administrare.
Validarea si calculul totalului sunt intr-un singur loc (parse_scores), folosit de toate."""
import math
import time

from app.config import CHECKPOINT_POINTS, CHECKPOINTS, SPEED_MAX_P1
from app.services import storage
from app.services.errors import CmdError
from app.services.timer import elapsed, reset_timer
from app.state import state


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


def check_proba(proba) -> int:
    if proba not in (1, 2) or isinstance(proba, bool):
        raise CmdError("Probă invalidă.")
    return proba


def parse_scores(proba: int, cmd: dict) -> dict:
    """Scorurile din comanda, validate, plus 'total' calculat de server (nu se ia niciodata de la client)."""
    a = {}
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
    return a


def parse_time(cmd: dict) -> float | None:
    """Timpul e optional: gol = fara timp."""
    if cmd.get("time_s") in (None, ""):
        return None
    return number(cmd, "time_s", "Timp (secunde)")


def parse_team(cmd: dict) -> int:
    team_id = cmd.get("team_id")
    if not storage.team_exists(team_id):
        raise CmdError("Alege o echipă.")
    return team_id


# ---------------------------------------------------------------- comenzi WebSocket (arbitru)

def save(cmd: dict) -> None:
    act = state["active"]
    proba = act["proba"]
    if act["team_id"] is None:
        raise CmdError("Alege o echipă.")
    # protectie impotriva scorului trecut la proba/echipa gresita (pagina veche, alt arbitru)
    if cmd.get("proba") != proba or cmd.get("team_id") != act["team_id"]:
        raise CmdError("Proba sau echipa de pe ecran nu mai corespunde cu cea activă. Reîncarcă pagina.")

    a = {"team_id": act["team_id"], "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
    e = elapsed()
    a["time_s"] = round(e, 1) if e > 0 else None
    a.update(parse_scores(proba, cmd))

    storage.insert_attempt(proba, a)      # daca scrierea esueaza, se arunca CmdError si timerul ramane
    reset_timer()


def delete_attempt(cmd: dict) -> None:
    proba = check_proba(cmd.get("proba"))
    if not storage.delete_attempt(proba, cmd.get("id")):
        raise CmdError("Încercarea nu există.")


# ---------------------------------------------------------------- pagina de administrare (HTTP)

def create(proba: int, data: dict) -> dict:
    """Incercare adaugata de mana (de ex. una uitata). Ora = momentul adaugarii."""
    check_proba(proba)
    a = {"team_id": parse_team(data), "time_s": parse_time(data),
         "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
    a.update(parse_scores(proba, data))
    a["id"] = storage.insert_attempt(proba, a)
    return a


def update(proba: int, attempt_id, data: dict) -> dict:
    """Corectura unei incercari existente: echipa, scorurile, timpul. Totalul se recalculeaza."""
    check_proba(proba)
    old = storage.get_attempt(proba, attempt_id)
    if old is None:
        raise CmdError("Încercarea nu există.")
    a = {"team_id": parse_team(data), "time_s": parse_time(data)}
    a.update(parse_scores(proba, data))
    if not storage.update_attempt(proba, attempt_id, a):
        raise CmdError("Încercarea nu există.")
    return {**old, **a}
