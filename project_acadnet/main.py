"""Server de arbitraj Acadnet.
Pornire:  uvicorn main:app --host 0.0.0.0 --port 8000
"""
import csv
import json
import math
import os
import time
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"

TEAMS_CSV = DATA_DIR / "teams.csv"
RESULTS_CSV = {1: DATA_DIR / "proba1.csv", 2: DATA_DIR / "proba2.csv"}

TEAM_FIELDS = ["id", "name", "country_code", "country_name"]
RESULT_FIELDS = {
    1: ["id", "team_id", "cp1", "cp2", "cp3", "cp4", "cp5",
        "speed_points", "total", "time_s", "timestamp"],
    2: ["id", "team_id", "control_points", "speed_points", "total", "time_s", "timestamp"],
}

# Proba 1: 5 checkpoint-uri x 10 puncte + maxim 50 puncte de viteza
CHECKPOINTS = 5
CHECKPOINT_POINTS = 10
SPEED_MAX_P1 = 50

# country_code = numele fisierului de steag din static/flags/ (ex. ro -> ro.svg); xx = dreptunghi alb
DEFAULT_TEAMS = [
    {"id": 1, "name": "Team 1", "country_code": "ro", "country_name": "România"},
    {"id": 2, "name": "Team 2", "country_code": "ro", "country_name": "România"},
    {"id": 3, "name": "Team 3", "country_code": "xx", "country_name": ""},
]

RECENT_LIMIT = 15

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
clients: set[WebSocket] = set()


class CmdError(Exception):
    """Eroare de validare, trimisa inapoi doar celui care a trimis comanda."""


# ---------------------------------------------------------------- CSV

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


teams: list[dict] = load_teams()
attempts: dict[int, list[dict]] = {}
for _p in (1, 2):
    attempts[_p] = [parse_attempt(r, _p) for r in read_rows(RESULTS_CSV[_p])]
    if not RESULTS_CSV[_p].exists():
        write_rows(RESULTS_CSV[_p], RESULT_FIELDS[_p], [])


def save_attempts(proba: int, rows: list[dict]) -> None:
    try:
        write_rows(RESULTS_CSV[proba], RESULT_FIELDS[proba],
                   [serialize(a, proba) for a in rows])
    except OSError:
        raise CmdError("Nu s-a putut scrie fișierul CSV (e deschis în Excel?). Închide-l și încearcă din nou.")


# ---------------------------------------------------------------- stare

state = {
    "timer": {
        "state": "stopped",        # stopped | running | paused
        "start": 0.0,              # ora serverului la ultimul start
        "elapsed_before_pause": 0.0,
    },
    "active": {"proba": 1, "team_id": None},
}


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


def team_by_id(team_id):
    return next((t for t in teams if t["id"] == team_id), None)

def leaderboard(proba: int) -> list[dict]:
    """Toate echipele; scorurile fiecarei echipe in ordine descrescatoare;
    echipele ordonate dupa cel mai bun scor (la egalitate, dupa timpul mai mic)."""
    rows = []
    for team in teams:
        mine = [a for a in attempts[proba] if a["team_id"] == team["id"]]
        best = None
        if mine:
            best = max(mine, key=lambda a: (a["total"], -(a["time_s"] if a["time_s"] is not None else 1e12)))
        rows.append({
            "team_id": team["id"],
            "name": team["name"],
            "country_code": team["country_code"],
            "country_name": team["country_name"],
            "best": best["total"] if best else None,
            "best_time": best["time_s"] if best else None,
            "scores": sorted((a["total"] for a in mine), reverse=True),
        })

    def sort_key(r):
        if r["best"] is None:
            return (1, 0, 0, r["name"].lower())
        return (0, -r["best"], r["best_time"] if r["best_time"] is not None else 1e12, r["name"].lower())

    rows.sort(key=sort_key)

    prev_key, rank = None, 0
    for i, r in enumerate(rows):
        if r["best"] is None:
            r["rank"] = None
            continue
        key = (r["best"], r["best_time"])
        if key != prev_key:
            rank = i + 1
            prev_key = key
        r["rank"] = rank
    return rows


def snapshot() -> dict:
    return {
        "type": "state",
        "server_time": time.time(),        "timer": state["timer"],
        "active": state["active"],
        "teams": teams,
        "leaderboards": {str(p): leaderboard(p) for p in (1, 2)},
        "attempts": {str(p): list(reversed(attempts[p]))[:RECENT_LIMIT] for p in (1, 2)},
        "counts": {str(p): len(attempts[p]) for p in (1, 2)},
    }


async def broadcast():
    msg = json.dumps(snapshot())
    for ws in list(clients):
        try:
            await ws.send_text(msg)
        except Exception:
            clients.discard(ws)


# ---------------------------------------------------------------- comenzi

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


def require_stopped():
    if state["timer"]["state"] != "stopped":
        raise CmdError("Dă Reset timerului înainte de a schimba proba sau echipa.")


def handle(cmd: dict) -> None:
    t = state["timer"]
    act = state["active"]
    action = cmd.get("action")

    if action == "set_proba":
        proba = cmd.get("proba")
        if proba not in (1, 2):
            raise CmdError("Probă invalidă.")
        require_stopped()
        act["proba"] = proba

    elif action == "set_team":
        team_id = cmd.get("team_id")
        if team_id is not None and team_by_id(team_id) is None:
            raise CmdError("Echipă necunoscută.")
        require_stopped()
        act["team_id"] = team_id

    elif action == "start":
        if act["team_id"] is None:
            raise CmdError("Alege o echipă înainte de start.")
        if t["state"] != "running":
            if t["state"] == "stopped":
                t["elapsed_before_pause"] = 0.0
            t["start"] = time.time()
            t["state"] = "running"

    elif action == "pause":
        if t["state"] == "running":
            t["elapsed_before_pause"] += time.time() - t["start"]
            t["state"] = "paused"

    elif action == "reset":
        reset_timer()

    elif action == "save":
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
        save_attempts(proba, new_rows)      # daca scrierea esueaza, memoria ramane neschimbata
        attempts[proba] = new_rows
        reset_timer()

    elif action == "delete_attempt":
        proba, aid = cmd.get("proba"), cmd.get("id")
        if proba not in (1, 2):
            raise CmdError("Probă invalidă.")
        new_rows = [x for x in attempts[proba] if x["id"] != aid]
        if len(new_rows) == len(attempts[proba]):
            raise CmdError("Încercarea nu există.")
        save_attempts(proba, new_rows)
        attempts[proba] = new_rows

    else:
        raise CmdError("Comandă necunoscută.")


# ---------------------------------------------------------------- rute

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    await ws.send_text(json.dumps(snapshot()))  # stare initiala la conectare
    try:
        while True:
            raw = await ws.receive_text()
            try:
                cmd = json.loads(raw)
                if not isinstance(cmd, dict):
                    raise CmdError("Comandă invalidă.")
                handle(cmd)
            except json.JSONDecodeError:
                continue
            except CmdError as err:
                await ws.send_text(json.dumps({"type": "error", "message": str(err)}))
                continue
            await broadcast()
    except WebSocketDisconnect:
        clients.discard(ws)


def page(name: str) -> FileResponse:
    return FileResponse(STATIC_DIR / name)


@app.get("/")
def index():
    return page("index.html")


@app.get("/timer")
def timer_page():
    return page("timer.html")


@app.get("/arbitru")
def arbitru_page():
    return page("arbitru.html")


@app.get("/clasament1")
def clasament1_page():
    return page("clasament1.html")


@app.get("/clasament2")
def clasament2_page():
    return page("clasament2.html")
