"""Proba si echipa selectate in acest moment (comune tuturor ecranelor)."""
from app.services.errors import CmdError
from app.state import state, team_by_id


def require_stopped() -> None:
    if state["timer"]["state"] != "stopped":
        raise CmdError("Dă Reset timerului înainte de a schimba proba sau echipa.")


def set_proba(cmd: dict) -> None:
    proba = cmd.get("proba")
    if proba not in (1, 2):
        raise CmdError("Probă invalidă.")
    require_stopped()
    state["active"]["proba"] = proba


def set_team(cmd: dict) -> None:
    team_id = cmd.get("team_id")
    if team_id is not None and team_by_id(team_id) is None:
        raise CmdError("Echipă necunoscută.")
    require_stopped()
    state["active"]["team_id"] = team_id
