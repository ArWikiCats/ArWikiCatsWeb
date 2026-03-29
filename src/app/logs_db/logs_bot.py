# -*- coding: utf-8 -*-

from ..handler import ViewLogsRequestHandler
from ..loader import load_logs_view


def view_logs(data: ViewLogsRequestHandler) -> dict:
    _viewer = load_logs_view()
    return _viewer.view_logs(data)
