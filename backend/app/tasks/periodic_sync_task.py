import logging
from .celery_app import celery_app
from ..database import SessionLocal
from ..models import User, SyncJob
from ..models.sync_job import JobStatus, JobType
from .sync_matches_task import sync_matches

logger = logging.getLogger(__name__)


@celery_app.task
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
