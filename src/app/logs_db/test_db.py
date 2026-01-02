# -*- coding: utf-8 -*-

import os

from bot import init_db, db_commit, fetch_all, log_request, count_all, get_logs

if __name__ == "__main__":
    # python3 I:/core/bots/ma/web/src/logs_db/test_db.py
    init_db()
    # ---
    print("count_all", count_all(status="no_result"))
    # ---
    # print("get_response_status", get_response_status())
    # ---
    print("get_logs", get_logs(status=""))
    print("get_logs", get_logs(status="no_result"))
