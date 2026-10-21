"""Logica scorurilor. Aici vor veni regulile specifice fiecarei probe."""
from app.state import state


def add_score(cmd: dict) -> None:
    team = str(cmd.get("team", "")).strip()
    if not team:
        return
    points = float(cmd.get("points", 0))
    state["scores"][team] = state["scores"].get(team, 0) + points
