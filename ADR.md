# Architecture Decision Record

## 1. Backend language and framework
Date: 2026-10-06
Status: Decided
Context: The app must be a small single-process web server backed by SQLite, and I have to be able to explain every line of it without notes.
Decision: Python with Flask, using the standard-library sqlite3 module directly instead of an ORM.
Alternatives considered: FastAPI, rejected because async and auto-generated docs add dependencies (uvicorn, pydantic) that this app doesn't need. Django, rejected because its ORM, admin and auth are unused overhead for two small domains.
Consequences: I write the SQL by hand and structure the two domains into separate packages myself, so the seam must be kept clean by discipline rather than by the framework.

## 2. Independently modularizable feature domains
Date: 2026-10-08
Status: Decided
Context: The assignment needs two feature domains that could later become separate services, but the app must stay a single process with no message broker.
Decision: The `solves/` and `stats/` packages each own their schema, repository, service and routes, and `stats/` may only call `solves.get_times(conn, session_id)`. `solves/` never imports `stats/`.
Alternatives considered: One flat module with shared models, rejected because the shared tables would couple the domains. Stats querying the `solves` table directly with a JOIN, rejected because that query could not survive a split into two services.
Consequences: Stats makes one extra function call instead of a JOIN, which is fine at this scale. Splitting later means replacing `get_times` with an HTTP call, and that function is the seam.

## 3. SQLite schema and how the domains' data relates
Date: 2026-10-08
Status: Decided
Context: Stats needs to know which session its personal bests belong to, but the two domains must not be coupled through the database.
Decision: `solves` owns `sessions` and `solves` (with a real foreign key and `ON DELETE CASCADE`), and `stats` owns `personal_bests`, which stores `session_id` as a plain integer with no foreign key. Times are stored as integer milliseconds, with the penalty in its own column.
Alternatives considered: A foreign key from `personal_bests.session_id` to `sessions(id)`, rejected because it makes Stats' schema depend on tables owned by Solves. Precomputing and storing an average for every solve, rejected because it goes stale when a penalty changes.
Consequences: Without a foreign key, the database won't stop an orphaned personal best, so the application code has to clean up. Integer milliseconds avoid float rounding errors, and keeping the penalty separate means changing it never loses the raw time.
