from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List
from ..database import get_db
from ..models import User, SyncJob
from ..models.sync_job import JobStatus, JobType
from ..schemas import SyncJobResponse, SyncJobCreate
from ..tasks import sync_matches_full, sync_matches_incremental, sync_matches, collect_match_ids, fetch_match_details
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

    # Trigger appropriate task
    if job_type == JobType.FULL_SYNC:
        task = sync_matches_full.delay(user.id, sync_job.id)
    elif job_type == JobType.INCREMENTAL_SYNC:
        task = sync_matches_incremental.delay(user.id, sync_job.id)
    elif job_type == JobType.COLLECT_MATCH_IDS:
        # Collect match IDs (can be full or incremental based on parameters)
        task = collect_match_ids.delay(user.id, sync_job.id, full_sync=True)
    elif job_type == JobType.FETCH_MATCH_DETAILS:
        # Fetch details for all stubs
        task = fetch_match_details.delay(user.id, sync_job.id)
    else:
        task = sync_matches.delay(user.id, sync_job.id, "manual_sync")

    sync_job.task_id = task.id
    db.commit()
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
