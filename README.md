# Music Logging App

A Letterboxd-style app for logging and rating albums.

## Quick start

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env
# Edit .env: set DATABASE_URL (SQLite is fine locally; Postgres for real use)
alembic upgrade head
uvicorn musicapp.main:app --reload
```

Open http://127.0.0.1:8000 — run tests with `pytest`.

## Stack
- Python 3.12, FastAPI, SQLAlchemy 2.x + Alembic, PostgreSQL
- Jinja + HTMX for the UI (no separate JS frontend)
- pytest for tests; httpx for outbound HTTP

## Data source: MusicBrainz
- Users log RELEASE GROUPS (albums as a concept), never individual releases.
- Use MBIDs as external keys; store fetched_at on cached entities.
- Rate limit: max 1 request/sec. All calls go through one client with a
  token-bucket limiter, retry/backoff on 503, and a User-Agent header with
  app name, version, and contact email.
- Check the local DB before calling the API; upsert on return.
- Cover art comes from coverartarchive.org; always handle missing art.
- Never hit the live API in tests; mock responses.

## Conventions
- Ratings stored as integers 1-10 (half-stars).
- All schema changes go through Alembic migrations.
- Type hints everywhere; small functions; no business logic in route handlers.

## Working rules
- Build one feature at a time; run tests before saying a task is done.
- Explain any non-trivial SQL you write.
- Ask before adding dependencies.