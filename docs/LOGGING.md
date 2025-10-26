# Logging System

## Overview

The application now has a dual logging system:
- **Stdout**: All logs (INFO and above) for `docker compose logs`
- **Files**: Only ERROR logs saved to persistent files in `logs/` folder

## Log File Locations

```
logs/
├── backend/
│   └── error.log          # Backend API errors
├── celery-worker/
│   └── error.log          # Celery worker task errors
├── celery-beat/
│   └── error.log          # Celery beat scheduler errors
└── flower/
    └── error.log          # Flower monitoring errors
```

## Viewing Logs

### Method 1: View in Real-time (Stdout)

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery-worker

# Last 100 lines
docker compose logs --tail=100 backend

# Since specific time
docker compose logs --since 10m backend
```

### Method 2: View Error Files

```bash
# View backend errors
cat logs/backend/error.log

# Tail errors in real-time
tail -f logs/backend/error.log

# View all errors from all services
tail -f logs/**/error.log

# Search for specific error
grep "DatabaseError" logs/backend/error.log
```

## Log Rotation

Error log files are automatically rotated:
- **Max size**: 10MB per file
- **Backups**: 5 files kept (error.log, error.log.1, ... error.log.5)
- **Automatic**: Oldest files are deleted automatically

Example rotation:
```
logs/backend/
├── error.log       # Current (newest)
├── error.log.1     # Previous
├── error.log.2
├── error.log.3
├── error.log.4
└── error.log.5     # Oldest
```

## Log Levels

### Stdout (Console):
- **INFO**: General information
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

### Files (Disk):
- **ERROR**: Error messages only
- **CRITICAL**: Critical errors only

## Log Format

### Console Format:
```
2025-10-26 13:00:00 - app.main - INFO - Starting Dota Stats API...
```

### File Format (more detailed):
```
2025-10-26 13:00:00 - app.main - ERROR - /app/app/main.py:45 - Failed to initialize database: connection refused
```

## Configuration

### Backend API Logging

Configured in `backend/app/logging_config.py`:
- Rotating file handler (10MB, 5 backups)
- Both console and file outputs
- ERROR and above to file

### Celery Logging

Configured via command-line flags in compose files:
- `--loglevel=info` for stdout
- `--logfile=/app/logs/error.log` for file

### Flower Logging

Configured via command-line flags:
- `--logging=error` for stdout
- `--log-file-prefix=/app/logs/error.log` for file

## Checking for Errors

### Quick Error Check

```bash
# Any errors in last hour?
find logs -name "error.log" -exec grep -l "ERROR" {} \;

# Count errors per service
wc -l logs/*/error.log

# Recent errors (last 20 lines)
tail -20 logs/backend/error.log
```

### Error Patterns

```bash
# Database errors
grep -r "DatabaseError" logs/

# API errors
grep -r "HTTP.*500" logs/

# Connection errors
grep -r "ConnectionError" logs/

# All errors today
grep "$(date +%Y-%m-%d)" logs/*/error.log
```

## Troubleshooting

### No log files created?

Check if containers are running:
```bash
docker compose ps
```

Check volume mounts:
```bash
docker compose config | grep -A 2 "volumes:"
```

### Permissions issues?

Fix log directory permissions:
```bash
chmod -R 755 logs/
```

### Log files too large?

Manually clean old logs:
```bash
# Remove old rotated logs
find logs -name "*.log.*" -delete

# Or keep only recent ones
find logs -name "*.log.*" -mtime +7 -delete
```

## Monitoring Recommendations

### Daily Checks

```bash
# Check if any errors occurred today
grep "$(date +%Y-%m-%d)" logs/*/error.log | head -20
```

### Weekly Cleanup

```bash
# Remove logs older than 30 days
find logs -name "*.log.*" -mtime +30 -delete
```

### Integration with Monitoring

Consider adding to cron for automated monitoring:
```bash
# Add to crontab
0 9 * * * grep "ERROR" /path/to/dota-stats/logs/*/error.log | mail -s "Dota Stats Errors" your@email.com
```

## Log Analysis Tips

### Most common errors

```bash
grep "ERROR" logs/backend/error.log | sort | uniq -c | sort -rn | head -10
```

### Errors by hour

```bash
grep "ERROR" logs/backend/error.log | cut -d' ' -f2 | cut -d':' -f1 | sort | uniq -c
```

### Specific error context

```bash
# Show 5 lines before and after error
grep -C 5 "DatabaseError" logs/backend/error.log
```

## Best Practices

1. **Check error logs regularly** - Don't wait for issues to escalate
2. **Archive old logs** - Keep logs directory manageable
3. **Monitor disk space** - Logs can grow quickly under errors
4. **Use timestamps** - All logs include timestamps for correlation
5. **Grep is your friend** - Use grep patterns to find specific issues

## Examples

### Example: Check if sync failed

```bash
grep "sync_matches" logs/celery-worker/error.log
```

### Example: Find API timeout errors

```bash
grep -i "timeout" logs/backend/error.log
```

### Example: Monitor logs during sync

```bash
# Terminal 1: Watch errors
tail -f logs/celery-worker/error.log

# Terminal 2: Watch all logs
docker compose logs -f celery-worker
```

---

**Log files persist across container restarts** - You won't lose error history when restarting services.
