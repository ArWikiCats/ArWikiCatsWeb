# -*- coding: utf-8 -*-
"""
Routes package for the ArWikiCats web service.

This package contains all URL route handlers, organized into:
- api: REST API endpoints under /api/*
- ui: Web UI pages under /

Blueprints:
    api_bp: REST API for category resolution and log access
    ui_bp: Web interface pages for human users
"""

from .api import api_bp
from .ui import ui_bp

__all__ = [
    "api_bp",
    "ui_bp",
]
