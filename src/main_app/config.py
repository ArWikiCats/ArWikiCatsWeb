"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _format_rate_limit(value: str) -> str:
    """Format rate limit value. If only a number is provided, append 'per minute'."""
    value = value.strip()
    if value.isdigit():
        return f"{value} per minute"
    return value


@dataclass(frozen=True)
class Settings:
    db_path: str
    allowed_tables: set[str]
    pagination_window: int = 2  # Number of pages to show before/after current page
    max_visible_pages: int = 4  # Maximum number of page links to display
    rate_limit: str = "200 per minute"  # Default rate limit for API requests


def _get_paths() -> str:
    # Database path configurable via DATABASE_PATH environment variable
    # Defaults to ~/www/python/dbs for backwards compatibility
    db_path_str = os.getenv("DATABASE_PATH", "")
    if db_path_str:
        db_path_str = os.path.expandvars(db_path_str)
        db_path = Path(db_path_str)
    else:
        db_path = Path("~") / "ArWikiCatsWeb.db"

    db_path = db_path.expanduser()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        db_path.touch()

    return str(db_path)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        db_path=_get_paths(),
        allowed_tables={"logs", "list_logs"},
        pagination_window=2,
        max_visible_pages=4,
        rate_limit=_format_rate_limit(os.getenv("RATE_LIMIT", "200")),
    )


settings = get_settings()
