"""Citirea si scrierea datelor in SQLite (fisierul acadnet.db).

Restul aplicatiei foloseste doar load_teams(), load_attempts() si save_attempts(),
asa ca nu stie daca datele sunt in CSV sau in baza de date.
"""
import csv
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.config import (CHECKPOINTS, DB_PATH, DEFAULT_TEAMS, RESULT_FIELDS,
                        RESULTS_CSV, TEAMS_CSV)
from app.services.errors import CmdError

# Cate un tabel pentru echipe si unul pentru fiecare proba.
SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    country_code TEXT NOT NULL DEFAULT 'xx',
    country_name TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS attempts_p1 (
    id           INTEGER PRIMARY KEY,
    team_id      INTEGER NOT NULL,
    cp1 INTEGER NOT NULL, cp2 INTEGER NOT NULL, cp3 INTEGER NOT NULL,
    cp4 INTEGER NOT NULL, cp5 INTEGER NOT NULL,
    speed_points REAL NOT NULL,
    total        REAL NOT NULL,
    time_s       REAL,
    timestamp    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts_p2 (
    id             INTEGER PRIMARY KEY,
    team_id        INTEGER NOT NULL,
    control_points REAL NOT NULL,
    speed_points   REAL NOT NULL,
    total          REAL NOT NULL,
    time_s         REAL,
    timestamp      TEXT NOT NULL
);
"""


@contextmanager
def _db():
    """O conexiune scurta: commit la final, rollback daca apare o eroare."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row        # randurile se pot citi ca dictionare
    try:
        with conn:
            yield conn
    finally:
        conn.close()


_ready = False


def _ensure_db() -> None:
    """Creeaza tabelele si, doar prima data (baza noua), importa datele din CSV."""
    global _ready
    if _ready:
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _db() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("PRAGMA user_version").fetchone()[0] == 0:   # 0 = baza noua
            _import_from_csv(conn)
            conn.execute("PRAGMA user_version = 1")
    _ready = True


# ------------------------------------------------------------ import din CSV (o singura data)

def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _csv_teams() -> list[dict]:
    if not TEAMS_CSV.exists():
        return DEFAULT_TEAMS
    return [
        {"id": int(r["id"]), "name": r["name"],
         "country_code": (r.get("country_code") or "xx").strip().lower(),
         "country_name": r.get("country_name") or ""}
        for r in _read_csv(TEAMS_CSV)
    ]


def _csv_attempts(proba: int) -> list[dict]:
    rows = []
    for r in _read_csv(RESULTS_CSV[proba]):
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
        rows.append(a)
    return rows


def _import_from_csv(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT INTO teams (id, name, country_code, country_name) VALUES (?, ?, ?, ?)",
        [(t["id"], t["name"], t["country_code"], t["country_name"]) for t in _csv_teams()],
    )
    for proba in (1, 2):
        _insert_attempts(conn, proba, _csv_attempts(proba))


# ------------------------------------------------------------ ce foloseste restul aplicatiei

def _insert_attempts(conn: sqlite3.Connection, proba: int, rows: list[dict]) -> None:
    fields = RESULT_FIELDS[proba]
    # numele tabelului si ale coloanelor vin din config.py, nu de la utilizator;
    # valorile merg mereu prin "?" (asa se evita SQL injection)
    conn.executemany(
        f"INSERT INTO attempts_p{proba} ({', '.join(fields)}) "
        f"VALUES ({', '.join('?' * len(fields))})",
        [[r.get(f) for f in fields] for r in rows],
    )


def load_teams() -> list[dict]:
    _ensure_db()
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, name, country_code, country_name FROM teams ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def load_attempts(proba: int) -> list[dict]:
    _ensure_db()
    fields = RESULT_FIELDS[proba]
    with _db() as conn:
        rows = conn.execute(
            f"SELECT {', '.join(fields)} FROM attempts_p{proba} ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def save_attempts(proba: int, rows: list[dict]) -> None:
    """Inlocuieste incercarile probei cu lista data, intr-o singura tranzactie:
    ori se salveaza tot, ori nimic."""
    _ensure_db()
    try:
        with _db() as conn:
            conn.execute(f"DELETE FROM attempts_p{proba}")
            _insert_attempts(conn, proba, rows)
    except sqlite3.Error:
        raise CmdError("Nu s-a putut scrie în baza de date (e blocată de altă aplicație?). Încearcă din nou.")
    