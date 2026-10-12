# Speedcubing Tracker

A small web app for timing 3x3 solves and tracking averages and personal bests.
It runs as a single process and stores everything in one SQLite file.

## Features
- **Solves domain:** sessions, timed solves with +2/DNF penalties, and a random-move 3x3 scramble generator.
- **Stats domain:** WCA-style ao5/ao12/ao100 and personal bests (single, ao5, ao12, ao100).
- The stats domain reads solve data only through `solves.get_times(conn, session_id)`.

## Run
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python app.py

Then open http://localhost:8000/ (health check at /health).
Press space to start the timer and space again to stop it.

## Configuration (environment variables)
| Variable | Default | Meaning |
|---|---|---|
| HOST | 0.0.0.0 | Bind address |
| PORT | 8000 | Port to listen on |
| DATA_DIR | ./data | Directory holding the SQLite file |

The database is created automatically at `$DATA_DIR/cubing.db` on startup (default `./data/cubing.db`). No setup step or `.env` file is needed.

## API
| Method | Path | Purpose |
|---|---|---|
| GET | /api/scramble | New random-move scramble |
| GET, POST | /api/sessions | List or create sessions |
| GET, POST | /api/sessions/<id>/solves | List or add solves |
| PATCH | /api/solves/<id> | Set penalty (OK, +2, DNF) |
| DELETE | /api/solves/<id> | Delete a solve |
| GET | /api/sessions/<id>/stats | Current averages, personal bests, new PBs |

## Tests and coverage
    python -m pytest -q
    python -m pytest --cov=solves --cov=stats --cov-report=term-missing

Result: TOTAL XX% coverage across the `solves` and `stats` packages (measured on <date>).

## Project layout
    app.py          entry point, registers both domains
    config.py       environment settings
    db.py           SQLite connection and startup schema creation
    solves/         domain 1: sessions, solves, scrambles
    stats/          domain 2: averages and personal bests
    templates/ static/   timer page
    tests/          unit and API tests
    ADR.md  AI_USAGE.md  docs/
