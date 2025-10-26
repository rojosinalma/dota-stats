# Dota Stats

A comprehensive Dota 2 statistics tracking application that helps you analyze your matches, track your performance, and improve your gameplay.

## Features

- **Steam OAuth Authentication** - Secure login using your Steam account
- **Match History** - Complete list of all your Dota 2 matches with detailed statistics
- **Hero Statistics** - Per-hero analytics including win rate, KDA, GPM/XPM, and more
- **Dashboard** - Overview of your performance with charts and visualizations
- **Time-based Analysis** - Track your progress over daily, weekly, monthly, and custom periods
- **Players Encountered** - See who you frequently play with and your win rate together
- **Background Sync** - Automatic hourly match synchronization
- **Manual Refresh** - Trigger match updates on demand
- **Detailed Match View** - Deep dive into individual match statistics, items, skills, and damage breakdowns

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database for storing match data
- **Celery** - Distributed task queue for background jobs
- **RabbitMQ** - Message broker for Celery
- **SQLAlchemy** - ORM for database interactions
- **Steam Web API / OpenDota API** - Data sources for match information

### Frontend
- **React** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **TanStack Query** - Data fetching and caching
- **Recharts** - Data visualization
- **React Router** - Client-side routing

### Deployment
- **Docker Compose** - Container orchestration
- **Nginx** - Web server for frontend

## Prerequisites

- Docker and Docker Compose
- Steam Web API Key ([Get one here](https://steamcommunity.com/dev/apikey))

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd dota-stats
```

### 2. Configure Environment Variables

Copy the example environment file and edit it with your credentials:

```bash
cp .env.example .env
```

Edit `.env` and configure the following required variables:

```env
# Steam API Configuration
STEAM_API_KEY=your_steam_api_key_here
STEAM_OPENID_CALLBACK_URL=http://localhost/auth/callback

# Database Configuration
POSTGRES_USER=dotastats
POSTGRES_PASSWORD=change_this_secure_password
POSTGRES_DB=dotastats

# Security
SECRET_KEY=change_this_to_a_random_string_in_production
```

### 3. Start the Application

```bash
docker compose up -d
```

This will start all services:
- PostgreSQL database
- RabbitMQ message broker
- FastAPI backend
- Celery worker and beat scheduler
- React frontend with Nginx

### 4. Access the Application

Open your browser and navigate to:

```
http://localhost
```

### 5. Initialize Heroes Database (Optional)

To populate the heroes database with Dota 2 hero information:

```bash
docker compose exec backend python cli.py init-heroes
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STEAM_API_KEY` | Your Steam Web API key | Required |
| `STEAM_OPENID_CALLBACK_URL` | OpenID callback URL | Required |
| `API_PROVIDER` | API provider: `valve` or `opendota` | `valve` |
| `SYNC_INTERVAL_MINUTES` | Auto-sync interval | `60` |
| `RATE_LIMIT_DELAY` | Delay between API calls (seconds) | `1.0` |
| `POSTGRES_USER` | Database username | `dotastats` |
| `POSTGRES_PASSWORD` | Database password | Required |
| `POSTGRES_DB` | Database name | `dotastats` |
| `SECRET_KEY` | Session encryption key | Required |

### Steam API Setup

1. Go to [Steam Web API Key page](https://steamcommunity.com/dev/apikey)
2. Enter a domain name (can be anything, e.g., "localhost")
3. You'll receive your Steam Web API Key
4. Add it to `.env` as `STEAM_API_KEY`

**Note**: This application uses Steam OpenID for authentication, which doesn't require OAuth credentials - just the Web API key!

### API Provider

The application supports two API providers:

- **Valve Web API** (default) - Official Steam API, requires API key
- **OpenDota API** - Community-driven alternative, more detailed stats

Set `API_PROVIDER=opendota` in `.env` to use OpenDota.

## CLI Commands

The backend includes a CLI tool for managing the application:

### List all users
```bash
docker compose exec backend python cli.py list-users
```

### Trigger full sync for a user
```bash
docker compose exec backend python cli.py sync-user <steam_id>
```

### Trigger incremental sync for all users
```bash
docker compose exec backend python cli.py sync-all
```

### Check job status
```bash
docker compose exec backend python cli.py job-status <user_id>
```

### Initialize heroes database
```bash
docker compose exec backend python cli.py init-heroes
```

## Development

### Development Mode with Hot-Reload (Recommended)

The easiest way to develop is using the development Docker Compose configuration which provides hot-reload for all services:

```bash
# Start all services in development mode
docker compose -f compose.dev.yaml up

# Or run in background
docker compose -f compose.dev.yaml up -d
```

**What you get with dev mode:**
- ✅ **Backend Hot-Reload** - FastAPI automatically restarts when you change Python files
- ✅ **Frontend Hot-Reload** - Vite dev server with instant updates (no page refresh needed)
- ✅ **Celery Auto-Restart** - Worker automatically restarts when task files change
- ✅ **Volume Mounts** - All code changes reflect immediately without rebuilding
- ✅ **Debug Logging** - More verbose logging for troubleshooting

**Services:**
- Frontend: http://localhost:8383
- Backend API: http://localhost:8282
- Flower (Celery Monitor): http://localhost:5555
- RabbitMQ Management: http://localhost:15672

**Rebuild containers after dependency changes:**
```bash
# Only needed when you modify requirements.txt or package.json
docker compose -f compose.dev.yaml build
docker compose -f compose.dev.yaml up
```

### Local Development (Without Docker)

If you prefer to run services locally:

#### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

The dev server will be available at `http://localhost:3000` with API proxy to the backend.

#### Running Celery Worker Locally

```bash
cd backend
# With auto-reload on file changes
watchmedo auto-restart --directory=. --pattern='*.py' --recursive -- celery -A app.tasks.celery_app worker --loglevel=info

# Or without auto-reload
celery -A app.tasks.celery_app worker --loglevel=info
```

#### Running Celery Beat Locally

```bash
cd backend
celery -A app.tasks.celery_app beat --loglevel=info
```

## Project Structure

```
dota-stats/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Celery tasks
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── main.py          # FastAPI app
│   ├── cli.py               # CLI tool
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend container
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client
│   │   ├── hooks/           # Custom hooks
│   │   ├── utils/           # Utility functions
│   │   └── main.tsx         # App entry point
│   ├── package.json         # Node dependencies
│   ├── Dockerfile           # Frontend container
│   └── nginx.conf           # Nginx configuration
├── compose.yaml             # Docker Compose config
├── .env.example             # Environment template
└── README.md                # This file
```

## Database Schema

### Main Tables

- **users** - Steam user information
- **matches** - Match data with player statistics
- **match_players** - All players in each match
- **heroes** - Dota 2 hero information
- **players_encountered** - Frequently played with players
- **sync_jobs** - Background job tracking

## API Endpoints

### Authentication
- `GET /auth/login` - Redirect to Steam login
- `GET /auth/callback` - OAuth callback
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

### Matches
- `GET /matches` - List matches (with filters and pagination)
- `GET /matches/{match_id}` - Get match details

### Statistics
- `GET /stats/dashboard` - Dashboard overview
- `GET /stats/player` - Player statistics
- `GET /stats/heroes` - Hero statistics
- `GET /stats/players-encountered` - Frequently played with
- `GET /stats/time-based` - Time-based statistics

### Sync
- `POST /sync/trigger` - Manually trigger sync
- `GET /sync/jobs` - List sync jobs
- `GET /sync/jobs/{job_id}` - Get job status
- `GET /sync/status` - Current sync status

### Heroes
- `GET /heroes` - List all heroes

## Troubleshooting

### Database Connection Issues

```bash
docker compose logs postgres
docker compose restart postgres
```

### Backend Not Starting

Check logs:
```bash
docker compose logs backend
```

### Celery Worker Issues

Check worker logs:
```bash
docker compose logs celery-worker
```

### Frontend Build Errors

Rebuild the frontend:
```bash
docker compose build frontend
docker compose up -d frontend
```

### Steam Authentication Failed

1. Verify Steam API key is correct
2. Check OAuth callback URL matches configuration
3. Ensure Steam Web API is accessible

## Performance Optimization

### Rate Limiting

The application implements rate limiting to avoid hitting API limits:
- Configurable delay between API calls
- Automatic retry on rate limit errors
- Incremental sync to minimize API calls

### Database Optimization

- Indexes on frequently queried columns
- Cached match data to avoid repeated API calls
- Efficient aggregation queries for statistics

### Background Jobs

- Periodic sync runs every hour (configurable)
- Initial full sync fetches all historical matches
- Incremental sync only fetches new matches

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Steam Web API for match data
- OpenDota for alternative data source
- Dota 2 community for support and feedback

## Support

For issues and questions:
1. Check existing issues on GitHub
2. Create a new issue with detailed information
3. Include logs and error messages

## Roadmap

- [ ] Real-time match notifications
- [ ] Advanced filtering and search
- [ ] Compare stats with friends
- [ ] Export data to CSV/JSON
- [ ] Mobile-responsive improvements
- [ ] Hero recommendations based on stats
- [ ] Team composition analysis
- [ ] Match predictions

---

Built with by the Dota Stats team
