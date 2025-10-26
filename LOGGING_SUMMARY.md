# Logging System Summary

## ✅ What Was Added

### Dual Logging System:
1. **Stdout** - All logs visible with `docker compose logs -f`
2. **Files** - Only ERROR logs saved to `logs/` folder on disk

## 📁 File Structure

```
logs/
├── backend/
│   └── error.log
├── celery-worker/
│   └── error.log
├── celery-beat/
│   └── error.log
└── flower/
    └── error.log
```

## 🚀 Quick Start

### View live logs (all levels):
```bash
docker compose logs -f
docker compose logs -f backend
docker compose logs -f celery-worker
```

### View error files:
```bash
# View backend errors
cat logs/backend/error.log

# Watch errors in real-time
tail -f logs/backend/error.log

# Watch all service errors
tail -f logs/**/error.log
```

## 📝 What Goes Where

### Stdout (Console):
- ✅ INFO messages
- ✅ WARNING messages  
- ✅ ERROR messages
- ✅ CRITICAL messages

### Files (Disk):
- ⛔ INFO messages (not saved)
- ⛔ WARNING messages (not saved)
- ✅ ERROR messages (saved)
- ✅ CRITICAL messages (saved)

## 🔄 Log Rotation

- **Automatic** rotation when file reaches 10MB
- **5 backup files** kept (error.log.1 through error.log.5)
- Oldest files automatically deleted

## 📄 Files Changed

1. **Created**:
   - `backend/app/logging_config.py` - Logging configuration
   - `logs/*/` directories - Log file storage
   - `LOGGING.md` - Full documentation

2. **Modified**:
   - `backend/app/main.py` - Added logging setup
   - `compose.yaml` - Added log volume mounts
   - `compose.dev.yaml` - Added log volume mounts
   - `.gitignore` - Ignore log files but keep structure

## 🎯 Common Commands

```bash
# Check for any errors today
grep "$(date +%Y-%m-%d)" logs/*/error.log

# Count total errors
wc -l logs/*/error.log

# Find specific error
grep -r "DatabaseError" logs/

# Monitor errors during sync
tail -f logs/celery-worker/error.log
```

## ✨ Benefits

1. **No more pasting logs** - Just check `logs/` folder
2. **Persistent** - Errors survive container restarts
3. **Automatic rotation** - No manual cleanup needed
4. **Easy searching** - Use grep on error files
5. **Space efficient** - Only errors are saved to disk

## 🔍 Next Steps

1. Restart services to enable logging:
   ```bash
   docker compose down
   docker compose up -d
   ```

2. Test error logging:
   ```bash
   # Errors will appear in both stdout and files
   docker compose logs -f backend
   tail -f logs/backend/error.log
   ```

3. Check for errors periodically:
   ```bash
   cat logs/*/error.log
   ```

---

**Full Documentation**: See `LOGGING.md` for detailed information
**Date**: 2025-10-26
