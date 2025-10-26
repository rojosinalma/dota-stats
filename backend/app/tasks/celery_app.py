from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init
from ..config import settings
from ..logging_config import setup_logging
import logging

celery_app = Celery(
    "dota_stats",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.sync_tasks"]
)


@worker_process_init.connect
def setup_celery_logging(**kwargs):
    """Setup logging when Celery worker process initializes"""
    setup_logging(log_level=settings.LOG_LEVEL, log_file_path="/app/logs/celery.log")
    logger = logging.getLogger(__name__)
    logger.info(f"Celery worker logging initialized with level: {settings.LOG_LEVEL}")

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_send_sent_event=True,
    worker_send_task_events=True,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "periodic-sync": {
        "task": "app.tasks.sync_tasks.periodic_sync",
        "schedule": crontab(minute=f"*/{settings.SYNC_INTERVAL_MINUTES}"),
    },
}
