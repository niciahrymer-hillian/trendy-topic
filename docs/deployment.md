# Deployment Guide — React frontend + PostgreSQL + FastAPI

This guide explains how to deploy the Trendy Topic stack (React dashboard,
FastAPI API, PostgreSQL database) and how to manage secrets safely. It is
written so a teammate can follow it end to end without prior context.

The stack has three services, all defined in [`docker-compose.yml`](../docker-compose.yml):

| Service    | Image / build        | Port (host→container) | Purpose                                   |
| ---------- | -------------------- | --------------------- | ----------------------------------------- |
| `db`       | `postgres:16-alpine` | `5432→5432`           | PostgreSQL analytics database             |
| `api`      | `Dockerfile`         | `8000→8000`           | FastAPI backend (`uvicorn api.main:app`)  |
| `frontend` | `frontend/Dockerfile`| `5173→80`             | React build served by nginx, proxies `/api` |

The React app is built to static files at image-build time and served by nginx.
nginx proxies every `/api/` request to the `api` service (see
[`frontend/nginx.conf`](../frontend/nginx.conf)), so the browser only ever talks
to one origin — there is no separate frontend API URL to configure.

---

## 1. Prerequisites

- Docker and Docker Compose v2 (`docker compose version`).
- A PostgreSQL-capable host (the bundled `db` service, or a managed instance
  such as RDS / Cloud SQL / Supabase).

---

## 2. Configure secrets

All secrets are read from a git-ignored `.env` file at the repo root. Never
commit real secrets — `.env` must stay out of version control.

1. Copy the template:

   ```bash
   cp .env.example .env
   ```

2. Fill in real values. The only **required** value is `DATABASE_URL` for the
   database-backed endpoints; the API keys enable optional features:

   | Variable                          | Required? | Used for                                  |
   | --------------------------------- | --------- | ----------------------------------------- |
   | `DATABASE_URL`                    | Yes       | All DB-backed endpoints                   |
   | `POSTGRES_USER` / `_PASSWORD` / `_DB` | Yes (if using bundled `db`) | PostgreSQL container credentials |
   | `GROQ_API_KEY`                    | Optional  | AI insights, topic extraction, Ask the Dataset |
   | `ANTHROPIC_API_KEY`               | Optional  | Alternate LLM provider                    |
   | `ELEVENLABS_API_KEY`              | Optional  | AI voice briefings                        |
   | `GOOGLE_CLOUD_TRANSLATION_API_KEY` / `GOOGLE_APPLICATION_CREDENTIALS` / `DEEPL_API_KEY` | Optional | Translation feature |
   | `DEWEY_ADMIN_TOKEN`               | Optional  | Protects the Dewey reindex/admin endpoints |

3. Confirm `.env` is ignored by git before committing anything:

   ```bash
   git check-ignore .env   # should print ".env"
   ```

### How secrets reach each service

- **Database URL:** `docker-compose.yml` sets `DATABASE_URL` on the `api`
  service to point at the internal `db` host. This value **overrides** anything
  in `.env`, so the API always talks to the compose database when run via
  compose.
- **API keys:** the `api` service loads `.env` via `env_file` (marked
  `required: false`, so the stack still boots without it). Missing keys only
  disable the specific feature that needs them.
- **PostgreSQL credentials:** the `db` service reads `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, and `POSTGRES_DB`. Change these from the defaults
  (`trendy`/`trendy`) for any deployment that is not purely local, and update
  `DATABASE_URL` to match.

> Secret-manager note: for production, inject these values from your platform's
> secret store (e.g. Docker/Kubernetes secrets, AWS Secrets Manager, GCP Secret
> Manager) instead of a checked-out `.env` file. The application only cares that
> the variables exist in the process environment.

---

## 3. Deploy with Docker Compose (recommended)

From the repo root:

```bash
docker compose up --build -d
```

This will:

1. Start PostgreSQL and wait until its healthcheck passes (`pg_isready`).
2. Build and start the API, which **auto-creates the database schema** on
   startup via `db.create_all()` — no manual migration step is required.
3. Build the React app and serve it through nginx.

Once it's up:

- Dashboard (frontend): http://localhost:5173
- API health/sample:    http://localhost:8000/api/summary

Tear down (data is preserved in the `pgdata` volume):

```bash
docker compose down
```

To also delete the database volume:

```bash
docker compose down -v
```

---

## 4. Initialize / load data

The schema is created automatically, but the tables start empty. Load data using
the project's ingestion tooling (run inside the `api` container or a local venv
with `DATABASE_URL` set):

```bash
# Inside the running api container
docker compose exec api python -m src.ingest --to-db
```

The SQL schema is also available as plain files in [`sql/`](../sql/) if you
prefer to provision the database manually:

```bash
psql "$DATABASE_URL" -f sql/01_create_tables.sql
psql "$DATABASE_URL" -f sql/02_indexes.sql
psql "$DATABASE_URL" -f sql/03_seed_countries.sql
```

---

## 5. Using a managed PostgreSQL instead of the bundled `db`

To point the API at an external/managed database (RDS, Cloud SQL, Supabase,
etc.):

1. Set `DATABASE_URL` in `.env` to the managed connection string, e.g.:

   ```
   DATABASE_URL=postgresql+psycopg://USER:PASSWORD@your-db-host:5432/trendy
   ```

2. Remove (or stop depending on) the `db` service and delete the
   `DATABASE_URL` override on the `api` service in `docker-compose.yml` so your
   `.env` value is used. Ensure `api` no longer `depends_on: db`.
3. Make sure the managed database is reachable from the API host and that TLS /
   network rules allow the connection.

---

## 6. Production hardening checklist

- [ ] Replace default `POSTGRES_USER`/`POSTGRES_PASSWORD` with strong, unique
      credentials.
- [ ] Inject secrets from a secret manager rather than a committed file.
- [ ] Do **not** expose PostgreSQL (`5432`) publicly — remove its `ports`
      mapping in production and keep it on the internal compose network.
- [ ] Put the frontend behind HTTPS (terminate TLS at a load balancer or add a
      TLS server block to nginx).
- [ ] Set `DEWEY_ADMIN_TOKEN` to protect admin/reindex endpoints.
- [ ] Back up the `pgdata` volume (or rely on managed-DB backups).
- [ ] Pin image versions and rebuild regularly for security patches.

---

## 7. Troubleshooting

| Symptom                                   | Likely cause / fix                                                |
| ----------------------------------------- | ----------------------------------------------------------------- |
| Frontend loads but data is empty          | Tables not yet loaded — run the ingestion step in section 4.      |
| API returns `Set DATABASE_URL ...` error  | `DATABASE_URL` missing/incorrect in the environment.              |
| AI insights show "needs a Groq API key"   | `GROQ_API_KEY` not set in `.env`; add it and restart `api`.       |
| Voice feature fails                       | `ELEVENLABS_API_KEY` not set.                                     |
| `db` never becomes healthy                | Check `docker compose logs db`; verify the `pgdata` volume isn't corrupt. |
| Changes to `.env` not picked up           | Recreate the API container: `docker compose up -d --force-recreate api`. |
