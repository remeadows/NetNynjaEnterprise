# NetNynja Enterprise - Issues Tracker

> Active issues and technical debt tracking

**Version**: 0.1.0
**Last Updated**: 2026-01-07 16:00 EST
**Open Issues**: 30 | **Resolved Issues**: 27

## Issue Categories

- 🔴 **Critical** - Blocking issues that prevent core functionality
- 🟠 **High** - Important issues that should be resolved soon
- 🟡 **Medium** - Issues that should be addressed in normal development
- 🟢 **Low** - Nice-to-have improvements

---

## Open Issues

### Phase 0: Repository Setup

| ID   | Priority | Title                                    | Assignee | Status   |
| ---- | -------- | ---------------------------------------- | -------- | -------- |
| #001 | 🟡       | Validate npm workspaces on all platforms | -        | Resolved |
| #002 | 🟡       | Test Poetry install on Windows           | -        | Resolved |
| #003 | 🟢       | Add pre-commit hooks                     | -        | Resolved |

### E2E Testing

| ID   | Priority | Title                                                         | Assignee | Status   |
| ---- | -------- | ------------------------------------------------------------- | -------- | -------- |
| #040 | 🟡       | Frontend tests fail - web-ui not running on port 5173         | -        | Resolved |
| #041 | 🟠       | Logout endpoint returns 400 due to empty JSON body validation | -        | Resolved |
| #042 | 🟠       | Operator role cannot delete networks (403 Forbidden)          | -        | Resolved |
| #043 | 🟡       | OpenAPI documentation not exposed at /docs                    | -        | Resolved |
| #044 | 🟡       | Grafana dashboards not provisioned                            | -        | Resolved |
| #045 | 🟡       | VictoriaMetrics missing netnynja\_\* metrics                  | -        | Resolved |

### Infrastructure

| ID   | Priority | Title                                | Assignee | Status   |
| ---- | -------- | ------------------------------------ | -------- | -------- |
| #010 | 🟠       | Configure production Vault unsealing | -        | Resolved |
| #011 | 🟡       | Add PostgreSQL backup scripts        | -        | Resolved |
| #012 | 🟡       | Configure log rotation for Loki      | -        | Resolved |

### Security

| ID   | Priority | Title                                   | Assignee | Status   |
| ---- | -------- | --------------------------------------- | -------- | -------- |
| #020 | 🔴       | Generate production JWT RSA keys        | -        | Resolved |
| #021 | 🟠       | Implement rate limiting in gateway      | -        | Resolved |
| #022 | 🟠       | Add CORS configuration                  | -        | Resolved |
| #023 | 🟡       | Set up container vulnerability scanning | -        | Resolved |

### Technical Debt

| ID   | Priority | Title                           | Assignee | Status   |
| ---- | -------- | ------------------------------- | -------- | -------- |
| #030 | 🟡       | Add comprehensive test coverage | -        | Resolved |
| #031 | 🟢       | Document API with OpenAPI spec  | -        | Resolved |
| #032 | 🟢       | Add performance benchmarks      | -        | Resolved |

### Phase 8: Cross-Platform Testing

| ID   | Priority | Title                                            | Assignee | Status   |
| ---- | -------- | ------------------------------------------------ | -------- | -------- |
| #050 | 🟡       | Port conflict: Grafana 3000 vs Vite dev server   | -        | Resolved |
| #051 | 🟡       | Port conflict: Auth service 3002 vs Grafana 3002 | -        | Resolved |

### IPAM Module

| ID   | Priority | Title                                                | Assignee | Status   |
| ---- | -------- | ---------------------------------------------------- | -------- | -------- |
| #060 | 🟡       | Cancel button not visible in Add Network modal       | -        | Resolved |
| #061 | 🟠       | Network "Active" status is hardcoded, not functional | -        | Resolved |
| #062 | 🟠       | Missing network scan/discovery feature               | -        | Resolved |
| #063 | 🟡       | Missing site designation field for networks          | -        | Resolved |

### User Management

| ID   | Priority | Title                                      | Assignee | Status   |
| ---- | -------- | ------------------------------------------ | -------- | -------- |
| #064 | 🟠       | No user management UI for admins and roles | -        | Resolved |

### NPM Module

| ID   | Priority | Title                                                         | Assignee | Status   |
| ---- | -------- | ------------------------------------------------------------- | -------- | -------- |
| #070 | 🟠       | Add SNMPv3 credentials management for FIPS compliance         | -        | Resolved |
| #071 | 🔴       | SNMPv3 Credentials - Security Level does not display          | -        | Open     |
| #072 | 🔴       | SNMPv3 Credentials - Auth Protocol does not display           | -        | Open     |
| #073 | 🔴       | SNMPv3 Credentials - Privacy Protocol does not display        | -        | Open     |
| #074 | 🔴       | SNMPv3 Credentials - Request failed with status 500           | -        | Open     |
| #075 | 🔴       | SNMPv3 Credentials - Cannot create and save credential        | -        | Open     |
| #076 | 🟠       | Need network discovery with ping/SNMPv3 options               | -        | Open     |
| #077 | 🟠       | Need ability to add devices discovered by IPAM                | -        | Open     |
| #078 | 🟡       | Need ability to export NPM Status/Health to PDF               | -        | Open     |
| #079 | 🟠       | SNMPv3 devices should show CPU, Memory, latency, availability | -        | Open     |
| #080 | 🟡       | Need ability to group devices                                 | -        | Open     |
| #081 | 🟠       | Need ability to monitor 3000 devices with volumes/interfaces  | -        | Open     |

### Settings Module

| ID   | Priority | Title                                                     | Assignee | Status |
| ---- | -------- | --------------------------------------------------------- | -------- | ------ |
| #082 | 🟠       | Users - Need ability to disable users (not self/admin)    | -        | Open   |
| #083 | 🟠       | Users - Admin-only ability to change other user passwords | -        | Open   |

### IPAM Module (New Issues)

| ID   | Priority | Title                                              | Assignee | Status |
| ---- | -------- | -------------------------------------------------- | -------- | ------ |
| #084 | 🟠       | Need ability to add and scan networks              | -        | Open   |
| #085 | 🟡       | Need ability to group discovered hosts by site     | -        | Open   |
| #086 | 🟠       | Need ability to rescan networks                    | -        | Open   |
| #087 | 🟡       | Need ability to fingerprint discovered hosts       | -        | Open   |
| #088 | 🟠       | Need discovery via PING and NMAP                   | -        | Open   |
| #089 | 🟡       | Need ability to delete scans                       | -        | Open   |
| #090 | 🟡       | Need ability to modify scan attributes             | -        | Open   |
| #091 | 🟡       | Need ability to export scan reports to PDF and CSV | -        | Open   |

### STIG Module (New Issues)

| ID   | Priority | Title                                                                  | Assignee | Status |
| ---- | -------- | ---------------------------------------------------------------------- | -------- | ------ |
| #092 | 🔴       | Adding asset - Platform/Connection type not visible                    | -        | Open   |
| #093 | 🟠       | Need STIG library to upload/manage STIGs from .zip files               | -        | Open   |
| #094 | 🟠       | Missing platforms: pfSense, Arista, HPE Aruba, RHEL, FreeBSD, Mellanox | -        | Open   |
| #095 | 🟠       | Assets must be editable with STIG selection                            | -        | Open   |
| #096 | 🟠       | Need ability to import .ckl, .cklb, .xml files                         | -        | Open   |

### Platform / New Features

| ID   | Priority | Title                                                       | Assignee | Status |
| ---- | -------- | ----------------------------------------------------------- | -------- | ------ |
| #097 | 🟠       | Add Syslog module to navigation (between STIG and Settings) | -        | Open   |

---

## Resolved Issues

| ID   | Priority | Title                                                 | Resolved Date | Resolution                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---- | -------- | ----------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| #040 | 🟡       | Frontend tests fail - web-ui not running on port 5173 | 2026-01-06    | Fixed `BASE_URL` in test_frontend.py to port 3000 (per vite.config.ts) and corrected test password                                                                                                                                                                                                                                                                                                                                      |
| #041 | 🟠       | Logout endpoint returns 400 due to empty JSON body    | 2026-01-06    | Modified auth.ts logout route to not send Content-Type header when no body, and handle empty responses                                                                                                                                                                                                                                                                                                                                  |
| #042 | 🟠       | Operator role cannot delete networks                  | 2026-01-06    | Updated IPAM delete route RBAC from `admin` only to `admin, operator` in ipam/index.ts:288                                                                                                                                                                                                                                                                                                                                              |
| #020 | 🔴       | Generate production JWT RSA keys                      | 2026-01-06    | Created generate-jwt-keys.sh script for 4096-bit RSA PKCS#8 key generation; Updated .gitignore and .env.example with RS256 config; Keys tested with jose library                                                                                                                                                                                                                                                                        |
| #021 | 🟠       | Implement rate limiting in gateway                    | 2026-01-06    | Enhanced rate-limit.ts with tiered limits: 100/min default, 10/min for auth endpoints, role-based multipliers (admin 3x, operator 2x); allowList for health endpoints; Updated error-handler.ts for 429 responses; Added config to .env.example                                                                                                                                                                                         |
| #022 | 🟠       | Add CORS configuration                                | 2026-01-06    | Enhanced config.ts with CORS_ORIGIN, CORS_CREDENTIALS, CORS_MAX_AGE, CORS_EXPOSED_HEADERS; Updated index.ts to use all config options; Added CORS Configuration section to .env.example with documentation                                                                                                                                                                                                                              |
| #045 | 🟡       | VictoriaMetrics missing netnynja\_\* metrics          | 2026-01-06    | Created metrics.ts plugin with prom-client; HTTP metrics (requests, duration, size), auth metrics, rate limit metrics, IPAM metrics, DB/Redis metrics; Endpoint at /metrics; Metrics use netnynja\_\* prefix for dashboards                                                                                                                                                                                                             |
| #043 | 🟡       | OpenAPI documentation at /docs                        | 2026-01-06    | Already working - endpoint redirects /docs to /docs/ which serves Swagger UI properly                                                                                                                                                                                                                                                                                                                                                   |
| #044 | 🟡       | Grafana dashboards not provisioned                    | 2026-01-06    | Added dashboards volume mount to docker-compose.yml; Created gateway-overview.json, ipam-overview.json, system-overview.json dashboards; Existing npm-overview.json and stig-overview.json now properly provisioned                                                                                                                                                                                                                     |
| #023 | 🟡       | Set up container vulnerability scanning               | 2026-01-06    | Created .github/workflows/security-scan.yml (Trivy, CodeQL, npm audit, SBOM), infrastructure/security/ with scan-containers.sh, trivy.yaml config, .trivyignore, and comprehensive README                                                                                                                                                                                                                                               |
| #012 | 🟡       | Configure log rotation for Loki                       | 2026-01-06    | Enhanced loki.yml with stream-specific retention (audit:1yr, auth:90d, errors:60d, debug:7d), compactor settings (apply_retention_interval, delete_max_interval), WAL replay ceiling, and comprehensive documentation                                                                                                                                                                                                                   |
| #011 | 🟡       | Add PostgreSQL backup scripts                         | 2026-01-06    | Created infrastructure/postgres/ with backup.sh (compressed pg_dump with retention), restore.sh (supports Docker and direct restore), and comprehensive README.md with cron examples                                                                                                                                                                                                                                                    |
| #010 | 🟠       | Configure production Vault unsealing                  | 2026-01-06    | Created infrastructure/vault/ with: vault-config.hcl (production config with auto-unseal options), policies/ (admin, gateway, service), scripts/ (init-vault.sh, unseal-vault.sh, setup-policies.sh, setup-secrets.sh), docker-compose.vault.yml, and comprehensive README.md                                                                                                                                                           |
| #001 | 🟡       | Validate npm workspaces on all platforms              | 2026-01-06    | Created scripts/validate-workspaces.sh with comprehensive checks; Added .github/workflows/validate-workspaces.yml for cross-platform CI; Updated clean scripts to use rimraf for Windows compatibility; Added rimraf@6.1.2 as devDependency                                                                                                                                                                                             |
| #002 | 🟡       | Test Poetry install on Windows                        | 2026-01-06    | Created scripts/validate-poetry.ps1 (PowerShell) and scripts/validate-poetry.sh (bash); Added .github/workflows/validate-poetry.yml for multi-platform CI; Checks Python/Poetry versions, pyproject.toml, dependency resolution, Windows-specific settings (long paths, VS Build Tools)                                                                                                                                                 |
| #003 | 🟢       | Add pre-commit hooks                                  | 2026-01-06    | Created .husky/pre-commit (lint-staged, security checks), .husky/commit-msg (conventional commits), .husky/pre-push (build verification); Added .pre-commit-config.yaml for Python (black, ruff, mypy, bandit); Added .yamllint.yml and .secrets.baseline configs                                                                                                                                                                       |
| #030 | 🟡       | Add comprehensive test coverage                       | 2026-01-06    | Created Jest config for gateway; Added test setup with mocks; Created config.test.ts (27 tests), rate-limit.test.ts (33 tests), health.test.ts (8 tests); All 67 tests passing; Added .github/workflows/test.yml for CI                                                                                                                                                                                                                 |
| #031 | 🟢       | Document API with OpenAPI spec                        | 2026-01-06    | Enhanced swagger.ts with comprehensive OpenAPI 3.1.0 documentation; Added schemas for all entities (User, Network, Subnet, IPAddress, Device, Alert, Benchmark, Assessment, etc.); Added reusable responses and parameters                                                                                                                                                                                                              |
| #032 | 🟢       | Add performance benchmarks                            | 2026-01-06    | Created benchmark suite using autocannon; health.benchmark.js (healthz, livez, readyz), auth.benchmark.js (login, profile, refresh), ipam.benchmark.js (networks, subnets, addresses, devices); Added run-all.js runner with JSON output; Added npm scripts (benchmark, benchmark:health, benchmark:auth, benchmark:ipam)                                                                                                               |
| #050 | 🟡       | Port conflict: Grafana 3000 vs Vite dev server        | 2026-01-07    | Changed Grafana port from 3000 to 3002 via GRAFANA_PORT env variable in docker-compose.yml; Updated .env.example with standardized port allocation documentation                                                                                                                                                                                                                                                                        |
| #051 | 🟡       | Port conflict: Auth service 3002 vs Grafana 3002      | 2026-01-07    | Changed auth service port from 3002 to 3006; Updated services/auth-service/.env, apps/gateway/.env, and config defaults; Created standardized port allocation (3000-3006)                                                                                                                                                                                                                                                               |
| #060 | 🟡       | Cancel button not visible in Add Network modal        | 2026-01-07    | Added text-gray-700 and dark:text-gray-200 to Button outline variant in shared-ui/Button.tsx                                                                                                                                                                                                                                                                                                                                            |
| #061 | 🟠       | Network "Active" status is hardcoded, not functional  | 2026-01-07    | Added isActive checkbox to Add Network modal; Updated gateway routes and database queries to handle isActive field; Updated UI to show actual status                                                                                                                                                                                                                                                                                    |
| #062 | 🟠       | Missing network scan/discovery feature                | 2026-01-07    | Feature already exists: POST /networks/:id/scan endpoint triggers network scans; NetworkDetailPage has "Scan Network" button; IPAM store has startScan function                                                                                                                                                                                                                                                                         |
| #063 | 🟡       | Missing site designation field for networks           | 2026-01-07    | Added site column to ipam.networks table; Updated gateway routes, Zod schema, shared-types; Added Site input to Add Network modal and Site column to networks table                                                                                                                                                                                                                                                                     |
| #064 | 🟠       | No user management UI for admins and roles            | 2026-01-07    | Created complete user management: apps/gateway/src/routes/users.ts (CRUD + reset password + unlock); apps/web-ui/src/stores/users.ts; apps/web-ui/src/modules/settings/pages/UsersPage.tsx; Added Settings module to navigation with admin-only access                                                                                                                                                                                  |
| #070 | 🟠       | Add SNMPv3 credentials management for FIPS compliance | 2026-01-07    | Created complete SNMPv3 credential management: npm.snmpv3*credentials table with encrypted storage; apps/gateway/src/routes/npm/snmpv3-credentials.ts (CRUD, test, device lookup); apps/web-ui/src/stores/snmpv3-credentials.ts; apps/web-ui/src/modules/npm/pages/SNMPv3CredentialsPage.tsx; Updated device model for ICMP/SNMPv3 polling; FIPS-compliant auth (SHA-*) and privacy (AES-\_) protocols; AES-256-GCM password encryption |

---

## Issue Template

```markdown
### Issue #XXX: [Title]

**Priority**: 🔴/🟠/🟡/🟢
**Category**: Infrastructure / Security / Application / Documentation
**Reported**: YYYY-MM-DD
**Assignee**:

#### Description

[Detailed description of the issue]

#### Steps to Reproduce (if applicable)

1.
2.
3.

#### Expected Behavior

[What should happen]

#### Actual Behavior

[What actually happens]

#### Proposed Solution

[How to fix it]

#### Related Issues

- #XXX
```

---

## Notes

- Issues are tracked here for visibility, but should also be created in GitHub Issues for proper tracking
- Update status during development
- Close issues with resolution notes
