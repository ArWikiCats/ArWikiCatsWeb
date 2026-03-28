# Code Audit Fix Plan - ArWikiCats Web Service

**Created:** 2026-03-26
**Source:** `docs/fix/CODE_AUDIT_REPORT.md`
**Total Issues:** 30

---

## Master Checklist

### 🔴 Critical Issues (Fix Immediately)

-   [ ] **#1** — SQL Injection Vulnerability (`logs_db/bot.py`, `logs_db/db.py`)
-   [ ] **#3** — Database File in Source Control (`new_logs.db`)

### 🟠 High / Medium Priority

-   [ ] **#4** — Inconsistent Error Handling — `print()` instead of logging
-   [ ] **#5** — Unused/Debug Code in Production
-   [ ] **#6** — Default DEBUG Level in Production
-   [ ] **#7** — Potential Path Traversal (`logs_db/db.py`)
-   [ ] **#17** — Missing Rate Limiting on API
-   [ ] **#18** — Missing Request Size Limits

### 🟡 Low Priority

-   [ ] **#8** — Inconsistent Type Hints
-   [ ] **#9** — Missing Input Validation on `/api/<title>`
-   [ ] **#10** — Deprecated `flask.__version__` usage
-   [ ] **#15** — `HOME` env var issue on Windows
-   [ ] **#16** — CORS Configuration review

### 🔵 Code Quality

-   [ ] **#12** — Magic Numbers in pagination
-   [ ] **#13** — Duplicate `CREATE TABLE` code
-   [ ] **#14** — Missing Docstrings
-   [ ] **#23** — Unnecessary List Conversion

### 🟣 Security Enhancements

-   [ ] **#17** — Rate Limiting _(also listed above)_
-   [ ] **#18** — Request Size Limits _(also listed above)_

### 🧪 Testing

-   [ ] **#19** — Test Coverage Gaps (logging, migration, error paths)
-   [ ] **#20** — Missing Integration Tests

### ⚡ Performance

-   [ ] **#21** — Database Connection Pooling
-   [ ] **#22** — Inefficient `OFFSET` Pagination
-   [ ] **#23** — Unnecessary List Conversion _(also listed above)_

### 📄 Documentation & Configuration

-   [ ] **#24** — Inconsistent README coverage info
-   [ ] **#25** — Missing API Documentation (OpenAPI/Swagger)
-   [ ] **#26** — Missing `.env.example` file
-   [ ] **#27** — Hardcoded CDN URLs in templates

### 🐛 Bug Fixes

-   [ ] **#28** — Potential None Reference in `/api/list`
-   [ ] **#29** — Timezone-Naive Timestamps
-   [ ] **#30** — Empty Result Handling — inconsistent return types

---

## Step-by-Step Fix Guide

### Phase 1 — Critical Fixes (4–8 hours)

#### Step 1.1 — Fix SQL Injection Vulnerability (#1)

**Files:** `src/app/logs_db/bot.py:139`, `src/app/logs_db/db.py:86`

1. Define an `ALLOWED_TABLES` whitelist constant at the top of each module:
    ```python
    ALLOWED_TABLES = {"logs", "list_logs"}
    ```
2. Add validation **before** every f-string query that interpolates `table_name`:
    ```python
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")
    ```
3. Search for all occurrences of `f"...{table_name}..."` across the codebase to ensure nothing is missed:
    ```bash
    grep -rn "f\".*{table_name}" src/
    ```
4. Add unit tests that pass an invalid table name and assert `ValueError` is raised.

#### Step 1.3 — Remove Database from Source Control (#3)

**File:** `src/new_logs.db`

1. Add to `.gitignore`:
    ```
    *.db
    !test*.db
    ```
2. Remove tracked db file from git history:
    ```bash
    git rm --cached src/new_logs.db
    git commit -m "chore: remove database file from source control"
    ```
3. Verify the db file is still present locally but no longer tracked.

---

### Phase 2 — Medium Priority (8–16 hours)

#### Step 2.1 — Replace `print()` with Logging (#4)

**Files:** `src/app/logs_db/db.py:44,99`, `src/app/logs_db/bot.py:44`

1. Add logger initialization at the top of each file:
    ```python
    import logging
    logger = logging.getLogger(__name__)
    ```
2. Replace every `print(f"...")` error message with `logger.error(...)`.
3. Search for any remaining `print(` calls:
    ```bash
    grep -rn "print(" src/app/ --include="*.py"
    ```

#### Step 2.2 — Remove Debug Code (#5)

**Files:** `src/app/logs_bot.py:200`, `src/app/logs_db/bot.py:93`, `src/app/logging_config.py:91`

1. Remove or convert debug `print()` statements at the listed lines.
2. Delete commented-out debug code in `logging_config.py:91`.
3. If any debug output is still needed, use `logger.debug(...)` instead.

#### Step 2.3 — Fix Default Log Level (#6)

**File:** `src/app/__init__.py:11`

1. Change to read from environment:
    ```python
    import os
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(level=log_level, name=Path(__file__).parent.name)
    ```

#### Step 2.4 — Fix Path Traversal Risk (#7)

**File:** `src/app/logs_db/db.py:12`

1. Replace string concatenation with safe path joining:
    ```python
    main_path = Path(HOME).joinpath("www", "python", "dbs") if HOME else Path(__file__).parent.parent.parent
    ```
2. Optionally add `main_path.resolve()` and validate it stays within an expected parent directory.

#### Step 2.5 — Add Rate Limiting (#17)

**File:** `src/app/__init__.py` and `src/app/routes/api.py`

1. Install Flask-Limiter:
    ```bash
    pip install Flask-Limiter
    ```
2. Initialize limiter in the app factory:

    ```python
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])
    limiter.init_app(app)
    ```

3. Add specific limits to API routes:
    ```python
    @api_bp.route("/<title>", methods=["GET"])
    @limiter.limit("100 per minute")
    def get_title(title):
    ```
4. Add `Flask-Limiter` to `requirements.txt`.

#### Step 2.6 — Add Request Size Limits (#18)

**File:** `src/app/__init__.py`

1. Set `MAX_CONTENT_LENGTH` in the app config:
    ```python
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1MB
    ```
2. Add a test that sends an oversized payload and asserts a `413` response.

---

### Phase 3 — Low Priority & Code Quality (16–24 hours)

#### Step 3.1 — Add Input Validation (#9)

**File:** `src/app/routes/api.py:78-101`

1. At the beginning of `get_title()`, add:
    ```python
    if not title or len(title) > 500:
        return jsonify({"error": "Invalid title"}), 400
    ```
2. Add tests for empty title, very long title, and titles with special characters.

#### Step 3.2 — Fix Deprecated Flask Version Access (#10)

**Files:** Test files using `flask.__version__`

1. Replace:

    ```python
    # Before
    import flask
    flask.__version__

    # After
    from importlib.metadata import version
    version("flask")
    ```

#### Step 3.4 — Fix `HOME` Environment Variable (#15)

**File:** `src/app/logs_db/db.py:11`

1. Replace `os.getenv("HOME")` with `pathlib.Path.home()`:
    ```python
    from pathlib import Path
    main_path = Path.home() / "www" / "python" / "dbs"
    ```

#### Step 3.5 — Add Consistent Type Hints (#8)

**Files:** Multiple

1. Audit all public functions missing type hints.
2. Add parameter and return type annotations:
    ```python
    def get_logs(per_page: int = 10, offset: int = 0, ...) -> list[dict]:
    ```
3. Run `mypy` to verify:
    ```bash
    mypy src/app/ --ignore-missing-imports
    ```

#### Step 3.6 — Replace Magic Numbers (#12)

**File:** `src/app/logs_bot.py:97-98`

1. Define constants at the top of the module:
    ```python
    PAGINATION_WINDOW = 2
    MAX_VISIBLE_PAGES = 5
    ```
2. Use them in place of raw numbers.

#### Step 3.7 — Extract Duplicate Table Creation (#13)

**File:** `src/app/logs_db/db.py:48-78`

1. Create a reusable helper:
    ```python
    def _create_logs_table(table_name: str) -> None:
        if table_name not in ALLOWED_TABLES:
            raise ValueError(f"Invalid table name: {table_name}")
        query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ...
            );
        """
        db_commit(query)
    ```
2. Replace both inline `CREATE TABLE` blocks with calls to this helper.

#### Step 3.8 — Add Docstrings (#14)

**Files:** Multiple

1. Add Google-style docstrings to all public functions.
2. Prioritize files: `api.py`, `bot.py`, `db.py`, `logs_bot.py`.

#### Step 3.9 — Optimize List Conversion (#23)

**File:** `src/app/routes/api.py:131-133`

1. Refactor:

    ```python
    # Before
    len_titles = len(titles)
    titles = list(set(titles))
    duplicates = len_titles - len(titles)

    # After
    titles_set = set(titles)
    duplicates = len(titles) - len(titles_set)
    titles = list(titles_set)
    ```

#### Step 3.10 — Review CORS Configuration (#16)

**File:** `src/app/__init__.py:25-28`

1. Verify the CORS origin list matches all expected consumers.
2. Document the CORS policy in the README.

---

### Phase 4 — Bug Fixes

#### Step 4.1 — Fix None Reference in `/api/list` (#28)

**File:** `src/app/routes/api.py` (around line 134)

1. Add a `None` check for `batch_resolve_labels` before it is called in the `/api/list` route:
    ```python
    if batch_resolve_labels is None:
        return jsonify({"error": "Library not loaded"}), 500
    ```
2. Add a test that simulates a failed import and verifies the 500 response.

#### Step 4.2 — Handle Timezone-Naive Timestamps (#29)

**File:** `src/app/logs_db/db.py:58`

1. Document that all timestamps are stored in UTC.
2. (Optional) Add a utility function to convert to local time for display:
    ```python
    from datetime import datetime, timezone
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()
    ```

#### Step 4.3 — Standardize `fetch_all` Return Type (#30)

**File:** `src/app/logs_db/bot.py:119-128`

1. Update `fetch_all` so that when `fetch_one=True`, it always returns a `dict` or `None`.
2. Remove the `isinstance(result, list)` guard at the call site.
3. Update all callers and corresponding tests.

---

### Phase 5 — Testing & Documentation

#### Step 5.1 — Increase Test Coverage (#19)

1. Add tests for:
    - `src/app/logging_config.py` — custom color formatting functions
    - `src/app/logs_db/bot_update.py` — database migration scripts
    - Error paths in database operations (connection failure, corrupt data)
2. Run coverage report:
    ```bash
    pytest --cov=src/app --cov-report=html
    ```
3. Target: ≥ 95% coverage.

#### Step 5.2 — Add Integration Tests (#20)

1. Create `tests/integration/` directory.
2. Write tests that:
    - Create a temporary SQLite database
    - Make actual API calls via Flask test client
    - Verify database state after each operation
    - Tear down the database after each test

#### Step 5.3 — Create `.env.example` (#26)

**File:** `.env.example` (project root)

1. Create file with all required/optional environment variables:
    ```env
    LOG_LEVEL=INFO
    ARWIKICATS_PATH=/path/to/bot
    DATABASE_PATH=/path/to/dbs
    FLASK_ENV=development
    ```

#### Step 5.4 — Update README Coverage Info (#24)

**File:** `README.md:237-239`

1. Re-run coverage and update the reported percentage.
2. Add a link to the HTML coverage report.

#### Step 5.5 — Add API Documentation (#25)

1. Choose a tool: Flask-RESTX or Flasgger.
2. Add OpenAPI annotations to each route.
3. Expose Swagger UI at `/api/docs`.
4. Add `flask-restx` or `flasgger` to `requirements.txt`.

#### Step 5.6 — Move CDN URLs to Config (#27)

**File:** `src/templates/main.html:1`

1. Move the CDN base URL to app config:
    ```python
    app.config['CDN_BASE'] = os.getenv("CDN_BASE", "https://tools-static.wmflabs.org/cdnjs/ajax/libs")
    ```
2. Use `{{ config.CDN_BASE }}` in templates instead of the hardcoded `{% set %}`.

---

## Effort Summary

| Phase     | Focus                       | Estimated Hours |
| --------- | --------------------------- | --------------- |
| 1         | Critical Fixes              | 4–8             |
| 2         | Medium Priority             | 8–16            |
| 3         | Low Priority & Code Quality | 16–24           |
| 4         | Bug Fixes                   | 4–6             |
| 5         | Testing & Documentation     | 8–12            |
| **Total** |                             | **40–66**       |

---

_Derived from `docs/fix/CODE_AUDIT_REPORT.md` — 2026-03-26_
