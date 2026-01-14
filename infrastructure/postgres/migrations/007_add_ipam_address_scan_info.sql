-- Migration: Add response_time_ms and open_ports to ipam.addresses
-- Purpose: Store scan discovery information (latency from ping, open ports from TCP/NMAP scans)

-- Add columns if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'ipam' AND table_name = 'addresses'
                   AND column_name = 'response_time_ms') THEN
        ALTER TABLE ipam.addresses ADD COLUMN response_time_ms NUMERIC(10, 3);
        COMMENT ON COLUMN ipam.addresses.response_time_ms IS 'Ping/TCP response latency in milliseconds';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'ipam' AND table_name = 'addresses'
                   AND column_name = 'open_ports') THEN
        ALTER TABLE ipam.addresses ADD COLUMN open_ports TEXT;
        COMMENT ON COLUMN ipam.addresses.open_ports IS 'Comma-separated list of discovered open TCP ports';
    END IF;
END $$;
