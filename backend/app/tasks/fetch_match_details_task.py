import asyncio
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from .celery_app import celery_app
from ..database import SessionLocal
from ..models import User, SyncJob
from ..models.sync_job import JobStatus
from ..services import DotaAPIService, SteamAuthService
from .sync_helpers import fetch_match_details_phase
from celery import Task

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
def fetch_match_details(self, user_id: int, job_id: int):
    """
    Phase 2: Fetch match details for stubs (can run in parallel)

    Args:
        user_id: User ID
        job_id: SyncJob ID
    """
    logger.info(f"Starting fetch_match_details task for user_id={user_id}, job_id={job_id}")

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

        # Fetch match details
        result = asyncio.run(fetch_match_details_phase(db, user, account_id, sync_job, dota_api))

        # Update job status
        sync_job.status = JobStatus.COMPLETED
        sync_job.completed_at = datetime.utcnow()
        sync_job.new_matches = result.get("details_fetched", 0)
        user.last_sync_at = datetime.utcnow()
        db.commit()

        logger.info(f"Job {job_id} completed successfully. Fetched {result.get('details_fetched', 0)} match details")
        return result

    except Exception as e:
        logger.error(f"Job {job_id} failed with error: {str(e)}", exc_info=True)
        sync_job.status = JobStatus.FAILED
        sync_job.error_message = str(e)
        sync_job.completed_at = datetime.utcnow()
        db.commit()
        raise
