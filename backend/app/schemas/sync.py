from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..models.sync_job import JobStatus, JobType


class SyncJobCreate(BaseModel):
    job_type: JobType = JobType.MANUAL_SYNC


class SyncJobResponse(BaseModel):
    id: int
    user_id: int
    job_type: JobType
    status: JobStatus
    total_matches: int
    processed_matches: int
    new_matches: int
    task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    error_message: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        if self.total_matches == 0:
            return 0.0
        return (self.processed_matches / self.total_matches) * 100

    class Config:
        from_attributes = True
