# -*- coding: utf-8 -*-

import logging

from bot import db_commit, init_db

logger = logging.getLogger(__name__)


def update_existing_records():
    db_commit("UPDATE logs SET date_only = DATE(timestamp) WHERE date_only IS NULL")
    db_commit("UPDATE list_logs SET date_only = DATE(timestamp) WHERE date_only IS NULL")


def update_existing_tables():
    # إضافة العمود بدون default
    try:
        db_commit("ALTER TABLE logs ADD COLUMN date_only DATE")
    except Exception as e:
        logger.debug("Skipping adding date_only column to logs table: %s", e)

    try:
        db_commit("ALTER TABLE list_logs ADD COLUMN date_only DATE")
    except Exception as e:
        logger.debug("Skipping adding date_only column to list_logs table: %s", e)


if __name__ == "__main__":
    # python3 I:/core/bots/ma/web/src/logs_db/bot_update.py
    init_db()
    # ---
    update_existing_tables()
    update_existing_records()
