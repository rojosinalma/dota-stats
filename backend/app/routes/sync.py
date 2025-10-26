from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
from ..database import get_db
from ..models import User, SyncJob
from ..models.sync_job import JobStatus, JobType
from ..schemas import SyncJobResponse, SyncJobCreate
from ..tasks import collect_match_ids, fetch_match_details
from ..tasks.celery_app import celery_app
from .auth import get_current_user

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/trigger", response_model=SyncJobResponse)
async def trigger_sync(
    sync_data: SyncJobCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger a sync job"""
    # Check if there's already a running job
    existing_job = (
        db.query(SyncJob)
        .filter(
            SyncJob.user_id == user.id,
            SyncJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
        )
        .first()
    )

    if existing_job:
        raise HTTPException(
            status_code=400,
            detail="A sync job is already running"
        )

    # Use the job type from request
    job_type = sync_data.job_type

    # Create sync job
    sync_job = SyncJob(
        user_id=user.id,
        job_type=job_type,
        status=JobStatus.PENDING
    )
    db.add(sync_job)
    db.commit()
    db.refresh(sync_job)

    # Trigger appropriate task based on job type
    if job_type == JobType.SYNC_ALL:
        # New: Sync All - collect all IDs then fetch all details
        # Create job for collecting IDs
        task = collect_match_ids.delay(user.id, sync_job.id, full_sync=True)
        sync_job.task_id = task.id
        db.commit()

        # Create second job for fetching details (will run after ID collection completes)
        details_job = SyncJob(
            user_id=user.id,
            job_type=JobType.FETCH_MATCH_DETAILS,
            status=JobStatus.PENDING
        )
        db.add(details_job)
        db.commit()
        db.refresh(details_job)

        # Chain the tasks: fetch details after collecting IDs
        fetch_match_details.apply_async((user.id, details_job.id), link_error=None)

    elif job_type == JobType.SYNC_MISSING:
        # New: Sync Missing - only fetch details for existing stubs (no ID collection)
        task = fetch_match_details.delay(user.id, sync_job.id)
        sync_job.task_id = task.id
        db.commit()

    elif job_type == JobType.SYNC_INCREMENTAL:
        # New: Sync Incremental - collect new IDs then fetch their details
        # Create job for collecting new IDs
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

        # Chain the tasks
        fetch_match_details.apply_async((user.id, details_job.id), link_error=None)

    elif job_type == JobType.COLLECT_MATCH_IDS:
        # Direct: Collect match IDs only
        task = collect_match_ids.delay(user.id, sync_job.id, full_sync=True)
        sync_job.task_id = task.id
        db.commit()

    elif job_type == JobType.FETCH_MATCH_DETAILS:
        # Direct: Fetch details for all stubs
        task = fetch_match_details.delay(user.id, sync_job.id)
        sync_job.task_id = task.id
        db.commit()

    else:
        # Invalid job type
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job type: {job_type}"
        )

    db.refresh(sync_job)
    return sync_job


@router.get("/jobs", response_model=List[SyncJobResponse])
async def get_sync_jobs(
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's sync job history"""
    jobs = (
        db.query(SyncJob)
        .filter(SyncJob.user_id == user.id)
        .order_by(SyncJob.created_at.desc())
        .limit(limit)
        .all()
    )
    return jobs


@router.get("/jobs/{job_id}", response_model=SyncJobResponse)
async def get_sync_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific sync job status"""
    job = (
        db.query(SyncJob)
        .filter(SyncJob.id == job_id, SyncJob.user_id == user.id)
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="Sync job not found")

    return job


@router.get("/status")
async def get_sync_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current sync status"""
    active_job = (
        db.query(SyncJob)
        .filter(
            SyncJob.user_id == user.id,
            SyncJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
        )
        .first()
    )

    return {
        "is_syncing": active_job is not None,
        "active_job": SyncJobResponse.model_validate(active_job) if active_job else None
    }


@router.post("/cancel/{job_id}", response_model=SyncJobResponse)
async def cancel_sync(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a running sync job"""
    # Get the sync job
    sync_job = (
        db.query(SyncJob)
        .filter(SyncJob.id == job_id, SyncJob.user_id == user.id)
        .first()
    )

    if not sync_job:
        raise HTTPException(status_code=404, detail="Sync job not found")

    # Check if job is cancellable
    if sync_job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status: {sync_job.status}"
        )

    # Revoke the Celery task if it exists
    if sync_job.task_id:
        celery_app.control.revoke(sync_job.task_id, terminate=True)

    # Update job status
    sync_job.status = JobStatus.CANCELLED
    sync_job.completed_at = func.now()
    sync_job.error_message = "Cancelled by user"
    db.commit()
    db.refresh(sync_job)

    return sync_job
