import logging
from .celery_app import celery_app
from ..database import SessionLocal
from ..models import User, SyncJob
from ..models.sync_job import JobStatus, JobType
from .collect_match_ids_task import collect_match_ids
from .fetch_match_details_task import fetch_match_details

logger = logging.getLogger(__name__)


@celery_app.task
def periodic_sync():
    """Periodic task to sync all users using incremental sync"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            # Create incremental sync job (collect new IDs)
            sync_job = SyncJob(
                user_id=user.id,
                job_type=JobType.COLLECT_MATCH_IDS,
                status=JobStatus.PENDING
            )
            db.add(sync_job)
            db.commit()
            db.refresh(sync_job)

            # Trigger ID collection (incremental)
            task = collect_match_ids.delay(user.id, sync_job.id, full_sync=False)
            sync_job.task_id = task.id
            db.commit()

            # Create second job for fetching details
            details_job = SyncJob(
                user_id=user.id,
                job_type=JobType.FETCH_MATCH_DETAILS,
                status=JobStatus.PENDING
            )
            db.add(details_job)
            db.commit()
            db.refresh(details_job)

            # Chain: fetch details after collecting IDs
            fetch_match_details.apply_async((user.id, details_job.id), link_error=None)

        return {"synced_users": len(users)}
    finally:
        db.close()
