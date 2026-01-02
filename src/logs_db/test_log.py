# -*- coding: utf-8 -*-

import os

from bot import init_db, db_commit, fetch_all, log_request, count_all, get_logs

if __name__ == "__main__":
    # python3 I:/core/bots/ma/web/src/logs_db/test_log.py
    # ---
    x = log_request(
        "/api/<title>", "Category:November 2002 events in South Africa", "تصنيف:أحداث نوفمبر 2002 في جنوب إفريقيا", 0.34
    )
