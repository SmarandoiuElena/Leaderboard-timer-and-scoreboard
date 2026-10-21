"""Clasamentul. Functie pura: primeste echipele si incercarile, nu atinge starea sau fisierele."""


def leaderboard(teams: list[dict], attempts: list[dict]) -> list[dict]:
    """Toate echipele; scorurile fiecarei echipe in ordine descrescatoare;
    echipele ordonate dupa cel mai bun scor (la egalitate, dupa timpul mai mic)."""
    rows = []
    for team in teams:
        mine = [a for a in attempts if a["team_id"] == team["id"]]
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
