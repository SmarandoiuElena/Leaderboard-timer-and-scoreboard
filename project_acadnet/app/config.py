"""Constante si cai. Nimic de aici nu are logica."""
from pathlib import Path

BASE_DIR = Path(__file__).parent          # folderul app/
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
