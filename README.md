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

## Run with Docker

The `Dockerfile` is the course template with the source-file lines filled in.

    docker build -t myapp .
    docker run -p 8000:8000 -v myapp-data:/data myapp

Then open http://localhost:8000/. In the container `DATA_DIR` is `/data`, so the database is `/data/cubing.db`, and it stays when the container is removed if the same volume is used. To change the port: `docker run -e PORT=9000 -p 9000:9000 myapp`.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/scramble` | New random-move scramble |
| GET, POST | `/api/sessions` | List or create sessions |
| GET, POST | `/api/sessions/<id>/solves` | List or add solves |
| PATCH | `/api/solves/<id>` | Set penalty (OK, +2, DNF) |
| DELETE | `/api/solves/<id>` | Delete a solve |
| GET | `/api/sessions/<id>/stats` | Current averages, personal bests, new PBs |

## Tests and coverage
    python -m pytest -q
    python -m pytest --cov=solves --cov=stats --cov-report=term-missing

Result: TOTAL 100% coverage across the `solves` and `stats` packages (199 statements, 59 tests passing, measured on 2026-10-12).

## Project layout
    app.py          entry point, registers both domains
    config.py       environment settings
    db.py           SQLite connection and startup schema creation
    solves/         domain 1: sessions, solves, scrambles
    stats/          domain 2: averages and personal bests
    templates/ static/   timer page
    tests/          unit and API tests
    ADR.md  AI_USAGE.md  docs/

## Container check (section 7 evidence)

Output of `container/run.sh` against this repo:

```
=== SDD Assignment 1 contract check ===
Repository: /Users/athulgokuldas/Desktop/Software Developent and Devops/speedcubing-tracker

==> Repository shape
  PASS  one Dockerfile, one manifest (requirements.txt)

==> Build from a clean context, no build args
  PASS  image built
  PASS  image size 245 MB

==> Start on PORT=8000 and reach it from the host
  PASS  HTTP 200 from http://localhost:8000/

==> SQLite file under DATA_DIR
  PASS  found in /data: cubing.db 

==> Data persists, and a second boot does not re-seed
  PASS  volume at /data persists
  WARN  Could not read row counts, skipping the re-seed check.

==> PORT override is honoured (not hardcoded)
  PASS  HTTP 200 from http://localhost:9123/

=== ALL CHECKS PASSED ===
Paste this output into your README as the §7 evidence.
```

The checker gave one warning: it could not read the row counts, so it skipped the re-seed check. The app has no seed data, and on start it only creates tables that are missing (`CREATE TABLE IF NOT EXISTS`), so booting twice changes nothing.
