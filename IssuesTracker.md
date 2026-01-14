# NetNynja Enterprise - Issues Tracker

> Active issues and technical debt tracking

**Version**: 0.1.23
**Last Updated**: 2026-01-14
**Stats**: 2 open | 1 deferred | 128 resolved (archived)
**Codex Review**: 2026-01-14 11:30 (E2E: READY, Security: Low)

---

## 🔥 NOW (Active / In Progress)

- [ ] SEC-008 — Enable NATS auth/TLS for non-dev profiles
- [ ] SEC-009 — Make `trustProxy` configurable in auth-service

## ⏭️ NEXT (Queued / Ready)

- [ ] CI-012 — Upgrade Vite 5.x to 7.x (npm audit esbuild/vite moderate vulnerability) - Deferred
- [ ] Phase 9 — Documentation site deployment (optional)
- [ ] v0.2.3 Release — Tag and publish when ready

## ⛔ BLOCKED (Waiting / External Dependency)

(none)

---

## 📝 Open Issues (Codex Review 2026-01-14)

| ID      | P   | Title                  | Category  | Evidence                                                   |
| ------- | --- | ---------------------- | --------- | ---------------------------------------------------------- |
| SEC-008 | 🟡  | NATS auth/TLS disabled | Messaging | `nats.conf:46,52` - auth/TLS commented out                 |
| SEC-009 | 🟢  | trustProxy always true | Auth      | `auth-service/src/index.ts:28` - spoofable X-Forwarded-For |

**Recommended Fix Order**: SEC-008 → SEC-009

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

| ID      | P   | Title                                   | Resolved   | Resolution                                 |
| ------- | --- | --------------------------------------- | ---------- | ------------------------------------------ |
| SEC-006 | 🟠  | .env tracked with secrets               | 2026-01-14 | Already in .gitignore, .env.example exists |
| SEC-007 | 🟠  | DB/Cache ports exposed                  | 2026-01-14 | Bound Postgres/Redis/NATS to 127.0.0.1     |
| APP-012 | 🔴  | Preflight CRLF errors on Windows        | 2026-01-14 | Converted to LF, added PowerShell wrapper  |
| APP-013 | 🔴  | Preflight Docker checks fail            | 2026-01-14 | Created preflight.ps1 for native Windows   |
| APP-014 | 🟠  | OpenAPI endpoint mismatch               | 2026-01-14 | Fixed endpoint to `/docs/json`             |
| CI-013  | 🟡  | Tests workflow - shared-types not found | 2026-01-14 | Simplified package.json exports            |
| CI-005  | 🟠  | Validate Workspaces fails all platforms | 2026-01-14 | Changed to npm run build (Turborepo)       |
| SEC-004 | 🟡  | STIG ZIP upload DoS limits              | 2026-01-14 | Already implemented (500 files, 100MB)     |
| SEC-005 | 🟢  | Observability ports exposed             | 2026-01-14 | Bound to localhost only                    |
| WIN-001 | 🟠  | Windows Hyper-V port conflicts          | 2026-01-14 | NATS→8322, Vault→8300                      |
| #113    | 🟠  | NPM disk/storage metrics                | 2026-01-12 | Added Sophos SFOS OIDs                     |
| #114    | 🟠  | NPM interface traffic summaries         | 2026-01-12 | Added IF-MIB 64-bit counters               |
| #115    | 🟡  | NPM Sophos service status               | 2026-01-12 | Added 20+ service status OIDs              |
| APP-008 | 🟠  | STIG Library 500 error                  | 2026-01-12 | Created missing database tables            |
| APP-009 | 🟠  | Auto-polling not working                | 2026-01-12 | Created npm.device_metrics table           |
| APP-010 | 🟠  | NPM Poll Now fails                      | 2026-01-12 | Created partitioned metrics tables         |
| APP-011 | 🟡  | Sidebar toggle not visible              | 2026-01-12 | Fixed Sidebar.tsx condition                |

---

## 🗄️ Deferred Issues

| ID     | P   | Title                   | Reason                                            | Target        |
| ------ | --- | ----------------------- | ------------------------------------------------- | ------------- |
| CI-012 | 🟡  | Upgrade Vite 5.x to 7.x | Major version bump, needs React 18 compat testing | Future sprint |

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
