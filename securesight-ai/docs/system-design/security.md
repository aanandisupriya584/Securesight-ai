# System design: security controls

## Implemented in the starter

- Passwords hashed using Argon2 through pwdlib.
- Signed, expiring HS256 bearer tokens; API refuses startup token creation when the configured secret is shorter than 32 characters.
- Organization membership is resolved server-side; asset list/create/delete queries include tenant scope.
- Pydantic validates and bounds asset input fields.
- API keys and AI provider credentials are absent from the browser.

## Required before production

- Replace demo login with controlled user provisioning, MFA/SSO, refresh/session revocation, brute-force controls and secure cookie or carefully managed token storage.
- Use strong secrets management, key rotation, TLS, database encryption/backups, least-privilege service accounts and network restrictions.
- Add migrations, CSRF protections if cookie auth is introduced, CSP/security headers, request rate limits, audit logging and tested recovery.
- Encrypt integration credentials with a managed key service and scope each credential to minimum permissions.
- Add event payload limits, schema validation, replay/idempotency protection, retention controls, and prompt-injection defenses by treating event text as untrusted data.
- Use authorized customer-owned assets only. Do not scan third parties or perform hack-back actions.
- Before any scan, record and verify explicit authorization and constrain execution to the declared scope. Enforce target allowlists, DNS rebinding/private-network protections, redirect checks, request budgets, adapter timeouts, concurrency caps, and an auditable stop control. Cloud connectors should request read-only inventory permissions where possible.
- Treat 30–60 seconds as a first-results objective for a bounded quick profile, not an exhaustive-scan guarantee. Persist partial coverage and continue longer tasks asynchronously.
- Notify users only through configured channels. Verify email destinations and webhook ownership, sign outbound webhooks, prevent secret-bearing payloads, and log delivery attempts without exposing credentials.
- Require human approval for disruptive production actions; never let an LLM directly run them.

## Known starter limitations

Demo account credentials are intentionally local-only. JWT is stored in browser localStorage for this MVP, which is vulnerable to token theft if a frontend XSS occurs. Do not expose this deployment to the public internet or use real customer data until the production requirements above are addressed.
