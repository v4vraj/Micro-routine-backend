from datetime import datetime
from zoneinfo import ZoneInfo

def now_ist():
    return datetime.now(ZoneInfo("Asia/Kolkata"))
