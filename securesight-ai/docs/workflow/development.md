# Development workflow

## Local setup

1. Copy `.env.example` to `.env` and replace local passwords/secrets if exposing ports beyond the machine.
2. Run all services using `docker compose up --build`.
3. For the npm workflow, start `db`, `redis`, and `api` with Compose, then use `cd frontend`, `npm install`, `npm run dev`.
4. Sign in with the seeded local-only account documented in the README.
5. Register only assets for which the organization has explicit authorization.

## Change flow

1. Write or update the relevant product/system design note in `docs/`.
2. Define API schemas and tenant authorization before adding UI flows.
3. Keep secrets server-side and redact sensitive event fields before any AI analysis.
4. Record evidence, actor, policy decision, approval and result for each security response.
5. Verify changes locally before presenting an integration as operational.

## Incident handling flow (target)

Sensor -> authenticated collector -> validation and normalization -> durable queue -> deterministic rules and correlation -> risk assessment -> evidence-linked explanation -> policy evaluation -> approval where required -> authorized action -> append-only audit entry -> recovery review.

The current starter implements authentication and asset inventory only. Its event and response steps are design targets.
