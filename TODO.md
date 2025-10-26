Next Tasks:
1. DONE - Fail gracefully when API returns 500
2. DONE - Configure log levels, INFO only stdout and errors to file. DEBUG throws everything into stdout and errors to file
3. IN PROGRESS - Two-Phase Match Sync (addresses progress bar issue)
4. BUG - Cancel sync button: Frontend shows cancelled but Celery worker keeps processing the task

## Two-Phase Match Sync Architecture Plan

### Current Problem:
- GetMatchHistory (batch IDs) → GetMatchDetails (one by one) → Save Match
- If GetMatchDetails fails, we lose the match ID completely
- Can't retry failed matches later
- Progress isn't truly recoverable
- Progress bar shows '?' because we don't know total until we finish

### Proposed Solution: Two-Phase Sync

#### Phase 1: Collect Match IDs (Fast & Reliable)
1. Fetch all match IDs from GetMatchHistory in batches
2. Save match IDs as "stubs" in database with minimal data
3. Mark stub status as `pending_details`
4. **This gives us the total count immediately!**

#### Phase 2: Fetch Match Details (Can fail & retry)
1. Query all stubs with `pending_details` status
2. Fetch details for each match
3. Update stub with full match data
4. Mark status as `completed` or `failed` (with retry count)

### Database Changes:

**Option A: New table `match_stubs`**
```
- id (match_id) - BigInteger, primary key
- user_id - Foreign key to users
- status - Enum: pending_details, completed, failed
- retry_count - Integer (for failed fetches)
- discovered_at - DateTime (when ID was found)
- last_attempt_at - DateTime (last fetch attempt)
- error_message - String (why it failed)
```

**Option B: Extend existing `matches` table (RECOMMENDED)**
```
- Add: has_details: Boolean (NULL = stub, TRUE = complete, FALSE = failed)
- Add: retry_count: Integer
- Add: last_fetch_attempt: DateTime
- Add: fetch_error: String
- Make most columns nullable (except id, user_id)
```

### New Functionality:

1. **Two-phase sync**:
   - Phase 1: Collect all IDs quickly (GetMatchHistory)
   - Phase 2: Backfill details (GetMatchDetails)
   - Progress bar shows: "Fetching match IDs: 450/450" then "Fetching details: 230/450"

2. **Backfill command**:
   - Retry failed matches
   - CLI: `python cli.py backfill-matches <user_id>`
   - API endpoint: `POST /sync/backfill`

3. **Fault tolerance**:
   - Never lose match IDs
   - Can resume after failures
   - Tracks retry attempts
   - Exponential backoff for retries

### Implementation Steps:

1. DONE - Add logging to API calls
2. Create Alembic migration (add columns to matches table)
3. Update sync_all_matches() to separate ID collection from detail fetching
4. Update sync_new_matches() similarly
5. Add backfill_match_details() Celery task
6. Add CLI command for manual backfill
7. Add API endpoint for backfill trigger
8. Update frontend to show two-phase progress
9. Update SyncJob model to track phase and details progress

### Benefits:
- Never lose match IDs even if API fails
- Progress bar shows accurate totals immediately
- Can retry failed matches without re-scanning history
- More resilient to API failures
- Better user experience (see total immediately)
- Future-proof for backfill scenarios
