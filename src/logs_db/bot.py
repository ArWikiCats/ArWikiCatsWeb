# -*- coding: utf-8 -*-
"""

from .logs_db.bot import change_db_path, db_commit, init_db, fetch_all

"""
import re

try:
    from .db import change_db_path as _change_db_path, db_commit, init_db, fetch_all
except ImportError:
    from db import change_db_path as _change_db_path, db_commit, init_db, fetch_all


def change_db_path(file):
    return _change_db_path(file)


def log_request(endpoint, request_data, response_status, response_time):
    # ---
    response_time = round(response_time, 3)
    # ---
    response_status = str(response_status)
    # ---
    table_name = "logs" if endpoint != "/api/list" else "list_logs"
    # ---
    result = db_commit(
        f"""
        INSERT INTO {table_name} (
            endpoint, request_data, response_status, response_time, date_only
            )
        VALUES (?, ?, ?, ?, DATE('now'))
        ON CONFLICT(request_data, response_status, date_only) DO UPDATE SET
            response_count = response_count + 1,
            response_time = excluded.response_time,
            timestamp = CURRENT_TIMESTAMP
    """,
        (endpoint, str(request_data), response_status, response_time),
    )
    # ---
    if result is not True:
        print(f"Error logging request: {result}")
        if "no such table" in str(result):
            init_db()
    # ---
    return result


def add_status(query, params, status="", like="", day=""):
    # ---
    if not isinstance(params, list):
        params = list(params)
    # ---
    added = []
    # ---
    if status:
        if status == "Category":
            added.append("response_status like 'تصنيف%'")
        else:
            added.append("response_status = ?")
            params.append(status)
    elif like:
        added.append("response_status like ?")
        params.append(like)
    # ---
    # 2025-04-23
    pattern = r"\d{4}-\d{2}-\d{2}"
    # ---
    if day and re.match(pattern, day):
        added.append("date_only = ?")
        params.append(day)
    # ---
    if added:
        query += " WHERE " + " AND ".join(added)
    # ---
    # params = tuple(params)
    # ---
    return query, params


def sum_response_count(status="", table_name="logs", like=""):
    # ---
    query = f"select sum(response_count) as count_all from {table_name}"
    # ---
    params = []
    # ---
    query, params = add_status(query, params, status=status, like=like)
    # ---
    result = fetch_all(query, params, fetch_one=True)
    # ---
    print("result", result)
    # ---
    result = result["count_all"] or 0
    # ---
    return result


def get_response_status(table_name="logs"):
    # ---
    query = f"select response_status, count(response_status) as numbers from {table_name} group by response_status having count(*) > 2"
    # ---
    result = fetch_all(query, ())
    # ---
    result = [row["response_status"] for row in result]
    # ---
    return result


def count_all(status="", table_name="logs", like=""):
    # ---
    query = f"SELECT COUNT(*) FROM {table_name}"
    # ---
    params = []
    # ---
    query, params = add_status(query, params, status=status, like=like)
    # ---
    result = fetch_all(query, params, fetch_one=True)
    # ---
    if not result:
        return 0
    # ---
    if isinstance(result, list):
        result = result[0]
    # ---
    total_logs = result["COUNT(*)"]
    # ---
    return total_logs


def get_logs(per_page=10, offset=0, order="DESC", order_by="timestamp", status="", table_name="logs", like="", day=""):
    # ---
    if order not in ["ASC", "DESC"]:
        order = "DESC"
    # ---
    query = f"SELECT * FROM {table_name} "
    # ---
    params = []
    # ---
    query, params = add_status(query, params, status=status, like=like, day=day)
    # ---
    query += f"ORDER BY {order_by} {order} LIMIT ? OFFSET ?"
    # ---
    # {'id': 1, 'endpoint': 'api', 'request_data': 'Category:1934-35 in Bulgarian football', 'response_status': 'true', 'response_time': 123123.0, 'response_count': 6, 'timestamp': '2025-04-10 01:08:58'}
    # ---
    params.extend([per_page, offset])
    # ---
    logs = fetch_all(query, params)
    # ---
    return logs


def logs_by_day(table_name="logs"):
    # ---
    query_by_day = """
        SELECT
            date_only,
            CASE
                WHEN response_status LIKE 'تصنيف%' THEN 'Category'
                ELSE response_status
            END AS status_group,
            COUNT(request_data) AS title_count,
            sum(response_count) AS count
        FROM {table_name}
        GROUP BY date_only, status_group
        ORDER BY date_only;
        """.format(
        table_name=table_name
    )
    # ---
    result = fetch_all(query_by_day, ())
    # ---
    return result


def all_logs_en2ar(day=None):
    # ---
    query_by_day = """
        SELECT request_data, response_status
        FROM logs
    """
    # ---
    params = []
    # ---
    if day:
        if re.match(r"\d{4}-\d{2}-\d{2}", day):
            query_by_day += " \n where date_only = ? \n "
            params.append(day)

        elif re.match(r"\d{4}-\d{2}", day):
            query_by_day += " \n where strftime('%Y-%m', date_only) = ? \n "
            params.append(day)
    # ---
    query_by_day += """
        GROUP BY request_data, response_status
        ORDER BY request_data;
    """
    # ---
    print(query_by_day, day)
    # ---
    data = fetch_all(query_by_day, params)
    # ---
    result = {x["request_data"]: x["response_status"] for x in data}
    # ---
    return result
