-- Migration 013: Fix syslog source statistics tracking
-- Issue: ON CONFLICT (ip_address) requires a UNIQUE constraint to work
-- Without it, duplicate sources are created and statistics never update

-- Step 1: Remove duplicate sources (keep the one with most events or oldest)
-- First, identify and remove duplicates, keeping the configured source
DELETE FROM syslog.sources a
USING syslog.sources b
WHERE a.id > b.id
  AND a.ip_address = b.ip_address;

-- Step 2: Add the unique constraint on ip_address
-- This enables ON CONFLICT (ip_address) to work correctly
ALTER TABLE syslog.sources
DROP CONSTRAINT IF EXISTS uq_syslog_sources_ip;

ALTER TABLE syslog.sources
ADD CONSTRAINT uq_syslog_sources_ip UNIQUE (ip_address);

-- Step 3: Update existing sources with event counts from syslog.events
-- This backfills statistics for sources that weren't being tracked
UPDATE syslog.sources s
SET
    events_received = COALESCE(stats.event_count, 0),
    last_event_at = stats.last_event
FROM (
    SELECT
        source_ip,
        COUNT(*) as event_count,
        MAX(received_at) as last_event
    FROM syslog.events
    GROUP BY source_ip
) stats
WHERE s.ip_address = stats.source_ip;

-- Step 4: For sources with events but no source record, create source records
-- (This handles auto-discovered sources that had events but no manual config)
INSERT INTO syslog.sources (name, ip_address, hostname, device_type, events_received, last_event_at)
SELECT
    COALESCE(e.hostname, host(e.source_ip)) as name,
    e.source_ip as ip_address,
    e.hostname,
    e.device_type,
    COUNT(*) as events_received,
    MAX(e.received_at) as last_event_at
FROM syslog.events e
WHERE NOT EXISTS (
    SELECT 1 FROM syslog.sources s WHERE s.ip_address = e.source_ip
)
GROUP BY e.source_ip, e.hostname, e.device_type
ON CONFLICT (ip_address) DO UPDATE SET
    events_received = EXCLUDED.events_received,
    last_event_at = EXCLUDED.last_event_at,
    updated_at = NOW();

-- Step 5: Update source_id in events table to link to correct source
UPDATE syslog.events e
SET source_id = s.id
FROM syslog.sources s
WHERE e.source_ip = s.ip_address
  AND (e.source_id IS NULL OR e.source_id != s.id);
