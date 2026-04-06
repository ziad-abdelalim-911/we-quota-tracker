import sys
from datetime import datetime
import logging
import requests
from db import insert_record
from api_client import fetch_quota_data
from utils import check_internet_connection
from quota import calculate_quota


logging.basicConfig(level=logging.INFO)

check_internet_connection()


with requests.Session() as session:
    auth, result = fetch_quota_data(session)

    if auth is None:
        logging.error(result)
        sys.exit(1)

    q = calculate_quota(result)

    # Write to DB after successful fetch
    now_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_success, dailyUsage = insert_record(
        now_datetime,
        q["current_day"],
        q["remain_gb"],
        q["overall_state"],
        q["overall_state_gbs"],
        q["state_days"],
        q["remaining_days"]
    )

    if db_success:
        logging.info("─── Quota Record Saved ───────────────────")
        logging.info("  Day            : %d", q["current_day"])
        logging.info("  Usage Today    : %.1f GB", dailyUsage)
        logging.info("  Remaining      : %.1f / %s GB (%.1f%% used)", q["remain_gb"], q["total_gb"], q["usage_prc"])
        logging.info("  Remaining Days : %d", q["remaining_days"])
        logging.info("  Overall State  : %s by %.1f GB (%.1f days)", q["overall_state"], q["overall_state_gbs"], q["state_days"])
        logging.info("──────────────────────────────────────────")
    else:
        logging.error("Couldn't add record to database. Please check your DB connection and try again.")