# Two-Phase Sync Implementation

## Overview

This document shows the proposed implementation for the two-phase match sync system.

## Current Flow (Single Phase)

```
For each batch of match history:
  1. Call GetMatchHistory() -> Get 100 match IDs
  2. For each match ID:
     a. Call GetMatchDetails(match_id)
     b. If successful, save complete match to DB
     c. If fails, skip (LOSE THE MATCH ID)
  3. Move to next batch
```

**Problems:**
- If GetMatchDetails fails, we lose the match ID
- Don't know total count until we finish
- Can't retry failed matches
- Progress bar shows "?"

## New Flow (Two Phases)

### Phase 1: Collect All Match IDs (Fast & Reliable)

```
Phase 1: ID Collection
  1. Call GetMatchHistory() in batches
  2. For each match ID in batch:
     a. Check if match stub exists in DB
     b. If not, create stub:
        - id = match_id
        - user_id = user_id
        - has_details = NULL (indicates stub)
        - All other columns = NULL
  3. Continue until no more matches
  4. Result: All match IDs saved, total count known
```

### Phase 2: Fetch Match Details (Can Fail & Retry)

```
Phase 2: Detail Fetching
  1. Query all matches WHERE has_details IS NULL
  2. For each stub:
     a. Call GetMatchDetails(match_id)
     b. If successful:
        - Update match with all details
        - Set has_details = TRUE
        - Save match_players
        - Update players_encountered
     c. If fails:
        - Set has_details = FALSE
        - Set retry_count += 1
        - Set last_fetch_attempt = NOW()
        - Set fetch_error = error message
  3. Can be retried later for failed matches
```

## Implementation Details

### New Helper Functions

```python
def save_match_stub(db: Session, user_id: int, match_id: int) -> Match:
    """
    Create a match stub with just the ID.
    Returns existing match if already present.
    """
    existing = db.query(Match).filter(Match.id == match_id).first()
    if existing:
        return existing

    stub = Match(
        id=match_id,
        user_id=user_id,
        has_details=None  # NULL indicates stub
    )
    db.add(stub)
    db.commit()
    db.refresh(stub)

    logger.debug(f"Created match stub for match_id={match_id}")
    return stub


def update_match_with_details(
    db: Session,
    match: Match,
    account_id: int,
    match_data: Dict,
    dota_api: DotaAPIService,
    error_status_code: Optional[int] = None
) -> bool:
    """
    Update an existing match stub with full details.

    Args:
        db: Database session
        match: Match stub to update
        account_id: Player account ID
        match_data: Match data from API (or None if failed)
        dota_api: API service
        error_status_code: HTTP status code if request failed

    Returns:
        True if successful, False otherwise

    Retry Logic:
        - 500 errors: Leave has_details=NULL, don't count as retry (API down)
        - Other errors: Set has_details=FALSE, increment retry_count
        - Max 3 retries for non-500 errors
    """
    try:
        # Handle API errors
        if match_data is None:
            match.last_fetch_attempt = datetime.utcnow()

            if error_status_code == 500:
                # API is down, don't count as retry, leave as stub
                match.has_details = None
                match.fetch_error = "API returned 500 (server error)"
                logger.warning(f"Match {match.id}: API 500 error, will retry later")
            else:
                # Other error, count as retry
                match.has_details = False
                match.retry_count += 1
                match.fetch_error = f"HTTP {error_status_code}" if error_status_code else "Unknown error"
                logger.error(f"Match {match.id}: Error (retry {match.retry_count}/3)")

            db.commit()
            return False

        normalized = dota_api.normalize_match_data(match_data, account_id)
        if not normalized:
            match.has_details = False
            match.retry_count += 1
            match.last_fetch_attempt = datetime.utcnow()
            match.fetch_error = "Failed to normalize match data"
            db.commit()
            return False

        player_data = normalized["player_data"]

        # Update match with details
        match.start_time = normalized["start_time"]
        match.duration = normalized["duration"]
        match.game_mode = normalized["game_mode"]
        match.lobby_type = normalized["lobby_type"]
        match.radiant_win = normalized["radiant_win"]
        match.hero_id = player_data.get("hero_id")
        match.player_slot = player_data.get("player_slot", 0)
        match.radiant_team = (player_data.get("player_slot", 0) < 128)
        match.kills = player_data.get("kills", 0)
        match.deaths = player_data.get("deaths", 0)
        match.assists = player_data.get("assists", 0)
        match.last_hits = player_data.get("last_hits")
        match.denies = player_data.get("denies")
        match.gold_per_min = player_data.get("gold_per_min")
        match.xp_per_min = player_data.get("xp_per_min")
        match.hero_damage = player_data.get("hero_damage")
        match.tower_damage = player_data.get("tower_damage")
        match.hero_healing = player_data.get("hero_healing")
        match.level = player_data.get("level")
        match.item_0 = player_data.get("item_0")
        match.item_1 = player_data.get("item_1")
        match.item_2 = player_data.get("item_2")
        match.item_3 = player_data.get("item_3")
        match.item_4 = player_data.get("item_4")
        match.item_5 = player_data.get("item_5")
        match.backpack_0 = player_data.get("backpack_0")
        match.backpack_1 = player_data.get("backpack_1")
        match.backpack_2 = player_data.get("backpack_2")
        match.item_neutral = player_data.get("item_neutral")
        match.ability_upgrades = player_data.get("ability_upgrades")
        match.net_worth = player_data.get("net_worth")
        match.rank_tier = player_data.get("rank_tier")
        match.raw_data = normalized["raw_data"]
        match.has_details = True

        # Save all players in match
        for player in normalized.get("all_players", []):
            match_player = MatchPlayer(
                match_id=match.id,
                account_id=player.get("account_id"),
                player_slot=player.get("player_slot", 0),
                hero_id=player.get("hero_id"),
                kills=player.get("kills"),
                deaths=player.get("deaths"),
                assists=player.get("assists"),
                gold_per_min=player.get("gold_per_min"),
                xp_per_min=player.get("xp_per_min"),
                hero_damage=player.get("hero_damage"),
                tower_damage=player.get("tower_damage"),
                hero_healing=player.get("hero_healing"),
                last_hits=player.get("last_hits"),
                denies=player.get("denies"),
                level=player.get("level"),
                net_worth=player.get("net_worth"),
                item_0=player.get("item_0"),
                item_1=player.get("item_1"),
                item_2=player.get("item_2"),
                item_3=player.get("item_3"),
                item_4=player.get("item_4"),
                item_5=player.get("item_5"),
            )
            db.add(match_player)

            # Update players encountered (teammates)
            player_account_id = player.get("account_id")
            if player_account_id and player_account_id != account_id:
                player_slot = player.get("player_slot", 0)
                user_slot = player_data.get("player_slot", 0)
                same_team = (player_slot < 128) == (user_slot < 128)

                if same_team:
                    update_player_encountered(
                        db, match.user_id, player_account_id,
                        match.radiant_team == match.radiant_win,
                        normalized["start_time"]
                    )

        db.commit()
        logger.info(f"Successfully updated match {match.id} with details")
        return True

    except Exception as e:
        db.rollback()
        match.has_details = False
        match.retry_count += 1
        match.last_fetch_attempt = datetime.utcnow()
        match.fetch_error = str(e)
        db.commit()
        logger.error(f"Error updating match {match.id} with details: {e}", exc_info=True)
        return False
```

### Updated sync_all_matches()

```python
async def sync_all_matches(
    db: Session,
    user: User,
    account_id: int,
    sync_job: SyncJob,
    dota_api: DotaAPIService
) -> Dict:
    """Sync all matches using two-phase approach"""

    # PHASE 1: Collect all match IDs
    logger.info(f"Phase 1: Collecting match IDs for user {user.id}")
    match_ids_collected = 0
    start_at_match_id = None

    while True:
        matches = await dota_api.get_match_history(
            account_id=account_id,
            matches_requested=100,
            start_at_match_id=start_at_match_id
        )

        if not matches:
            break

        for match_summary in matches:
            match_id = match_summary.get("match_id")
            start_at_match_id = match_id  # For pagination

            # Save stub (or get existing)
            save_match_stub(db, user.id, match_id)
            match_ids_collected += 1

        # Update progress
        sync_job.total_matches = match_ids_collected
        sync_job.processed_matches = 0  # Reset for phase 2
        db.commit()

        logger.info(f"Collected {match_ids_collected} match IDs so far")

        if len(matches) < 100:
            break

    logger.info(f"Phase 1 complete: Collected {match_ids_collected} match IDs")

    # PHASE 2: Fetch match details for stubs
    logger.info(f"Phase 2: Fetching match details for user {user.id}")

    # Get all stubs (has_details IS NULL) and failed with retries left
    stubs = db.query(Match).filter(
        Match.user_id == user.id,
        db.or_(
            Match.has_details.is_(None),  # New stubs
            db.and_(
                Match.has_details == False,
                Match.retry_count < 3  # Failed but retries left
            )
        )
    ).all()

    details_fetched = 0
    details_failed = 0
    api_down = 0
    batch = []
    BATCH_SIZE = 25

    for i, match in enumerate(stubs):
        logger.debug(f"Fetching details for match_id={match.id} (attempt {match.retry_count + 1})")

        try:
            match_details = await dota_api.get_match_details(match.id)
            error_code = None
        except Exception as e:
            match_details = None
            # Extract status code from exception if available
            error_code = getattr(e, 'status_code', None) if hasattr(e, 'status_code') else None
            logger.error(f"Exception fetching match {match.id}: {e}")

        success = update_match_with_details(
            db, match, account_id, match_details, dota_api, error_code
        )

        if success:
            details_fetched += 1
        else:
            if error_code == 500:
                api_down += 1
            else:
                details_failed += 1

        batch.append(match)

        # Commit in batches of 25
        if len(batch) >= BATCH_SIZE or i == len(stubs) - 1:
            sync_job.processed_matches = details_fetched + details_failed + api_down
            sync_job.new_matches = details_fetched
            db.commit()
            logger.info(f"Batch committed: {details_fetched}/{len(stubs)} successful")
            batch = []

    logger.info(f"Phase 2 complete: {details_fetched} successful, {details_failed} failed, {api_down} API errors (500)")

    return {
        "total_fetched": match_ids_collected,
        "new_matches": details_fetched,
        "failed_matches": details_failed
    }
```

## Progress Tracking

With this approach:

### Phase 1 Progress:
```
"Collecting match IDs: 450/? (still fetching)"
-> Shows as it discovers more IDs
```

### Phase 2 Progress:
```
"Fetching match details: 230/450"
-> Shows exact progress since we know the total
```

## Benefits

1. **Never lose match IDs**: Even if GetMatchDetails fails for all matches, we have the IDs
2. **Accurate progress**: Total count known immediately after Phase 1
3. **Retry failed matches**: Query WHERE has_details = FALSE to retry
4. **Graceful degradation**: Can show matches list even without full details
5. **Backfill support**: Easy to implement backfill for failed matches
6. **Better UX**: User sees progress immediately

## Backfill Implementation (Future)

```python
@celery_app.task(base=DatabaseTask, bind=True)
def backfill_failed_matches(self, user_id: int):
    """Retry fetching details for failed matches"""
    db: Session = self.db
    dota_api = DotaAPIService()
    steam_auth = SteamAuthService()

    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    account_id = steam_auth.steam_id_to_account_id(user.steam_id)

    # Get failed matches (has_details = FALSE, retry_count < 3)
    failed_matches = db.query(Match).filter(
        Match.user_id == user_id,
        Match.has_details == False,
        Match.retry_count < 3
    ).all()

    for match in failed_matches:
        match_details = await dota_api.get_match_details(match.id)
        if match_details:
            update_match_with_details(db, match, account_id, match_details, dota_api)
```

## Decisions Made

1. **Batch detail fetching**: Fetch one-by-one (respecting 7-second rate limit), commit every 25 matches
2. **Retry logic**:
   - **500 errors**: Set has_details=NULL, don't increment retry_count (API is down, try another day)
   - **Other errors**: Set has_details=FALSE, increment retry_count, max 3 retries
   - After 3 retries for non-500 errors, stop trying
3. **Show stubs in UI**: Yes, display with "No data available yet" message
4. **Batch size**: 25 matches per DB commit during Phase 2

## API Changes Needed

Currently `get_match_details()` returns `None` on error, which loses the status code.

### Option 1: Return tuple (data, status_code)
```python
async def get_match_details(self, match_id: int) -> tuple[Optional[Dict], Optional[int]]:
    # ...
    return data, status_code
```

### Option 2: Raise exception with status code
```python
class APIException(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

async def get_match_details(self, match_id: int) -> Optional[Dict]:
    # On error: raise APIException("Error", status_code=500)
```

**Recommended: Option 2** - More Pythonic, caller can catch and handle

## Next Steps

1. Review this implementation
2. Update valve_api.py to raise exceptions with status codes
3. Run migration to add columns
4. Implement helper functions (save_match_stub, update_match_with_details)
5. Update sync_all_matches() and sync_new_matches()
6. Test with real data
7. Add backfill command
8. Update frontend to show two-phase progress and stub matches
