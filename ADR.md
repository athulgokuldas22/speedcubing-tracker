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
Consequences: Without a foreign key, the database won't stop an orphaned personal best, so the application code has to keep that link valid. Integer milliseconds avoid float rounding errors, and keeping the penalty separate means changing it never loses the raw time.

## 4. Testing approach
Date: 2026-10-10
Status: Decided
Context: The assignment requires at least 70% coverage on core business logic, and the part most likely to hide bugs is the WCA averaging rules.
Decision: I put most tests on pure logic and the service layers (averages, records, penalties, validation, scramble rules), using a temporary SQLite file per test, plus a handful of API tests with Flask's test client. The JavaScript timer is only checked by hand.
Alternatives considered: Testing everything through HTTP only, rejected because failures would be harder to trace to the rule that broke. Mocking the database in service tests, rejected because the SQL constraints are part of the behaviour I want to verify.
Consequences: Coverage on the `solves` and `stats` packages is 100% across 59 tests (command in README), but the front end has no automated tests, so timer bugs would only be caught manually.

## 5. Not building: true WCA random-state scrambles
Date: 2026-10-12
Status: Decided
Context: Official WCA scrambles come from a uniformly random cube state solved with a two-phase solver, but a scramble only has to look random for a practice timer.
Decision: I generate random-move scrambles (20 moves, no two in a row on the same axis) in `solves/scramble.py` and say so in the code and README.
Alternatives considered: Using an existing Kociemba solver library to generate random-state scrambles, rejected because it adds a dependency and may need slow lookup-table generation, which risks the few-seconds startup requirement in the deployment contract.
Consequences: Scrambles are slightly less statistically uniform than official ones, so this is a practice tool and not a competition tool. A solver-based generator could later replace `generate_scramble` without touching anything else.
## 6. The split into two services
Date: 2026-11-12
Status: Decided
Context: Assignment 2 requires one service per feature domain, each in its own container with its own database, and at least one user-visible flow that crosses the seam.
Decision: The seam from ADR-2 held, so I split along it. `solves` owns sessions, solves and scrambles, and `stats` owns averages and personal bests. The only thing that crosses the seam is the times list: `get_times(conn, session_id)` became `GET /api/sessions/<id>/times` on solves, which stats calls server side through `SOLVES_URL` with a 2 second timeout. If solves does not answer, stats returns a 503 with "solves service unavailable, try again later" instead of hanging or showing a stack trace.
Alternatives considered: Letting the UI fetch the times from solves and send them to stats (client side), rejected because the brief needs at least one flow to cross the seam server side and the stats would then trust numbers sent by the browser. Moving the stats logic into solves, rejected because it would leave one service doing everything.
Consequences: Opening the stats of a session now costs an HTTP call instead of a function call, and the stats page fails with a clear error while solves is down, but timing and saving solves keeps working when stats is down. The foreign key from ADR-3 never crossed the seam, so nothing was lost there.
