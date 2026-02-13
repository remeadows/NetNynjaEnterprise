# CLAUDE COWORK SKILLS CHECK — NetNynjaEnterprise

**Timestamp**: 2026-02-13 16:21 UTC
**Analyst**: Claude (Cowork Orchestration Layer)
**Scope**: CLAUDE_ENTERPRISE_SKILL.md, CLAUDE.md, CONTEXT.md, PROJECT_STATUS.md, IssuesTracker.md, GO.md, codebase review
**Method**: Document cross-reference + codebase grep + structural analysis

---

## SECTION 1: IDENTIFIED ISSUES (7 Found)

---

### ISSUE 1: CLAUDE_ENTERPRISE_SKILL.md Stack Bias Does Not Match Actual Architecture

**Severity**: HIGH — Agent Drift Risk
**Files**: `CLAUDE_ENTERPRISE_SKILL.md` (§1, §5), `CLAUDE.md`, `CONTEXT.md`

The skill doc defines a "default stack bias" of **FastAPI (Python)** as the backend framework (§1 line 21, §5 line 99). It dedicates an entire section (§5) to "PYTHON ENGINEERING STANDARD (FASTAPI)" including async I/O discipline, layering patterns, and persistence rules.

**Reality**: The actual gateway — the central API surface — is **Fastify (Node.js/TypeScript)**, not FastAPI. Python services are *backend workers* behind the gateway, not the API layer. CLAUDE.md correctly documents `Node.js 20+ / Fastify 5.x / TypeScript 5.3+` as the API Gateway stack.

**Impact**: Any agent that ingests CLAUDE_ENTERPRISE_SKILL.md first (which GO.md doesn't even list in its ingest order) may produce FastAPI code for gateway-level work, or attempt to restructure the gateway as Python. This directly contradicts the actual architecture and will cause Codex/Claude to generate wrong-stack artifacts.

**Fix**: Add a section to CLAUDE_ENTERPRISE_SKILL.md that explicitly acknowledges the hybrid stack: "Gateway = Fastify/TypeScript, Workers = Python/FastAPI" and update §5 to scope its guidance to Python worker services only.

---

### ISSUE 2: Document Ingest Order Conflict Between GO.md and AGENTS.md

**Severity**: HIGH — Agent Execution Ambiguity
**Files**: `GO.md`, `AGENTS.md`

GO.md (§MANDATORY INGEST ORDER) specifies:
```
1. AGENTS.md
2. CLAUDE.md
3. CONTEXT.md
4. PROJECT_STATUS.md
5. IssuesTracker.md
6. README.md
7. COMMIT.md
```

AGENTS.md (§1 Mandatory Startup Sequence) specifies:
```
1. GO.md
2. AGENTS.md
3. CLAUDE.md
4. CONTEXT.md
5. PROJECT_STATUS.md
6. IssuesTracker.md
7. README.md
```

These are contradictory. GO.md says "start with AGENTS.md" but AGENTS.md says "start with GO.md." COMMIT.md appears in GO.md's list but not AGENTS.md. GO.md itself is absent from its own list. Neither list includes `CLAUDE_ENTERPRISE_SKILL.md`.

**Impact**: Agents choose whichever file they encounter first, creating non-deterministic startup behavior. The AGENTS.md §2 conflict resolution hierarchy doesn't address this circular dependency.

**Fix**: Unify into a single canonical sequence in AGENTS.md. GO.md should contain ONLY the execution objectives (outputs 1-3) and defer startup sequence entirely to AGENTS.md. Add CLAUDE_ENTERPRISE_SKILL.md to the ingest order explicitly.

---

### ISSUE 3: CLAUDE.md Version Drift — Stale Technology Versions

**Severity**: MEDIUM — Documentation Accuracy
**Files**: `CLAUDE.md`, `PROJECT_STATUS.md`, `CONTEXT.md`

CLAUDE.md §Technology Standards still lists:
- `Fastify 4.25` — **Actual: Fastify 5.2.0** (upgraded 2026-02-04, SEC-012c)
- `Vite 5` — **Actual: Vite 7.3.1** (upgraded 2026-01-15, v0.2.6)
- `Grafana 10.2` — **Actual: Grafana 11.4.0** (upgraded 2026-02-04, SEC-012b)
- `Python 3.11+` — **Actual: Python 3.13** (upgraded 2026-02-04, SEC-012d)

CONTEXT.md was partially updated (Vite 7.3 correct) but still shows `Fastify` without version in the architecture table.

**Impact**: CLAUDE.md is listed as the #3 source-of-truth per AGENTS.md §2. Agents that ingest CLAUDE.md will target deprecated versions, generate incompatible plugin code (Fastify 4 vs 5 has breaking API changes), or pin wrong base images.

**Fix**: Update CLAUDE.md §Technology Standards to match production reality. Add a "Last Verified" date to the technology table.

---

### ISSUE 4: package.json Version Frozen at 0.1.0 While PROJECT_STATUS Reports 0.2.15

**Severity**: MEDIUM — Version Integrity
**Files**: `package.json`, `pyproject.toml`, `PROJECT_STATUS.md`

Both `package.json` and `pyproject.toml` declare `version: "0.1.0"`. PROJECT_STATUS.md reports the current version as **0.2.15** with a full changelog from 0.2.3 through 0.2.15. CONTEXT.md reports **0.2.6**.

This means:
- No code artifact actually carries the version the docs claim
- Container images tagged with version numbers don't match the source manifest
- `npm version` / `poetry version` commands will produce wrong output
- Any CI/CD pipeline that reads version from package.json will stamp artifacts as 0.1.0

**Impact**: Version traceability is broken. If you deploy, the binary says 0.1.0 while the docs say 0.2.15. This fails DoD RMF CM-3 (configuration change control) and SI-7 (software integrity) controls that the project explicitly claims compliance with.

**Fix**: Bump package.json and pyproject.toml to 0.2.15. Add a `version-check` CI step that validates docs match manifests.

---

### ISSUE 5: CLAUDE_ENTERPRISE_SKILL.md "GRIDWATCH-STYLE" Brand Leak

**Severity**: MEDIUM — Brand Coherence / Agent Confusion
**Files**: `CLAUDE_ENTERPRISE_SKILL.md` (§7, §17)

Section 7 header reads: `## 7) MODULE BLUEPRINTS (GRIDWATCH-STYLE)`
Section 17 (North Star) reads: `Build NetNynja-class systems`

"GridWatch" appears nowhere else in the codebase. This is a leaked reference to the planned rename (or a prior project name) inside a governance document that agents actively consume. Meanwhile, the North Star still references "NetNynja."

**Impact**: Agents parsing this doc encounter an undefined brand ("GridWatch") with no context. It creates ambiguity about project identity and signals that the skill doc was adapted from another project without full sanitization.

**Fix**: Either replace "GRIDWATCH-STYLE" with "NETNYNJA-STYLE" (if rename hasn't happened) or do the full rename (see Section 3 below). Remove the inconsistency.

---

### ISSUE 6: CLAUDE_ENTERPRISE_SKILL.md Recommends a Different Repo Structure Than What Exists

**Severity**: MEDIUM — Architectural Drift
**Files**: `CLAUDE_ENTERPRISE_SKILL.md` (§12), `CLAUDE.md`, actual repo

The skill doc §12 proposes:
```
services/api/        # FastAPI
services/worker/     # collectors
services/ui/         # React/Vite
infra/compose/
libs/common/
libs/device_clients/
db/migrations/
```

The actual repo uses:
```
apps/gateway/        # Fastify (TypeScript)
apps/web-ui/         # React/Vite
apps/ipam/           # Python workers
apps/npm/            # Python workers
apps/stig/           # Python workers
packages/shared-*/   # TypeScript libs
services/auth-service/
infrastructure/postgres/migrations/
```

These are fundamentally different structures. The skill doc's recommendation is a single-service Python monolith pattern. The actual codebase is a multi-app monorepo with clear TypeScript/Python separation.

**Impact**: If an agent follows the skill doc's §12 layout when creating a new module, it'll drop files in the wrong place, create conflicting directory structures, and break the npm workspace + poetry group organization.

**Fix**: Replace §12 with the actual repo structure from CLAUDE.md, or add a preamble: "The below is a generic template — for THIS repo, see CLAUDE.md §Repository Structure."

---

### ISSUE 7: IssuesTracker.md Exceeds Its Own Archiving Rules

**Severity**: LOW — Token Efficiency / Agent Context Window
**Files**: `IssuesTracker.md`

IssuesTracker.md §Notes states: "Keep this file under 200 lines for token efficiency." The file is currently **746 lines** — 3.7x over its own limit. The "Recently Resolved" section alone contains 80+ entries going back to 2026-01-06, well beyond the "last 30 days" rule. The archiving instructions say to archive when resolved issues exceed 50 entries — there are currently 100+.

**Impact**: Every agent session ingests all 746 lines (43KB), consuming ~10K tokens of context window on historical data that's been resolved. This reduces available context for actual work, especially in Codex and Claude Code which have tighter windows.

**Fix**: Archive resolved issues per the existing instructions. Move everything before 2026-02-01 to `archive/sprint-history/IssuesTracker.archive.md`. Collapse the SEC-012 detail section into a one-line summary with a link.

---

## SECTION 2: INTEROPERABILITY ASSESSMENT

### What's Working Well

- **Gateway ↔ Python services**: Proxy pattern is consistent. Gateway forwards to Python backends with body wrappers (`{"data": {...}}`).
- **NATS subject conventions**: Clean separation by module (`ipam.*`, `npm.*`, `stig.*`, `shared.*`).
- **DB schema namespacing**: PostgreSQL schemas properly isolate modules (`ipam.*`, `npm.*`, `stig.*`, `shared.*`).
- **Auth flow**: Centralized JWT through gateway with Argon2id. Consistent `requireAuth` hook usage.
- **Observability**: Unified Prometheus metrics with `netnynja_` prefix, structured logging, Grafana dashboards per module.
- **Security posture**: Dual review (Codex + Gemini) with full remediation sprint. 191 of 192 issues resolved.

### Interoperability Gaps

1. **Syslog → NPM cross-reference**: CONTEXT.md describes syslog as a domain but the NATS subject table in CLAUDE.md doesn't include syslog subjects. The syslog module operates as a standalone FastAPI service bypassing the gateway for some operations.
2. **No shared Python library**: TypeScript has `@netnynja/shared-auth`, `@netnynja/shared-types`, `@netnynja/shared-ui`. Python services have no equivalent shared package — each service duplicates config patterns, logging setup, and DB connection logic.
3. **DB connection retry**: SYSLOG-001 revealed the syslog collector crashes on startup if Postgres isn't ready (`asyncpg.CannotConnectNowError`). Other Python services likely have the same fragility — no shared retry/backoff pattern exists.

---

## SECTION 3: RENAME DEPENDENCY MAP — NetNynjaEnterprise → GridWatchEnterprise

### 3.1 Rename Scope Summary

| Category | Estimated Occurrences | Complexity |
|---|---|---|
| Documentation (.md files) | 200+ references | Low (find/replace) |
| NPM Package Names (@netnynja/*) | 6 packages × all consumers | HIGH (breaks imports) |
| Python Package Name | 1 (pyproject.toml) | Low |
| Docker Image Names | 14 images × compose + CI | Medium |
| Prometheus Metrics Prefix | 80+ metric names | HIGH (breaks dashboards) |
| JWT Issuer/Audience | 2 config defaults | Medium (token invalidation) |
| Database Names | POSTGRES_DB, POSTGRES_USER | HIGH (data migration) |
| Docker Network Name | 1 | Low |
| Docker Container Names | 14+ | Medium |
| Helm Chart | Chart name, values, templates | Medium |
| GitHub Actions / CI | Image names, DB names, artifacts | Medium |
| UI Branding | Logo file, display text, CSS | Medium |
| Domain/URL References | 8+ URLs | Low |
| OTEL Service Name | 1 config default | Low |
| Zustand Store Keys | 2 stores | Low-Medium |
| Git Remote / Repo Name | 1 | LOW (GitHub rename) |

### 3.2 Detailed Dependency Manifest

#### TIER 0: BREAKING CHANGES (Must coordinate)

**A. NPM Scoped Packages (@netnynja → @gridwatch)**
```
packages/shared-auth/package.json    → @gridwatch/shared-auth
packages/shared-types/package.json   → @gridwatch/shared-types
packages/shared-ui/package.json      → @gridwatch/shared-ui
apps/gateway/package.json            → @gridwatch/gateway
apps/web-ui/package.json             → @gridwatch/web-ui
services/auth-service/package.json   → @gridwatch/auth-service
```
Every `import` and `require` referencing `@netnynja/*` across all TypeScript files must update. Every `package.json` dependency list that references these packages must update. The npm workspace configuration in root `package.json` will need the name updated.

**B. Prometheus Metrics (netnynja_ → gridwatch_)**
```
apps/gateway/src/plugins/metrics.ts  → All 80+ metric definitions
infrastructure/grafana/dashboards/*  → All PromQL queries
infrastructure/prometheus/*          → Any scrape/relabel configs
```
This is the highest-risk rename. Grafana dashboards, alerting rules, and any external monitoring integration will break instantly. Requires a migration strategy (dual-emit or dashboard bulk update).

**C. Database Name & User**
```
.env / .env.example:  POSTGRES_DB=netnynja → gridwatch
.env / .env.example:  POSTGRES_USER=netnynja → gridwatch
docker-compose.yml:   POSTGRES_DB / POSTGRES_USER
docker-compose.prod.yml: same
infrastructure/postgres/init.sql
seed-admin.sql
.github/workflows/*.yml: test DB name
```
Requires a Postgres dump/restore or `ALTER DATABASE RENAME`. All connection strings, init scripts, and CI configs must update simultaneously.

#### TIER 1: IMAGE & CONTAINER NAMES

**D. Docker Images (14 images)**
```
docker-compose.yml:       image: netnynja-enterprise-* → gridwatch-enterprise-*
docker-compose.prod.yml:  same
.github/workflows/build-images.yml: image tags
.github/workflows/release.yml: image references
RELEASE.md: signing commands
charts/netnynja-enterprise/values.yaml: image repos
```

**E. Docker Container & Network Names**
```
docker-compose.yml:  container_name: netnynja-*
docker-compose.yml:  networks: netnynja-network → gridwatch-network
```

#### TIER 2: CONFIGURATION & IDENTITY

**F. JWT Issuer/Audience**
```
apps/gateway/src/config.ts:          JWT_ISSUER: "netnynja-enterprise" → "gridwatch-enterprise"
                                     JWT_AUDIENCE: "netnynja-api" → "gridwatch-api"
services/auth-service/src/config.ts: same pattern
```
WARNING: Changing JWT issuer invalidates ALL existing tokens. Must coordinate with a token rotation or accept forced re-auth.

**G. OTEL / Logging Service Names**
```
apps/gateway/src/config.ts:  OTEL_SERVICE_NAME: "netnynja-gateway" → "gridwatch-gateway"
docker-compose.yml:          OTEL_SERVICE_NAME env vars
```

**H. Zustand Store Keys**
```
apps/web-ui/src/stores/*:  "netnynja-auth" → "gridwatch-auth"
                           "netnynja-theme" → "gridwatch-theme"
```
NOTE: Changing localStorage keys means users lose saved state on upgrade.

#### TIER 3: BRANDING & DOCUMENTATION

**I. UI Assets**
```
apps/web-ui/public/assets/NetNynjaLogo.png → GridWatchLogo.png
apps/web-ui/src/components/layouts/MainLayout.tsx: logo ref + "NetNynja" text
apps/web-ui/src/pages/auth/LoginPage.tsx: logo ref + "NetNynja Enterprise" text
apps/web-ui/src/App.tsx: brand comment
apps/web-ui/src/index.css: CSS header comment
apps/gateway/src/plugins/swagger.ts: API title, contact name
```

**J. Documentation (all .md files)**
```
AGENTS.md, CLAUDE.md, CONTEXT.md, PROJECT_STATUS.md, IssuesTracker.md,
GO.md, README.md, COMMIT.md, RELEASE.md, CLAUDE_ENTERPRISE_SKILL.md,
docs/*.md, docs/*.html, archive/**/*.md
```
Estimated 200+ occurrences of "NetNynja" / "netnynja" across ~30 files.

**K. Domain / URL References**
```
apps/gateway/src/config.ts:          https://app.netnynja.com
apps/gateway/src/plugins/swagger.ts: support@netnynja.local, docs URLs
charts/*/Chart.yaml:                 support@netnynja.io, github URL
```

**L. Helm Chart**
```
charts/netnynja-enterprise/ → charts/gridwatch-enterprise/
charts/*/Chart.yaml: name, maintainer, home URL, keywords
charts/*/values.yaml: image repos
charts/*/templates/_helpers.tpl: chart name references
charts/*/README.md
```

**M. GitHub / CI**
```
.github/workflows/*.yml: image names, DB names, artifact names
Repository name: NetNynjaEnterprise → GridWatchEnterprise
GHCR path: ghcr.io/remeadows/netnynja* → ghcr.io/remeadows/gridwatch*
cosign signatures: all invalidated by image rename (must re-sign)
```

**N. Python Package**
```
pyproject.toml: name = "netnynja-enterprise" → "gridwatch-enterprise"
```

### 3.3 Recommended Rename Execution Plan

| Phase | Actions | Risk | Duration |
|---|---|---|---|
| **Phase 0: Prep** | Create feature branch `refactor/brand-rename`. Dump DB. Backup Grafana dashboards. Export cosign pub key. Document all token rotation steps. | None | 1 session |
| **Phase 1: Code** | NPM package names, imports, pyproject.toml, config defaults, metrics prefix, Docker names, Helm chart. Single atomic commit. | Build breaks until complete | 2-3 sessions |
| **Phase 2: Infra** | docker-compose files, .env.example, CI workflows, Grafana dashboards (PromQL queries), Prometheus configs. | Monitoring gap during transition | 1-2 sessions |
| **Phase 3: Data** | Rename Postgres DB/user (or fresh init). Rotate JWT keys. Clear Redis. Re-sign all container images with Cosign. | Data migration risk | 1 session |
| **Phase 4: Docs** | Global find/replace across all .md files. Update logo asset. Update ISSO report. | None | 1 session |
| **Phase 5: Verify** | Full CI run. Docker compose up. Smoke tests. Grafana dashboard validation. Security scan. | Regression | 1 session |
| **Phase 6: GitHub** | Rename repository. Update all git remotes. Update GHCR paths. | External link breakage | 30 min |

**Total estimated effort**: 6-8 focused sessions
**Recommended assignment**: Codex (Phase 1-2), Claude (Phase 4-5), Human (Phase 3, 6)

---

## SECTION 4: RECOMMENDATIONS (Priority Order)

1. **Fix CLAUDE.md version drift** — 15 min, high impact on agent accuracy
2. **Unify ingest order** — Resolve GO.md vs AGENTS.md contradiction
3. **Update CLAUDE_ENTERPRISE_SKILL.md** — Add Fastify/TypeScript acknowledgment, fix repo structure, remove "GRIDWATCH" leak
4. **Bump package.json + pyproject.toml** — Version 0.2.15 to match reality
5. **Archive IssuesTracker.md** — Compress from 746 lines to <200
6. **Add shared Python library** — Prevent config/retry duplication across 4 Python services
7. **Execute rename** — Once issues 1-5 are clean, proceed with GridWatch rebrand per Phase plan above

---

*End of analysis. No code was modified during this review.*
