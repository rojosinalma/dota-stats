#!/usr/bin/env python3
"""
CLI tool for managing Dota Stats background jobs
"""
import click
import asyncio
from app.database import SessionLocal
from app.models import User, SyncJob
from app.models.sync_job import JobStatus, JobType
from app.tasks import sync_matches_full, sync_matches_incremental
from app.services import DotaAPIService
from app.config import settings


@click.group()
def cli():
    """Dota Stats CLI"""
    pass


@cli.command()
@click.argument('steam_id')
def sync_user(steam_id: str):
    """Trigger full sync for a specific user by Steam ID"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.steam_id == steam_id).first()
        if not user:
            click.echo(f"User with Steam ID {steam_id} not found")
            return

        # Create sync job
        sync_job = SyncJob(
            user_id=user.id,
            job_type=JobType.FULL_SYNC,
            status=JobStatus.PENDING
        )
        db.add(sync_job)
        db.commit()
        db.refresh(sync_job)

        # Trigger sync
        task = sync_matches_full.delay(user.id, sync_job.id)
        click.echo(f"Sync job {sync_job.id} triggered for user {user.persona_name}")
        click.echo(f"Task ID: {task.id}")

    finally:
        db.close()


@cli.command()
def sync_all():
    """Trigger incremental sync for all users"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        click.echo(f"Found {len(users)} users")

        for user in users:
            # Create sync job
            sync_job = SyncJob(
                user_id=user.id,
                job_type=JobType.INCREMENTAL_SYNC,
                status=JobStatus.PENDING
            )
            db.add(sync_job)
            db.commit()
            db.refresh(sync_job)

            # Trigger sync
            task = sync_matches_incremental.delay(user.id, sync_job.id)
            click.echo(f"  - {user.persona_name}: Job {sync_job.id}, Task {task.id}")

    finally:
        db.close()


@cli.command()
def list_users():
    """List all registered users"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        click.echo(f"Total users: {len(users)}\n")

        for user in users:
            click.echo(f"Steam ID: {user.steam_id}")
            click.echo(f"  Name: {user.persona_name}")
            click.echo(f"  Last Sync: {user.last_sync_at or 'Never'}")
            click.echo()

    finally:
        db.close()


@cli.command()
def init_heroes():
    """Initialize heroes database from Dota 2 API"""
    from app.models import Hero

    db = SessionLocal()
    try:
        dota_api = DotaAPIService()

        click.echo("Fetching heroes from API...")
        heroes_data = asyncio.run(dota_api.get_heroes())

        click.echo(f"Found {len(heroes_data)} heroes")

        for hero_data in heroes_data:
            if settings.API_PROVIDER == "valve":
                hero_id = hero_data.get("id")
                name = hero_data.get("name", "").replace("npc_dota_hero_", "")
                localized_name = hero_data.get("localized_name", name)

                hero = Hero(
                    id=hero_id,
                    name=name,
                    localized_name=localized_name
                )
            else:  # OpenDota
                hero = Hero(
                    id=hero_data.get("id"),
                    name=hero_data.get("name"),
                    localized_name=hero_data.get("localized_name"),
                    primary_attr=hero_data.get("primary_attr"),
                    attack_type=hero_data.get("attack_type"),
                    roles=hero_data.get("roles", []),
                    img=hero_data.get("img"),
                    icon=hero_data.get("icon")
                )

            # Check if hero exists
            existing = db.query(Hero).filter(Hero.id == hero.id).first()
            if existing:
                # Update
                for key, value in hero.__dict__.items():
                    if key != "_sa_instance_state" and value is not None:
                        setattr(existing, key, value)
            else:
                db.add(hero)

        db.commit()
        click.echo("Heroes database initialized successfully")

    finally:
        db.close()


@cli.command()
@click.argument('user_id', type=int)
def job_status(user_id: int):
    """Check sync job status for a user"""
    db = SessionLocal()
    try:
        jobs = (
            db.query(SyncJob)
            .filter(SyncJob.user_id == user_id)
            .order_by(SyncJob.created_at.desc())
            .limit(10)
            .all()
        )

        if not jobs:
            click.echo("No sync jobs found")
            return

        for job in jobs:
            click.echo(f"\nJob ID: {job.id}")
            click.echo(f"  Type: {job.job_type.value}")
            click.echo(f"  Status: {job.status.value}")
            click.echo(f"  Progress: {job.processed_matches}/{job.total_matches}")
            click.echo(f"  New Matches: {job.new_matches}")
            click.echo(f"  Created: {job.created_at}")
            if job.error_message:
                click.echo(f"  Error: {job.error_message}")

    finally:
        db.close()


@cli.command()
def clean_stuck_jobs():
    """Clean up stuck sync jobs (jobs marked as PENDING or RUNNING but no longer active)"""
    from sqlalchemy.sql import func

    db = SessionLocal()
    try:
        # Find all jobs marked as PENDING or RUNNING
        stuck_jobs = db.query(SyncJob).filter(
            SyncJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
        ).all()

        if not stuck_jobs:
            click.echo("No stuck jobs found")
            return

        click.echo(f"Found {len(stuck_jobs)} stuck jobs")

        for job in stuck_jobs:
            click.echo(f"  - Job ID: {job.id}, Type: {job.job_type.value}, Created: {job.created_at}")
            job.status = JobStatus.FAILED
            job.completed_at = func.now()
            job.error_message = "Job was stuck and automatically cleaned up"

        db.commit()
        click.echo(f"Successfully cleaned up {len(stuck_jobs)} stuck jobs")

    finally:
        db.close()


if __name__ == "__main__":
    cli()
