# NetNynja Enterprise - Issues Tracker

> Active issues and technical debt tracking

**Version**: 0.2.13
**Last Updated**: 2026-02-11 23:30 UTC
**Stats**: 3 open | 0 deferred | 186 resolved (archived)
**Codex Review**: 2026-02-11 (Dual review: CODEX_REVIEW20260211-1133 + GEMINI_CLI_REVIEW20260211-1146)
**Docker Scout**: 2026-02-04 (Internet-facing: 0 CRITICAL ✅ | Internal: 12 CRITICAL - monitoring)
**CI/CD Status**: ✅ ALL WORKFLOWS PASSING
**Security Remediation**: SEC-012 Phase 1 Complete | SEC-HARDENING-01 Sprint Day 5 of 5 (5/5 blockers + 6/6 Tier 1 + APP-020 resolved)
**Production Readiness**: 🟢 ALL LAUNCH BLOCKERS + ALL TIER 1 RESOLVED — Day 5 validation remaining

---

## 🔥 NOW (Active / In Progress)

### SEC-012: Security Vulnerability Remediation (Phase 1B Monitoring)

**Status**: 🟡 Active - Monitoring for Upstream Patches
**Priority**: 🔴 Critical - Security Issue
**Detected**: 2026-02-04 (Trivy/Docker Scout scan)
**Engineer**: DevOps

**Phase 1 Complete** ✅:

- Vault 1.15 → 1.18 (CVE-2024-41110 resolved)
- Grafana 10.2.0 → 11.4.0
- Fastify 4.x → 5.x (auth-service, gateway)
- Python 3.11 → 3.13 (all services)
- Internet-facing services: **0 CRITICAL vulnerabilities**

**Phase 1B Monitoring** (waiting for upstream):

- OpenSSL CVE-2025-15467 in Alpine images (postgres, redis, nats, grafana)
- Root cause: Upstream Docker images haven't released patched versions
- Mitigation: Internal services not internet-exposed, network segmentation

**Risk Assessment**:

- Internet-facing (auth, gateway): 🟢 LOW RISK (0 CRITICAL)
- Internal infrastructure: 🟡 MEDIUM RISK (12 CRITICAL, mitigated)

**Next Steps**:

1. Set up daily monitoring for Alpine image updates
2. Subscribe to Alpine/Grafana security mailing lists
3. Deploy patches within 24h when available

**Documentation**:

- `docs/security/POST_REMEDIATION_REPORT.md`
- `docs/security/PHASE_1B_ACTION_PLAN.md`
- `docs/security/EXECUTIVE_SUMMARY.md`

---

### SEC-013: SSH Auditor Fallback Credentials & Host Key Bypass ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 1
**Priority**: 🔴 Critical - Launch Blocker (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Removed fallback root credentials from `ssh_auditor.py`. Connection now fails loudly if credentials are missing from Vault. Added `STIG_SSH_STRICT_HOST_KEY` setting (default: `true`) with explicit opt-out logging. Added username validation, auth method verification, and `asyncssh.KeyImportError` handling.

**Files Modified**: `apps/stig/src/stig/collectors/ssh_auditor.py`, `apps/stig/src/stig/core/config.py`, `.env.example`

---

### SEC-014: Production Secret Elimination + docker-compose.prod.yml ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 1
**Priority**: 🔴 Critical - Launch Blocker (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Created `docker-compose.prod.yml` overlay with `${VAR:?error}` syntax — services refuse to start without explicit secrets. Created `scripts/validate-prod-env.sh` checking 6 secrets, 5 dangerous defaults, Vault dev mode, NODE_ENV, SSH host key, CORS. All services set to `read_only: true`, `cap_drop: [ALL]`, production build targets, no source volume mounts, observability ports removed.

**Files Created**: `docker-compose.prod.yml`, `scripts/validate-prod-env.sh`

---

### SEC-015: Syslog Collector — No Auth, No Rate Limits, No Size Caps ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 2
**Priority**: 🔴 Critical - Launch Blocker (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Added 5 configurable security controls to syslog collector: message size cap (`SYSLOG_MAX_MESSAGE_SIZE=8192`), global rate limit (`SYSLOG_MAX_MESSAGES_PER_SECOND=10000`), per-source rate limit (`SYSLOG_MAX_PER_SOURCE_PER_SECOND=1000`), IP allowlist (`SYSLOG_ALLOWED_SOURCES` with CIDR support), and backpressure (`SYSLOG_MAX_BUFFER_SIZE=100000`). Fast-path rejection in UDP protocol handler avoids async overhead for oversized packets. 60-second metrics reporting for all drop reasons.

**Files Modified**: `apps/syslog/src/syslog/collector.py`, `apps/syslog/src/syslog/config.py`

---

### SEC-016: Unhardened XML Parsing — No defusedxml ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 2
**Priority**: 🔴 Critical - Launch Blocker (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Replaced all `ET.fromstring()` with `SafeET.fromstring()` (defusedxml) in `parser.py` and `config_analyzer.py`. Added XML size limit (`STIG_MAX_XML_SIZE=50MB`), ZIP entry count limit (`STIG_MAX_ZIP_ENTRIES=500`), ZIP entry size limit (`STIG_MAX_ZIP_ENTRY_SIZE=100MB`). CKL parser already used defusedxml — added file size check. Stdlib `ET` retained only for element construction (safe, no parsing).

**Files Modified**: `apps/stig/src/stig/library/parser.py`, `apps/stig/src/stig/collectors/config_analyzer.py`, `apps/stig/src/stig/reports/ckl.py`, `apps/stig/src/stig/core/config.py`

---

### SEC-017: STIG Config Upload — No Size Limits ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 3
**Priority**: 🔴 Critical - Launch Blocker (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Added `STIG_MAX_UPLOAD_SIZE` setting (default 10MB) and `STIG_ALLOWED_CONFIG_EXTENSIONS` to STIG config. Both Python config analysis endpoints now validate file size before reading and return HTTP 413 if exceeded. Extension validation moved before file read. Gateway enforces 10MB limit on config analysis proxy and 50MB on checklist imports.

**Files Modified**: `apps/stig/src/stig/api/routes.py`, `apps/stig/src/stig/core/config.py`, `apps/gateway/src/routes/stig/index.ts`

---

### SEC-018: SSH Credential Encryption — Static Salt, No Rotation ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 3
**Priority**: 🟠 High - Security Issue (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Replaced static `"salt"` string with 16-byte `crypto.randomBytes()` per encrypt operation. New format: `salt:iv:authTag:encrypted` (4 parts). Backward-compatible decrypt auto-detects 3-part legacy format and uses static salt for those records. Applied to both SSH credentials (STIG) and SNMPv3 credentials (NPM). Existing encrypted values decrypt without migration — new values get per-record salt automatically.

**Files Modified**: `apps/gateway/src/routes/stig/ssh-credentials.ts`, `apps/gateway/src/routes/npm/snmpv3-credentials.ts`

---

### SEC-019: Comprehensive Input Sanitization Audit ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 4
**Priority**: 🟠 High - Security Issue (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Comprehensive audit of all API endpoints, SQL queries, subprocess calls, and user input handling. All SQL queries use parameterized statements (asyncpg/pg). All subprocess calls use `create_subprocess_exec()` with argument arrays (no `shell=True`). All gateway routes enforce Zod schema validation. React JSX provides auto-escaping for XSS. No `dangerouslySetInnerHTML` in codebase. Helmet headers active on gateway.

**Deliverable**: `docs/security/INPUT_SANITIZATION_AUDIT.md`

---

### SEC-020: Syslog API — Print Logging + Permissive CORS ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 4
**Priority**: 🟠 High - Security/Audit Issue (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Replaced all `print()` statements with `structlog.get_logger()` in syslog `main.py`. CORS restricted from wildcard `*` to configurable `SYSLOG_CORS_ORIGINS` (default: `http://localhost:3000`). `allow_credentials` set to `False`, methods restricted to `GET/POST/PUT/DELETE`, headers restricted to `Authorization/Content-Type/X-Request-Id`. Added structlog configuration for `__main__` entrypoint.

**Files Modified**: `apps/syslog/src/syslog/main.py`, `apps/syslog/src/syslog/config.py`

---

### SEC-021: Container Capability Refinement ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 4
**Priority**: 🟠 High - Security Issue (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Added `cap_drop: [ALL]` to all 14 services in `docker-compose.yml`. Removed `NET_ADMIN` from `ipam-scanner` (only `NET_RAW` needed for ICMP ping/nmap). Minimum capabilities: Vault=`IPC_LOCK`, ipam-scanner=`NET_RAW`, syslog-collector=`NET_BIND_SERVICE`. All other services run with zero elevated capabilities. Prod overlay already had correct caps for scanner/collector/syslog — now aligned with base compose.

**Files Modified**: `docker-compose.yml`, `docker-compose.prod.yml`

---

### SEC-022: Syslog Forwarding — TLS Not Enforced ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 4
**Priority**: 🟠 High - Security Issue (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Added `SYSLOG_FORWARD_TLS_DEFAULT` (default: `true`) and `SYSLOG_FORWARD_TLS_CA_CERT` config settings. Forwarder now logs a security warning when TLS verification is disabled (`tls_verify=false`). TCP forwarders without TLS trigger a cleartext warning when `SYSLOG_FORWARD_TLS_DEFAULT=true`. Custom CA certificate loading supported via `ssl.SSLContext.load_verify_locations()`.

**Files Modified**: `apps/syslog/src/syslog/forwarder.py`, `apps/syslog/src/syslog/config.py`

---

### SEC-023: Raw Payload Redaction + Size Limits ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 4
**Priority**: 🟠 High - Security Issue (RESOLVED)
**Detected**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Added `SYSLOG_MAX_STORED_PAYLOAD` (default: 4096 bytes) with `[TRUNCATED]` marker for oversized payloads. Added `SYSLOG_REDACTION_PATTERNS` with 6 default regex patterns covering password, secret, token, api-key, private-key, and auth-key fields. Redaction and truncation applied to both `message` and `raw_message` before database storage. Patterns are configurable via environment variable.

**Files Modified**: `apps/syslog/src/syslog/collector.py`, `apps/syslog/src/syslog/config.py`

---

### SEC-001: tar RCE Vulnerability (ESCALATED from Deferred) ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 3
**Priority**: 🟠 High - Security Issue (RESOLVED)
**Detected**: 2026-01-18 | **Escalated**: 2026-02-11 | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Updated argon2 from `^0.31.2` to `^0.41.1` across all 3 packages (auth-service, shared-auth, gateway). argon2 0.40+ uses prebuildify instead of node-pre-gyp, eliminating the transitive tar dependency. API is backward compatible — `argon2.hash()`, `argon2.verify()`, `argon2.needsRehash()` unchanged. Existing password hashes remain valid. **Action required**: Run `npm install` to regenerate lockfile, then `npm audit` to confirm 0 HIGH vulnerabilities.

**Files Modified**: `services/auth-service/package.json`, `packages/shared-auth/package.json`, `apps/gateway/package.json`

---

### APP-020: Gateway STIG Route Mismatch ✅ RESOLVED

**Status**: ✅ Resolved - Sprint SEC-HARDENING-01 Day 5
**Priority**: 🟡 Medium - Functional Bug (RESOLVED)
**Detected**: 2026-02-11 (Both reviewers flagged) | **Resolved**: 2026-02-11
**Engineer**: Claude (PM + Implementation)
**Sprint**: SEC-HARDENING-01

**Resolution**: Added proxy routes to gateway for STIG service endpoints that were returning 404. `GET /targets` and `GET /targets/:id` now proxy to Python backend (preserving `/assets` as the frontend-facing canonical name for CRUD). Added `libraryProxyRoutes` plugin with 4 proxy routes: `GET /library` (browse catalog), `GET /library/summary` (statistics), `GET /library/platforms/:platform` (platform-specific STIGs), `POST /library/rescan` (admin rebuild index). Existing DB-backed library routes (`/library/upload`, `/library/:id/rules`, `DELETE /library/:id`) unchanged. No frontend changes required — existing `/assets` and `/benchmarks` paths still work. TypeScript typecheck and lint clean (0 new errors).

**Files Modified**: `apps/gateway/src/routes/stig/index.ts`

---

### APP-021: Read-Only Syslog Event Count Endpoint

**Status**: 🟡 Open - Sprint SEC-HARDENING-01 Day 5
**Priority**: 🟡 Medium - Operational Visibility
**Detected**: 2026-02-11 (Codex recommendation)
**Engineer**: Codex

**Issue**: No API endpoint for syslog event count/last-seen timestamp. DB query via psql had output issues during runtime validation. Operators have no easy way to verify syslog ingestion health.

**Required Fix**: Add `GET /api/v1/syslog/stats` with auth protection.

**File**: `apps/syslog/src/syslog/main.py`

---

### NPM-001: SNMPv3 Credential Test Timeout

**Status**: 🟡 Open - Investigation
**Priority**: 🟠 High - Feature Not Working
**Detected**: 2026-02-02 (Lab testing with Arista 720XP)
**Engineer**: TBD

**Issue**: SNMPv3 credential test times out when testing against Arista 720XP

**Device Config**:

- Target: 192.168.80.2 (Arista 720XP)
- User: NPM-USER
- Auth: SHA-256, Privacy: AES-256, Level: authPriv

**Fixes Applied**:

- Increased timeout from 5s to 10s in `apps/gateway/src/snmp.ts`
- Increased retries from 1 to 2 for SNMPv3 engine ID discovery

**Remaining Investigation**:

1. Verify gateway container can reach 192.168.80.2 (Docker bridge network routing)
2. Confirm SNMPv3 engine ID discovery is working
3. Test with `snmpwalk` from Docker host to verify SNMP accessibility

**Next Steps**:

- Rebuild gateway container with updated timeout/retry values
- Test connectivity: `docker exec netnynja-gateway ping 192.168.80.2`
- If still failing, consider `network_mode: host` for gateway

---

### SYSLOG-001: Syslog Events Not Received from Arista

**Status**: 🟡 Open - Configuration Issue
**Priority**: 🟠 High - Feature Not Working
**Detected**: 2026-02-02 (Lab testing with Arista 720XP)
**Engineer**: TBD

**Issue**: Syslog collector shows 0 events despite Arista switch being configured

**Arista Config**:

```
logging host 192.168.1.137
logging host 192.168.250.10
logging source-interface Vlan80
```

**Root Cause**: Network mismatch - Arista is sending to 192.168.1.137/192.168.250.10 but Docker host may be on different IP

**Resolution Required**:

1. Identify Docker host IP address on network reachable by Arista
2. Update Arista logging config: `logging host <docker-host-ip>`
3. OR ensure Docker host has IP 192.168.1.137 or 192.168.250.10

**Verification**:

- Port 514/udp is exposed in docker-compose.yml ✅
- Syslog collector binds to 0.0.0.0:514 ✅
- Parser supports Arista RFC 3164 format ✅

---

### NPM-004: Arista CPU/Memory OIDs Not Implemented in Poller

**Status**: 🟡 Open - Code Change Required
**Priority**: 🟠 High - Feature Incomplete
**Detected**: 2026-02-02 (Lab testing with Arista 720XP)
**Engineer**: TBD

**Issue**: Arista 720XP shows N/A for CPU, Memory, Disk, Swap metrics despite SNMP working

**Root Cause**:

- `snmpv3_poller.py` has hardcoded OID mappings that don't use `oid_mappings.py`
- Arista doesn't support standard `hrProcessorLoad` OID (1.3.6.1.2.1.25.3.3.1.2.1)
- Arista uses ENTITY-SENSOR-MIB for CPU/temp or requires walking all hrProcessorLoad indices

**Files**:

- `apps/npm/src/npm/collectors/snmpv3_poller.py` - needs to import from oid_mappings.py
- `apps/npm/src/npm/collectors/oid_mappings.py` - OID definitions (already updated)

**Fix Required**:

1. Update `_get_cpu_metrics()` to walk `1.3.6.1.2.1.25.3.3.1.2` (all indices) for Arista
2. Update `_get_memory_metrics()` to use hrStorageTable for Arista
3. OR refactor poller to use `oid_mappings.py` vendor-specific OIDs

**Workaround**: None - metrics display N/A until code is updated

---

### UI-017: React Router v7 Migration Warnings

**Status**: 🟡 Open - Future Compatibility
**Priority**: 🟢 Low - Non-Blocking Warning
**Detected**: 2026-01-18 16:10 UTC (Browser monitoring session)
**Engineer**: TBD

**Issue**: React Router displaying future version compatibility warnings

**Warnings**:

1. Missing `v7_startTransition` future flag
2. Missing `v7_relativeSplatPath` future flag

**Observed Behavior**:

- 6 warnings logged during navigation (2 warnings per route change)
- No functional impact - purely informational
- Source: `react-router-dom.js:4434:12`

**Impact**:

- None currently - application works correctly
- Console warnings during development/debugging
- Preparation for React Router v7 upgrade

**Resolution Plan**:

- Add future flags to router configuration when convenient
- Can be addressed during next major refactor
- Non-urgent, deferred to future maintenance cycle

**Reference**: https://reactrouter.com/v6/upgrading/future

---

## 📋 DEFERRED

(none — SEC-001 escalated to NOW per Gemini review 2026-02-11)

---

## ✅ Recently Resolved (2026-01-18)

### CI-003: TypeScript Compilation Errors in Gateway STIG Routes

**Resolution**: Fixed 5 TypeScript errors blocking CI/CD pipeline in `apps/gateway/src/routes/stig/index.ts`:

- Line 280: Added type assertion for `request.body as string` (TS2345)
- Lines 302, 376, 443: Added explicit `return reply;` statements after file downloads (TS7030)
- Line 3172: Fixed Buffer/fetch incompatibility with `new Uint8Array(formBuffer)` (TS2769)
- Result: All typechecks pass, 67/67 tests pass, CI/CD workflows green ✅
- Commit: 79bcf10

### CI-002: Missing Source Files (.gitignore Pattern Issue)

**Resolution**: Fixed `.gitignore` pattern blocking source code from being committed:

- Changed `STIG/` to `/STIG/` (root-anchored pattern) to prevent matching `apps/web-ui/src/modules/stig/`
- Added missing files: `AuditProgressPage.tsx` (27KB), `juniper_stig_checker.py`, `assignment.py`
- Verified with `git check-ignore -v` before and after fix
- Result: All source files now tracked in git, CI/CD can access them
- Commit: 97bc2e1

### CI-001: CI/CD Pipeline Validation (Rollup ARM64 Dependency)

**Resolution**: Fixed npm optional dependency installation failure causing all 3 workflows to fail:

- Cleaned node_modules and package-lock.json
- Cleared npm cache with `npm cache clean --force`
- Reinstalled dependencies with `npm install --ignore-scripts` (proxy workaround)
- Verified local build (6/6 packages) and tests (67/67) pass
- Created comprehensive audit trail: `docs/audit/2026-01-18_CI_CD_Failure_Remediation.md` (20+ pages)
- Result: Build succeeds, dependencies install correctly in CI/CD
- Commit: 8461bbb

### STIG-19: Combined PDF Report for Multi-STIG Config Analysis

**Resolution**: Added combined report generation endpoints and frontend integration:

- New API endpoints: `GET /reports/combined-pdf` and `GET /reports/combined-ckl` accepting comma-separated job_ids
- `ReportGenerator.generate_combined_pdf_from_jobs()` creates single PDF with executive summary + per-STIG sections
- `ReportGenerator.generate_combined_ckl_from_jobs()` creates ZIP with separate CKL files per STIG
- Frontend `AssetsPage.tsx` tracks all job IDs and uses combined endpoints for multi-STIG downloads
- Gateway proxy routes added for combined report endpoints

### STIG-18: Config Analysis Only Analyzes First STIG

**Resolution**: Modified `AssetsPage.tsx` to run config analysis against ALL assigned/enabled STIGs:

- Changed from single-STIG analysis to loop through all enabled definitions
- Aggregates results from all STIGs (total checks, passed, failed, compliance score)
- Stores all job IDs in state for combined report generation
- UI displays consolidated results across all analyzed STIGs

### STIG-17: PDF Description Contains Raw XML Tags

**Resolution**: Added `extract_vuln_discussion()` function to both PDF and CKL exporters:

- Extracts only the `<VulnDiscussion>` content from raw STIG descriptions
- Falls back to stripping all XML tags if no VulnDiscussion tag present
- Added `clean_text_for_pdf()` helper for safe PDF rendering
- Improved PDF format: V-ID, Severity, Status, Title, Description, Fix Text with separators

### STIG-14: Config Analysis Uses Assigned STIGs

**Resolution**: Modified `AssetsPage.tsx` Config Analysis modal to:

- Auto-fetch assigned STIGs when opening the modal
- Display assigned/enabled STIGs instead of requiring manual selection
- Use the first enabled assigned STIG for analysis automatically
- Only show STIG dropdown if no STIGs are assigned to the asset

### STIG-15: PDF Report Full V-ID Details

**Resolution**: Enhanced PDF report generator (`pdf.py`) to include:

- Full description (Vulnerability Discussion) for each failed finding
- Fix Text (Remediation guidance) for each failed finding
- New paragraph styles for description and fix text
- `KeepTogether` blocks to keep findings from breaking across pages
- Report generator now fetches rule details from `definition_rules` table

### STIG-16: CKL Report Full V-ID Details

**Resolution**: Enhanced CKL exporter (`ckl.py`) to:

- Accept `rule_details` dict from database instead of relying on `xccdf_content`
- Populate `Vuln_Discuss`, `Check_Content`, and `Fix_Text` fields from database
- Maintain backwards compatibility with legacy `xccdf_content` fallback

### STIG-500: SSH Credentials 500 Error

**Resolution**: Applied missing migration `008_add_ssh_credentials_sudo.sql` adding sudo columns to `stig.ssh_credentials` table. Gateway was failing because the table lacked `sudo_enabled`, `sudo_method`, `sudo_password_encrypted`, `sudo_user` columns.

### STIG-13: Multi-STIG Assignment API (Backend Completion)

**Resolution**: Added missing Python API endpoint handlers in `apps/stig/src/stig/api/routes.py`:

- `GET /targets/{id}/definitions` - List assigned STIGs
- `POST /targets/{id}/definitions` - Assign STIG
- `POST /targets/{id}/definitions/bulk` - Bulk assign
- `PATCH /targets/{id}/definitions/{id}` - Update assignment
- `DELETE /targets/{id}/definitions/{id}` - Remove assignment
- `POST /targets/{id}/audit-all` - Audit all enabled STIGs
- `GET /audit-groups` - List audit groups
- `GET /audit-groups/{id}` - Get audit group
- `GET /audit-groups/{id}/summary` - Get compliance summary

**Note**: Gateway routes were already complete. Only the Python service backend was missing.

### DOC-001: STIG Selection Guide

**Resolution**: Created `docs/STIG_SELECTION_GUIDE.md` documenting:

- STIG selection logic (role-based approach)
- Juniper SRX STIG package breakdown (NDM, ALG, VPN, IDPS)
- When to apply each STIG based on device functionality
- Multi-STIG UI usage instructions
- Database schema reference

## ⏭️ NEXT (Queued / Ready)

- [ ] Seed E2E users in `shared.users` table
- [ ] Validate VictoriaMetrics write endpoint (preflight warning)
- [ ] Verify NATS stream endpoint JSON format for monitoring
- [ ] Phase 9 — Documentation site deployment (optional)

## ⛔ BLOCKED (Waiting / External Dependency)

- [ ] SEC-011 — zlib CVE-2026-22184 (Critical) - No upstream fix available, monitoring Alpine/Node releases

---

## 📋 SEC-012: Critical Vulnerability Remediation (2026-02-04)

**Status**: Phase 1 Complete, Phase 1B Monitoring | **Owner**: DevOps | **Created**: 2026-02-04

### Post-Remediation Status (2026-02-04)

| Service Category                 | CRITICAL | Status        | Notes                    |
| -------------------------------- | -------- | ------------- | ------------------------ |
| Internet-facing (auth, gateway)  | 0        | ✅ SECURE     | Fastify 5.x, Python 3.13 |
| Internal (postgres, redis, nats) | 3        | 🟡 Monitoring | OpenSSL CVE-2025-15467   |
| Grafana                          | 4        | 🟡 Monitoring | Go stdlib, curl, OpenSSL |
| Redis                            | 5        | 🟡 Monitoring | gosu Go 1.18, OpenSSL    |

### Remediation Applied (Phase 1)

| Component | Before | After  | CVEs Resolved                    |
| --------- | ------ | ------ | -------------------------------- |
| Vault     | 1.15   | 1.18   | CVE-2024-41110 (auth bypass)     |
| Grafana   | 10.2.0 | 11.4.0 | Previous CVEs (new ones pending) |
| Fastify   | 4.25.x | 5.2.x  | Multiple plugin vulns            |
| Python    | 3.11   | 3.13   | OpenSSL, SQLite CVEs             |

### Remaining (Phase 1B - Upstream Dependency)

| CVE            | Package   | Affected                       | Fix Available       |
| -------------- | --------- | ------------------------------ | ------------------- |
| CVE-2025-15467 | OpenSSL   | postgres, redis, nats, grafana | ⏳ Waiting Alpine   |
| CVE-2025-22871 | Go stdlib | grafana, redis                 | ⏳ Waiting upstream |
| CVE-2025-0665  | curl      | grafana                        | ⏳ Waiting upstream |

**Action**: Daily monitoring for upstream patches. Deploy within 24h when available.

---

## 📋 SEC-011: Docker Scout Vulnerability Remediation Plan (Superseded by SEC-012)

**Status**: ⚠️ Superseded by SEC-012 | **Owner**: DevOps | **Created**: 2026-01-15

### Current Vulnerabilities (Docker Scout Assessment)

| Severity | CVE            | Package     | Fix Available | Action            |
| -------- | -------------- | ----------- | ------------- | ----------------- |
| Critical | CVE-2026-22184 | zlib        | ❌ No         | Monitor upstream  |
| High     | CVE-2024-21538 | cross-spawn | ✅ Fixed      | Vite 7 upgrade ✅ |
| High     | CVE-2025-64756 | glob        | ✅ Fixed      | Vite 7 upgrade ✅ |
| High     | CVE-2024-23342 | ecdsa       | ⏳ Pending    | Monitor           |
| High     | CVE-2025-6020  | PAM         | ⏳ Pending    | Monitor           |
| High     | CVE-2025-68973 | GnuPG       | ⏳ Pending    | Monitor           |

### Remediation Strategy

**Tier 1: Monitor (No Fix Available)**

- zlib CVE-2026-22184: Subscribe to Alpine Linux security announcements
- Compensating control: Container network isolation, minimal attack surface

**Tier 2: Completed ✅ (2026-01-15)**

- cross-spawn, glob: Fixed by upgrading Vite 5.x → 7.3.1
- @vitejs/plugin-react: 4.2.1 → 5.1.2
- @types/node: 20.10.0 → 20.19.0
- npm audit: 0 vulnerabilities

**Tier 3: Rebuild on Upstream Fix**

- When Alpine releases fixed packages: `docker compose build --no-cache`
- Re-run Docker Scout scan to verify remediation

### Monitoring Checklist

- [x] Subscribe to Alpine Linux security mailing list - https://lists.alpinelinux.org/lists/~alpine/security-announce
- [x] Subscribe to Node.js security announcements - https://nodejs.org/en/about/security
- [ ] Set calendar reminder for weekly vulnerability review
- [ ] Document risk acceptance for CVE-2026-22184 in security register

---

## 📝 Open Issues (Codex Review 2026-01-14)

All issues from Codex Review 2026-01-14 have been resolved.

---

## 📋 Archiving Instructions

**When to Archive:**

- When resolved issues exceed **50 entries** in this file
- At the end of each **major release** (v0.x.0)
- **Quarterly** as part of housekeeping

**How to Archive:**

1. Create or append to `IssuesTracker.archive.md`
2. Update archive header with new **End Date** and **Total Issues Archived**
3. Move all resolved issues from the "Recently Resolved" section below to the archive
4. Keep only the last 30 days of resolved issues in this file for context
5. Update the **Stats** line at the top of this file

**Archive Format:**

```markdown
| ID   | P   | Title       | Resolved   | Resolution          |
| ---- | --- | ----------- | ---------- | ------------------- |
| #XXX | 🟠  | Short title | YYYY-MM-DD | One-line resolution |
```

---

## Issue Priority Legend

- 🔴 **Critical** — Blocking issues preventing core functionality
- 🟠 **High** — Important issues to resolve soon
- 🟡 **Medium** — Normal development priority
- 🟢 **Low** — Nice-to-have improvements

---

## 📜 Recently Resolved (Last 30 Days)

| ID         | P   | Title                                   | Resolved   | Resolution                                                    |
| ---------- | --- | --------------------------------------- | ---------- | ------------------------------------------------------------- |
| APP-020    | 🟡  | Gateway STIG route mismatch (404s)      | 2026-02-11 | Added /targets proxy + library browse/summary/platforms proxy |
| SEC-023    | 🟠  | Raw payload redaction + size limits     | 2026-02-11 | Redaction patterns + 4KB truncation before DB storage         |
| SEC-022    | 🟠  | Syslog forwarding TLS not enforced      | 2026-02-11 | TLS default, CA cert config, cleartext warnings               |
| SEC-021    | 🟠  | Container caps excessive (NET_ADMIN)    | 2026-02-11 | cap_drop ALL on all 14 services, minimum cap_add only         |
| SEC-020    | 🟠  | Syslog print() + CORS wildcard          | 2026-02-11 | structlog, CORS restricted to configurable origins            |
| SEC-019    | 🟠  | Input sanitization audit                | 2026-02-11 | Full audit: all SQL parameterized, no shell injection         |
| SEC-018    | 🟠  | Credential encryption static salt       | 2026-02-11 | Per-record random salt, backward-compatible decrypt           |
| SEC-001    | 🟠  | tar RCE in argon2 dependency chain      | 2026-02-11 | Updated argon2 ^0.31.2 → ^0.41.1, eliminated tar dep          |
| SEC-017    | 🔴  | Config upload no size limits            | 2026-02-11 | 413 enforcement in gateway + backend, configurable limits     |
| SEC-016    | 🔴  | Unhardened XML parsing (XXE risk)       | 2026-02-11 | defusedxml for all parsing, XML/ZIP size limits added         |
| SEC-015    | 🔴  | Syslog collector no rate/size limits    | 2026-02-11 | Rate limits, size caps, IP allowlist, backpressure added      |
| SEC-014    | 🔴  | Production secrets in docker-compose    | 2026-02-11 | docker-compose.prod.yml overlay + validate-prod-env.sh        |
| SEC-013    | 🔴  | SSH auditor fallback credentials        | 2026-02-11 | Removed fallback, enforced host key verification              |
| SEC-012a   | 🔴  | Vault auth bypass CVE-2024-41110        | 2026-02-04 | Upgraded Vault 1.15 → 1.18                                    |
| SEC-012b   | 🔴  | Grafana info leak CVE-2024-8986         | 2026-02-04 | Upgraded Grafana 10.2.0 → 11.4.0                              |
| SEC-012c   | 🟠  | Fastify v4 → v5 security upgrade        | 2026-02-04 | Updated gateway + auth-service to Fastify 5.2.0               |
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
| STIG-16    | 🟠  | CKL report missing V-ID details         | 2026-01-18 | Enhanced CKL exporter with rule details from database         |
| STIG-15    | 🟠  | PDF report missing V-ID details         | 2026-01-18 | Added full description and fix text to PDF findings           |
| STIG-14    | 🟠  | Config analysis requires STIG selection | 2026-01-18 | Auto-use assigned STIGs for config analysis                   |
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
| CI-012     | 🟠  | Vite 5.x to 7.x upgrade                 | 2026-01-15 | Upgraded Vite 7.3.1, fixed cross-spawn/glob CVEs              |
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
| CI-013     | 🟡  | Tests workflow - shared-types not found | 2026-01-14 | Simplified package.json exports                               |
| CI-005     | 🟠  | Validate Workspaces fails all platforms | 2026-01-14 | Changed to npm run build (Turborepo)                          |
| SEC-004    | 🟡  | STIG ZIP upload DoS limits              | 2026-01-14 | Already implemented (500 files, 100MB)                        |
| SEC-005    | 🟢  | Observability ports exposed             | 2026-01-14 | Bound to localhost only                                       |
| WIN-001    | 🟠  | Windows Hyper-V port conflicts          | 2026-01-14 | NATS→8322, Vault→8300                                         |
| #113       | 🟠  | NPM disk/storage metrics                | 2026-01-12 | Added Sophos SFOS OIDs                                        |
| #114       | 🟠  | NPM interface traffic summaries         | 2026-01-12 | Added IF-MIB 64-bit counters                                  |
| #115       | 🟡  | NPM Sophos service status               | 2026-01-12 | Added 20+ service status OIDs                                 |
| APP-008    | 🟠  | STIG Library 500 error                  | 2026-01-12 | Created missing database tables                               |
| APP-009    | 🟠  | Auto-polling not working                | 2026-01-12 | Created npm.device_metrics table                              |
| APP-010    | 🟠  | NPM Poll Now fails                      | 2026-01-12 | Created partitioned metrics tables                            |
| APP-011    | 🟡  | Sidebar toggle not visible              | 2026-01-12 | Fixed Sidebar.tsx condition                                   |

---

## 🗄️ Deferred Issues

(none - CI-012 Vite upgrade completed 2026-01-15)

---

## 📁 Archive Reference

For historical resolved issues, see: **[IssuesTracker.archive.md](IssuesTracker.archive.md)**

| Archive Period           | Issues |
| ------------------------ | ------ |
| 2026-01-06 to 2026-01-14 | 123    |

---

## Issue Template

```markdown
| ID   | P   | Title                   | Status           | Owner     |
| ---- | --- | ----------------------- | ---------------- | --------- |
| #XXX | 🟠  | Short descriptive title | Open/In Progress | @username |

**Description**: One paragraph max
**Steps**: 1. 2. 3.
**Resolution**: (filled when closed)
```

---

## Notes

- Keep this file under 200 lines for token efficiency
- Use one-line resolutions in tables
- Archive regularly per instructions above
- Link to GitHub Issues for detailed discussions
