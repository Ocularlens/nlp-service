# AGENTS.md

## Quick start

```bash
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
# Requires PostgreSQL + Redis running locally (see .env for credentials)
uvicorn app.main:server --reload --host 0.0.0.0 --port 8000
# Open http://localhost:8000 in your browser
```

## Key facts

- **Framework**: FastAPI + SQLAlchemy + Alembic + spaCy (sentiment analysis)
- **Entrypoint**: `app.main:server` — the FastAPI instance is named `server`, not `app`
- **Testing**: pytest 8.x with FastAPI TestClient; 90 tests covering routes, services, repositories
- **Python 3.11** (Docker uses `python:3.11-slim`)
- **Dependencies listed in `requirements.txt`** only — no `pyproject.toml` or `setup.py`
- **.env is gitignored** — `DATABASE_URL` and `REDIS_URL` required at runtime; loaded via `python-dotenv`
- **Frontend** at `app/static/index.html` served on `GET /` — single-page app that submits reviews to `POST /api/v1/reviews/`

## Architecture

`app/` packages by layer (each with `__init__.py` re-exporting key names):

| Layer        | Key exports                                     |
|---|---|
| `infra`      | `database`, `init_db` (DB session generator), `Base` (declarative base) |
| `models`     | `Review` (aliased from `ReviewModel`) — table `reviews`, PK is `review_id` (UUID string, 64 chars) |
| `schema`     | `ReviewRequest`, `ReviewResponse` — Pydantic models (`text`, `productName`, optional `translation`) |
| `services`   | `SpacyInteg` (sentiment), `Translator` (Google Translate via `deep-translator`) |
| `repository` | `BaseRepository`, `ReviewRepository` — wraps SQLAlchemy session |
| `routes`     | `review_router` — mounted at `GET/POST /api/v1/reviews/` |
| `static`     | `index.html` — single-page frontend app (plain HTML/CSS/JS with ESM module pattern) |
| `utils`      | `logger` (uvicorn access logger), `limiter` (slowapi, backed by Redis), `generate_unique_id` (uuid4) |

### Key patterns

- **Every route depends on `init_db`** to get a SQLAlchemy session via `Depends(init_db)`, except `GET /` (frontend) and `GET /health` (health check).
- **Rate limiting**: `@limiter.limit("30/minute")` for POST, `"60/minute"` for GET, `"5/minute"` default.
- **Request tracing**: middleware injects `request.state.request_id` (uuid4); always include in log messages.
- **CORS**: only `http://localhost:3000` allowed. Update `allow_origins` if frontend origin changes. The built-in frontend at `GET /` is same-origin, so CORS does not apply.
- **Translation**: optional — if `review.translation` is set, text is translated to English via GoogleTranslate before analysis.

## Frontend (`app/static/index.html`)

A single-page application served at `GET /` for submitting product reviews and viewing sentiment analysis results.

### Features
- **Form**: review text (3–120 chars), product name (max 64 chars), optional translation with source language code.
- **Client-side validation**: inline validation with toast notifications for errors.
- **API integration**: POSTs to `/api/v1/reviews/` and displays the analysis result.
- **Result display**: color-coded mood badge (positive/negative/neutral/mixed), sentiment score, positive/negative word counts, signals list, review ID.
- **UX**: loading spinner on submit, smooth scroll to result, auto-hide toast.
- **Responsive**: works on mobile and desktop via CSS variables, flexbox/grid, and relative units.
- **Tech**: plain HTML/CSS/JS with `<script type="module">` (ESM), no framework.

### How to access
```bash
# Start the server and open http://localhost:8000
uvicorn app.main:server --reload --host 0.0.0.0 --port 8000
```

## Testing

```bash
source venv/bin/activate
python -m pytest tests/ -v            # full suite (90 tests, ~65s)
python -m pytest tests/ -v -k spacy   # run only spaCy tests
python -m pytest tests/ --tb=short    # shorter tracebacks
```

### Test infrastructure (`tests/conftest.py`)

- **Database**: Overrides `init_db` via `server.dependency_overrides` to use a temporary file-based SQLite DB. A fresh DB file is created per test fixture (avoids per-connection isolation issues of `:memory:` with TestClient's threading).
- **Rate limiter**: Sets `REDIS_URL=memory://` before app imports — slowapi uses in-memory storage, no Redis needed.
- **Translation**: Mocks `deep_translator.GoogleTranslator` to prevent real HTTP calls.
- **TestClient**: `test_client` fixture returns a `fastapi.testclient.TestClient` bound to the overridden app. Dependencies are cleared after each test.

### Test files

| File | Tests | What it covers |
|---|---|---|
| `tests/test_health_endpoint.py` | 3 | GET /health returns 200, correct body, X-Request-ID header |
| `tests/test_review_routes.py` | 36 | POST/GET `/api/v1/reviews/` — success, validation, pagination, sorting, filters, translation, product-based lookup |
| `tests/test_spacy_integ.py` | 20 | Positive/negative/neutral/mixed mood, negation (not/n't/never), signals, all word lists |
| `tests/test_translator.py` | 5 | Delegation to GoogleTranslator, default args, error propagation, edge cases |
| `tests/test_review_repository.py` | 11 | CRUD, pagination, sorting, filters, UUID generation, known `get_by_id` bug |
| `tests/test_base_repository.py` | 15 | Full CRUD, pagination, sorting, where filters, update/delete/not-found |

### Known test limitations / bugs discovered

- **`sort_by` enum not enforced**: The `enum` parameter in `Query("review_id", enum=["review_id", "rating", "product"])` does not validate with a `str` type annotation. Passing an invalid value crashes the endpoint with `AttributeError` (cannot be tested via HTTP response — TestClient raises the exception).
- **`sort_order` not validated**: Any value other than `"desc"` is silently treated as `"asc"`.
- **`get_by_id` broken for Review**: `BaseRepository.get_by_id()` uses `self.model.id` but `ReviewModel` uses `review_id`. This method will fail for the Review model.

## Database & Alembic

```bash
alembic upgrade head          # apply pending migrations
alembic revision --autogenerate -m "desc"   # create migration
```

- **`alembic/env.py` sets `target_metadata = None`** — autogenerate will NOT detect model changes automatically. Manually specify or update `target_metadata` to use `Base.metadata`.
- **`alembic.ini`** `sqlalchemy.url` is placeholder; overridden at runtime by `DATABASE_URL` env var.
- **Review model** uses `review_id` (String(64), UUID) as primary key, not auto-increment integer.
- **Migrations history**: started with integer `id` PK, migrated to `review_id` as PK in later revision.
- **`.dockerignore` excludes `alembic/`** — migrations not bundled in runtime image.

## spaCy sentiment analysis (`app/services/spacy_integ.py`)

- Loads `en_core_web_sm` model.
- Sentiment detection from hardcoded `POSITIVE_WORDS` / `NEGATIVE_WORDS` sets (lemma-matched).
- Negation handling: words preceded by `{not, never, no, n't, neither, nor}` flip polarity.
- Negation check is **case-sensitive** (`"not"` works, `"Not"` does not) and only checks the **immediately preceding token** (`"never good"` works, `"never feel good"` does not).
- Returns: `mood` (positive/negative/neutral/mixed), `sentiment_score`, `positive_count`, `negative_count`, `signals`.

## Docker

```bash
docker build -t nlp-service:latest .
docker run -p 8000:8000 -e DATABASE_URL=... -e REDIS_URL=... nlp-service:latest
```

- Multi-stage build: builder installs deps + downloads spaCy model; runtime copies only site-packages + `app/`.
- `CMD` is `uvicorn app.main:server --host 0.0.0.0 --port 8000` (no `--reload`).
- Frontend static files are bundled inside the Docker image (`app/static/` is part of `app/`).

## Gotchas

- **`GET /`** serves the single-page frontend (`app/static/index.html`) via `FileResponse`. It is the only route that does not require a database session or rate limiting.
- **`GET /health`** returns `{"message": "Service is healthy!"}` — probe uses `@server.get`, not under the review router prefix.
- **`app/__init__.py`** logs on import — triggers `uvicorn.access` logger at module load time.
- **No pagination safety** in `get_all()`: `total // size` integer division; pass `page >= 1`.
- **`base_repository.py:get_by_id`** uses `self.model.id` — but `ReviewModel` primary key is `review_id`, not `id`. This method will fail for `Review`.
- **`base_repository.py:get_all`** uses `and_(*where)` with `True` placeholders for inactive filters — SQLAlchemy ignores `True` conditions, but this works in practice.
- **`sort_by` parameter** uses `Query(..., enum=[...])` but the enum is not enforced at the Pydantic/FastAPI level — invalid values pass through and crash the repository layer.
- **SQLite threading**: When writing tests, use a file-based SQLite database (not `:memory:`) to avoid per-connection isolation issues with TestClient's multi-threaded request execution.
