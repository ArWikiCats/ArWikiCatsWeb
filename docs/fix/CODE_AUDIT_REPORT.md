# Code Audit Report - ArWikiCats Web Service

**Generated:** 2026-03-26
**Branch:** update
**Python Version:** 3.13.7
**Flask Version:** 3.1.3

---

## Executive Summary

The ArWikiCats Web Service is a Flask-based application for resolving Arabic Wikipedia category labels. The codebase has **89 passing tests** with good coverage. However, several bugs, security concerns, and improvement opportunities were identified.

---

## Critical Issues

### 1. SQL Injection Vulnerability

**Severity:** CRITICAL
**Location:** `src/app/logs_db/bot.py:139`, `src/app/logs_db/db.py:86`

**Problem:** Table names are directly interpolated into SQL queries without validation:

```python
query = f"SELECT * FROM {table_name} "
```

**Risk:** Although `table_name` is validated against `db_tables` list in `logs_bot.py:47-49`, this validation is bypassed if functions are called directly.

**Fix:**

```python
# Validate table_name against whitelist before use
ALLOWED_TABLES = {"logs", "list_logs"}
if table_name not in ALLOWED_TABLES:
    raise ValueError(f"Invalid table name: {table_name}")
```

---

### 2. Hardcoded Development Path

**Severity:** HIGH
**Location:** `src/app1.py:9`

**Problem:** Hardcoded Windows path in production code:

```python
sys.path.insert(0, "D:/categories_bot/make2_new")
```

**Fix:** Use environment variable or configuration file:

```python
import os
custom_path = os.getenv("ARWIKICATS_PATH")
if custom_path:
    sys.path.insert(0, custom_path)
```

---

### 3. Database File in Source Control

**Severity:** HIGH
**Location:** `src/new_logs.db` (17MB)

**Problem:** Database file should not be in source directory. Should be in `.gitignore`.

**Fix:** Add to `.gitignore`:

```
*.db
!test*.db
```

---

## Medium Priority Issues

### 4. Inconsistent Error Handling

**Severity:** MEDIUM
**Locations:**

-   `src/app/logs_db/db.py:44, 99`
-   `src/app/logs_db/bot.py:44`

**Problem:** Using `print()` statements instead of proper logging:

```python
print(f"init_db Database error: {e}")
print(f"Database error in view_logs: {e}")
```

**Fix:** Use the configured logger:

```python
import logging
logger = logging.getLogger(__name__)
logger.error(f"Database error: {e}")
```

---

### 5. Unused/Debug Code in Production

**Severity:** MEDIUM
**Locations:**

-   `src/app/logs_bot.py:200` - Debug print statement
-   `src/app/logs_db/bot.py:93` - Debug print statement
-   `src/app/logging_config.py:91` - Commented debug code

**Fix:** Remove debug statements or use proper logging with appropriate log levels.

---

### 6. Default DEBUG Level in Production

**Severity:** MEDIUM
**Location:** `src/app/__init__.py:11`

**Problem:** Logging set to DEBUG level by default:

```python
setup_logging(level="DEBUG", name=Path(__file__).parent.name)
```

**Fix:** Use environment variable:

```python
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(level=log_level, name=Path(__file__).parent.name)
```

---

### 7. Potential Path Traversal

**Severity:** MEDIUM
**Location:** `src/app/logs_db/db.py:12`

**Problem:** Database path construction could be vulnerable:

```python
HOME = os.getenv("HOME")
main_path = Path(HOME + "/www/python/dbs") if HOME else Path(__file__).parent.parent.parent
```

**Fix:** Use `Path.joinpath()` and validate paths:

```python
main_path = Path(HOME).joinpath("www", "python", "dbs") if HOME else ...
```

---

## Low Priority Issues

### 8. Inconsistent Type Hints

**Severity:** LOW
**Locations:** Multiple files

**Problem:** Mixed use of type hints. Some functions have them, others don't.

**Fix:** Add consistent type hints across all functions:

```python
def get_logs(
    per_page: int = 10,
    offset: int = 0,
    order: str = "DESC",
    order_by: str = "timestamp",
    status: str = "",
    table_name: str = "logs",
    day: str = ""
) -> list[dict]:
```

---

### 9. Missing Input Validation

**Severity:** LOW
**Location:** `src/app/routes/api.py:78-101`

**Problem:** Title parameter not validated for length or special characters:

```python
@api_bp.route("/<title>", methods=["GET"])
def get_title(title) -> str:
```

**Fix:** Add validation:

```python
if not title or len(title) > 500:
    return jsonify({"error": "Invalid title"}), 400
```

---

### 10. Deprecated Flask Version Access

**Severity:** LOW
**Location:** Test files

**Problem:** Using deprecated `flask.__version__`:

```
DeprecationWarning: The '__version__' attribute is deprecated
```

**Fix:** Use `importlib.metadata.version("flask")` instead.

---

### 11. Unused File: `src/app1.py`

**Severity:** LOW

**Problem:** Duplicate entry point with hardcoded path. Appears to be development-only file.

**Fix:** Remove or document purpose clearly.

---

## Code Quality Improvements

### 12. Magic Numbers

**Location:** `src/app/logs_bot.py:97-98`

```python
start_page = max(1, page - 2)
end_page = min(start_page + 4, total_pages)
```

**Fix:** Use named constants:

```python
PAGINATION_WINDOW = 2
start_page = max(1, page - PAGINATION_WINDOW)
```

---

### 13. Duplicate Code

**Location:** `src/app/logs_db/db.py:48-78`

Two nearly identical `CREATE TABLE` statements for `logs` and `list_logs`.

**Fix:** Create a helper function:

```python
def create_logs_table(table_name: str):
    query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ...
        );
    """
    db_commit(query)
```

---

### 14. Missing Docstrings

**Location:** Multiple files

Many public functions lack docstrings explaining parameters and return values.

**Fix:** Add Google or NumPy style docstrings:

```python
def get_logs(per_page: int = 10, offset: int = 0) -> list[dict]:
    """Fetch logs with pagination.

    Args:
        per_page: Number of logs per page (1-200)
        offset: Starting offset for pagination

    Returns:
        List of log entries as dictionaries
    """
```

---

### 15. Environment Variable for HOME

**Location:** `src/app/logs_db/db.py:11`

**Problem:** `HOME` environment variable doesn't exist on Windows (uses `USERPROFILE`).

**Fix:** Use `pathlib.Path.home()`:

```python
from pathlib import Path
main_path = Path.home() / "www" / "python" / "dbs"
```

---

## Security Recommendations

### 16. CORS Configuration Too Restrictive/Permissive

**Location:** `src/app/__init__.py:25-28`

**Current:**

```python
CORS(app, resources={r"/api/*": {"origins": ["https://ar.wikipedia.org", "https://www.ar.wikipedia.org"]}})
```

**Issue:** If this is meant to be public API, consider if this is correct. If internal, ensure it's sufficient.

---

### 17. Missing Rate Limiting

**Severity:** MEDIUM

**Problem:** No rate limiting on API endpoints could allow abuse.

**Fix:** Add Flask-Limiter:

```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

@api_bp.route("/<title>", methods=["GET"])
@limiter.limit("100 per minute")
def get_title(title):
```

---

### 18. Missing Request Size Limits

**Location:** `src/app/routes/api.py:103-157`

**Problem:** POST `/api/list` endpoint has no size limit on JSON payload.

**Fix:** Configure Flask:

```python
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB max
```

---

## Testing Improvements

### 19. Test Coverage Gaps

**Current Coverage:** 89%

**Uncovered Areas:**

-   `src/app/logging_config.py` - Custom color formatting functions
-   Error paths in database operations

**Fix:** Add tests for:

-   Color formatting edge cases
-   Database migration scenarios
-   Error handling paths

---

### 20. Missing Integration Tests

**Problem:** No tests for full request-response cycle with actual database.

**Fix:** Add integration tests that:

-   Create test database
-   Make actual API calls
-   Verify database state changes

---

## Performance Improvements

### 21. Database Connection Pooling

**Location:** `src/app/logs_db/db.py:38-39`

**Problem:** New connection opened for every query:

```python
with sqlite3.connect(db_path_main[1]) as conn:
```

**Fix:** Consider connection pooling or at least keep connection open longer for batch operations.

---

### 22. Inefficient Pagination

**Location:** `src/app/logs_db/bot.py:148-149`

**Problem:** `OFFSET` queries become slow with large datasets:

```python
query += f"ORDER BY {order_by} {order} LIMIT ? OFFSET ?"
```

**Fix:** Use keyset pagination for better performance:

```python
# Instead of OFFSET, use WHERE id > last_seen_id
```

---

### 23. Unnecessary List Conversion

**Location:** `src/app/routes/api.py:131-133`

```python
len_titles = len(titles)
titles = list(set(titles))
duplicates = len_titles - len(titles)
```

**Fix:** More efficient:

```python
titles_set = set(titles)
duplicates = len(titles) - len(titles_set)
titles = list(titles_set)
```

---

## Documentation Issues

### 24. Inconsistent README Information

**Location:** `README.md:237-239`

**Problem:** Claims 89% coverage but doesn't match actual uncovered files.

**Fix:** Update with accurate coverage report.

---

### 25. Missing API Documentation

**Problem:** No OpenAPI/Swagger documentation for REST API.

**Fix:** Add Flask-RESTX or Flasgger for auto-generated API docs.

---

## Configuration Issues

### 26. Missing `.env` Example

**Problem:** No `.env.example` file showing required environment variables.

**Fix:** Create `.env.example`:

```
LOG_LEVEL=INFO
ARWIKICATS_PATH=/path/to/bot
DATABASE_PATH=/path/to/dbs
FLASK_ENV=development
```

---

### 27. Hardcoded CDN URLs

**Location:** `src/templates/main.html:1`

**Problem:** CDN URLs hardcoded in templates:

```html
{% set cdn_base = "https://tools-static.wmflabs.org/cdnjs/ajax/libs" %}
```

**Fix:** Use configuration or environment variable for flexibility.

---

## Bug Fixes

### 28. Potential None Reference

**Location:** `src/app/routes/api.py:88-90`

```python
if resolve_arabic_category_label is None:
    log_request("/api/<title>", title, "error", time.time() - start_time)
    return jsonify({"error": "حدث خطأ أثناء تحميل المكتبة"}), 500
```

**Problem:** If import fails, `batch_resolve_labels` is also None but not checked in `/api/list`.

**Fix:** Add check at line 134 as well.

---

### 29. Timezone-Naive Timestamps

**Location:** `src/app/logs_db/db.py:58`

```python
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
```

**Problem:** SQLite `CURRENT_TIMESTAMP` is UTC, but no timezone handling in code.

**Fix:** Use timezone-aware timestamps or document UTC assumption.

---

### 30. Empty Result Handling

**Location:** `src/app/logs_db/bot.py:119-128`

```python
result = fetch_all(query, params, fetch_one=True)
if not result:
    return 0
if isinstance(result, list):
    result = result[0]
```

**Problem:** Inconsistent return types from `fetch_all` when `fetch_one=True`.

**Fix:** Standardize return type to always return dict or None.

---

## Summary Statistics

| Category         | Count  |
| ---------------- | ------ |
| Critical         | 3      |
| High             | 2      |
| Medium           | 4      |
| Low              | 6      |
| Code Quality     | 4      |
| Security         | 3      |
| Testing          | 2      |
| Performance      | 3      |
| Documentation    | 2      |
| Configuration    | 2      |
| Bug Fixes        | 3      |
| **Total Issues** | **30** |

---

## Recommended Priority Order

1. **Fix SQL injection vulnerability** (Issue #1)
2. **Remove hardcoded paths** (Issue #2)
3. **Add database to .gitignore** (Issue #3)
4. **Replace print() with logging** (Issue #4)
5. **Remove debug statements** (Issue #5)
6. **Use environment variables for config** (Issues #6, #15)
7. **Add input validation** (Issue #9)
8. **Add rate limiting** (Issue #17)
9. **Improve test coverage** (Issue #19)
10. **Add API documentation** (Issue #25)

---

## Positive Findings

-   ✅ All 89 tests passing
-   ✅ Good test coverage on core modules
-   ✅ Clean separation of concerns (blueprints)
-   ✅ Application factory pattern used correctly
-   ✅ CORS properly configured for use case
-   ✅ Pagination implemented
-   ✅ Error handlers defined
-   ✅ Type hints used in newer code
-   ✅ Black/Ruff configuration present
-   ✅ CI/CD pipeline configured

---

## Conclusion

The ArWikiCats Web Service is a well-structured Flask application with solid test coverage. The most critical issues are the SQL injection vulnerability (mitigated by validation), hardcoded development paths, and debug code in production. Addressing these issues will significantly improve security, maintainability, and production readiness.

**Estimated Effort:**

-   Critical fixes: 4-8 hours
-   Medium priority: 8-16 hours
-   Low priority + improvements: 16-24 hours
-   **Total:** 28-48 hours

---

_Report generated by automated code audit_
