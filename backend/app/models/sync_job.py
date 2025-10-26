from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
import enum
from ..database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    FULL_SYNC = "full_sync"
    INCREMENTAL_SYNC = "incremental_sync"
    MANUAL_SYNC = "manual_sync"


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    job_type = Column(SQLEnum(JobType), nullable=False)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)

    # Progress tracking
    total_matches = Column(Integer, default=0)
    processed_matches = Column(Integer, default=0)
    new_matches = Column(Integer, default=0)

    # Celery task info
    task_id = Column(String, nullable=True, index=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Error info
    error_message = Column(String, nullable=True)
