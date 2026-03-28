"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    main_path: str
    db_path_main: str


@dataclass(frozen=True)
class Settings:
    paths: Paths
    allowed_tables: set[str]


def _get_paths() -> Paths:
    # Database path configurable via DATABASE_PATH environment variable
    # Defaults to ~/www/python/dbs for backwards compatibility
    db_path_str = os.getenv("DATABASE_PATH", "")
    if db_path_str:
        main_path = Path(db_path_str)
    else:
        main_path = Path.home() / "www" / "python" / "dbs"

    main_path.mkdir(parents=True, exist_ok=True)

    db_path_main = str(main_path / "new_logs.db")

    return Paths(
        main_path=main_path,
        db_path_main=db_path_main,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        paths=_get_paths(),
        allowed_tables={"logs", "list_logs"},
    )


settings = get_settings()
