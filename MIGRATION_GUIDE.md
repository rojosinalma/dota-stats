# Database Migration Guide

## Adding the CANCELLED Status

The sync cancellation feature requires adding a new value to the PostgreSQL enum type.

### Migration Already Run ✅

The migration has been executed successfully. The `jobstatus` enum now includes:
- pending
- running
- completed
- failed
- **cancelled** ← New!

### How It Was Done

```bash
docker compose exec backend alembic upgrade head
```

This executed the migration file: `backend/alembic/versions/001_add_cancelled_status.py`

### Verify Migration

To check if the migration is applied:

```bash
docker compose exec postgres psql -U dotastats -d dotastats -c "\dT+ jobstatus"
```

You should see all 5 enum values including 'cancelled'.

### If You Need to Run It Again

If you reset your database or are setting up a new instance:

```bash
# Run all migrations
docker compose exec backend alembic upgrade head
```

### Troubleshooting

**Error: "invalid input value for enum jobstatus: 'CANCELLED'"**

This means the migration hasn't been run yet. Solution:
```bash
docker compose exec backend alembic upgrade head
```

**Error: "alembic command not found"**

Make sure you're inside the backend container:
```bash
docker compose exec backend bash
cd /app
alembic upgrade head
```

**Error: "value already exists"**

This is safe to ignore - it means the migration was already applied.

### Future Migrations

To create new migrations:

```bash
# Auto-generate migration from model changes
docker compose exec backend alembic revision --autogenerate -m "description"

# Create blank migration
docker compose exec backend alembic revision -m "description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback one migration
docker compose exec backend alembic downgrade -1
```

### Migration Files Location

All migration files are in: `backend/alembic/versions/`

Current migrations:
- `001_add_cancelled_status.py` - Adds CANCELLED enum value

---

**Status**: Migration completed successfully ✅
**Date**: 2025-10-26
