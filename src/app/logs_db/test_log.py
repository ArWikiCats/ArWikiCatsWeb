# -*- coding: utf-8 -*-

import os

from bot import count_all, db_commit, fetch_all, get_logs, init_db, log_request

if __name__ == "__main__":
    # python3 I:/core/bots/ma/web/src/logs_db/test_log.py
    # ---
    x = log_request(
        "/api/<title>", "Category:November 2002 events in South Africa", "تصنيف:أحداث نوفمبر 2002 في جنوب إفريقيا", 0.34
    )
