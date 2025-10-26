import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime
from typing import Dict, Optional
from ..models import User, Match, MatchPlayer, PlayerEncountered, SyncJob
from ..services import DotaAPIService
from ..services.exceptions import APIException

logger = logging.getLogger(__name__)


async def collect_match_ids_phase(
    db: Session,
    user: User,
    account_id: int,
    sync_job: SyncJob,
    dota_api: DotaAPIService,
    full_sync: bool
) -> Dict:
    """
    Phase 1: Collect match IDs only

    Args:
        full_sync: If True, collect all historical matches. If False, only new matches.
    """
    match_ids_collected = 0

    if full_sync:
        # Full sync: collect all historical matches
        logger.info(f"Full sync: Collecting all match IDs for user {user.id}")
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

            # Update progress after each batch
            sync_job.total_matches = match_ids_collected
            db.commit()

            logger.info(f"Collected {match_ids_collected} match IDs so far")

            if len(matches) < 100:
                break
    else:
        # Incremental sync: collect only new matches
        logger.info(f"Incremental sync: Collecting new match IDs for user {user.id}")

        # Get most recent match with details
        latest_match = (
            db.query(Match)
            .filter(
                Match.user_id == user.id,
                Match.has_details == True
            )
            .order_by(Match.id.desc())
            .first()
        )

        latest_match_id = latest_match.id if latest_match else None

        # Fetch recent matches
        matches = await dota_api.get_match_history(
            account_id=account_id,
            matches_requested=100
        )

        for match_summary in matches:
            match_id = match_summary.get("match_id")

            # Stop if we've reached matches we already have
            if latest_match_id and match_id <= latest_match_id:
                break

            # Save stub (or get existing)
            save_match_stub(db, user.id, match_id)
            match_ids_collected += 1

        # Update progress
        sync_job.total_matches = match_ids_collected
        db.commit()

    logger.info(f"Phase 1 complete: Collected {match_ids_collected} match IDs")

    return {
        "match_ids_collected": match_ids_collected
    }


async def fetch_match_details_phase(
    db: Session,
    user: User,
    account_id: int,
    sync_job: SyncJob,
    dota_api: DotaAPIService
) -> Dict:
    """
    Phase 2: Fetch match details for stubs
    """
    logger.info(f"Phase 2: Fetching match details for user {user.id}")

    # Get all stubs (has_details IS NULL) and failed with retries left
    stubs = db.query(Match).filter(
        Match.user_id == user.id,
        or_(
            Match.has_details.is_(None),  # New stubs
            and_(
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

    # Update total for progress tracking
    sync_job.total_matches = len(stubs)
    db.commit()

    for i, match in enumerate(stubs):
        logger.debug(f"Fetching details for match_id={match.id} (attempt {match.retry_count + 1})")

        try:
            match_details = await dota_api.get_match_details(match.id)
            error_code = None
        except APIException as e:
            match_details = None
            error_code = e.status_code
            logger.error(f"APIException fetching match {match.id}: {e}")
        except Exception as e:
            match_details = None
            error_code = None
            logger.error(f"Unexpected exception fetching match {match.id}: {e}")

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
            db.commit()
            logger.info(f"Batch committed: {details_fetched}/{len(stubs)} successful")
            batch = []

    logger.info(f"Phase 2 complete: {details_fetched} successful, {details_failed} failed, {api_down} API errors (500)")

    return {
        "details_fetched": details_fetched,
        "details_failed": details_failed,
        "api_down": api_down
    }


def save_match_stub(db: Session, user_id: int, match_id: int) -> Match:
    """
    Create a match stub with just the ID.
    Returns existing match if already present.

    Args:
        db: Database session
        user_id: User ID who played the match
        match_id: Match ID from API

    Returns:
        Match object (either existing or newly created stub)
    """
    existing = db.query(Match).filter(Match.id == match_id).first()
    if existing:
        return existing

    stub = Match(
        id=match_id,
        user_id=user_id,
        has_details=None  # NULL indicates stub without details
    )
    db.add(stub)
    db.flush()  # Don't commit yet, caller will batch commit

    logger.debug(f"Created match stub for match_id={match_id}")
    return stub


def update_match_with_details(
    db: Session,
    match: Match,
    account_id: int,
    match_data: Optional[Dict],
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

            return False

        normalized = dota_api.normalize_match_data(match_data, account_id)
        if not normalized:
            match.has_details = False
            match.retry_count += 1
            match.last_fetch_attempt = datetime.utcnow()
            match.fetch_error = "Failed to normalize match data"
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
        match.fetch_error = None

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

        logger.info(f"Successfully updated match {match.id} with details")
        return True

    except Exception as e:
        match.has_details = False
        match.retry_count += 1
        match.last_fetch_attempt = datetime.utcnow()
        match.fetch_error = str(e)
        logger.error(f"Error updating match {match.id} with details: {e}", exc_info=True)
        return False


def update_player_encountered(
    db: Session,
    user_id: int,
    account_id: int,
    won: bool,
    match_time: datetime
):
    """Update or create player encountered record"""
    player = (
        db.query(PlayerEncountered)
        .filter(
            PlayerEncountered.user_id == user_id,
            PlayerEncountered.account_id == account_id
        )
        .first()
    )

    if player:
        player.games_together += 1
        if won:
            player.games_won += 1
        else:
            player.games_lost += 1
        player.last_match_at = match_time
    else:
        player = PlayerEncountered(
            user_id=user_id,
            account_id=account_id,
            games_together=1,
            games_won=1 if won else 0,
            games_lost=0 if won else 1,
            first_match_at=match_time,
            last_match_at=match_time
        )
        db.add(player)

    db.commit()
