from celery import Task
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict
import asyncio
from .celery_app import celery_app
from ..database import SessionLocal
from ..models import User, Match, MatchPlayer, SyncJob, PlayerEncountered, Hero
from ..models.sync_job import JobStatus, JobType
from ..services import DotaAPIService, SteamAuthService


class DatabaseTask(Task):
    """Base task with database session"""
    _db: Optional[Session] = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def sync_matches(self, user_id: int, job_id: int, job_type: str = "manual_sync"):
    """Main task to sync matches for a user"""
    db: Session = self.db
    dota_api = DotaAPIService()
    steam_auth = SteamAuthService()

    # Get sync job
    sync_job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
    if not sync_job:
        return {"error": "Sync job not found"}

    # Update job status
    sync_job.status = JobStatus.RUNNING
    sync_job.started_at = datetime.utcnow()
    sync_job.task_id = self.request.id
    db.commit()

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception("User not found")

        account_id = steam_auth.steam_id_to_account_id(user.steam_id)

        # Determine if full or incremental sync
        if job_type == "full_sync":
            result = asyncio.run(sync_all_matches(db, user, account_id, sync_job, dota_api))
        else:
            result = asyncio.run(sync_new_matches(db, user, account_id, sync_job, dota_api))

        # Update job status
        sync_job.status = JobStatus.COMPLETED
        sync_job.completed_at = datetime.utcnow()
        sync_job.new_matches = result.get("new_matches", 0)
        user.last_sync_at = datetime.utcnow()
        db.commit()

        return result

    except Exception as e:
        sync_job.status = JobStatus.FAILED
        sync_job.error_message = str(e)
        sync_job.completed_at = datetime.utcnow()
        db.commit()
        raise


@celery_app.task(base=DatabaseTask)
def sync_matches_full(user_id: int, job_id: int):
    """Full sync of all historical matches"""
    return sync_matches(user_id, job_id, "full_sync")


@celery_app.task(base=DatabaseTask)
def sync_matches_incremental(user_id: int, job_id: int):
    """Incremental sync of new matches only"""
    return sync_matches(user_id, job_id, "incremental_sync")


@celery_app.task(base=DatabaseTask)
def periodic_sync():
    """Periodic task to sync all users"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            # Create incremental sync job
            sync_job = SyncJob(
                user_id=user.id,
                job_type=JobType.INCREMENTAL_SYNC,
                status=JobStatus.PENDING
            )
            db.add(sync_job)
            db.commit()
            db.refresh(sync_job)

            # Trigger sync
            sync_matches.delay(user.id, sync_job.id, "incremental_sync")

        return {"synced_users": len(users)}
    finally:
        db.close()


async def sync_all_matches(
    db: Session,
    user: User,
    account_id: int,
    sync_job: SyncJob,
    dota_api: DotaAPIService
) -> Dict:
    """Sync all matches from the beginning"""
    new_matches = 0
    total_fetched = 0
    start_at_match_id = None

    while True:
        # Fetch match history
        matches = await dota_api.get_match_history(
            account_id=account_id,
            matches_requested=100,
            start_at_match_id=start_at_match_id
        )

        if not matches:
            break

        total_fetched += len(matches)

        # Process each match
        for match_summary in matches:
            match_id = match_summary.get("match_id")
            start_at_match_id = match_id  # For pagination

            # Check if match already exists
            existing = db.query(Match).filter(Match.id == match_id).first()
            if existing:
                continue

            # Fetch full match details
            match_details = await dota_api.get_match_details(match_id)
            if not match_details:
                continue

            # Save match
            saved = save_match(db, user.id, account_id, match_details, dota_api)
            if saved:
                new_matches += 1

            # Update progress
            sync_job.processed_matches = total_fetched
            sync_job.new_matches = new_matches
            db.commit()

        # Check if we got less than requested (end of history)
        if len(matches) < 100:
            break

    sync_job.total_matches = total_fetched
    db.commit()

    return {
        "total_fetched": total_fetched,
        "new_matches": new_matches
    }


async def sync_new_matches(
    db: Session,
    user: User,
    account_id: int,
    sync_job: SyncJob,
    dota_api: DotaAPIService
) -> Dict:
    """Sync only new matches since last sync"""
    # Get most recent match
    latest_match = (
        db.query(Match)
        .filter(Match.user_id == user.id)
        .order_by(Match.start_time.desc())
        .first()
    )

    latest_match_id = latest_match.id if latest_match else None
    new_matches = 0
    total_fetched = 0

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

        total_fetched += 1

        # Check if match exists
        existing = db.query(Match).filter(Match.id == match_id).first()
        if existing:
            continue

        # Fetch full match details
        match_details = await dota_api.get_match_details(match_id)
        if not match_details:
            continue

        # Save match
        saved = save_match(db, user.id, account_id, match_details, dota_api)
        if saved:
            new_matches += 1

        # Update progress
        sync_job.processed_matches = total_fetched
        sync_job.new_matches = new_matches
        db.commit()

    sync_job.total_matches = total_fetched
    db.commit()

    return {
        "total_fetched": total_fetched,
        "new_matches": new_matches
    }


def save_match(
    db: Session,
    user_id: int,
    account_id: int,
    match_data: Dict,
    dota_api: DotaAPIService
) -> bool:
    """Save match and related data to database"""
    try:
        normalized = dota_api.normalize_match_data(match_data, account_id)
        if not normalized:
            return False

        player_data = normalized["player_data"]

        # Create match record
        match = Match(
            id=normalized["match_id"],
            user_id=user_id,
            start_time=normalized["start_time"],
            duration=normalized["duration"],
            game_mode=normalized["game_mode"],
            lobby_type=normalized["lobby_type"],
            radiant_win=normalized["radiant_win"],
            hero_id=player_data.get("hero_id"),
            player_slot=player_data.get("player_slot", 0),
            radiant_team=(player_data.get("player_slot", 0) < 128),
            kills=player_data.get("kills", 0),
            deaths=player_data.get("deaths", 0),
            assists=player_data.get("assists", 0),
            last_hits=player_data.get("last_hits"),
            denies=player_data.get("denies"),
            gold_per_min=player_data.get("gold_per_min"),
            xp_per_min=player_data.get("xp_per_min"),
            hero_damage=player_data.get("hero_damage"),
            tower_damage=player_data.get("tower_damage"),
            hero_healing=player_data.get("hero_healing"),
            level=player_data.get("level"),
            item_0=player_data.get("item_0"),
            item_1=player_data.get("item_1"),
            item_2=player_data.get("item_2"),
            item_3=player_data.get("item_3"),
            item_4=player_data.get("item_4"),
            item_5=player_data.get("item_5"),
            backpack_0=player_data.get("backpack_0"),
            backpack_1=player_data.get("backpack_1"),
            backpack_2=player_data.get("backpack_2"),
            item_neutral=player_data.get("item_neutral"),
            ability_upgrades=player_data.get("ability_upgrades"),
            net_worth=player_data.get("net_worth"),
            rank_tier=player_data.get("rank_tier"),
            raw_data=normalized["raw_data"]
        )

        db.add(match)

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
                # Check if same team
                player_slot = player.get("player_slot", 0)
                user_slot = player_data.get("player_slot", 0)
                same_team = (player_slot < 128) == (user_slot < 128)

                if same_team:
                    update_player_encountered(
                        db, user_id, player_account_id,
                        match.radiant_team == match.radiant_win,
                        normalized["start_time"]
                    )

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error saving match {match_data.get('match_id')}: {e}")
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
