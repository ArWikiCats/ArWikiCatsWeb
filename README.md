# ArWikiCats Web Service

[![CI/CD](https://github.com/ArWikiCats/ArWikiCatsWeb/workflows/pytest/badge.svg)](https://github.com/ArWikiCats/ArWikiCatsWeb/actions)
[![codecov](https://codecov.io/gh/ArWikiCats/ArWikiCatsWeb/branch/main/graph/badge.svg)](https://codecov.io/gh/ArWikiCats/ArWikiCatsWeb)
<!-- [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ArWikiCats/ArWikiCatsWeb) -->

A Flask-based web service for resolving Arabic Wikipedia category labels. Provides both a web interface and REST API for working with Arabic Wikipedia categories.

## Features

- **REST API**: Resolve Arabic category labels via HTTP endpoints
- **Web Interface**: Interactive UI for testing and exploring category labels
- **Batch Processing**: Support for resolving multiple categories at once
- **Logging System**: SQLite-based logging for tracking API usage and performance
- **CORS Support**: Configured for cross-origin requests from Wikipedia domains
- **Comprehensive Tests**: 89% test coverage with pytest
- **CI/CD**: Automated testing with GitHub Actions

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`:
  - flask
  - flask_cors
  - ArWikiCats

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/ArWikiCats/ArWikiCatsWeb.git
cd ArWikiCatsWeb
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install dev dependencies (optional):**
```bash
pip install -r requirements-dev.txt
```

4. **Run the application:**
```bash
# Using Python directly
python -m flask --app src.app run

# Or using the entry point
flask --app src.app run

# For development with auto-reload
flask --app src.app run --debug
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

## Project Structure

```
ArWikiCatsWeb/
├── src/
│   ├── app/                    # Flask application package
│   │   ├── __init__.py        # Application factory (create_app)
│   │   ├── logs_bot.py        # Logging bot functionality
│   │   ├── logs_db/           # Database logging module
│   │   │   ├── __init__.py
│   │   │   ├── bot.py         # Database operations
│   │   │   └── db.py          # Core database functions
│   │   └── routes/            # Route blueprints
│   │       ├── __init__.py
│   │       ├── api.py         # API endpoints
│   │       └── ui.py          # UI routes
│   ├── templates/             # HTML templates
│   ├── static/                # Static assets (CSS, JS)
│   ├── app.py                 # Application entry point
├── tests/                     # Test suite
│   ├── test_api.py            # API endpoint tests
│   ├── test_db_operations.py  # Database tests
│   ├── test_logs_bot.py       # Logs bot tests
│   ├── test_ui.py             # UI route tests
│   └── test_user_agent.py     # User-Agent validation tests
├── .github/
│   └── workflows/
│       └── pytest.yml         # CI/CD configuration
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies
├── service.template           # Toolforge service configuration
├── run.bat                    # Windows run script
└── README.md                  # This file
```

## API Endpoints

### Single Category Resolution

**Endpoint**: `GET /api/<title>`

Resolve a single Arabic category label.

**Example:**
```bash
curl -H "User-Agent: MyBot/1.0" http://localhost:5000/api/Category%3AYemen
```

**Response:**
```json
{
    "result": "تصنيف:اليمن",
    "sql": "log_entry_id"
}
```

### Batch Processing

**Endpoint**: `POST /api/list`

Resolve multiple category labels at once.

**Request body:**
```json
{
    "titles": ["Category:Yemen", "Category:Saudi_Arabia"]
}
```

**Response:**
```json
{
    "results": {
        "Category:Yemen": "تصنيف:اليمن",
        "Category:Saudi_Arabia": "تصنيف:السعودية"
    },
    "no_labs": 0,
    "with_labs": 2,
    "duplicates": 0,
    "time": 0.123
}
```

### Logs & Statistics

- `GET /api/logs_by_day` - Get logs aggregated by day
- `GET /api/all` - Get all logs
- `GET /api/all/<day>` - Get logs for a specific day
- `GET /api/category` - Get category-related logs
- `GET /api/category/<day>` - Get category logs for a specific day
- `GET /api/no_result` - Get entries without results
- `GET /api/no_result/<day>` - Get no_result entries for a specific day
- `GET /api/status` - Get status table
- `GET /api/logs` - View logs with pagination

## Web UI Routes

- `/` - Main interface for testing category resolution
- `/list` - Batch processing interface
- `/chart` - Statistics and charts
- `/logs` - View logs with filtering
- `/logs_by_day` - View logs grouped by day

## API Requirements

**User-Agent Header:**

All API requests MUST include a `User-Agent` header. Requests without this header will return a 400 error.

**Valid request:**
```bash
curl -H "User-Agent: MyBot/1.0" http://localhost:5000/api/Category:Test
```

**Invalid request:**
```bash
curl http://localhost:5000/api/Category:Test
# Returns: 400 {"error": "User-Agent header is required"}
```

## Deployment

### Toolforge

This service is configured for deployment on Wikimedia Toolforge. Configuration is provided in `service.template`:

- **Backend**: Kubernetes
- **Runtime**: Python 3.11
- **CPU**: 3 cores
- **Memory**: 6Gi
- **Replicas**: 2

Deploy using:
```bash
webservice start
```

### UWSGI

The project includes UWSGI configuration for production deployments.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Code Coverage

Current coverage: **89%**

Fully covered modules:
- `src/app/logs_bot.py` - 100%
- `src/app/routes/api.py` - 100%
- `src/app/routes/ui.py` - 100%

### CI/CD

The project uses GitHub Actions for continuous integration. Tests run automatically on push and pull requests.

## Main Components

- **ArWikiCats Library**: Core library for resolving Arabic category labels
- **Flask Application**: Web server and API endpoints using application factory pattern
- **Logging System**: SQLite-based logging for tracking requests and performance
- **CORS Configuration**: Allows requests from ar.wikipedia.org domains
- **Test Suite**: Comprehensive pytest-based tests with mocking

## License

This project is part of the ArWikiCats organization for Arabic Wikipedia tools and services.

## Contributing

Contributions are welcome! Please ensure your code follows the current style and includes appropriate tests.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Ensure all tests pass: `pytest`
6. Submit a pull request

## Support

For issues and questions, please use the GitHub issue tracker.
