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
from .sync_helpers import collect_match_ids_phase
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
def collect_match_ids(self, user_id: int, job_id: int, full_sync: bool = False):
    """
    Phase 1: Collect match IDs only (fast, reliable)

    Args:
        user_id: User ID
        job_id: SyncJob ID
        full_sync: If True, collect all historical matches. If False, only new matches.
    """
    logger.info(f"Starting collect_match_ids task for user_id={user_id}, job_id={job_id}, full_sync={full_sync}")

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

        # Collect match IDs
        result = asyncio.run(collect_match_ids_phase(db, user, account_id, sync_job, dota_api, full_sync))

        # Update job status
        sync_job.status = JobStatus.COMPLETED
        sync_job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Job {job_id} completed successfully. Collected {result.get('match_ids_collected', 0)} match IDs")
        return result

    except Exception as e:
        logger.error(f"Job {job_id} failed with error: {str(e)}", exc_info=True)
        sync_job.status = JobStatus.FAILED
        sync_job.error_message = str(e)
        sync_job.completed_at = datetime.utcnow()
        db.commit()
        raise
