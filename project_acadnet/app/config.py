from pathlib import Path

# Radacina proiectului (folderul care contine "app/" si "static/")
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
