# NetNynja Enterprise - Issues Archive

> Historical resolved issues archive

---

## Archive Coverage

| Field                     | Value      |
| ------------------------- | ---------- |
| **Start Date**            | 2026-01-06 |
| **End Date**              | 2026-02-12 |
| **Total Issues Archived** | 191        |
| **Last Updated**          | 2026-02-13 |

---

## Resolved Issues

| ID      | P   | Title                                    | Resolved   | Resolution                                                     |
| ------- | --- | ---------------------------------------- | ---------- | -------------------------------------------------------------- |
| #001    | 🟡  | Validate npm workspaces on all platforms | 2026-01-06 | Created validate-workspaces.sh with cross-platform CI workflow |
| #002    | 🟡  | Test Poetry install on Windows           | 2026-01-06 | Created validate-poetry.ps1 and validate-poetry.sh with CI     |
| #003    | 🟢  | Add pre-commit hooks                     | 2026-01-06 | Created Husky hooks and .pre-commit-config.yaml                |
| #010    | 🟠  | Configure production Vault unsealing     | 2026-01-06 | Created infrastructure/vault/ with policies and scripts        |
| #011    | 🟡  | Add PostgreSQL backup scripts            | 2026-01-06 | Created backup.sh and restore.sh with README                   |
| #012    | 🟡  | Configure log rotation for Loki          | 2026-01-06 | Enhanced loki.yml with stream-specific retention               |
| #020    | 🔴  | Generate production JWT RSA keys         | 2026-01-06 | Created generate-jwt-keys.sh for 4096-bit RSA keys             |
| #021    | 🟠  | Implement rate limiting in gateway       | 2026-01-06 | Enhanced rate-limit.ts with tiered limits                      |
| #022    | 🟠  | Add CORS configuration                   | 2026-01-06 | Added CORS config options to gateway                           |
| #023    | 🟡  | Set up container vulnerability scanning  | 2026-01-06 | Created security-scan.yml workflow with Trivy, CodeQL          |
| #030    | 🟡  | Add comprehensive test coverage          | 2026-01-06 | Created Jest tests (67 tests passing)                          |
| #031    | 🟢  | Document API with OpenAPI spec           | 2026-01-06 | Enhanced swagger.ts with OpenAPI 3.1.0                         |
| #032    | 🟢  | Add performance benchmarks               | 2026-01-06 | Created autocannon benchmark suite                             |
| #040    | 🟡  | Frontend tests fail - web-ui port        | 2026-01-06 | Fixed BASE_URL to port 3000                                    |
| #041    | 🟠  | Logout endpoint returns 400              | 2026-01-06 | Fixed auth.ts logout route                                     |
| #042    | 🟠  | Operator role cannot delete networks     | 2026-01-06 | Updated RBAC to allow operator                                 |
| #043    | 🟡  | OpenAPI documentation at /docs           | 2026-01-06 | Already working                                                |
| #044    | 🟡  | Grafana dashboards not provisioned       | 2026-01-06 | Added dashboards volume mount                                  |
| #045    | 🟡  | VictoriaMetrics missing metrics          | 2026-01-06 | Created metrics.ts plugin                                      |
| #050    | 🟡  | Port conflict: Grafana vs Vite           | 2026-01-07 | Changed Grafana to port 3002                                   |
| #051    | 🟡  | Port conflict: Auth vs Grafana           | 2026-01-07 | Changed auth service to port 3006                              |
| #052    | 🟢  | Windows: Docker not in PATH              | 2026-01-08 | Documented workaround                                          |
| #053    | 🟡  | Windows: Docker credential helper        | 2026-01-08 | Documented fix for config.json                                 |
| #054    | 🟢  | Windows: .env requires passwords         | 2026-01-08 | Documented setup steps                                         |
| #060    | 🟡  | Cancel button not visible in modal       | 2026-01-07 | Fixed Button outline variant colors                            |
| #061    | 🟠  | Network Active status hardcoded          | 2026-01-07 | Added isActive field                                           |
| #062    | 🟠  | Missing network scan feature             | 2026-01-07 | Feature already existed                                        |
| #063    | 🟡  | Missing site designation field           | 2026-01-07 | Added site column                                              |
| #064    | 🟠  | No user management UI                    | 2026-01-07 | Created complete user management                               |
| #070    | 🟠  | Add SNMPv3 credentials management        | 2026-01-07 | Created FIPS-compliant SNMPv3 system                           |
| #071    | 🔴  | SNMPv3 Security Level not displayed      | 2026-01-08 | Created missing database table                                 |
| #072    | 🔴  | SNMPv3 Auth Protocol not displayed       | 2026-01-08 | Fixed via #071                                                 |
| #073    | 🔴  | SNMPv3 Privacy Protocol not displayed    | 2026-01-08 | Fixed via #071                                                 |
| #074    | 🔴  | SNMPv3 Request failed 500                | 2026-01-08 | Created table with full schema                                 |
| #075    | 🔴  | SNMPv3 Cannot create credential          | 2026-01-08 | Fixed via #074                                                 |
| #076    | 🟠  | Need network discovery                   | 2026-01-08 | Created complete NPM discovery feature                         |
| #077    | 🟠  | Add IPAM devices to NPM                  | 2026-01-08 | Created IPAM-to-NPM integration                                |
| #078    | 🟡  | Export NPM Status/Health to PDF          | 2026-01-08 | Created PDF/CSV export with pdfmake                            |
| #079    | 🟠  | SNMPv3 devices show metrics              | 2026-01-08 | Created complete device metrics system                         |
| #080    | 🟡  | Need ability to group devices            | 2026-01-08 | Added device groups table                                      |
| #081    | 🟠  | Monitor 3000 devices                     | 2026-01-08 | Scaled NPM with optimized queries                              |
| #082    | 🟠  | Disable users (not self/admin)           | 2026-01-08 | Added validation in users.ts                                   |
| #083    | 🟠  | Admin reset passwords                    | 2026-01-08 | Already implemented                                            |
| #084    | 🟠  | Add and scan networks                    | 2026-01-08 | Enhanced IPAM scanning                                         |
| #085    | 🟡  | Group discovered hosts by site           | 2026-01-08 | Created site grouping for NPM                                  |
| #086    | 🟠  | Rescan networks                          | 2026-01-08 | Implemented via #084                                           |
| #087    | 🟡  | Fingerprint discovered hosts             | 2026-01-08 | Added OS/vendor detection                                      |
| #088    | 🟠  | Discovery via PING and NMAP              | 2026-01-08 | Implemented via #084                                           |
| #089    | 🟡  | Delete scans                             | 2026-01-08 | Created scan deletion feature                                  |
| #090    | 🟡  | Modify scan attributes                   | 2026-01-08 | Added name/notes fields                                        |
| #091    | 🟡  | Export scan reports                      | 2026-01-08 | Created PDF/CSV export                                         |
| #092    | 🔴  | STIG Platform/Connection not visible     | 2026-01-08 | Fixed Select component colors                                  |
| #093    | 🟠  | STIG library for .zip files              | 2026-01-08 | Created STIG Library feature                                   |
| #094    | 🟠  | Missing platforms                        | 2026-01-08 | Added 6 new platforms (16 total)                               |
| #095    | 🟠  | Assets must be editable                  | 2026-01-08 | Added Edit Asset modal                                         |
| #096    | 🟠  | Import .ckl, .cklb, .xml                 | 2026-01-08 | Created checklist import                                       |
| #097    | 🟠  | Add Syslog module                        | 2026-01-08 | Created complete Syslog module                                 |
| #098    | 🟠  | Syslog UDP 514 listener                  | 2026-01-08 | Created Python listener service                                |
| #099    | 🟠  | Syslog 10GB buffer                       | 2026-01-08 | Implemented circular buffer                                    |
| #100    | 🟠  | Syslog forwarder                         | 2026-01-08 | Created forwarder.py                                           |
| #101    | 🔴  | IPAM scans stuck pending (Windows)       | 2026-01-08 | Fixed async execution with setImmediate                        |
| #102    | 🟠  | NPM Poll Now button                      | 2026-01-09 | Created complete Poll Now functionality                        |
| #103    | 🔴  | NPM background polling                   | 2026-01-09 | Created BackgroundPoller plugin                                |
| #104    | 🔴  | NPM Poll Now PostgreSQL error            | 2026-01-10 | Created missing tables, fixed casts                            |
| #105    | 🟠  | Intuitive SNMPv3 enablement              | 2026-01-10 | Created Device Settings modal                                  |
| #106    | 🟠  | IPAM multi-select scan types             | 2026-01-10 | Changed to checkboxes                                          |
| #107    | 🟠  | IPAM fingerprinting not working          | 2026-01-10 | Enhanced nmap XML parsing                                      |
| #108    | 🟡  | IPAM pagination controls                 | 2026-01-10 | Added page size selector                                       |
| #109    | 🟡  | Delete scans from Networks Page          | 2026-01-10 | Added scan management                                          |
| #110    | 🔴  | View Scans API fails                     | 2026-01-10 | Fixed SQL query                                                |
| #111    | 🔴  | NMAP not installed                       | 2026-01-10 | Updated gateway Dockerfile                                     |
| #112    | 🟡  | MAC addresses not detected               | 2026-01-10 | Added network_mode: host option                                |
| #113    | 🟠  | NPM disk/storage metrics                 | 2026-01-12 | Added Sophos SFOS OIDs                                         |
| #114    | 🟠  | NPM interface traffic summaries          | 2026-01-12 | Added IF-MIB 64-bit counters                                   |
| #115    | 🟡  | NPM Sophos service status                | 2026-01-12 | Added 20+ service status OIDs                                  |
| APP-001 | 🔴  | Gateway not responding /healthz          | 2026-01-10 | Fixed Docker health check                                      |
| APP-002 | 🔴  | Auth service unhealthy                   | 2026-01-10 | Fixed via APP-001                                              |
| APP-003 | 🟡  | Grafana preflight port mismatch          | 2026-01-10 | Fixed preflight.sh port                                        |
| APP-004 | 🟠  | NPM collector crash (structlog)          | 2026-01-10 | Fixed structlog config                                         |
| APP-005 | 🟠  | STIG crash (staticmethod)                | 2026-01-10 | Fixed JetStream subscription                                   |
| APP-006 | 🟡  | IPAM scanner restart loop                | 2026-01-10 | Fixed module import                                            |
| APP-007 | 🟢  | Preflight trace count warning            | 2026-01-10 | Fixed integer parsing                                          |
| APP-008 | 🟠  | STIG Library 500 error                   | 2026-01-12 | Created missing tables                                         |
| APP-009 | 🟠  | Auto-polling not working                 | 2026-01-12 | Fixed via APP-010                                              |
| APP-010 | 🟠  | NPM Poll Now fails                       | 2026-01-12 | Created npm.device_metrics table                               |
| APP-011 | 🟡  | Sidebar toggle not visible               | 2026-01-12 | Fixed Sidebar.tsx condition                                    |
| SR-001  | 🔴  | Default admin seed credentials           | 2026-01-10 | Made JWT_SECRET required                                       |
| SR-002  | 🔴  | Hardcoded JWT secret in STIG             | 2026-01-10 | Removed default value                                          |
| SR-003  | 🟡  | JWT verification disabled                | 2026-01-10 | Enabled aud/iss validation                                     |
| SR-004  | 🔴  | Default encryption key (SNMPv3)          | 2026-01-10 | Fixed via SR-005                                               |
| SR-005  | 🟡  | NPM crypto static salt                   | 2026-01-10 | Rewrote with per-encryption salts                              |
| SR-006  | 🟡  | Unauthenticated /metrics                 | 2026-01-10 | Added IP allowlist                                             |
| SR-007  | 🟡  | Auth tokens in localStorage              | 2026-01-10 | Implemented HttpOnly cookies                                   |
| SR-008  | 🟡  | CORS defaults origin:true                | 2026-01-10 | Changed to explicit allowlist                                  |
| SR-009  | 🟢  | NATS lacks TLS/auth                      | 2026-01-10 | Added TLS and auth support                                     |
| SR-010  | 🟢  | Prometheus label escaping                | 2026-01-10 | Added escape_label_value()                                     |
| SR-011  | 🟢  | npm audit vulnerabilities                | 2026-01-10 | Fixed React Router XSS                                         |
| SR-012  | 🟡  | Prettier fails on Helm                   | 2026-01-10 | Excluded charts/ from Prettier                                 |
| SEC-004 | 🟡  | STIG ZIP upload DoS                      | 2026-01-14 | Already implemented (500 files, 100MB)                         |
| SEC-005 | 🟢  | Observability ports exposed              | 2026-01-14 | Bound to localhost only                                        |
| CI-001  | 🔴  | Build Gateway fails                      | 2026-01-11 | Rewrote Dockerfile                                             |
| CI-002  | 🔴  | Build Web UI fails                       | 2026-01-11 | Fixed shared-types                                             |
| CI-003  | 🔴  | Build Auth Service fails                 | 2026-01-11 | Fixed shared-types                                             |
| CI-004  | 🔴  | Build Syslog fails                       | 2026-01-11 | Created main.py                                                |
| CI-005  | 🟠  | Validate Workspaces fails                | 2026-01-14 | Changed to npm run build                                       |
| CI-006  | 🟠  | Container Scan Docker errors             | 2026-01-11 | Fixed Dockerfile builds                                        |
| CI-007  | 🟢  | CodeQL SARIF upload                      | 2026-01-11 | Repository made public                                         |
| CI-008  | 🔴  | test.yml hashFiles() error               | 2026-01-11 | Fixed with check step                                          |
| CI-009  | 🟠  | CodeQL v3 deprecation                    | 2026-01-11 | Upgraded to v4                                                 |
| CI-010  | 🔴  | Permission errors                        | 2026-01-11 | Added actions: read                                            |
| CI-011  | 🟡  | Gateway DTS generation                   | 2026-01-11 | Changed to --no-dts                                            |
| CI-013  | 🟡  | shared-types module not found            | 2026-01-14 | Simplified package exports                                     |
| WIN-001 | 🟠  | Windows Hyper-V port conflicts           | 2026-01-14 | Changed NATS/Vault ports                                       |

---

## Resolved Issues (2026-01-14 to 2026-02-12)

| ID         | P   | Title                                   | Resolved   | Resolution                                                    |
| ---------- | --- | --------------------------------------- | ---------- | ------------------------------------------------------------- |
| STIG-023   | 🔴  | Audit-All 422 - missing body wrapper    | 2026-02-12 | Wrapped proxy body in {"data": {...}} matching STIG-021 pattern|
| NPM-001    | 🟠  | SNMPv3 credential test timeout          | 2026-02-12 | User confirmed working — timeout/retry increases resolved it  |
| UI-017     | 🟢  | React Router v7 migration warnings      | 2026-02-12 | Added v7_startTransition + v7_relativeSplatPath future flags  |
| NPM-004    | 🟠  | Arista CPU/Memory OIDs not working      | 2026-02-12 | Walk hrProcessorLoad + hrStorageTable for Arista/generic      |
| APP-021    | 🟡  | Syslog stats endpoint missing           | 2026-02-12 | Added GET /api/v1/syslog/stats with event count + last event  |
| APP-020    | 🟡  | Gateway STIG route mismatch (404s)      | 2026-02-11 | Added /targets proxy + library browse/summary/platforms proxy |
| SEC-023    | 🟠  | Raw payload redaction + size limits     | 2026-02-11 | Redaction patterns + 4KB truncation before DB storage         |
| SEC-022    | 🟠  | Syslog forwarding TLS not enforced      | 2026-02-11 | TLS default, CA cert config, cleartext warnings               |
| SEC-021    | 🟠  | Container caps excessive (NET_ADMIN)    | 2026-02-11 | cap_drop ALL on all 14 services, minimum cap_add only         |
| SEC-020    | 🟠  | Syslog print() + CORS wildcard          | 2026-02-11 | structlog, CORS restricted to configurable origins            |
| SEC-019    | 🟠  | Input sanitization audit                | 2026-02-11 | Full audit: all SQL parameterized, no shell injection         |
| SEC-018    | 🟠  | Credential encryption static salt       | 2026-02-11 | Per-record random salt, backward-compatible decrypt           |
| SEC-001    | 🟠  | tar RCE in argon2 dependency chain      | 2026-02-11 | Updated argon2 ^0.31.2 → ^0.41.1, eliminated tar dep         |
| SEC-017    | 🔴  | Config upload no size limits            | 2026-02-11 | 413 enforcement in gateway + backend, configurable limits     |
| SEC-016    | 🔴  | Unhardened XML parsing (XXE risk)       | 2026-02-11 | defusedxml for all parsing, XML/ZIP size limits added         |
| SEC-015    | 🔴  | Syslog collector no rate/size limits    | 2026-02-11 | Rate limits, size caps, IP allowlist, backpressure added      |
| SEC-014    | 🔴  | Production secrets in docker-compose    | 2026-02-11 | docker-compose.prod.yml overlay + validate-prod-env.sh        |
| SEC-013    | 🔴  | SSH auditor fallback credentials        | 2026-02-11 | Removed fallback, enforced host key verification              |
| SEC-012a   | 🔴  | Vault auth bypass CVE-2024-41110        | 2026-02-04 | Upgraded Vault 1.15 → 1.18                                    |
| SEC-012b   | 🔴  | Grafana info leak CVE-2024-8986         | 2026-02-04 | Upgraded Grafana 10.2.0 → 11.4.0                              |
| SEC-012c   | 🟠  | Fastify v4 → v5 security upgrade       | 2026-02-04 | Updated gateway + auth-service to Fastify 5.2.0               |
| SEC-012d   | 🟠  | Python 3.11 OpenSSL vulnerabilities     | 2026-02-04 | Updated all Python services to 3.13-slim-bookworm             |
| SYSLOG-002 | 🟠  | Syslog source stats showing 0 events    | 2026-02-04 | Added UNIQUE constraint migration 013, backfill stats         |
| STIG-021   | 🟠  | STIG audit 422 Unprocessable Entity     | 2026-02-04 | Fixed gateway body wrapper for FastAPI {"data": {...}}        |
| STIG-022   | 🟠  | STIG assignment 500 error               | 2026-02-04 | Applied migration 010_add_target_definitions.sql              |
| APP-019    | 🔴  | Auth refresh returns 200 instead of 401 | 2026-02-02 | Changed to reply.status(401).send() pattern in auth-service   |
| APP-018    | 🔴  | Syslog events API 500 error             | 2026-02-02 | Fixed SQL parameter indexing, added try-catch error handler   |
| STIG-020   | 🟠  | Mellanox AAA parsing missing            | 2026-02-02 | Added AAA/TACACS/RADIUS parsing to MellanoxParser             |
| CI-003     | 🔴  | TypeScript compilation errors           | 2026-01-18 | Fixed 5 TS errors in gateway STIG routes (79bcf10)            |
| CI-002     | 🔴  | Missing source files (gitignore)        | 2026-01-18 | Root-anchored STIG/ pattern, added 3 files (97bc2e1)          |
| CI-001     | 🔴  | CI/CD pipeline failures (Rollup ARM64)  | 2026-01-18 | Clean reinstall, audit trail, all workflows pass (8461bbb)    |
| STIG-19    | 🟠  | Combined PDF for multi-STIG analysis    | 2026-01-18 | New combined-pdf/ckl endpoints with executive summary         |
| STIG-18    | 🟠  | Config analysis only first STIG         | 2026-01-18 | Loop through all enabled STIGs, aggregate results             |
| STIG-17    | 🟡  | PDF description raw XML tags            | 2026-01-18 | extract_vuln_discussion() + clean_text_for_pdf()              |
| STIG-16    | 🟠  | CKL report missing V-ID details         | 2026-01-18 | Enhanced CKL exporter with rule details from database         |
| STIG-15    | 🟠  | PDF report missing V-ID details         | 2026-01-18 | Added full description and fix text to PDF findings           |
| STIG-14    | 🟠  | Config analysis requires STIG selection | 2026-01-18 | Auto-use assigned STIGs for config analysis                   |
| STIG-500   | 🔴  | SSH Credentials 500 Error               | 2026-01-18 | Applied migration 008_add_ssh_credentials_sudo.sql            |
| STIG-13    | 🔴  | Multi-STIG selection for assets         | 2026-01-17 | Target-STIG associations, batch audits, combined PDF/CKL      |
| STIG-12    | 🔴  | Report PDF/CKL download fails           | 2026-01-17 | Fixed config import, Pydantic model access, enhanced report   |
| STIG-11    | 🟠  | Config analysis 401 Unauthorized        | 2026-01-16 | Fixed frontend to use api client with auth header             |
| STIG-10    | 🟠  | Config analysis 404 gateway route       | 2026-01-16 | Added proxy route in gateway for STIG service                 |
| STIG-09    | 🟠  | SSH audit endpoint proxy missing        | 2026-01-16 | Added audit routes proxy to gateway (STIG service)            |
| STIG-08    | 🟠  | STIG Library XCCDF indexer              | 2026-01-16 | Created library module: catalog, parser, indexer              |
| STIG-07    | 🟠  | STIG Library API endpoints              | 2026-01-16 | Added 6 API endpoints for browsing/searching library          |
| STIG-06    | 🟠  | Config file analysis feature            | 2026-01-16 | Added parsers for 6 platforms, API endpoint, UI modal         |
| CI-017     | 🔴  | Turbo/ESLint compatibility              | 2026-01-16 | Created ESLint 9.x flat config (eslint.config.mjs)            |
| APP-016    | 🔴  | Syslog forwarder crash (missing DB)     | 2026-01-16 | Created migration 009_add_syslog_forwarders.sql               |
| APP-017    | 🟠  | E2E tests blocked by artifacts          | 2026-01-16 | Fixed CI workflow path, updated .gitignore                    |
| DOC-001    | 🟢  | STIG Selection Guide                    | 2026-01-16 | Created docs/STIG_SELECTION_GUIDE.md                          |
| CI-012     | 🟠  | Vite 5.x to 7.x upgrade               | 2026-01-15 | Upgraded Vite 7.3.1, fixed cross-spawn/glob CVEs              |
| CI-015     | 🟠  | Tests workflow failing                  | 2026-01-15 | Added --passWithNoTests to Jest config                        |
| CI-016     | 🟡  | E2E cleanup step failing                | 2026-01-15 | Added fallback to docker compose down in CI                   |
| SEC-010    | 🟠  | Container security vulnerability scan   | 2026-01-15 | Docker Scout scan completed, report generated                 |
| DOC-003    | 🟢  | Code signing implementation guide       | 2026-01-15 | Created CODE_SIGNING_GUIDE.md with Cosign/GPG docs            |
| INFRA-8    | 🟠  | Container image signing and publishing  | 2026-01-15 | All 14 images signed with Cosign, pushed to GHCR              |
| UI-016     | 🟢  | ISSO Executive Summary document         | 2026-01-15 | Created HTML/Word doc with project overview for ISSO          |
| UI-015     | 🟡  | Subtitle text illegible on dark bg      | 2026-01-15 | Brighter colors + text-shadow for gray-400/500                |
| UI-014     | 🟢  | Add condensed display density           | 2026-01-15 | Added "Condensed" option with 9-15px fonts                    |
| UI-013     | 🟡  | Display density system                  | 2026-01-15 | CSS variables for 4 density levels + toggle + prefs           |
| STIG-05    | 🟠  | SSH credentials need sudo support       | 2026-01-15 | Added sudo fields to SSH credentials (method/user/pw)         |
| STIG-04    | 🟠  | SSH credentials management UI           | 2026-01-15 | Created CredentialsPage with CRUD for SSH creds               |
| APP-015    | 🟠  | Settings Preferences nav link           | 2026-01-15 | Added Preferences to Settings sidebar navigation              |
| SEC-008    | 🟡  | NATS auth/TLS disabled                  | 2026-01-14 | Created nats.prod.conf, cert gen script, updated docs         |
| SEC-009    | 🟢  | trustProxy always true                  | 2026-01-14 | Made configurable via TRUST_PROXY env var                     |
| SEC-006    | 🟠  | .env tracked with secrets               | 2026-01-14 | Already in .gitignore, .env.example exists                    |
| SEC-007    | 🟠  | DB/Cache ports exposed                  | 2026-01-14 | Bound Postgres/Redis/NATS to 127.0.0.1                        |
| APP-012    | 🔴  | Preflight CRLF errors on Windows        | 2026-01-14 | Converted to LF, added PowerShell wrapper                     |
| APP-013    | 🔴  | Preflight Docker checks fail            | 2026-01-14 | Created preflight.ps1 for native Windows                      |
| APP-014    | 🟠  | OpenAPI endpoint mismatch               | 2026-01-14 | Fixed endpoint to `/docs/json`                                |

---

## Archive Notes

- This archive contains all resolved issues from project inception through the archive end date
- For issue details including full resolution descriptions, see git history or PROJECT_STATUS.md changelog
- New issues should be tracked in IssuesTracker.md
- Archive when IssuesTracker.md exceeds 200 resolved issues or quarterly, whichever comes first
