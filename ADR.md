# Architecture Decision Record

## 1. Backend language and framework
Date: 2026-10-06
Status: Decided
Context: The app must be a small single-process web server backed by SQLite, and I have to be able to explain every line of it without notes.
Decision: Python with Flask, using the standard-library sqlite3 module directly instead of an ORM.
Alternatives considered: FastAPI, rejected because async and auto-generated docs add dependencies (uvicorn, pydantic) that this app doesn't need. Django, rejected because its ORM, admin and auth are unused overhead for two small domains.
Consequences: I write the SQL by hand and structure the two domains into separate packages myself, so the seam must be kept clean by discipline rather than by the framework.
