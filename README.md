# Decent Visualizer

A coffee-shot tracker with a React/Vite frontend on Cloudflare Pages and a
FastAPI backend on an Oracle Linux ARM VM.

## Architecture

- **Frontend:** Cloudflare Pages.
- **Backend:** Docker Compose on the Oracle VM, reached through a Cloudflare
  Tunnel sidecar; no inbound HTTP port is exposed.
- **Database:** SQLite in the persistent `decent-visualizer_database` Docker
  volume.
- **Migrations:** Alembic revisions in `backend/migrations/`; the backend
  upgrades to the current revision at startup.
- **Backups:** a Compose sidecar uploads a compressed SQLite snapshot to a
  private OCI Object Storage bucket daily. OCI lifecycle management deletes
  snapshots after 30 days.
- **Secrets:** Infisical. GitHub Actions uses OCI workload identity federation;
  the backend has a read-only Universal Auth identity for `/backend`.

## Local development

```sh
make dev
```

This starts the frontend and backend. Local SQLite data is stored at
`backend/.data/decent-visualizer.sqlite3`.

Run checks with:

```sh
make lint
(cd backend && uv run pytest)
```

## Deployment

Push to `main`. GitHub Actions tests the app, applies OCI/Cloudflare
infrastructure through OpenTofu, then deploys the backend and frontend.

## Layout

- `backend/`: FastAPI app, SQLite storage, Alembic migrations, and tests.
- `frontend/`: React/Vite app.
- `infra/`: OpenTofu for OCI backups, Cloudflare, and Infisical.
- `config/`: committed non-secret configuration.
