"""Citirea si scrierea fisierelor CSV (teams.csv, proba1.csv, proba2.csv)."""
import csv
import os
from pathlib import Path

from app.config import (CHECKPOINTS, DATA_DIR, DEFAULT_TEAMS, RESULT_FIELDS,
                        RESULTS_CSV, TEAM_FIELDS, TEAMS_CSV)
from app.services.errors import CmdError


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, fields: list[str], rows: list[dict]) -> None:
    """Scriere atomica: fisier temporar + inlocuire, ca un crash sa nu strice CSV-ul."""
    DATA_DIR.mkdir(exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    # utf-8-sig: Excel afiseaza corect diacriticele
    with tmp.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def num_out(v):
    if v is None:
        return ""
    return int(v) if float(v) == int(v) else v


def serialize(a: dict, proba: int) -> dict:
    return {k: num_out(a.get(k)) if k != "timestamp" else a.get(k, "")
            for k in RESULT_FIELDS[proba]}


def parse_attempt(r: dict, proba: int) -> dict:
    a = {
        "id": int(r["id"]),
        "team_id": int(r["team_id"]),
        "speed_points": float(r["speed_points"]),
        "total": float(r["total"]),
        "time_s": float(r["time_s"]) if r.get("time_s") else None,
        "timestamp": r.get("timestamp", ""),
    }
    if proba == 1:
        for i in range(1, CHECKPOINTS + 1):
            a[f"cp{i}"] = int(r[f"cp{i}"])
    else:
        a["control_points"] = float(r["control_points"])
    return a


def load_teams() -> list[dict]:
    if not TEAMS_CSV.exists():
        write_rows(TEAMS_CSV, TEAM_FIELDS, DEFAULT_TEAMS)
    return [
        {"id": int(r["id"]), "name": r["name"],
         "country_code": (r.get("country_code") or "xx").strip().lower(),
         "country_name": r.get("country_name", "")}
        for r in read_rows(TEAMS_CSV)
    ]


def load_attempts(proba: int) -> list[dict]:
    rows = [parse_attempt(r, proba) for r in read_rows(RESULTS_CSV[proba])]
    if not RESULTS_CSV[proba].exists():
        write_rows(RESULTS_CSV[proba], RESULT_FIELDS[proba], [])
    return rows


def save_attempts(proba: int, rows: list[dict]) -> None:
    try:
        write_rows(RESULTS_CSV[proba], RESULT_FIELDS[proba],
                   [serialize(a, proba) for a in rows])
    except OSError:
        raise CmdError("Nu s-a putut scrie fișierul CSV (e deschis în Excel?). Închide-l și încearcă din nou.")
