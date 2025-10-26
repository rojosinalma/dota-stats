# Coding Standards

## General Principles

- Write code for humans first, machines second
- Prefer explicit over implicit
- Favor composition over inheritance
- Keep functions small and focused
- Write tests for critical business logic
- **One task per file**: Each Celery task should be in its own file for clarity and maintainability

## Style Guidelines

### NO Emojis
- Never use emojis in code, comments, documentation, or TODO files
- Use clear professional language instead

### Naming Conventions

**Python:**
- `snake_case` for variables, functions, methods
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Prefix private methods with `_`

**TypeScript:**
- `camelCase` for variables, functions
- `PascalCase` for classes, interfaces, types, components
- `UPPER_CASE` for constants

### Comments & Documentation

- Add docstrings to all public functions/classes
- Use type hints in Python
- Document complex logic with inline comments
- Keep comments up-to-date with code changes
- Explain WHY, not WHAT (code shows what)

### Error Handling

**Python:**
```python
# Good: Specific exceptions with logging
try:
    result = await api.get_data()
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
    raise
except httpx.RequestError as e:
    logger.error(f"Request error: {str(e)}")
    raise

# Bad: Bare except
try:
    result = await api.get_data()
except:
    pass
```

**TypeScript:**
```typescript
// Good: Specific error handling
try {
  const response = await api.getData()
  return response.data
} catch (error) {
  if (axios.isAxiosError(error)) {
    console.error('API error:', error.response?.data)
  }
  throw error
}

// Bad: Silent failure
try {
  const response = await api.getData()
} catch (error) {
  // Nothing
}
```

## Logging Standards

### Log Levels

- **DEBUG**: Detailed diagnostic info (API requests, parameters, responses)
- **INFO**: General informational messages (task started, completed)
- **WARNING**: Something unexpected but recoverable
- **ERROR**: Error events that might still allow the app to continue
- **CRITICAL**: Severe errors causing application failure

### Logging Format

```python
# Good: Structured logging with context
logger.info(f"Starting sync for user_id={user_id}, job_id={job_id}")
logger.debug(f"Fetching match history for account_id={account_id}, limit={limit}")
logger.error(f"HTTP error {status_code} for match_id={match_id}: {error_text}")

# Bad: Vague logging
logger.info("Starting sync")
logger.error("Error occurred")
```

### What to Log

**Always log:**
- API requests (with parameters)
- API responses (status codes)
- API errors (with full error text)
- Task start/completion
- Database operations that modify data
- User actions (login, logout, sync triggers)

**Never log:**
- Passwords or secrets
- Full API keys (mask them)
- Personal identifying information unnecessarily
- Inside tight loops (use aggregation)

## Git Commit Standards

### Commit Message Format
```
<type>: <subject>

<body>

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat: Add two-phase match sync for better fault tolerance

- Phase 1: Collect all match IDs from GetMatchHistory
- Phase 2: Fetch details for each match
- Never lose match IDs even if API fails
- Shows accurate progress immediately

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Testing Standards

### What to Test
- API endpoints (happy path and errors)
- Business logic in services
- Data transformations
- Edge cases and error conditions

### Test Organization
```
tests/
├── unit/           # Unit tests (isolated)
├── integration/    # Integration tests (DB, APIs)
└── e2e/           # End-to-end tests
```

## Project Organization

### Task Structure
Each Celery task must be in its own file for clarity:

```
backend/app/tasks/
├── __init__.py                    # Export all tasks
├── celery_app.py                  # Celery app configuration
├── sync_helpers.py                # Shared helper functions (phase logic, stubs, updates)
├── collect_match_ids_task.py      # Phase 1: Collect match IDs
├── fetch_match_details_task.py    # Phase 2: Fetch match details
└── periodic_sync_task.py          # Periodic sync for all users
```

**Sync Architecture:**
- All sync operations use two-phase approach:
  - Phase 1: Collect match IDs (fast, reliable)
  - Phase 2: Fetch match details (can fail, retryable)
- Three user-facing options:
  - `SYNC_ALL`: Collect all historical IDs + fetch all details
  - `SYNC_MISSING`: Skip ID collection, only fetch details for stubs
  - `SYNC_INCREMENTAL`: Collect new IDs + fetch their details

**Benefits:**
- Easy to find specific tasks
- Clear separation of concerns
- Simpler imports and dependencies
- Better for code review and maintenance
- Never lose match IDs even if API fails

## Security Standards

### API Keys & Secrets
- Never hardcode secrets
- Use environment variables
- Don't log full API keys
- Rotate keys regularly

### Input Validation
- Validate all user inputs
- Use Pydantic for API request validation
- Sanitize inputs before DB queries
- Use parameterized queries (SQLAlchemy ORM)

### Authentication
- Use secure session cookies
- Set httponly and samesite flags
- Implement CSRF protection
- Use HTTPS in production

## Performance Standards

### Database
- Add indexes on frequently queried columns
- Use connection pooling
- Avoid N+1 queries
- Use pagination for large datasets

### API Calls
- Implement rate limiting
- Use connection pooling (httpx AsyncClient)
- Add timeouts to all requests
- Cache responses when appropriate

### Frontend
- Lazy load routes and components
- Use React Query for caching
- Debounce user inputs
- Optimize images and assets

## Code Review Checklist

Before considering code complete:
- [ ] No emojis in code or documentation
- [ ] All functions have type hints/types
- [ ] Error handling with proper logging
- [ ] No hardcoded secrets or API keys
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] No console.log or print() left in code
- [ ] Environment variables added to .env.example
- [ ] Database migrations created if needed
- [ ] README updated if user-facing changes
