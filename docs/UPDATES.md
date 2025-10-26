# Recent Updates

## Bug Fixes

### Steam API Endpoint URLs (CRITICAL)
- **Fixed**: Added trailing slashes to all Steam API endpoints
- **Impact**: Resolves 500 Internal Server Error when fetching match data
- **Files Changed**:
  - `backend/app/services/dota_api.py`
    - `/IDOTA2Match_570/GetMatchHistory/v1/`
    - `/IDOTA2Match_570/GetMatchDetails/v1/`
    - `/IEconDOTA2_570/GetHeroes/v1/`

## New Features

### Flower - Celery Monitoring
- **Added**: Flower web interface for real-time Celery task monitoring
- **Access**: http://10.10.10.20:5555 (or http://localhost:5555)
- **Features**:
  - Real-time task monitoring
  - Worker status and statistics
  - Task history and results
  - Task progress tracking
  - Success/failure rates
  - Task retry monitoring

### Files Changed:
- `backend/requirements.txt` - Added flower==2.0.1
- `compose.yaml` - Added flower service (port 5555)
- `compose.dev.yaml` - Added flower service for development

## How to Apply Changes

### Option 1: Restart All Services (Recommended)
```bash
docker compose down
docker compose build
docker compose up -d
```

### Option 2: Restart Specific Services
```bash
# Rebuild backend (for Steam API fix and Flower)
docker compose build backend celery-worker celery-beat flower

# Restart services
docker compose up -d backend celery-worker celery-beat flower
```

## Verify Changes

1. **Check Flower is running**:
   - Visit: http://10.10.10.20:5555
   - You should see the Flower dashboard

2. **Test match sync**:
   - Login to the app
   - Click "Sync Matches"
   - Watch progress in Flower dashboard
   - Verify no 500 errors in logs

3. **View logs**:
   ```bash
   docker compose logs -f celery-worker
   docker compose logs -f flower
   ```

## Monitoring with Flower

Once Flower is running, you can:
- View active sync tasks
- See task success/failure rates
- Monitor worker health
- Inspect task arguments and results
- View task execution time
- Debug failed tasks

Navigate to http://10.10.10.20:5555 to access the dashboard.

---

**Date**: 2025-10-26
**Status**: Ready to deploy
