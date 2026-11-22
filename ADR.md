# Architecture Decision Record

## 1. Backend language and framework
Date: 2026-10-06
Status: Superseded by 7
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
Status: Superseded by 7
Context: Stats needs to know which session its personal bests belong to, but the two domains must not be coupled through the database.
Decision: `solves` owns `sessions` and `solves` (with a real foreign key and `ON DELETE CASCADE`), and `stats` owns `personal_bests`, which stores `session_id` as a plain integer with no foreign key. Times are stored as integer milliseconds, with the penalty in its own column.
Alternatives considered: A foreign key from `personal_bests.session_id` to `sessions(id)`, rejected because it makes Stats' schema depend on tables owned by Solves. Precomputing and storing an average for every solve, rejected because it goes stale when a penalty changes.
Consequences: Without a foreign key, the database won't stop an orphaned personal best, so the application code has to keep that link valid. Integer milliseconds avoid float rounding errors, and keeping the penalty separate means changing it never loses the raw time.

## 4. Testing approach
Date: 2026-10-10
Status: Superseded by 9
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

## 7. Data and migrations
Date: 2026-11-16
Status: Decided
Context: Assignment 1 kept every table in one SQLite file and created them on first boot. Now each service has its own SQL Server database, and once a database holds data its schema has to change in place, not be recreated.
Decision: Each service owns its tables in its own database, reached with its own login that cannot see the other database: `sessions` and `solves` in solves, `personal_bests` in stats. Flask from ADR-1 stays, but `sqlite3` is replaced by `pymssql`, and the SQLite types became SQL Server ones (`INT IDENTITY`, `NVARCHAR`, `DATETIME2`). No rows were copied from the Assignment 1 SQLite file, because it only held my own test solves, so both databases start from `001_init.sql`. Schema changes are numbered SQL files in `services/<name>/migrations/`, applied in order on startup by `app/migrate.py` and recorded in `schema_migrations`, so each runs exactly once, and an applied file is never edited.
Alternatives considered: Alembic, rejected because it brings SQLAlchemy and model classes, while the services use plain SQL. A one-off script to copy the SQLite data into the new databases, rejected because there was no real data worth keeping.
Consequences: The split lost no foreign key, because `personal_bests.session_id` was already a plain number (ADR-3). What is not enforced is that a personal best points to a session that still exists. Stats compensates by asking solves for the session's times on every stats request, which returns 404 for a missing session, and by recomputing the bests each time, so a stale row is never shown. There is no endpoint that deletes a session, so this cannot happen yet. Recovery plan for a bad migration: migrations are forward-only. Each file runs in one transaction with its `schema_migrations` row, so one that fails rolls back completely, the new container does not start and nothing half-applied is left. The fix is a new numbered migration, never an edit. A migration that changes data adds the new column and backfills it first, and anything destructive, like dropping the old column, waits for a later migration once the new one is verified. Restoring a backup on Azure would create a third database, which the allowance forbids, so this order is what keeps the data safe.

## 8. Serverless hosting on Azure
Date: 2026-11-19
Status: Decided
Context: The system has to run on Azure in my Azure for Students subscription, using only pay-per-use resources, and an idle system should use almost none of the credit. Both services and their databases scale to zero, which affects how they start.
Decision: Everything is in `rg-agokuldas-ieu2024` in France Central, one of the five regions my subscription allows. The two services run on Azure Container Apps (Consumption plan) in one environment, each with minimum 0 and maximum 1 replica, 0.25 vCPU and 0.5 GiB, so they cost nothing while idle and are billed per second while they serve requests. Each service has its own Azure SQL Database, serverless General Purpose Gen5 with 0.5 to 1 vCore, on the free offer, which pauses after 60 minutes without connections and costs nothing within the monthly free allowance. The UI is a Storage static website, because Static Web Apps is not available in the student regions. The images stay in GHCR, which is free, instead of Azure Container Registry, which has a fixed monthly cost. The Log Analytics workspace that the Container Apps environment needs is created with my prefix and is billed only for the log volume, so the services log one line per request and nothing else.
Alternatives considered: Always-on hosting (App Service, a VM, or Container Apps with minimum 1 replica), rejected because it costs the same when nobody is using it. Azure Container Registry, rejected because of its fixed cost.
Consequences: After a quiet period, the first request has to start the container (a few seconds) and may find the database paused, and resuming takes up to about a minute. Meanwhile connections fail with error 40613 or a timeout, so `connect_with_retry` waits 1, 2, 4, 8 and then 15 seconds between attempts, and Container Apps may answer that first request with a 503 after about 30 seconds. The UI retries GET requests during that time and shows a "starting up" message, and the post-deploy health check retries for up to 4 minutes. Migrations run at startup, and because there is at most one replica they never run twice at the same time. At 100 times the traffic I would raise the maximum replicas and move migrations out of startup into a pipeline step, so that several replicas could not run them at once. I would also leave the free offer for a database tier with a longer or disabled auto-pause, to avoid cold starts, and consider a gateway in front of both services.

## 9. Pipeline and testing
Date: 2026-11-20
Status: Decided
Context: Every push has to be linted, tested and built, each service needs at least 70% coverage, there must be at least one integration test across the seam, `system.yaml` and the OpenAPI documents have to be validated, CI must never connect to Azure SQL, and every merge to `main` has to reach Azure with no manual steps.
Decision: Two workflows. `ci.yml` runs on every push to a branch and on every pull request. Its `test` job runs once per service: `ruff`, then `pytest --cov-fail-under=70` against a throwaway SQL Server container that CI starts with a random password. Its `specs` job validates both OpenAPI documents and checks `system.yaml` against `system.schema.json`. Its `images` job only runs if both pass, builds every Dockerfile, and pushes to GHCR, tagged with the commit SHA, only from `main`. `cd.yml` runs on every push to `main`: it reuses `ci.yml`, then deploys those exact images, writes `ui/config.js`, uploads the UI, and fails the run if `/health` on either service does not return 200 within 4 minutes. Changes reach `main` only through pull requests, so CI has already passed on the branch before CD runs. The cross-seam test (`services/stats/tests/test_seam.py`) runs the real stats app and database against a stub of solves over real HTTP, covering the normal flow, a 404, an error from solves, and solves stopped (a 503 in under 3 seconds). The stub answers in the shape that a contract test on the solves side checks. `test_openapi.py` fails if a document and the app's real routes differ.
Alternatives considered: Running the cross-seam test against the whole compose stack, rejected because every push would build both images and start SQL Server and db-init, which is slower and harder to debug, while the stub still exercises the real HTTP call, the timeout and the error handling. A fixed SQL Server password written in the workflow, rejected because the brief forbids secrets in the repository.
Consequences: If the times endpoint changes shape, the solves contract test fails, but the stub has to be updated by hand, so the two tests must change together. Deliberately not tested automatically: the JavaScript in `ui/` (timer, inspection, hold-to-start), which I check by hand. Migrations on a database that already holds data, because CI only runs them on an empty database, so this is checked on Azure with the before-and-after evidence in the report. The real Azure deployment, which is checked by the post-deploy health check.

## 10. No gateway in front of the services
Date: 2026-11-22
Status: Decided
Context: The UI talks to two services on two different URLs, and stats also talks to solves. I could put a gateway in front of them (an nginx container or Azure API Management) so everything sits behind one URL. But I am only allowed two Container Apps.
Decision: I did not build a gateway. CD writes both URLs into `ui/config.js` and the UI calls each service directly. Each service only accepts requests from the UI's origin (`CORS_ORIGINS`), and stats finds solves through `SOLVES_URL`.
Alternatives considered: An nginx gateway would be a third Container App, which the allowance does not allow, and it would add another cold start. API Management costs money and is much more than two services need.
Consequences: There are two public URLs, and CORS has to be set up in both services. If the project grew past two or three services, or they all needed the same login or rate limiting, a gateway would be worth it. Then the UI would only need one URL and I could drop CORS.
