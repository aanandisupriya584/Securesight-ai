# IDE integration: SecureSight Developer Security

## Product direction

Give developers vulnerability feedback in the editor while they work, with the same findings also available in the SecureSight organization dashboard. Snyk documents IDE extensions as a way to scan projects and surface remediation guidance; SecureSight will provide its own extension and scanner rather than require a Snyk account or forward scans through Snyk.

## First release: VS Code dependency scanning

1. The developer installs the SecureSight VS Code extension and signs into their SecureSight organization.
2. The extension locates supported package manifests and lockfiles in the open workspace. The developer can run a command or enable scans after dependency-file changes.
3. A local SecureSight scanner builds an inventory from supported lockfiles, then checks exact package versions against the configured vulnerability source (initial candidate: OSV).
4. Findings appear as VS Code diagnostics, in the Problems panel, and in an extension side panel. Each result includes package, installed version, severity, advisory identifier, dependency path when available, fixed version when known, and source link.
5. With organization sign-in, the extension sends normalized finding metadata and a repository/asset reference to the SecureSight API. Raw source files and secrets are not uploaded by default.
6. SecureSight correlates the result with the organization's inventory and dashboard, keeps first/last seen status, and can notify the user through configured channels.

## Supported scan types, staged

- **SCA (first):** vulnerable open-source dependencies from lockfiles for npm, Python, and additional ecosystems as support is verified.
- **Secrets (next):** local patterns and high-confidence secret detectors with redaction. Secret values must never be uploaded; only a redacted finding and local file reference may be synchronized.
- **IaC (next):** local checks for Terraform, Kubernetes, and Docker configuration.
- **SAST (later):** source analysis with line-level diagnostics. Make source transfer explicit, explain retention, and support a fully local mode.

## Technical boundaries

- Keep the scanner engine independent from editor UI. VS Code calls it through a narrow extension interface; JetBrains can be added later through an LSP adapter or dedicated plugin.
- Support offline/local scanning where vulnerability data is cached. Show database age and partial coverage; never mark an unavailable source as clean.
- Keep API credentials in VS Code's secret storage. Authenticate to the API; scope all uploaded findings to the signed-in organization. Never place service credentials in workspace settings or source files.
- Process only the opened workspace and declared repository scope. Do not probe remote hosts or scan third-party assets from an IDE action.
- Do not execute package manager lifecycle scripts merely to scan. Prefer lockfiles and bounded parsers; ask before any optional package-manager operation that runs project code.
- Show evidence and source per finding. A vulnerability match is a candidate that should be triaged; avoid claiming exploitability without evidence.
- Allow the developer to suppress a finding with a reason. Store policy and audit data server-side so local suppression does not silently hide the organization-wide issue.
- AI can summarize remediation after redaction, but does not modify files or run commands without developer approval.

## Shared finding contract

```json
{
  "source": "secure-sca",
  "rule_id": "OSV-EXAMPLE",
  "severity": "high",
  "confidence": "confirmed-version-match",
  "package": {"ecosystem": "npm", "name": "example", "version": "1.2.3"},
  "location": {"path": "package-lock.json"},
  "fixed_version": "1.2.4",
  "references": [],
  "fingerprint": "stable-redacted-dedup-key"
}
```

The API should accept findings in batches with tenant authentication, schema validation, payload limits, deduplication, and audit records. If API upload is unavailable, keep results locally and retry only with explicit, bounded behavior.

## Delivery plan

1. Add a backend finding schema, ingest endpoint, tenant ownership and notification preference controls.
2. Build a local scanner CLI/library for lockfile inventory and OSV queries, with a small supported ecosystem list and tests.
3. Add a VS Code extension for scan, diagnostics, remediation detail, authentication, and optional finding sync.
4. Add workspace policies, suppressions, alert delivery, and centralized scan history.
5. Add secrets/IaC scans; evaluate JetBrains/LSP support after the finding contract stabilizes.

## References

- Snyk describes IDE extensions as providing project scanning and remediation guidance and documents their CLI/vulnerability-database dependency: https://docs.snyk.io/developer-tools/overview
- VS Code exposes diagnostics and other editor language features through its extension API: https://code.visualstudio.com/api/extension-capabilities/overview
- OSV's query batch API accepts package ecosystem, name and version queries: https://google.github.io/osv.dev/post-v1-querybatch/
