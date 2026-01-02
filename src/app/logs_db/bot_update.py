# -*- coding: utf-8 -*-

from bot import init_db, db_commit

def update_existing_records():
    db_commit("UPDATE logs SET date_only = DATE(timestamp) WHERE date_only IS NULL")
    db_commit("UPDATE list_logs SET date_only = DATE(timestamp) WHERE date_only IS NULL")

def update_existing_tables():
    # إضافة العمود بدون default
    try:
        db_commit("ALTER TABLE logs ADD COLUMN date_only DATE")
    except Exception as e:
        print(f"تخطي إضافة العمود 'date_only' إلى جدول logs: {e}")

    try:
        db_commit("ALTER TABLE list_logs ADD COLUMN date_only DATE")
    except Exception as e:
        print(f"تخطي إضافة العمود 'date_only' إلى جدول list_logs: {e}")

if __name__ == "__main__":
    # python3 I:/core/bots/ma/web/src/logs_db/bot_update.py
    init_db()
    # ---
    update_existing_tables()
    update_existing_records()
