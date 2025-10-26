import asyncio
import logging
from celery import Task
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict
from .celery_app import celery_app
from ..database import SessionLocal
from ..models import User, Match, SyncJob
from ..models.sync_job import JobStatus
from ..services import DotaAPIService, SteamAuthService
from ..services.exceptions import APIException
from .sync_helpers import (
    save_match_stub,
    update_match_with_details,
    update_player_encountered
)
from sqlalchemy import or_, and_

logger = logging.getLogger(__name__)


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
    logger.info(f"Starting sync task for user_id={user_id}, job_id={job_id}, job_type={job_type}")

    db: Session = self.db
    dota_api = DotaAPIService()
    steam_auth = SteamAuthService()

    # Get sync job
    sync_job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
    if not sync_job:
        logger.error(f"Sync job {job_id} not found")
        return {"error": "Sync job not found"}

    # Update job status
    sync_job.status = JobStatus.RUNNING
    sync_job.started_at = datetime.utcnow()
    sync_job.task_id = self.request.id
    db.commit()
    logger.info(f"Job {job_id} status updated to RUNNING")

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            raise Exception("User not found")

        account_id = steam_auth.steam_id_to_account_id(user.steam_id)
        logger.debug(f"Steam ID {user.steam_id} converted to account_id {account_id}")

        # Determine if full or incremental sync
        if job_type == "full_sync":
            logger.info(f"Starting full sync for user {user_id}")
            result = asyncio.run(sync_all_matches(db, user, account_id, sync_job, dota_api))
        else:
            logger.info(f"Starting incremental sync for user {user_id}")
            result = asyncio.run(sync_new_matches(db, user, account_id, sync_job, dota_api))

        # Update job status
        sync_job.status = JobStatus.COMPLETED
        sync_job.completed_at = datetime.utcnow()
        sync_job.new_matches = result.get("new_matches", 0)
        user.last_sync_at = datetime.utcnow()
        db.commit()

        logger.info(f"Job {job_id} completed successfully. New matches: {result.get('new_matches', 0)}, Total fetched: {result.get('total_fetched', 0)}")
        return result

    except Exception as e:
        logger.error(f"Job {job_id} failed with error: {str(e)}", exc_info=True)
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

        # Update progress after each batch
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


async def sync_new_matches(
    db: Session,
    user: User,
    account_id: int,
    sync_job: SyncJob,
    dota_api: DotaAPIService
) -> Dict:
    """Sync only new matches since last sync using two-phase approach"""

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

    # PHASE 1: Collect new match IDs
    logger.info(f"Phase 1: Collecting new match IDs for user {user.id}")
    match_ids_collected = 0

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

    # Update progress after collecting IDs
    sync_job.total_matches = match_ids_collected
    sync_job.processed_matches = 0  # Reset for phase 2
    db.commit()

    logger.info(f"Phase 1 complete: Collected {match_ids_collected} new match IDs")

    # PHASE 2: Fetch match details for new stubs
    logger.info(f"Phase 2: Fetching match details for user {user.id}")

    # Get stubs from this sync and any previous failed attempts
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
