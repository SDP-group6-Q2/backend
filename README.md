# Backend

The REST API for the AROL fleet platform. It serves access level scoped machine, telemetry, maintenance, commercial (quotes/orders) and manuals data, manages users/clients and provides login/authentication for the system via access token.

Built with **FastAPI**, **SQLAlchemy 2.0** (async, via `asyncpg`). Data storage using on **PostgreSQL** and document storage using **Supabase** bucket.

## Domain model

- **Client / User** — a client is a company (tenant); users belong to a client and are scoped to
  it. Each user has a `visibility` tier (`full`, `technician`, `commercial`) that determines which
  parts of the API it can see. New users are inactive until a superuser activates them.
- **Machine / Machine model** — installed machines, each tied to a product line (model) and a
  client/company.
- **Telemetry** — time-series snapshots reported by machines.
- **Alarms** — alarm events raised by machines, with severity and status.
- **Maintenance tickets** — service/maintenance work items tied to a machine, with priority and
  status.
- **Quotes / Orders** — commercial documents (quotes, quote revisions/lines, orders, order lines)
  tied to a client.
- **Manuals** — machine manual PDFs, stored in a Supabase bucket and linked to machines.
- **Conversations** — chat history between a user and the AI assistant.

## Authentication & authorization

- JWT bearer tokens issued at `POST /auth/jwt/login`, via `fastapi-users`.
- Every route other than `/auth/*` requires an authenticated, active user.
- Access is scoped by the user's client (tenant isolation) and `visibility` tier; a handful of
  operations (e.g. creating clients) require superuser privileges.
- Attempts to access data outside a user's tenant are rejected (and, deliberately, not
  distinguished from a 404) so that the API never leaks the existence of another company's data.

## API conventions

- Responses and errors follow consistent shapes across routers (see `app/core/exceptions.py`):
  403 for access denied, 404 for not found, 400 for invalid input (e.g. a bad pagination cursor),
  503 when document storage is unavailable.
- Endpoints returning result sets that can grow unbounded (telemetry, alarms, tickets) use
  cursor-based pagination: rows are returned newest-first, capped at a maximum page size, with an
  opaque cursor to fetch the next page when the result was truncated (`app/core/pagination.py`).
- List endpoints that support filtering accept repeated query parameters (e.g.
  `?priority=Critical&priority=High`) and match rows against any of the given values
  (`app/core/filters.py`).

## Project layout

```
app/
  core/        # settings, auth, pagination, filters, exceptions
  models/      # SQLAlchemy ORM models
  schemas/     # Pydantic request/response schemas
  repositories/# database access layer
  services/    # business logic, orchestrated by routes
  routes/      # FastAPI routers (one per resource)
  storage/     # manual PDF storage (Supabase)
  db/          # engine/session setup
alembic/       # database migrations
```

## Configuration

Settings are loaded from environment variables, or a `.env` file in this directory
(`app/core/config.py`). Copy the template and adjust it:

```bash
cp .env.example .env
```

| Variable | Default | Purpose |
| --- | --- | --- |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB` | — | Connection to the PostgreSQL database. |
| `JWT_SECRET` | — | Signing secret for access tokens. Use a long random value outside development. |
| `ACCESS_TOKEN_LIFETIME_SECONDS` | `3600` | How long an issued JWT stays valid. |
| `FIRST_SUPERUSER_EMAIL`, `FIRST_SUPERUSER_PASSWORD` | — | Credentials for the superuser bootstrapped on first run. Leave unset to skip creating one. |
| `FIRST_SUPERUSER_USERNAME` | `admin` | Username for that superuser. |
| `FIRST_SUPERUSER_CLIENT_NAME` | `default` | Client (tenant) the superuser is created under; created if it doesn't exist. |
| `SEED_DATASET_USERS` | `true` | Whether the sample dataset's Users sheet is also loaded as accounts (dev only). |
| `DATASET_PATH` | `/app/data/AROL_Q2_synthetic_fleet_dataset.xlsx` | Path to the sample fleet dataset `.xlsx` file. |
| `SEED_DATASET` | `true` | Read only by `docker-entrypoint.sh`: skip dataset seeding on container start. |
| `ORCHESTRATOR_URL` | `http://orchestrator:8001` | Base URL of the AI orchestrator service backing `/assistant`. |
| `ORCHESTRATOR_TIMEOUT_SECONDS` | `120` | Timeout for requests to the orchestrator. |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | — | Optional. Enables manual PDF storage/retrieval; without them, `/manuals` returns 503. |
| `MANUALS_BUCKET` | `manuals` | Supabase storage bucket holding manual PDFs. |
| `MANUAL_URL_TTL_SECONDS` | `60` | How long a generated manual download URL stays valid. |

## Running

### Prerequisites

- Python 3.13
- A reachable PostgreSQL instance
- (Optional) the sample dataset `.xlsx` file, if you want seeded data
- (Optional) a running `orchestrator` service and/or Supabase credentials, if you want
  `/assistant` and `/manuals` to work

### Standalone

1. **Install dependencies** (ideally in a virtualenv):

   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**: `cp .env.example .env` and fill in at least the `POSTGRES_*` and
   `JWT_SECRET` values, pointing `POSTGRES_HOST`/`POSTGRES_PORT` at your database.

3. **Run migrations**:

   ```bash
   alembic upgrade head
   ```

4. **Create the first superuser**, from `FIRST_SUPERUSER_*` in `.env` (safe to re-run; it's a
   no-op if that user already exists):

   ```bash
   python -m app.initial_data
   ```

5. **(Optional) Load the sample fleet dataset** (machines, telemetry, alarms, tickets,
   quotes/orders, and optionally users):

   ```bash
   python -m app.seed_dataset --path /path/to/AROL_Q2_synthetic_fleet_dataset.xlsx
   ```

6. **(Optional) Link machines to their manual PDFs** in the Supabase bucket (requires
   `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` and having run step 5 first):

   ```bash
   python -m app.sync_manuals
   ```

7. **Start the API**:

   ```bash
   uvicorn app.main:app --reload
   ```

Interactive API docs are then available at `/docs` (Swagger UI) and `/redoc`.

### Docker

The image's entrypoint (`docker-entrypoint.sh`) runs steps 3–6 above automatically on every
container start (migrations and superuser creation are idempotent; dataset seeding and manual
linking are skipped if their file/credentials aren't present), then launches uvicorn.

```bash
docker build -t backend-api .

docker run --rm -p 8000:8000 \
  --env-file .env \
  backend-api
```

Notes:

- `POSTGRES_HOST` must be reachable *from inside the container* — e.g. a Postgres container's
  name on a shared Docker network, or `host.docker.internal` if Postgres runs on your host.
- To seed the sample dataset on startup, mount it where `DATASET_PATH` points and leave
  `SEED_DATASET=true`, e.g.:

  ```bash
  docker run --rm -p 8000:8000 \
    --env-file .env \
    -v "$(pwd)/data:/app/data:ro" \
    backend-api
  ```
