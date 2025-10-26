# Sync Improvements - Cancellation and Type Selection

## Changes Made

### Backend Changes

#### 1. Added CANCELLED Status
**File**: `backend/app/models/sync_job.py`
- Added `CANCELLED = "cancelled"` to `JobStatus` enum
- Allows tracking of cancelled sync jobs

#### 2. Cancel Sync Endpoint
**File**: `backend/app/routes/sync.py`
- Added `POST /sync/cancel/{job_id}` endpoint
- Revokes Celery task using `celery_app.control.revoke()`
- Updates job status to CANCELLED
- Sets completion timestamp and error message
- Only allows cancelling PENDING or RUNNING jobs

#### 3. Updated Sync Trigger
**File**: `backend/app/routes/sync.py`
- Removed automatic full sync logic
- Now respects user's choice of sync type
- User explicitly chooses between:
  - `incremental_sync` - Only new matches
  - `full_sync` - All historical matches

### Frontend Changes

#### 1. Updated API Service
**File**: `frontend/src/services/api.ts`
- Added `cancel(jobId)` method to `syncAPI`
- Changed default sync type to `incremental_sync`

#### 2. Dashboard UI Improvements
**File**: `frontend/src/pages/Dashboard.tsx`
- Added sync type selection with radio buttons:
  - "New Matches Only" (incremental)
  - "Full Sync (All Matches)" (full)
- Added "Cancel Sync" button when sync is active
- Button shows "Cancelling..." while processing
- Selector hidden during active sync
- Auto-refreshes status after cancellation

#### 3. Dashboard Styling
**File**: `frontend/src/pages/Dashboard.css`
- Added `.sync-controls` flex container
- Added `.sync-type-selector` styling
- Radio button group with proper spacing
- Responsive layout for sync controls

## Features

### Sync Type Selection
Users can now choose between two sync modes:

1. **Incremental Sync (Default)**
   - Only fetches new matches not in database
   - Fast and efficient
   - Recommended for regular updates
   - Stops when reaching existing matches

2. **Full Sync**
   - Fetches all historical matches
   - Recommended for first-time use
   - Re-fetches and updates all match data
   - Takes longer but ensures completeness

### Sync Cancellation
Users can now cancel ongoing sync operations:

- Click "Cancel Sync" button during active sync
- Immediately stops the Celery worker task
- Updates job status to CANCELLED
- Frees up system for new sync
- Prevents stuck "syncing" state

## API Endpoints

### Cancel Sync
```
POST /sync/cancel/{job_id}
```

**Response**: Updated SyncJob with CANCELLED status

**Errors**:
- 404: Job not found
- 400: Cannot cancel job (already completed/failed)

### Trigger Sync (Updated)
```
POST /sync/trigger
Body: { "job_type": "incremental_sync" | "full_sync" }
```

**Response**: Created SyncJob with task details

## How to Use

### For Users

1. **Choose Sync Type**:
   - Select "New Matches Only" for regular updates
   - Select "Full Sync" to re-fetch everything

2. **Start Sync**:
   - Click "Sync Matches" button
   - Watch progress in sync status bar

3. **Cancel If Needed**:
   - Click "Cancel Sync" if you need to stop
   - Status will update to cancelled
   - Can start new sync immediately

### For Developers

Monitor sync jobs in Flower:
- Visit http://10.10.10.20:5555
- See task status and progress
- Check if tasks were properly revoked

## Database Schema Changes

**Migration Required**: The CANCELLED enum value needs to be added to PostgreSQL.

Migration file: `backend/alembic/versions/001_add_cancelled_status.py`

This migration adds the 'cancelled' value to the existing `jobstatus` enum type.

## Testing

1. **Test Incremental Sync**:
   - Select "New Matches Only"
   - Click Sync
   - Should only fetch recent matches

2. **Test Full Sync**:
   - Select "Full Sync (All Matches)"
   - Click Sync
   - Should fetch all historical data

3. **Test Cancellation**:
   - Start any sync
   - Click "Cancel Sync" immediately
   - Check Flower - task should be revoked
   - Check database - job status should be CANCELLED

## Deployment

```bash
# Step 1: Run database migration
docker compose exec backend alembic upgrade head

# Step 2: Rebuild backend (for new endpoint and status)
docker compose build backend celery-worker

# Step 3: Restart services
docker compose up -d backend celery-worker

# Frontend will rebuild automatically if using dev mode
# For production:
docker compose build frontend
docker compose up -d frontend
```

**Important**: The migration must be run before the new code can work, otherwise you'll get:
```
invalid input value for enum jobstatus: "CANCELLED"
```

---

**Date**: 2025-10-26
**Status**: Complete and tested
