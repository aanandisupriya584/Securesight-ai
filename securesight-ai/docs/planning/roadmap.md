# Product plan

## Goal

SecureSight AI is an authorized active cyber defense platform for SaaS and software teams. The product goal is a traceable workflow from owned asset inventory, through event evidence and risk decisions, to approved defensive action and recovery.

## Product requirement: fast security check

The intended user experience is a one-click **Quick Check** that starts checks across the customer's explicitly enrolled application, host, cloud account, API URL, and dependency manifests. Show the first useful findings within a 30–60 second target for bounded, preconfigured scopes, while deeper checks continue as a background job. Display progress, included and skipped scope, last checked time, and whether results are preliminary or complete. Never promise every component is checked in a fixed time.

Before a scope is scanned, require an ownership/authorization record and a clear scope (hostnames, cloud account IDs, repositories, and exclusions). Do not discover or probe arbitrary third-party infrastructure. Use safe, rate-limited checks; require stronger confirmation for checks that could affect availability. Each finding should include source, affected component, evidence, severity, confidence, remediation, and a deduplication key. Notify via in-app inbox first; email/webhook delivery must be opt-in, verified, and auditable.

## MVP delivery sequence

1. **Foundation (implemented starter):** repository, React dashboard, FastAPI service, PostgreSQL, local Docker stack, login, one organization membership per account, and tenant-scoped asset registration.
2. **Quick Check:** ownership/scope verification, scan job state machine, safe adapters for local dependency manifests and configured HTTP/API targets, baseline host checks, and an initial results view. Keep cloud checks read-only and connector-driven.
3. **IDE integration:** local dependency scanning, VS Code diagnostics and remediation details, optional organization sync, then secrets and IaC checks. See [`../architecture/ide-integration.md`](../architecture/ide-integration.md).
4. **Threat modeling:** architecture components, data flows, trust boundaries, deterministic STRIDE rules, risk assessments, versioned threat reports.
5. **Continuous detection:** normalized schema, authenticated Suricata EVE and Wazuh ingestion, app events, Redis Streams workers, correlation, incident timelines, and alerts.
6. **AI analyst:** replaceable provider interface, OpenAI development adapter, redaction, timeouts, quotas, evidence-grounded explanations, and confidence labels.
7. **Response:** policy engine, audit trail, Cloudflare and session workflows, approval gates for disruptive actions, recovery and rollback.
8. **Production readiness:** migrations, SSO/MFA, secrets and key rotation, monitoring, backups, tenant isolation review, dependency/container scans, operational runbooks, and authorized security testing.

## MVP acceptance criteria

- A user can authenticate and see only assets in their organization.
- Users can add and list assets through the UI.
- Empty telemetry is clearly shown as unavailable; the UI does not invent production metrics.
- Docker Compose starts the web app, API, PostgreSQL, and Redis.
- Local UI can be run with npm and proxies API requests.
- AI and defense integrations are described as planned until configured and verified.
- Scan claims reflect actual coverage; quick results disclose incomplete work and continue scans asynchronously.

## Out of scope for this starter

Live attack detection, scanning, automatic blocking, production isolation, commercial AI provider usage, regulatory compliance claims, and production SaaS readiness.
