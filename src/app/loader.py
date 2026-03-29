# -*- coding: utf-8 -*-
import functools

from .config import settings
from .logs_db import Database, LogsManager, LogsView


@functools.lru_cache(maxsize=1)
def load_database() -> Database:
    _db = Database(settings.paths.db_path_main)
    return _db


@functools.lru_cache(maxsize=1)
def load_data_manager() -> LogsManager:
    _db = load_database()
    _manager = LogsManager(db=_db, allowed_tables=settings.allowed_tables)
    return _manager


@functools.lru_cache(maxsize=1)
def load_logs_view() -> LogsView:
    _manager = load_data_manager()
    _viewer = LogsView(manager=_manager)
    return _viewer
