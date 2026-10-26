"""Citirea si scrierea datelor in SQLite (fisierul acadnet.db).

Baza de date este singura sursa de adevar: nimic nu se tine in memorie.
Restul aplicatiei foloseste doar functiile publice de la sfarsit.
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

DB_ERROR = "Nu s-a putut scrie în baza de date (e blocată de altă aplicație?). Încearcă din nou."


@contextmanager
def _db():
    """O conexiune scurta: commit la final, rollback daca apare o eroare."""
    conn = sqlite3.connect(DB_PATH, timeout=10)   # asteapta pana la 10 s daca baza e ocupata o clipa
    conn.row_factory = sqlite3.Row                # randurile se pot citi ca dictionare
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
        conn.execute("PRAGMA journal_mode = WAL")   # cititorii (ecranele) nu mai blocheaza scrierile
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
        fields = RESULT_FIELDS[proba]
        conn.executemany(
            f"INSERT INTO attempts_p{proba} ({', '.join(fields)}) VALUES ({', '.join('?' * len(fields))})",
            [[r.get(f) for f in fields] for r in _csv_attempts(proba)],
        )


# ------------------------------------------------------------ ce foloseste restul aplicatiei
# Numele tabelelor si ale coloanelor vin din config.py, nu de la utilizator;
# valorile merg mereu prin "?" (asa se evita SQL injection).

def load_teams() -> list[dict]:
    _ensure_db()
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, name, country_code, country_name FROM teams ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def team_exists(team_id) -> bool:
    _ensure_db()
    if isinstance(team_id, bool) or not isinstance(team_id, int):
        return False
    with _db() as conn:
        return conn.execute("SELECT 1 FROM teams WHERE id = ?", (team_id,)).fetchone() is not None


def load_attempts(proba: int) -> list[dict]:
    _ensure_db()
    fields = RESULT_FIELDS[proba]
    with _db() as conn:
        rows = conn.execute(
            f"SELECT {', '.join(fields)} FROM attempts_p{proba} ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


@contextmanager
def _write():
    """Ca _db(), dar o eroare SQLite devine CmdError (mesaj pentru utilizator)."""
    _ensure_db()
    try:
        with _db() as conn:
            yield conn
    except sqlite3.Error:
        raise CmdError(DB_ERROR)


def _is_id(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


# ---- incercari

def get_attempt(proba: int, attempt_id) -> dict | None:
    _ensure_db()
    if not _is_id(attempt_id):
        return None
    with _db() as conn:
        row = conn.execute(
            f"SELECT {', '.join(RESULT_FIELDS[proba])} FROM attempts_p{proba} WHERE id = ?",
            (attempt_id,),
        ).fetchone()
    return dict(row) if row else None


def insert_attempt(proba: int, row: dict) -> int:
    """Adauga o singura incercare. Id-ul il da baza de date; il returnam."""
    fields = [f for f in RESULT_FIELDS[proba] if f != "id"]
    with _write() as conn:
        cur = conn.execute(
            f"INSERT INTO attempts_p{proba} ({', '.join(fields)}) "
            f"VALUES ({', '.join('?' * len(fields))})",
            [row.get(f) for f in fields],
        )
        return cur.lastrowid


def update_attempt(proba: int, attempt_id, row: dict) -> bool:
    """Rescrie scorurile unei incercari (id-ul si ora salvarii raman). False daca nu exista."""
    if not _is_id(attempt_id):
        return False
    fields = [f for f in RESULT_FIELDS[proba] if f not in ("id", "timestamp")]
    with _write() as conn:
        cur = conn.execute(
            f"UPDATE attempts_p{proba} SET {', '.join(f + ' = ?' for f in fields)} WHERE id = ?",
            [row.get(f) for f in fields] + [attempt_id],
        )
        return cur.rowcount > 0


def delete_attempt(proba: int, attempt_id) -> bool:
    """Sterge o singura incercare. Returneaza False daca nu exista."""
    if not _is_id(attempt_id):
        return False
    with _write() as conn:
        cur = conn.execute(f"DELETE FROM attempts_p{proba} WHERE id = ?", (attempt_id,))
        return cur.rowcount > 0


# ---- echipe

def count_team_attempts(team_id: int) -> int:
    _ensure_db()
    with _db() as conn:
        return sum(
            conn.execute(f"SELECT COUNT(*) FROM attempts_p{p} WHERE team_id = ?", (team_id,)).fetchone()[0]
            for p in (1, 2)
        )


def insert_team(team: dict) -> int:
    with _write() as conn:
        cur = conn.execute(
            "INSERT INTO teams (name, country_code, country_name) VALUES (?, ?, ?)",
            (team["name"], team["country_code"], team["country_name"]),
        )
        return cur.lastrowid


def update_team(team_id, team: dict) -> bool:
    if not _is_id(team_id):
        return False
    with _write() as conn:
        cur = conn.execute(
            "UPDATE teams SET name = ?, country_code = ?, country_name = ? WHERE id = ?",
            (team["name"], team["country_code"], team["country_name"], team_id),
        )
        return cur.rowcount > 0


def delete_team(team_id) -> bool:
    if not _is_id(team_id):
        return False
    with _write() as conn:
        cur = conn.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        return cur.rowcount > 0
