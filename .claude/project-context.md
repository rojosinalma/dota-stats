# Dota Stats Project Context

This file contains persistent context and instructions for Claude Code across sessions.

## Project Overview

A Dota 2 statistics tracking application with:
- **Backend**: FastAPI + PostgreSQL + Celery + RabbitMQ
- **Frontend**: React + TypeScript + Vite
- **APIs**: Valve Web API (primary) and OpenDota API (alternative)
- **Deployment**: Docker Compose

## Code Style & Preferences

### General Rules
- **No emojis** in code, documentation, or TODO files
- Use clear, professional language
- Prefer explicit over clever code

### Python (Backend)
- Use type hints for all functions
- Follow PEP 8 style guide
- Use descriptive variable names
- Add docstrings to all public functions/classes
- Prefer async/await for I/O operations

### TypeScript (Frontend)
- Use functional components with hooks
- Prefer named exports over default exports
- Use TypeScript strict mode
- Add JSDoc comments for complex functions

### Logging
- Use `LOG_LEVEL` environment variable (INFO or DEBUG)
- All logs go to both stdout AND log files
- Use structured logging with context (user_id, job_id, etc.)
- Log API requests/responses with debug level
- Log errors with full stack traces

## Architecture Decisions

### API Rate Limiting
- Valve API: 7 seconds between requests (`VALVE_RATE_LIMIT_DELAY`)
- OpenDota API: 1 second between requests (`OPENDOTA_RATE_LIMIT_DELAY`)
- Never use a single `RATE_LIMIT_DELAY` variable

### Logging Configuration
- **Primary variable**: `LOG_LEVEL` (not DEBUG)
- Values: INFO or DEBUG
- Both stdout and file output enabled
- Celery workers use same logging configuration
- Never clear all logging handlers (preserves Celery's own logs)

### Development Workflow
- Use `compose.dev.yaml` for development (hot-reload enabled)
- Backend: uvicorn with --reload
- Frontend: Vite dev server with HMR
- Celery: watchmedo for auto-restart on code changes
- All services output logs to stdout (no --logfile flags)

## Environment Variables

### Required
- `STEAM_API_KEY`: Steam Web API key
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Database credentials
- `SECRET_KEY`: Session encryption key

### Optional with Defaults
- `LOG_LEVEL=INFO`: Logging verbosity (INFO or DEBUG)
- `API_PROVIDER=valve`: API provider (valve or opendota)
- `VALVE_RATE_LIMIT_DELAY=7.0`: Valve API rate limit
- `OPENDOTA_RATE_LIMIT_DELAY=1.0`: OpenDota API rate limit
- `SYNC_INTERVAL_MINUTES=60`: Auto-sync interval

### Deprecated/Removed
- `DEBUG`: Removed, use `LOG_LEVEL` instead
- `RATE_LIMIT_DELAY`: Split into provider-specific delays

## Common Commands

### Development
```bash
# Start dev environment with hot-reload
docker compose -f compose.dev.yaml up

# Restart specific service
docker compose -f compose.dev.yaml restart celery-worker

# View logs
docker compose -f compose.dev.yaml logs -f celery-worker

# Rebuild after dependency changes
docker compose -f compose.dev.yaml build
```

### Database
```bash
# Create migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Run migrations
docker compose exec backend alembic upgrade head
```

### CLI Commands
```bash
# List users
docker compose exec backend python cli.py list-users

# Sync user matches
docker compose exec backend python cli.py sync-user <steam_id>

# Initialize heroes
docker compose exec backend python cli.py init-heroes
```

## Known Issues & Current Work

### In Progress
1. **Two-Phase Match Sync**: Separate match ID collection from detail fetching
   - See TODO.md for full plan
   - Improves fault tolerance and progress tracking
   - Shows accurate totals immediately

### Known Bugs
1. **Cancel Sync**: Frontend shows cancelled but Celery keeps processing
   - Backend marks job as CANCELLED
   - Worker doesn't stop immediately
   - Needs task revocation check in sync loop

### Completed
- Valve API error handling (500 errors logged)
- Logging configuration (LOG_LEVEL standardization)
- API refactoring (valve_api.py, opendota_api.py separation)
- Hot-reload development setup

## File Organization

### Documentation Location
- Root: Only README.md and TODO.md
- Other docs: `docs/` directory
  - COMPLETE_CHANGELOG.md
  - LOGGING.md
  - LOGGING_SUMMARY.md
  - MIGRATION_GUIDE.md
  - PROJECT_SUMMARY.md
  - QUICKSTART.md
  - SYNC_IMPROVEMENTS.md
  - UPDATES.md

### Backend Structure
```
backend/app/
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── routes/          # FastAPI endpoints
├── services/        # Business logic
│   ├── valve_api.py      # Valve API implementation
│   ├── opendota_api.py   # OpenDota API implementation
│   └── dota_api.py       # API factory/router
├── tasks/           # Celery tasks
├── config.py        # Settings (Pydantic)
├── logging_config.py # Logging setup
├── database.py      # DB connection
└── main.py          # FastAPI app
```

## Important Notes

- Always read TODO.md for current priorities
- Check .env.example when adding new env variables
- Update both .env and .env.example together
- Never use emojis in code or documentation
- All API calls must have proper error handling and logging
- Preserve Celery's logging handlers (don't clear all handlers)
