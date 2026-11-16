# Architecture overview

## Current development architecture

```text
Browser (React / TypeScript / Vite)
  └── REST API (FastAPI, bearer JWT)
        ├── PostgreSQL (users, organizations, memberships, assets)
        └── Redis (reserved; event stream worker not implemented)
```

Docker Compose provides PostgreSQL, Redis, the API, and an Nginx-served React build. The Vite development server proxies `/api` to the API. The API owns authentication and tenant selection; client-supplied organization IDs are never used to authorize asset access.

## Target service boundaries

- **Identity and tenant service:** accounts, organization memberships, roles, sessions and audit records.
- **Asset and threat model service:** authorized inventory, architecture graph and deterministic STRIDE findings.
- **Event pipeline:** sensor adapters, normalization, queueing, detection and correlation.
- **Analyst gateway:** provider-neutral interface; server-side credentials; field minimization/redaction; bounded requests and evidence-based outputs.
- **Response policy service:** deterministic policy evaluation, approval workflow, least-privilege integrations, idempotency and audit.
- **Web app:** accessible workspace UI; no provider credentials or direct security control credentials.

## Target scan workflow

```text
Verified scope -> scan coordinator -> bounded adapters -> normalized findings
                         ├── app/repository and dependency manifests
                         ├── configured HTTP/API target
                         ├── enrolled host agent
                         └── read-only cloud inventory connector
  -> results store -> in-app/email notification preferences -> remediation tracking
```

Quick Check returns the first bounded checks quickly, then updates a durable job as slower connectors finish. Timeouts or connector errors become explicit `not_checked`/`partial` coverage states, never clean bills of health. Scan adapters must enforce allowlisted targets, DNS/IP safety checks, per-tenant concurrency and rate budgets, and an authorization record. Avoid arbitrary port sweeps or exploit attempts. Deep active testing is a separately scoped, explicitly approved workflow.

The current application has no scanner or alert delivery implementation. Asset registration is the current starting point for an authorized inventory.

## Key decisions

- PostgreSQL is the source of truth. Redis is a transport for future event processing, not authoritative incident storage.
- Tenant scope is derived from authenticated membership on every tenant-data query.
- Deterministic rules decide risk and response eligibility. AI can explain evidence and recommend actions but cannot execute production controls.
- Production-impacting isolation/blocking requires customer policy and human approval.
- This repository currently uses SQLAlchemy metadata creation for a local starter; a reviewed migration system is required before production.
