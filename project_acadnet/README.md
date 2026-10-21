# Acadnet – sistem de arbitraj

## Pornire

#### Linux
```
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Windows
```
py -m pip install fastapi uvicorn websockets
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Comanda se rulează din folderul proiectului (cel care conține `app/`).
Pe celelalte dispozitive din rețea deschizi `http://<IP-ul-laptopului>:8000/`.

| Pagină | Adresă |
|---|---|
| Meniu | `/` |
| Panou arbitru | `/arbitru` |
| Timer (ecran public) | `/timer` |
| Clasament Proba 1 | `/clasament1` |
| Clasament Proba 2 | `/clasament2` |

## Structura proiectului

```
project_acadnet/
├── README.md
├── requirements.txt
└── app/
    ├── main.py          # creează aplicația, montează /static, include routerele
    ├── config.py        # căi (static/, data/) și constante (checkpoint-uri, punctaj max)
    ├── state.py         # starea din memorie + snapshot() (ce primesc toate ecranele)
    ├── data/            # teams.csv, proba1.csv, proba2.csv
    ├── routers/
    │   └── pages.py     # rutele paginilor HTML
    ├── services/        # logica, fără nimic de WebSocket sau HTTP
    │   ├── errors.py    # CmdError (eroare de validare)
    │   ├── storage.py   # citit/scris CSV
    │   ├── scoring.py   # clasamentul
    │   ├── timer.py     # start / pauză / reset
    │   ├── active.py    # alegerea probei și a echipei
    │   └── attempts.py  # salvare / ștergere încercări
    ├── ws/
    │   ├── manager.py   # clienții conectați + broadcast
    │   └── endpoint.py  # ruta /ws + tabelul de comenzi
    └── static/
        ├── *.html       # index, arbitru, timer, clasament1, clasament2
        ├── css/
        ├── js/          # common.js = conexiunea WebSocket + funcții comune
        └── flags/
```

## Cum funcționează

Serverul ține toată starea în memorie și e singura sursă de adevăr. Paginile doar desenează ce primesc, nu calculează nimic (în afară de timpul care curge pe ecran).

```
arbitru.html ──{action: ...}──► /ws ──► service ──► state (+ CSV)
                                  │
timer / clasament ◄── snapshot ───┴── broadcast la toți clienții
```

1. Fiecare pagină se conectează la `/ws` și primește starea completă (`snapshot()` din `state.py`).
2. Arbitrul apasă ceva și pagina trimite o comandă JSON, de exemplu `{"action": "start"}`.
3. `ws/endpoint.py` caută acțiunea în dicționarul `COMMANDS` și apelează funcția din `services/`.
4. Dacă merge, serverul trimite noua stare **tuturor**. Dacă nu (ex. scor negativ), doar cel care a trimis comanda primește `{"type": "error", "message": ...}`.

Timerul nu trimite secunde. Serverul trimite ora de start și timpul adunat până la pauză, iar fiecare ecran calculează singur cât a trecut. Așa nu se decalează între ecrane.

Regula de bază: `services/` nu știu de WebSocket, `ws/` nu știe de reguli de punctaj.

## Cum adaug ceva

#### O comandă nouă
1. Scrii funcția în `services/` (primește `cmd: dict`, aruncă `CmdError` dacă ceva nu e ok)
2. O adaugi în `COMMANDS` din `ws/endpoint.py`
3. O trimiți din JS cu `link.send({ action: "..." })`

#### O echipă nouă
O linie în `data/teams.csv` și repornești serverul.

#### O pagină nouă
Fișierul HTML în `static/`, o rută în `routers/pages.py`.

## Date (folderul `app/data/`)

- `teams.csv` – echipele (`id,name,country_code,country_name`). Adaugi o linie nouă și repornești serverul.
- `proba1.csv`, `proba2.csv` – o linie pe încercare. Se rescriu la fiecare salvare/ștergere.
  Nu edita fișierele în Excel cât timp rulează serverul (le suprascrie din memorie).

## Steaguri

`country_code` este numele fișierului din `app/static/flags/` (ex. `ro` → `ro.svg`, sau `.png`).
Dacă fișierul nu există, se afișează dreptunghiul alb (`xx.svg`).

## Punctaj

- Proba 1: 5 checkpoint-uri × 10 p + punctaj viteză introdus de arbitru (0–50).
- Proba 2: punctaj control + punctaj viteză (grosime linie), ambele introduse de arbitru (≥ 0).
- Clasament: echipele după cel mai bun scor (la egalitate, timpul mai mic); scorurile fiecărei echipe descrescător.
- După salvarea unei încercări, timerul se resetează automat.