# STIG-13: Multi-STIG Selection for Assets

## Problem Statement

Network devices and servers typically require compliance against **multiple STIGs**. For example:

| Device                   | Required STIGs                            |
| ------------------------ | ----------------------------------------- |
| Juniper SRX Firewall     | NDM (68 rules) + ALG (24 rules)           |
| Red Hat Enterprise Linux | RHEL OS STIG + Application-specific STIGs |
| Cisco Router             | NDM STIG + RTR STIG                       |
| Windows Server           | OS STIG + IIS STIG + SQL Server STIG      |

The current system assumes **one STIG per audit job**, requiring admins to run separate audits and manually aggregate results.

## Current Architecture

```
stig.targets                    stig.definitions
┌─────────────────┐            ┌─────────────────┐
│ id (UUID)       │            │ id (UUID)       │
│ name            │            │ stig_id         │
│ ip_address      │            │ title           │
│ platform        │            │ platform        │
│ ...             │            │ ...             │
└────────┬────────┘            └────────┬────────┘
         │                              │
         │    stig.audit_jobs           │
         │   ┌─────────────────┐        │
         └──►│ target_id       │◄───────┘
             │ definition_id   │  (1:1 relationship)
             │ status          │
             └─────────────────┘
```

**Limitation**: Each audit job links to exactly ONE definition.

---

## Proposed Solution

### Option A: Target-STIG Association Table (Recommended)

Create a many-to-many relationship between targets and STIG definitions, allowing pre-configuration of applicable STIGs per asset.

```
stig.targets                    stig.definitions
┌─────────────────┐            ┌─────────────────┐
│ id (UUID)       │            │ id (UUID)       │
│ name            │            │ stig_id         │
│ ...             │            │ ...             │
└────────┬────────┘            └────────┬────────┘
         │                              │
         │  stig.target_definitions     │
         │ ┌─────────────────────┐      │
         └►│ target_id (FK)      │◄─────┘
           │ definition_id (FK)  │
           │ is_primary          │
           │ enabled             │
           │ created_at          │
           └─────────────────────┘
```

**Benefits**:

- Pre-configure which STIGs apply to each asset
- Run "Audit All" to execute all applicable STIGs
- Clear audit history per STIG per target
- Flexible: enable/disable individual STIGs without deletion

### Option B: Audit Job Groups

Keep current schema, add grouping mechanism for related audit jobs.

```
stig.audit_job_groups
┌─────────────────┐
│ id (UUID)       │
│ name            │
│ target_id       │
│ created_at      │
└────────┬────────┘
         │
         │ stig.audit_jobs
         │ ┌─────────────────┐
         └►│ group_id (FK)   │  (nullable)
           │ target_id       │
           │ definition_id   │
           └─────────────────┘
```

**Benefits**:

- Minimal schema change
- Groups related audits for reporting
- Backward compatible

**Drawbacks**:

- No pre-configuration of applicable STIGs
- Must select STIGs every audit run

---

## Recommended Implementation: Option A

### Database Schema Changes

```sql
-- Migration: 010_add_target_definitions.sql

-- Many-to-many relationship between targets and STIG definitions
CREATE TABLE IF NOT EXISTS stig.target_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id UUID NOT NULL REFERENCES stig.targets(id) ON DELETE CASCADE,
    definition_id UUID NOT NULL REFERENCES stig.definitions(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT false,  -- Primary STIG for quick audits
    enabled BOOLEAN DEFAULT true,      -- Can disable without removing
    notes TEXT,                        -- Admin notes about applicability
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(target_id, definition_id)
);

-- Indexes for common queries
CREATE INDEX idx_target_definitions_target ON stig.target_definitions(target_id);
CREATE INDEX idx_target_definitions_definition ON stig.target_definitions(definition_id);
CREATE INDEX idx_target_definitions_enabled ON stig.target_definitions(target_id, enabled);

-- Add group_id to audit_jobs for batch audits
ALTER TABLE stig.audit_jobs
ADD COLUMN IF NOT EXISTS audit_group_id UUID;

-- Audit groups for batch operations
CREATE TABLE IF NOT EXISTS stig.audit_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    target_id UUID NOT NULL REFERENCES stig.targets(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    total_jobs INTEGER DEFAULT 0,
    completed_jobs INTEGER DEFAULT 0,
    created_by UUID REFERENCES shared.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_audit_groups_target ON stig.audit_groups(target_id);
CREATE INDEX idx_audit_jobs_group ON stig.audit_jobs(audit_group_id);
```

### API Changes

#### 1. Target-STIG Associations

```
GET    /api/v1/stig/targets/:id/definitions
       → List all STIG definitions assigned to a target

POST   /api/v1/stig/targets/:id/definitions
       Body: { definitionIds: ["uuid1", "uuid2"], isPrimary: "uuid1" }
       → Assign STIGs to a target

DELETE /api/v1/stig/targets/:id/definitions/:definitionId
       → Remove a STIG assignment

PATCH  /api/v1/stig/targets/:id/definitions/:definitionId
       Body: { enabled: false, isPrimary: true }
       → Update assignment (enable/disable, set primary)
```

#### 2. Batch Audit Operations

```
POST   /api/v1/stig/targets/:id/audit-all
       Body: { definitionIds?: ["uuid1", "uuid2"] }  // Optional filter
       → Create audit jobs for all (or specified) assigned STIGs
       → Returns audit_group_id

GET    /api/v1/stig/audit-groups/:groupId
       → Get batch audit status and individual job statuses

GET    /api/v1/stig/audit-groups/:groupId/summary
       → Aggregated compliance summary across all STIGs
```

#### 3. Enhanced Report Generation

```
GET    /api/v1/stig/reports/download/:groupId?format=pdf
       → Combined PDF report for all STIGs in the group

GET    /api/v1/stig/reports/download/:groupId?format=ckl
       → ZIP file containing individual CKL files per STIG
```

### UI Changes

#### 1. Asset Edit Modal - STIG Assignments Tab

```
┌─────────────────────────────────────────────────────────────┐
│ Edit Asset: TestJunos                                       │
├─────────────────────────────────────────────────────────────┤
│ [General] [Connection] [STIGs] [Audit History]              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Assigned STIGs                              [+ Add STIG]    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ☑ Juniper SRX SG NDM STIG V3R3        ⭐ Primary  [✕]  │ │
│ │   68 rules | High: 12, Medium: 48, Low: 8               │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ☑ Juniper SRX SG ALG STIG V3R3        ○ Primary  [✕]  │ │
│ │   24 rules | High: 4, Medium: 18, Low: 2                │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ☐ Juniper SRX SG VPN STIG V3R2        ○ Primary  [✕]  │ │
│ │   (disabled) 32 rules                                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Save]                                         [Cancel]     │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Add STIG Modal (Filtered by Platform)

```
┌─────────────────────────────────────────────────────────────┐
│ Add STIG to TestJunos                                       │
├─────────────────────────────────────────────────────────────┤
│ Platform: juniper_srx                    [Search...]        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Compatible STIGs:                                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ □ Juniper SRX SG IDPS STIG V2R1                         │ │
│ │   Intrusion Detection/Prevention | 28 rules             │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ □ Network Device Management SRG V3R9                    │ │
│ │   Generic NDM requirements | 156 rules                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ☑ Already assigned STIGs are hidden                        │
│                                                             │
│ [Add Selected]                                 [Cancel]     │
└─────────────────────────────────────────────────────────────┘
```

#### 3. Asset Actions - Audit Options

```
┌──────────────────────────────────┐
│ Actions ▾                        │
├──────────────────────────────────┤
│ 🔍 Quick Audit (Primary STIG)    │
│ 📋 Audit All STIGs               │
│ ─────────────────────────────    │
│ 📊 View Compliance Dashboard     │
│ 📄 Download Combined Report      │
└──────────────────────────────────┘
```

#### 4. Compliance Dashboard (Per Asset)

```
┌─────────────────────────────────────────────────────────────┐
│ TestJunos - Compliance Overview                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Overall Compliance: 76%  ████████████░░░░                   │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ STIG              │ Score  │ Pass │ Fail │ Last Audit  │ │
│ ├───────────────────┼────────┼──────┼──────┼─────────────┤ │
│ │ NDM V3R3          │  82%   │  56  │  12  │ 2026-01-17  │ │
│ │ ALG V3R3          │  80%   │  19  │   5  │ 2026-01-17  │ │
│ │ VPN V3R2          │   -    │   -  │   -  │ Never       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Run All Audits]  [Download Report]  [View History]         │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Database & API Foundation

1. Create migration `010_add_target_definitions.sql`
2. Add Python models for `TargetDefinition` and `AuditGroup`
3. Implement repository methods
4. Add gateway routes for CRUD operations

### Phase 2: Target-STIG Assignment UI

1. Add "STIGs" tab to Asset Edit modal
2. Create "Add STIG" modal with platform filtering
3. Enable/disable and primary STIG toggles
4. Save/load assignments via API

### Phase 3: Batch Audit Operations

1. Implement "Audit All" endpoint
2. Create audit group tracking
3. Update audit status aggregation
4. Add progress tracking for batch audits

### Phase 4: Combined Reporting

1. Generate combined PDF report across all STIGs
2. Generate ZIP with multiple CKL files
3. Add compliance dashboard per asset
4. Historical trend tracking

---

## Data Model Summary

```
┌─────────────┐       ┌──────────────────────┐       ┌─────────────────┐
│   Target    │◄─────►│  target_definitions  │◄─────►│   Definition    │
│             │ 1   * │  (junction table)    │ *   1 │                 │
│ - id        │       │ - target_id          │       │ - id            │
│ - name      │       │ - definition_id      │       │ - stig_id       │
│ - platform  │       │ - is_primary         │       │ - title         │
│ - ip_address│       │ - enabled            │       │ - rules (1:N)   │
└──────┬──────┘       └──────────────────────┘       └────────┬────────┘
       │                                                      │
       │              ┌──────────────────────┐                │
       │              │    audit_groups      │                │
       │              │ - id                 │                │
       │              │ - target_id          │                │
       │              │ - status             │                │
       │              │ - total_jobs         │                │
       │              └──────────┬───────────┘                │
       │                         │                            │
       │     ┌───────────────────┼───────────────────┐        │
       │     │                   │                   │        │
       ▼     ▼                   ▼                   ▼        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   audit_job 1   │    │   audit_job 2   │    │   audit_job N   │
│ - target_id     │    │ - target_id     │    │ - target_id     │
│ - definition_id │    │ - definition_id │    │ - definition_id │
│ - group_id      │    │ - group_id      │    │ - group_id      │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ audit_results   │    │ audit_results   │    │ audit_results   │
│ (NDM rules)     │    │ (ALG rules)     │    │ (VPN rules)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## Acceptance Criteria

- [x] Admin can assign multiple STIGs to a single target
- [x] Admin can designate a "primary" STIG for quick audits
- [x] Admin can enable/disable STIGs without removing assignment
- [x] "Audit All" runs all enabled STIGs and groups results
- [x] Combined PDF report shows compliance across all STIGs
- [x] CKL download provides ZIP with individual checklist files
- [x] Compliance dashboard shows per-STIG breakdown
- [x] Platform filtering suggests compatible STIGs

**Implementation Complete**: 2026-01-17

---

## Design Decisions (Resolved)

| Question                              | Decision                                                                                                                                 |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Auto-suggest STIGs based on platform? | **Yes** - When creating/editing an asset, suggest all compatible STIGs based on platform (e.g., Juniper SRX shows all Juniper SRX STIGs) |
| Disabled STIGs in "Audit All"?        | **Completely excluded** - Only enabled STIGs are audited                                                                                 |
| Combined report format?               | **One summary + separate sections** - Keep STIG titles distinct, show per-STIG breakdown                                                 |
| STIG profiles/presets?                | **Platform-based suggestions** - Auto-suggest compatible STIGs; admin selects which are applicable                                       |
