# ArWikiCatsWeb

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/ArWikiCats/ArWikiCatsWeb)

A Flask-based web service for resolving Arabic Wikipedia category labels. This service provides both a web interface and REST API for working with Arabic Wikipedia categories.

## Features

- **REST API**: Resolve Arabic category labels through HTTP endpoints
- **Web Interface**: Interactive UI for testing and exploring category labels
- **Batch Processing**: Support for resolving multiple category labels at once
- **Logging System**: Track API usage and performance with SQLite database
- **CORS Support**: Configured for cross-origin requests from Wikipedia domains
- **Status Monitoring**: View logs and usage statistics

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`:
  - flask
  - flask_cors
  - ArWikiCats

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ArWikiCats/ArWikiCatsWeb.git
cd ArWikiCatsWeb
```

2. Install dependencies:
```bash
cd src
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

For debug mode:
```bash
python app.py debug
```

## API Endpoints

### Single Category Label

**Endpoint**: `GET /api/<title>`

Resolve a single Arabic category label.

**Example**:
```bash
curl -H "User-Agent: MyBot/1.0" https://yourserver/api/Category%3AExample
```

**Response**:
```json
{
    "result": "resolved_label",
    "sql": "log_entry_id"
}
```

### Batch Processing

**Endpoint**: `POST /api/list`

Resolve multiple category labels at once.

**Request Body**:
```json
{
    "titles": ["Category:Example1", "Category:Example2"]
}
```

### Logs and Statistics

- `GET /api/logs_by_day` - Get logs grouped by day
- `GET /api/all` - Get all logs
- `GET /api/all/<day>` - Get logs for a specific day
- `GET /api/category` - Get category-related logs
- `GET /api/category/<day>` - Get category logs for a specific day
- `GET /api/no_result` - Get entries with no results
- `GET /api/no_result/<day>` - Get no-result entries for a specific day
- `GET /api/status` - Get status table

## Web Interface Routes

- `/` - Main interface for testing category resolution
- `/list` - Batch processing interface
- `/chart` - Statistics and charts
- `/logs` - View logs
- `/logs_by_day` - View logs grouped by day

## Deployment

### Toolforge

This service is configured for deployment on Wikimedia Toolforge. Configuration is provided in `service.template`:

- **Backend**: Kubernetes
- **Runtime**: Python 3.11

Deploy using:
```bash
toolforge webservice python3.11 start
```

### UWSGI

The service includes UWSGI configuration in `src/uwsgi.ini` for production deployments.

## Development

### Project Structure

```
ArWikiCatsWeb/
├── src/
│   ├── app.py              # Main Flask application
│   ├── logs_bot.py         # Logging bot functionality
│   ├── logs_db/            # Database logging module
│   ├── templates/          # HTML templates
│   ├── static/             # Static assets (CSS, JS)
│   └── uwsgi.ini           # UWSGI configuration
├── service.template        # Toolforge service configuration
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Dev dependencies
├── run.bat                 # Windows run script
└── README.md               # This file
```

### Key Components

- **ArWikiCats Library**: Core library for resolving Arabic category labels
- **Flask Application**: Web server and API endpoints
- **Logging System**: SQLite-based logging for tracking requests and performance
- **CORS Configuration**: Allows requests from ar.wikipedia.org domains

## API Requirements

All API requests must include a `User-Agent` header. Requests without this header will return a 400 error.

## License

This project is part of the ArWikiCats organization for Arabic Wikipedia tools and utilities.

## Contributing

Contributions are welcome! Please ensure your code follows the existing style and includes appropriate tests.

## Support

For issues and questions, please use the GitHub issue tracker.
