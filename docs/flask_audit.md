# Flask Application Audit Report

**Date:** 2026-02-23
**Auditor:** Claude Code
**Reference:** `.github/flask/SKILL.md`
**Scope:** SVG Translate Flask Application (`src/` directory)

---

## Executive Summary

This audit evaluates the Flask application against the standards documented in the SKILL.md file. The application uses the Flask factory pattern with Blueprints but has **significant architectural gaps**, **missing security implementations**, and **deviations from best practices**.

### Severity Overview

| Severity | Count | Description |
|----------|-------|-------------|
| **Critical** | 4 | Security vulnerabilities, missing SECRET_KEY, SQL injection risks |
| **High** | 5 | Missing configuration management, extension patterns, test infrastructure |
| **Medium** | 6 | Code organization, error handling, logging issues |
| **Low** | 3 | Style consistency, documentation gaps |

---

## Critical Issues

### 1. Missing SECRET_KEY Configuration

**Location:** `src/app/__init__.py:19-23`
**SKILL Reference:** Section "Configuration"

**Issue:** The Flask application is initialized without a `SECRET_KEY`, which is required for:
- Session security
- CSRF protection (when forms are added)
- Flash message integrity

```python
# CURRENT (src/app/__init__.py)
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static",
)
# No SECRET_KEY configured!
```

**Recommendation:**
```python
# RECOMMENDED - Create config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# In app/__init__.py
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__, ...)
    app.config.from_object(config_class)
```

---

### 2. SQL Injection Vulnerabilities

**Location:** `src/app/logs_db/bot.py:30-41`, `83-97`, `100-108`, `111-129`, `132-151`, `154-174`
**SKILL Reference:** Security Best Practices

**Issue:** Multiple functions use f-string interpolation for table names and column names in SQL queries. While `table_name` has some validation, it's insufficient:

```python
# VULNERABLE CODE (src/app/logs_db/bot.py)
def log_request(endpoint, request_data, response_status, response_time):
    table_name = "logs" if endpoint != "/api/list" else "list_logs"
    result = db_commit(
        f"""
        INSERT INTO {table_name} (  -- String interpolation!
            endpoint, request_data, response_status, response_time, date_only
            )
        ...
        """,
        (endpoint, str(request_data), response_status, response_time),
    )
```

**Issues:**
1. No whitelist validation of `table_name` parameter in `get_logs()`, `count_all()`, `sum_response_count()`
2. `order_by` column name is interpolated without validation

```python
# VULNERABLE (src/app/logs_db/bot.py:143)
query += f"ORDER BY {order_by} {order} LIMIT ? OFFSET ?"
```

**Recommendation:**
```python
# RECOMMENDED - Add whitelist validation
ALLOWED_TABLES = {"logs", "list_logs"}
ALLOWED_COLUMNS = {
    "id", "endpoint", "request_data", "response_status",
    "response_time", "response_count", "timestamp", "date_only"
}

def get_logs(..., table_name="logs", order_by="timestamp", ...):
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table: {table_name}")
    if order_by not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid column: {order_by}")
    # Now safe to use f-strings
```

---

### 3. No Input Validation on API Endpoints

**Location:** `src/app/routes/api.py:103-156`
**SKILL Reference:** Section "API Routes (JSON)"

**Issue:** The `/api/list` endpoint accepts arbitrary JSON without validation:

```python
# CURRENT (src/app/routes/api.py:107-108)
data = request.get_json()
titles = data.get("titles", [])
```

Missing validations:
- No maximum length check for titles list
- No sanitization of title strings
- No rate limiting

**Recommendation:**
```python
from flask import abort

@api_bp.route("/list", methods=["POST"])
def get_titles():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    titles = data.get("titles", [])

    # Add validation
    if not isinstance(titles, list):
        return jsonify({"error": "titles must be a list"}), 400

    if len(titles) > 1000:  # Set reasonable limit
        return jsonify({"error": "Too many titles (max 1000)"}), 400

    # Sanitize titles
    titles = [str(t).strip()[:500] for t in titles if t]  # Limit string length
```

---

### 4. Missing CSRF Protection

**Location:** All forms in templates
**SKILL Reference:** Issue #6, Section "Critical Rules"

**Issue:** The application has no CSRF protection for forms. While the API uses JSON, any forms rendered in templates are vulnerable.

**Recommendation:**
```bash
# Add Flask-WTF
pip install flask-wtf
```

```python
# RECOMMENDED - extensions.py
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

# In create_app
csrf.init_app(app)
```

```html
<!-- In templates with forms -->
<form method="post">
    {{ csrf_token() }}
    <!-- form fields -->
</form>
```

---

## High Priority Issues

### 5. Missing Extensions Module

**Location:** Project structure
**SKILL Reference:** Section "Extensions Module", "Project Structure"

**Issue:** The SKILL.md explicitly recommends an `extensions.py` file to prevent circular imports. The current code initializes extensions in `__init__.py`:

```python
# CURRENT (src/app/__init__.py)
from flask_cors import CORS
from .logging_config import setup_logging

setup_logging(...)  # Called at import time!

def create_app():
    CORS(app, ...)  # Initialized in factory (correct)
```

**Recommendation:**
```python
# RECOMMENDED - src/app/extensions.py
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy  # If migrating

cors = CORS()

# In create_app
from app.extensions import cors
cors.init_app(app, resources={...})
```

---

### 6. No Configuration Classes

**Location:** Entire project
**SKILL Reference:** Section "Configuration"

**Issue:** The application lacks environment-specific configuration:
- No `config.py` file
- No `DevelopmentConfig`, `TestingConfig`, `ProductionConfig`
- Database path is hardcoded in `db.py:12`
- Logging level is hardcoded in `__init__.py:11`

```python
# CURRENT (src/app/logs_db/db.py:12)
main_path = Path(HOME + "/www/python/dbs") if HOME else Path(__file__).parent.parent.parent
```

**Recommendation:**
```python
# RECOMMENDED - config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = "INFO"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "instance/app.db")

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = ":memory:"

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "WARNING"
    SECRET_KEY = os.environ.get("SECRET_KEY")  # Must be set
```

---

### 7. Inadequate Test Fixtures

**Location:** `tests/conftest.py`
**SKILL Reference:** Section "Testing"

**Issue:** The `conftest.py` file is essentially empty, yet multiple test files duplicate the same fixture code:

```python
# CURRENT (tests/conftest.py)
# -*- coding: utf-8 -*-
"""
Pytest configuration for the tests directory.
"""
# EMPTY!

# DUPLICATED in test_api.py, test_ui.py, test_user_agent.py (lines 47-52, 81-88, etc.)
@pytest.fixture
def client(self):
    from src.app import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
```

**Recommendation:**
```python
# RECOMMENDED - tests/conftest.py
import pytest
from src.app import create_app
from src.app.logs_db import init_db

class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    DATABASE_PATH = ":memory:"

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestConfig)
    with app.app_context():
        init_db()
        yield app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()
```

---

### 8. Custom jsonify Instead of Flask's

**Location:** `src/app/routes/api.py:20-22`
**SKILL Reference:** Section "API Routes (JSON)"

**Issue:** A custom `jsonify` function is implemented instead of using Flask's built-in:

```python
# CURRENT (src/app/routes/api.py:20-22)
def jsonify(data: dict) -> str:
    response_json = json.dumps(data, ensure_ascii=False, indent=4)
    return Response(response=response_json, content_type="application/json; charset=utf-8")
```

This bypasses Flask's response handling and may miss features like:
- Automatic status code handling
- Flask's JSON encoder extensions
- Content negotiation

**Recommendation:**
```python
# RECOMMENDED
from flask import jsonify as flask_jsonify

# Or if custom formatting is needed, still use Flask's helper
from flask import jsonify as flask_jsonify

def jsonify(data: dict, status_code: int = 200):
    response = flask_jsonify(data)
    response.status_code = status_code
    return response
```

---

### 9. No Database Connection Pooling

**Location:** `src/app/logs_db/db.py:35-45`
**SKILL Reference:** Best Practices

**Issue:** Every database operation creates a new connection:

```python
# CURRENT (src/app/logs_db/db.py:35-41)
def db_commit(query, params=[]):
    try:
        with sqlite3.connect(db_path_main[1]) as conn:  # New connection each time!
            cursor = conn.cursor()
            cursor.execute(query, params)
        conn.commit()
```

Under load, this creates significant overhead.

**Recommendation:**
```python
# RECOMMENDED - Use connection pooling or at least thread-local connections
import sqlite3
from contextlib import contextmanager
from threading import local

_thread_local = local()

def get_connection():
    if not hasattr(_thread_local, 'connection'):
        _thread_local.connection = sqlite3.connect(db_path_main[1])
    return _thread_local.connection

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
```

---

## Medium Priority Issues

### 10. No Error Handling for External Dependencies

**Location:** `src/app/routes/api.py:78-100`, `103-156`
**SKILL Reference:** Error Handling Best Practices

**Issue:** External library calls lack try-except blocks:

```python
# CURRENT (src/app/routes/api.py:92)
label = resolve_arabic_category_label(title)  # May throw!
```

**Recommendation:**
```python
@api_bp.route("/<title>", methods=["GET"])
def get_title(title):
    start_time = time.time()

    try:
        label = resolve_arabic_category_label(title)
    except Exception as e:
        log_request("/api/<title>", title, f"error: {str(e)}", time.time() - start_time)
        return jsonify({"error": "Translation service error"}), 503
```

---

### 11. Hardcoded CORS Origins

**Location:** `src/app/__init__.py:25-28`
**SKILL Reference:** Configuration

**Issue:** CORS origins are hardcoded instead of being configurable:

```python
# CURRENT
CORS(
    app,
    resources={r"/api/*": {"origins": ["https://ar.wikipedia.org", "https://www.ar.wikipedia.org"]}},
)
```

**Recommendation:**
```python
# RECOMMENDED
from flask import Config

class Config:
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "https://ar.wikipedia.org,https://www.ar.wikipedia.org"
    ).split(",")

# In create_app
CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
```

---

### 12. Global State for Database Path

**Location:** `src/app/logs_db/db.py:17`
**SKILL Reference:** Best Practices

**Issue:** Database path is stored in a global dictionary:

```python
# CURRENT
db_path_main = {1: f"{str(main_path)}/new_logs.db"}  # Global mutable state
```

This makes testing difficult and is not thread-safe.

**Recommendation:**
```python
# RECOMMENDED - Use Flask's app context
def get_db_path():
    from flask import current_app
    return current_app.config.get("DATABASE_PATH", "instance/app.db")
```

---

### 13. Inconsistent Type Hints

**Location:** Various files
**SKILL Reference:** Code Quality

**Issue:** Type hints are used inconsistently:

```python
# GOOD (src/app/routes/api.py:33)
def get_logs_by_day() -> str:

# INCONSISTENT (src/app/routes/api.py:103)
def get_titles():  # No return type

# INCONSISTENT (src/app/logs_bot.py:8)
def view_logs(request):  # No type hints
```

**Recommendation:** Add type hints to all public functions.

---

### 14. Hardcoded Template/Static Paths

**Location:** `src/app/__init__.py:21-22`
**SKILL Reference:** Project Structure

**Issue:** Path construction is fragile:

```python
# CURRENT
app = Flask(
    __name__,
    template_folder="../templates",  # Relative path that may break
    static_folder="../static",
)
```

**Recommendation:**
```python
# RECOMMENDED
from pathlib import Path

def create_app():
    base_dir = Path(__file__).parent.parent
    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )
```

---

### 15. Missing Health Check Endpoint

**Location:** API routes
**SKILL Reference:** API Design

**Issue:** No health check endpoint for monitoring:

**Recommendation:**
```python
@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    })
```

---

## Low Priority Issues

### 16. Logging Setup at Import Time

**Location:** `src/app/__init__.py:10-13`
**SKILL Reference:** Best Practices

**Issue:** Logging is configured at module import time rather than in the factory.

**Recommendation:** Move logging setup into `create_app()`.

---

### 17. Comment Noise

**Location:** `src/app/logs_bot.py`, `src/app/logs_db/bot.py`
**SKILL Reference:** Code Quality

**Issue:** Excessive separator comments reduce readability:

```python
# CURRENT (src/app/logs_bot.py)
def view_logs(request):
    # ---
    db_path = request.args.get("db_path")
    # ---
    dbs = []
    # ---
```

**Recommendation:** Remove redundant separator comments.

---

### 18. Unused Parameter in Logging Config

**Location:** `src/app/logging_config.py:136`
**SKILL Reference:** Code Quality

**Issue:** `name` parameter is passed but not used for logger naming convention consistently.

---

## Summary Table

| ID | Issue | Severity | File(s) | Line(s) |
|----|-------|----------|---------|---------|
| 1 | Missing SECRET_KEY | Critical | `src/app/__init__.py` | 19-23 |
| 2 | SQL Injection Vulnerabilities | Critical | `src/app/logs_db/bot.py` | Multiple |
| 3 | No Input Validation | Critical | `src/app/routes/api.py` | 103-156 |
| 4 | Missing CSRF Protection | Critical | Templates | All forms |
| 5 | Missing Extensions Module | High | Project structure | N/A |
| 6 | No Configuration Classes | High | Entire project | N/A |
| 7 | Inadequate Test Fixtures | High | `tests/conftest.py` | 1-5 |
| 8 | Custom jsonify | High | `src/app/routes/api.py` | 20-22 |
| 9 | No Connection Pooling | High | `src/app/logs_db/db.py` | 35-45 |
| 10 | No Error Handling | Medium | `src/app/routes/api.py` | 78-100 |
| 11 | Hardcoded CORS Origins | Medium | `src/app/__init__.py` | 25-28 |
| 12 | Global DB Path State | Medium | `src/app/logs_db/db.py` | 17 |
| 13 | Inconsistent Type Hints | Medium | Various | Multiple |
| 14 | Hardcoded Paths | Medium | `src/app/__init__.py` | 21-22 |
| 15 | Missing Health Check | Medium | `src/app/routes/api.py` | N/A |
| 16 | Logging at Import Time | Low | `src/app/__init__.py` | 10-13 |
| 17 | Comment Noise | Low | `src/app/logs_bot.py` | Multiple |
| 18 | Unused Parameter | Low | `src/app/logging_config.py` | 136 |

---

## Recommendations Priority Matrix

### Immediate Action Required (Critical)

1. **Add SECRET_KEY configuration** - Required for any production deployment
2. **Fix SQL injection vulnerabilities** - Security risk
3. **Add input validation** - Prevent abuse and crashes
4. **Add CSRF protection** - Required for form security

### Short-term (High)

5. Create `extensions.py` module
6. Implement configuration classes
7. Fix test fixtures in `conftest.py`
8. Use Flask's built-in `jsonify` or extend it properly
9. Implement connection pooling

### Medium-term (Medium/Low)

10. Add comprehensive error handling
11. Make CORS origins configurable
12. Fix global state issues
13. Add type hints consistently
14. Create health check endpoint
15. Code cleanup (comments, imports)

---

## Appendix: SKILL.md Compliance Checklist

### Architecture Patterns

| Pattern | Required | Status | Notes |
|---------|----------|--------|-------|
| Application Factory | Yes | Partial | Missing config parameter |
| Extensions Module | Yes | Missing | No `extensions.py` file |
| Blueprints | Yes | Compliant | Correctly implemented |
| Configuration Classes | Yes | Missing | No `config.py` file |
| Separate Routes Files | Yes | Compliant | Correctly organized |

### Security Requirements

| Requirement | Required | Status | Notes |
|-------------|----------|--------|-------|
| SECRET_KEY | Yes | Missing | Not configured |
| CSRF Protection | Yes | Missing | No Flask-WTF |
| Input Validation | Yes | Missing | No validation on API |
| SQL Injection Prevention | Yes | Non-compliant | String interpolation used |
| CORS Configuration | Yes | Partial | Hardcoded origins |

### Code Quality

| Requirement | Required | Status | Notes |
|-------------|----------|--------|-------|
| Type Hints | Recommended | Partial | Inconsistent usage |
| Error Handling | Required | Partial | Missing try-except blocks |
| Logging | Required | Partial | Setup at import time |
| Test Fixtures | Required | Non-compliant | Empty conftest.py |

---

*End of Audit Report*
