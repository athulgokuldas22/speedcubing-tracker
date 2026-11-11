# Speedcubing Tracker

A small web app for timing 3x3 solves and tracking averages and personal bests.
It runs as two services (`solves` and `stats`), each with its own SQL Server database, plus a static UI.

## Features
- **Solves service:** sessions, timed solves with +2/DNF penalties, and a random-move 3x3 scramble generator. Owns the `sessions` and `solves` tables.
- **Stats service:** WCA-style ao5/ao12/ao100 and personal bests (single, ao5, ao12, ao100). Owns the `personal_bests` table.
- Stats reads solve data only through the solves service: `GET /api/sessions/<id>/times`. If solves is down, stats answers 503 after a 2 s timeout.

## Run
    cp .env.example .env          # change the passwords
    docker compose up --build     # first start takes about 30 s: SQL Server must be healthy before db-init runs

- UI: http://localhost:8080 · solves: http://localhost:8001/health · stats: http://localhost:8002/health
- Reset the data: `docker compose down -v`.

Press space to start the timer and space again to stop it.

## Configuration (environment variables)
| Variable | Service | Meaning |
|---|---|---|
| DATABASE_URL | both | `mssql://user:password@host:port/database` |
| SOLVES_URL | stats | Address of the solves service |
| CORS_ORIGINS | both | Addresses allowed to call the service from a browser (the UI) |
| PORT | both | Port to listen on (default 8000) |

Locally the passwords live in `.env` (git-ignored). `.env.example` shows the names.

## API

All paths are on the solves service except `/stats`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/scramble` | New random-move scramble |
| GET, POST | `/api/sessions` | List or create sessions |
| GET, POST | `/api/sessions/<id>/solves` | List or add solves |
| PATCH | `/api/solves/<id>` | Set penalty (OK, +2, DNF) |
| DELETE | `/api/solves/<id>` | Delete a solve |
| GET | `/api/sessions/<id>/times` | Effective times for the stats service |
| GET | `/api/sessions/<id>/stats` | Current averages, personal bests, new PBs (stats service) |

## Tests
Run in each service folder:

    pip install -r requirements-dev.txt
    python -m pytest -q

## Project layout
    services/solves/   service 1: sessions, solves, scrambles (Dockerfile, app/, tests/)
    services/stats/    service 2: averages and personal bests (Dockerfile, app/, tests/)
    ui/                static timer page, served by nginx
    db/init.sql        creates one database and one login per service
    docker-compose.yml starts SQL Server, db-init, both services and the UI
    ADR.md  AI_USAGE.md  docs/
