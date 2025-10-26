# Quick Start Guide

## Prerequisites Checklist

- [ ] Docker and Docker Compose installed
- [ ] Steam Web API Key ([Get here](https://steamcommunity.com/dev/apikey))
- [ ] Steam account for authentication

## Setup in 5 Minutes

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set these required fields:

```env
STEAM_API_KEY=YOUR_STEAM_WEB_API_KEY_HERE
STEAM_OPENID_CALLBACK_URL=http://localhost/auth/callback
POSTGRES_PASSWORD=change_me
SECRET_KEY=change_me_to_random_string
```

### 2. Start All Services

```bash
docker compose up -d
```

Wait 30-60 seconds for all services to start.

### 3. Initialize Heroes (Optional but Recommended)

```bash
docker compose exec backend python cli.py init-heroes
```

### 4. Open Application

Navigate to: **http://localhost**

Click "Sign in with Steam" and you're ready to go!

## First Time Setup

1. **Login**: Use Steam to authenticate
2. **Sync Matches**: Click "Sync Matches" button on dashboard
3. **Wait**: First sync fetches all historical matches (may take a few minutes)
4. **Explore**: Browse your stats, matches, and hero performance

## Development Mode

To run with hot-reload for development:

```bash
docker compose -f compose.dev.yaml up
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- RabbitMQ Management: http://localhost:15672 (guest/guest)

## Useful Commands

### View Logs
```bash
docker compose logs -f backend
docker compose logs -f celery-worker
```

### Restart Services
```bash
docker compose restart backend
docker compose restart celery-worker
```

### Stop All Services
```bash
docker compose down
```

### Stop and Remove Data
```bash
docker compose down -v
```

## Troubleshooting

### Services won't start
```bash
docker compose down
docker compose up -d
docker compose ps
```

### Database issues
```bash
docker compose restart postgres
docker compose logs postgres
```

### Frontend not loading
```bash
docker compose build frontend
docker compose up -d frontend
```

### Check if services are healthy
```bash
docker compose ps
```

All services should show "healthy" or "running".

## Next Steps

- Configure automatic sync interval in `.env` (default: 60 minutes)
- Set up Cloudflare Tunnel for external access
- Customize game mode filters
- Explore detailed match statistics

## Getting Help

- Check the main [README.md](README.md) for detailed documentation
- Review logs: `docker compose logs -f`
- Verify environment variables in `.env`
- Ensure Steam API key is valid

---

**Ready to track your Dota 2 stats!**
