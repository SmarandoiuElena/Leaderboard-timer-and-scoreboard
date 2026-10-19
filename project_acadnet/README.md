# Acadnet – sistem de arbitraj

## Pornire

#### Linux
```
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Windows
```
py -m pip install fastapi uvicorn websockets
py -m uvicorn main:app --host 0.0.0.0 --port 8000
```
Pe celelalte dispozitive din rețea deschizi `http://<IP-ul-laptopului>:8000/`.

| Pagină | Adresă |
|---|---|
| Panou arbitru | `/arbitru` |
| Timer (ecran public) | `/timer` |
| Clasament Proba 1 | `/clasament1` |
| Clasament Proba 2 | `/clasament2` |

## Date (folderul `data/`)

- `teams.csv` – echipele (`id,name,country_code,country_name`). Adaugi o linie nouă și repornești serverul.
- `proba1.csv`, `proba2.csv` – o linie pe încercare. Se rescriu la fiecare salvare/ștergere.
  Nu edita fișierele în Excel cât timp rulează serverul (le suprascrie din memorie).

## Steaguri

`country_code` este numele fișierului din `static/flags/` (ex. `ro` → `ro.svg`, sau `.png`).
Dacă fișierul nu există, se afișează dreptunghiul alb (`xx.svg`).

## Punctaj

- Proba 1: 5 checkpoint-uri × 10 p + punctaj viteză introdus de arbitru (0–50).
- Proba 2: punctaj control + punctaj viteză (grosime linie), ambele introduse de arbitru (≥ 0).
- Clasament: echipele după cel mai bun scor (la egalitate, timpul mai mic); scorurile fiecărei echipe descrescător.
