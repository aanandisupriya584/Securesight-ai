# SecureSight AI

Active Cyber Defense Platform MVP — Detect. Defend. Contain. Recover.

This repository is the Phase 1 foundation: a React dashboard, FastAPI API, PostgreSQL persistence, tenant-scoped organizations and assets, and a Docker Compose development environment. Detection and response integrations are documented extension points; they are not represented as connected sensors or live defenses in this MVP.

The product roadmap now includes a scoped **Quick Check** across enrolled applications, hosts, cloud accounts, APIs, and dependency manifests. The 30–60 second target is for first results from bounded checks; longer checks continue in the background and report partial coverage explicitly. Scanning is not implemented in this Phase 1 starter.

With `SEED_DEMO=true`, startup inserts clearly labeled synthetic assets, events, and incidents for dashboard testing. Set `SEED_DEMO=false` outside local development; demo data is never live telemetry.

## Architecture

```text
React + TypeScript (Vite) ── REST / JWT ── FastAPI ── PostgreSQL
                                              └── Redis (reserved for event pipeline)
```

The API uses organization membership checks on tenant data and hashed passwords. Local development uses a seeded demo organization. The dashboard labels its sample overview values as demo data so they cannot be mistaken for production security telemetry. See [`docs/architecture/overview.md`](docs/architecture/overview.md) and [`docs/system-design/data-model.md`](docs/system-design/data-model.md).

## Run with Docker

Copy `.env.example` to `.env`, then run:

```sh
docker compose up --build
```

Open the Docker UI at http://localhost:9005 and API docs at http://localhost:8000/docs. The local development login is configured by `SEED_DEMO_USERNAME` and `SEED_DEMO_PASSWORD` in your untracked `.env` file.

## Run the React UI with npm

Start the API and dependencies with `docker compose up db redis api`, then in another terminal:

```sh
cd frontend
npm install
npm run dev
```

The npm UI runs at http://localhost:9000 and proxies `/api` requests to the local API. Build the UI with `npm run build`.

## Run the API outside Docker

Use Python 3.11+, create a virtual environment, install `backend/requirements.txt`, set `DATABASE_URL` and `JWT_SECRET` from `.env.example`, then run `uvicorn app.main:app --reload --app-dir backend`. A local PostgreSQL instance is required. The API seeds a demo tenant and account on first startup when `SEED_DEMO=true`.

## Documents

- [`docs/planning/roadmap.md`](docs/planning/roadmap.md)
- [`docs/workflow/development.md`](docs/workflow/development.md)
- [`docs/architecture/overview.md`](docs/architecture/overview.md)
- [`docs/system-design/data-model.md`](docs/system-design/data-model.md)
- [`docs/system-design/security.md`](docs/system-design/security.md)
- [`docs/architecture/ai-provider.md`](docs/architecture/ai-provider.md)

## Scope and security

This is a development MVP, not a production-ready security product. There is no production SSO/MFA, migrations workflow, credential vault, deployed Suricata/Wazuh collector, live AI provider, or active blocking integration. Never connect it to real customer assets or enter production secrets until those controls and operational requirements are implemented and reviewed. Integrations must only be used for explicitly authorized customer-owned assets.
