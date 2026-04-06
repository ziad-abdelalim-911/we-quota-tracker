import sys
from datetime import datetime, timedelta, timezone
import requests
import re
import logging
from db import insert_record
from api_client import fetch_quota_data


logging.basicConfig(level=logging.INFO)


def tsConv(unix_timestamp, returnUntil=False):
    # Convert UNIX timestamp to timezone-aware datetime object in UTC
    dt_utc = datetime.fromtimestamp(unix_timestamp / 1000.0, tz=timezone.utc)
    
    # Get the local timezone
    local_tz = datetime.now().astimezone().tzinfo
    
    # Convert UTC datetime to local datetime
    dt_local = dt_utc.astimezone(local_tz)
    
    # Format the local datetime in "DD/MM/YYYY at HH:MM AM/PM" format
    formatted_date = dt_local.strftime("%d/%m/%Y at %I:%M %p")

    dates = [formatted_date]
    
    if returnUntil:
        # Calculate the time difference between now and the timestamp date
        now_local = datetime.now().astimezone(local_tz)
        time_difference = dt_local - now_local
        
        if time_difference <= timedelta(days=1):
            hours_left = int(time_difference.total_seconds() // 3600)
            dates.append(f"in {hours_left} hours")
        else:
            days_left = time_difference.days
            dates.append(f"in {days_left} days")
    
    return dates

def check_internet_connection():
    try:
        response = requests.get("https://google.com/", timeout=5)
        if response.status_code == 200:
            logging.info("Internet connection is available.")
    except requests.RequestException as e:
        logging.error("Internet Connection Error — No internet connection available. Exiting...")
        sys.exit(1)

check_internet_connection()


with requests.Session() as session:
    auth, result = fetch_quota_data(session)

    if auth is None:
        logging.error(result)
        sys.exit(1)

    qoutaBody = result

    offerName = qoutaBody["offerName"]
    totalGB = qoutaBody["total"]
    usedGB = qoutaBody["used"]
    remainGB = qoutaBody["remain"]
    usagePrc = usedGB / totalGB * 100
    renewedDate = tsConv(qoutaBody["effectiveTime"])[0]
    expiryDate = tsConv(qoutaBody["expireTime"], returnUntil=True)
    expDate = expiryDate[0]
    daysUntilExp = expiryDate[1]

    oneDayGB = totalGB / 30
    remainingDays = int(re.search(r'\d+', daysUntilExp).group())
    currentDay = 30 - remainingDays

    atLeastRemain = remainingDays * oneDayGB
    overAllState = "Under" if remainGB >= atLeastRemain else "Over"
    overAllStateGbs = abs(remainGB - atLeastRemain)
    stateDays = overAllStateGbs / oneDayGB

    # Write to DB after successful fetch
    now_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_success, dailyUsage = insert_record(
        now_datetime,
        currentDay,
        remainGB,
        overAllState,
        overAllStateGbs,
        stateDays,
        remainingDays
    )

    if db_success:
        logging.info("─── Quota Record Saved ───────────────────")
        logging.info("  Day            : %d", currentDay)
        logging.info("  Usage Today    : %.1f GB", dailyUsage)
        logging.info("  Remaining      : %.1f / %s GB (%.1f%% used)", remainGB, totalGB, usagePrc)
        logging.info("  Remaining Days : %d", remainingDays)
        logging.info("  Overall State  : %s by %.1f GB (%.1f days)", overAllState, overAllStateGbs, stateDays)
        logging.info("──────────────────────────────────────────")
    else:
        logging.error("Couldn't add record to database. Please check your DB connection and try again.")