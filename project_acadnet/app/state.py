"""Starea aplicatiei, tinuta in memorie.

Acesta este locul care va fi inlocuit cu baza de date (SQLite) la issue 1.1.
Restul codului acceseaza starea doar prin acest modul, deci schimbarea
se face intr-un singur loc.
"""
import time

state = {
    "timer": {
        "state": "stopped",          # stopped | running | paused
        "duration": 180,             # secunde
        "start": 0.0,                # ora serverului la ultimul start
        "elapsed_before_pause": 0.0,
    },
    "scores": {},                    # {"Echipa": puncte}
}


def snapshot() -> dict:
    """Starea completa, cu ora serverului (pentru sincronizarea ceasurilor)."""
    return {"server_time": time.time(), **state}
