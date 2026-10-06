# Speedcubing Tracker

A small web app for timing 3x3 solves and tracking averages and personal bests.

## Run
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python app.py

## Configuration (environment variables)
| Variable | Default | Meaning |
|---|---|---|
| HOST | 0.0.0.0 | Bind address |
| PORT | 8000 | Port to listen on |
| DATA_DIR | ./data | Directory holding the SQLite file (cubing.db) |

## Tests and coverage
(coverage command and result to be added)
