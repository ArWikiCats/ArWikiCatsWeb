# routes package
from .api import api_bp
from .ui import ui_bp

__all__ = [
    "api_bp",
    "ui_bp",
]
