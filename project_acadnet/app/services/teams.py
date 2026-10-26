"""Echipele: adaugare / editare / stergere (din pagina de administrare)."""
import re

from app.services import storage
from app.services.errors import CmdError


def clean(data: dict) -> dict:
    name = str(data.get("name") or "").strip()
    if not name:
        raise CmdError("Completează numele echipei.")
    if len(name) > 60:
        raise CmdError("Numele echipei e prea lung (maxim 60 de caractere).")

    code = str(data.get("country_code") or "").strip().lower() or "xx"
    if not re.fullmatch(r"[a-z]{2}", code):
        raise CmdError("Codul țării trebuie să aibă 2 litere (ex. ro). Gol = fără steag.")

    country = str(data.get("country_name") or "").strip()
    if len(country) > 60:
        raise CmdError("Numele țării e prea lung (maxim 60 de caractere).")
    return {"name": name, "country_code": code, "country_name": country}


def create(data: dict) -> dict:
    team = clean(data)
    team["id"] = storage.insert_team(team)
    return team


def update(team_id, data: dict) -> dict:
    team = clean(data)
    if not storage.update_team(team_id, team):
        raise CmdError("Echipa nu există.")
    return {"id": team_id, **team}


def delete(team_id) -> None:
    n = storage.count_team_attempts(team_id) if isinstance(team_id, int) else 0
    if n:
        raise CmdError(f"Echipa are {n} încercări salvate. Șterge-le întâi, ca să nu rămână scoruri fără echipă.")
    if not storage.delete_team(team_id):
        raise CmdError("Echipa nu există.")
