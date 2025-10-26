-- Migration script to update JobType enum and migrate old job types
--
-- This script:
-- 1. Adds new job type enum values
-- 2. Migrates old job types to new ones
-- 3. Removes old enum values

BEGIN;

-- Step 1: Add new enum values to jobtype
ALTER TYPE jobtype ADD VALUE IF NOT EXISTS 'SYNC_ALL';
ALTER TYPE jobtype ADD VALUE IF NOT EXISTS 'SYNC_MISSING';
ALTER TYPE jobtype ADD VALUE IF NOT EXISTS 'SYNC_INCREMENTAL';
ALTER TYPE jobtype ADD VALUE IF NOT EXISTS 'COLLECT_MATCH_IDS';
ALTER TYPE jobtype ADD VALUE IF NOT EXISTS 'FETCH_MATCH_DETAILS';

COMMIT;

-- Step 2: Migrate old job types to new ones
-- Note: We can't remove enum values in PostgreSQL, so we migrate and leave old values unused

BEGIN;

-- Migrate FULL_SYNC to SYNC_ALL
UPDATE sync_jobs
SET job_type = 'SYNC_ALL'::jobtype
WHERE job_type = 'FULL_SYNC'::jobtype;

-- Migrate INCREMENTAL_SYNC to SYNC_INCREMENTAL
UPDATE sync_jobs
SET job_type = 'SYNC_INCREMENTAL'::jobtype
WHERE job_type = 'INCREMENTAL_SYNC'::jobtype;

-- Migrate MANUAL_SYNC to SYNC_INCREMENTAL (if any exist)
UPDATE sync_jobs
SET job_type = 'SYNC_INCREMENTAL'::jobtype
WHERE job_type = 'MANUAL_SYNC'::jobtype;

COMMIT;

-- Verify migration
SELECT job_type, COUNT(*)
FROM sync_jobs
GROUP BY job_type
ORDER BY job_type;
