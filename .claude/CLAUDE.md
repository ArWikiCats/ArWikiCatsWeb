# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ArWikiCatsWeb is a Flask-based web service for resolving Arabic Wikipedia category labels. It translates English category names to their Arabic equivalents and provides both a REST API and a web interface.

**External Dependency**: The `ArWikiCats` library (pip package) provides the core category resolution logic via `ArWikiCats.getlabel()`.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing

# Run development server
cd src && python app.py           # Production mode
cd src && python app.py debug     # Debug mode with auto-reload
flask --app src.app run --debug   # Alternative via Flask CLI

# Run tests
pytest                           # All tests
pytest --cov=src                 # With coverage
pytest tests/test_api.py -v      # Specific test file
pytest -m network                # Network tests (skipped by default)

# Linting/formatting
black .
isort .
ruff check .
ruff format .
```

## Architecture

### Layered Structure

```
Entry Points (app.py, app1.py)
    ↓
Application Factory (create_app in src/app/__init__.py)
    ↓
Routing Layer (routes/api.py, routes/ui.py)
    ↓
Business Logic (logs_bot.py, ArWikiCats library)
    ↓
Data Access Layer (logs_db/bot.py, logs_db/db.py)
    ↓
Storage (SQLite - new_logs.db)
```

### Key Patterns

- **Application Factory**: `create_app()` in `src/app/__init__.py` creates the Flask instance, registers blueprints, and configures CORS
- **Two Blueprints**: `api_bp` (`/api/*`) for REST endpoints, `ui_bp` (`/`) for web interface
- **Hybrid Rendering**: Jinja2 templates render initial HTML; JavaScript fetches dynamic data via AJAX
- **Data Access Layer**: Two-tier structure - `logs_db/bot.py` (high-level operations) wraps `logs_db/db.py` (low-level SQL)

### Important Files

| File | Purpose |
|------|---------|
| `src/app/__init__.py` | Application factory with CORS for ar.wikipedia.org |
| `src/app/routes/api.py` | All REST API endpoints (requires User-Agent header) |
| `src/app/routes/ui.py` | Web UI routes that render Jinja2 templates |
| `src/app/logs_bot.py` | Business logic for log retrieval and analysis |
| `src/app/logs_db/db.py` | Core SQL operations, database initialization |
| `src/app/logs_db/bot.py` | High-level DB operations like `log_request()` |

## API Requirements

**All API requests require a `User-Agent` header** - returns 400 if missing.

```bash
curl -H "User-Agent: MyBot/1.0" http://localhost:5000/api/Category:Yemen
```

## Database

- **Engine**: SQLite
- **File**: `new_logs.db` (in `src/` locally, `$HOME/www/python/dbs/` on Toolforge)
- **Tables**: `logs` (general API logs), `list_logs` (batch endpoint logs)
- **Schema**: id, endpoint, request_data, response_status, response_time, response_count, timestamp, date_only

## Code Style

Configured in `pyproject.toml`:
- **Line length**: 120 characters
- **Formatter**: Black (with isort profile)
- **Target**: Python 3.10+ (Black), Python 3.13 (Ruff)

## Deployment

- **Platform**: Wikimedia Toolforge (Kubernetes)
- **Config**: `service.template` - Python 3.11, 3 CPU, 6Gi memory, 2 replicas
- **CI/CD**: GitHub Actions - tests run on PRs, auto-deploy on push to main
