-- Migration: 010_add_target_definitions.sql
-- Description: Add multi-STIG support for targets (STIG-13)
-- Author: Claude
-- Date: 2026-01-17

-- ============================================================================
-- Target-STIG Assignments (Many-to-Many)
-- ============================================================================
-- Allows assigning multiple STIGs to a single target asset.
-- Example: Juniper SRX can have NDM, ALG, VPN, and IDPS STIGs assigned.

CREATE TABLE IF NOT EXISTS stig.target_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id UUID NOT NULL REFERENCES stig.targets(id) ON DELETE CASCADE,
    definition_id UUID NOT NULL REFERENCES stig.definitions(id) ON DELETE CASCADE,

    -- Configuration
    is_primary BOOLEAN DEFAULT false,      -- Primary STIG for "Quick Audit"
    enabled BOOLEAN DEFAULT true,          -- Can disable without removing assignment
    notes TEXT,                            -- Admin notes about applicability

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure unique pairing
    UNIQUE(target_id, definition_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_target_definitions_target
    ON stig.target_definitions(target_id);
CREATE INDEX IF NOT EXISTS idx_target_definitions_definition
    ON stig.target_definitions(definition_id);
CREATE INDEX IF NOT EXISTS idx_target_definitions_enabled
    ON stig.target_definitions(target_id, enabled) WHERE enabled = true;

-- ============================================================================
-- Audit Groups (Batch Audit Operations)
-- ============================================================================
-- Groups multiple audit jobs together for "Audit All" operations.
-- Tracks overall progress across all STIGs for a target.

CREATE TABLE IF NOT EXISTS stig.audit_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    target_id UUID NOT NULL REFERENCES stig.targets(id) ON DELETE CASCADE,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    total_jobs INTEGER DEFAULT 0,
    completed_jobs INTEGER DEFAULT 0,

    -- Metadata
    created_by UUID REFERENCES shared.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_audit_groups_target
    ON stig.audit_groups(target_id);
CREATE INDEX IF NOT EXISTS idx_audit_groups_status
    ON stig.audit_groups(status);
CREATE INDEX IF NOT EXISTS idx_audit_groups_created
    ON stig.audit_groups(created_at DESC);

-- ============================================================================
-- Add group reference to audit_jobs
-- ============================================================================
-- Links individual audit jobs to their parent group (if any).

ALTER TABLE stig.audit_jobs
ADD COLUMN IF NOT EXISTS audit_group_id UUID REFERENCES stig.audit_groups(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_audit_jobs_group
    ON stig.audit_jobs(audit_group_id) WHERE audit_group_id IS NOT NULL;

-- ============================================================================
-- Helper function: Ensure only one primary STIG per target
-- ============================================================================

CREATE OR REPLACE FUNCTION stig.ensure_single_primary()
RETURNS TRIGGER AS $$
BEGIN
    -- If setting this definition as primary, unset others for the same target
    IF NEW.is_primary = true THEN
        UPDATE stig.target_definitions
        SET is_primary = false, updated_at = NOW()
        WHERE target_id = NEW.target_id
          AND id != NEW.id
          AND is_primary = true;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_ensure_single_primary ON stig.target_definitions;
CREATE TRIGGER trigger_ensure_single_primary
    AFTER INSERT OR UPDATE OF is_primary ON stig.target_definitions
    FOR EACH ROW
    WHEN (NEW.is_primary = true)
    EXECUTE FUNCTION stig.ensure_single_primary();

-- ============================================================================
-- Helper function: Update audit group progress
-- ============================================================================

CREATE OR REPLACE FUNCTION stig.update_audit_group_progress()
RETURNS TRIGGER AS $$
DECLARE
    v_completed INTEGER;
    v_total INTEGER;
    v_all_done BOOLEAN;
BEGIN
    -- Only process if job belongs to a group
    IF NEW.audit_group_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Count completed jobs in this group
    SELECT
        COUNT(*) FILTER (WHERE status IN ('completed', 'failed', 'cancelled')),
        COUNT(*)
    INTO v_completed, v_total
    FROM stig.audit_jobs
    WHERE audit_group_id = NEW.audit_group_id;

    -- Check if all jobs are done
    v_all_done := (v_completed = v_total);

    -- Update the group
    UPDATE stig.audit_groups
    SET
        completed_jobs = v_completed,
        total_jobs = v_total,
        status = CASE
            WHEN v_all_done AND EXISTS (
                SELECT 1 FROM stig.audit_jobs
                WHERE audit_group_id = NEW.audit_group_id AND status = 'failed'
            ) THEN 'failed'
            WHEN v_all_done THEN 'completed'
            WHEN v_completed > 0 THEN 'running'
            ELSE 'pending'
        END,
        completed_at = CASE WHEN v_all_done THEN NOW() ELSE NULL END
    WHERE id = NEW.audit_group_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_audit_group_progress ON stig.audit_jobs;
CREATE TRIGGER trigger_update_audit_group_progress
    AFTER INSERT OR UPDATE OF status ON stig.audit_jobs
    FOR EACH ROW
    EXECUTE FUNCTION stig.update_audit_group_progress();

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE stig.target_definitions IS
    'Many-to-many relationship between targets and STIG definitions. Allows assigning multiple STIGs to a single asset.';

COMMENT ON COLUMN stig.target_definitions.is_primary IS
    'Primary STIG used for quick audits. Only one per target.';

COMMENT ON COLUMN stig.target_definitions.enabled IS
    'When false, this STIG is excluded from "Audit All" operations but assignment is preserved.';

COMMENT ON TABLE stig.audit_groups IS
    'Groups related audit jobs for batch operations like "Audit All STIGs".';

COMMENT ON COLUMN stig.audit_jobs.audit_group_id IS
    'Reference to parent audit group for batch operations. NULL for individual audits.';
