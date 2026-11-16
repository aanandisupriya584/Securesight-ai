# System design: data model

## Current tables

- `users`: UUID string ID, normalized unique email, password hash, created timestamp.
- `organizations`: UUID string ID, name, created timestamp.
- `organization_members`: UUID ID, organization/user foreign keys, role, unique organization/user pair.
- `assets`: UUID ID, organization foreign key, name, type, identifier, created timestamp.

All asset endpoints constrain queries to the organization membership resolved from the bearer token. Organization IDs are not accepted from asset create payloads.

## Planned entities

Threat models and components; threats and risk assessments; normalized security events; detection rules; incidents and evidence; response policies and actions; integrations and encrypted credentials; immutable audit records; notifications; asset authorization evidence. Add foreign keys, tenant indexes, retention rules and migrations alongside each feature.

For Quick Check, add `scan_scopes` (tenant, target, scope type, exclusions, verification method, verifier, timestamp, expiry), `scan_jobs` (status, started/updated/completed timestamps, scan profile, coverage summary), `scan_tasks` (adapter, bounded status, timing, error class), `findings` (tenant, asset, source, stable fingerprint, severity, confidence, evidence reference, remediation, first/last seen, lifecycle state), and `notification_preferences`/`notification_deliveries`. Index tenant + fingerprint and tenant + status. Store compact evidence with retention and redaction rules; do not put secrets in findings or AI prompts.

## Tenant and audit requirements

Every tenant-owned row needs an organization key and an organization-scoped access path. Audit entries should capture actor, tenant, request/action, evidence references, policy version, approval, result and timestamp. Tamper resistance requires an append-only database role and external/immutable log export; a normal mutable table alone is not tamper-proof.
