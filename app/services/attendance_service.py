import logging
from datetime import datetime
from app.database import attendance_collection
from app.utils.timezone_utils import now_ist   # <-- use IST
from bson import ObjectId


def _today_ist():
    """Return today's date in Asia/Kolkata timezone."""
    return now_ist().strftime("%Y-%m-%d")


def get_today_attendance(employee_id: str):
    """Fetch today's attendance and auto-fix stale previous-day checkins."""
    today = _today_ist()

    # Find latest attendance record (could be stale)
    record = attendance_collection.find_one(
        {"employee_id": employee_id},
        sort=[("_id", -1)]
    )

    if not record:
        return None

    record_date = record.get("date")

    # If record is stale AND no checkout → auto-close using checkin_time
    if record_date != today and record.get("checkout_time") is None:
        attendance_collection.update_one(
            {"_id": record["_id"]},
            {"$set": {"checkout_time": record["checkin_time"]}}
        )
        record["checkout_time"] = record["checkin_time"]

    # Now fetch today's valid attendance record
    today_record = attendance_collection.find_one({
        "employee_id": employee_id,
        "date": today
    })

    return today_record


def checkin(employee_id: str, mood: int):
    """Create a check-in entry in IST."""
    try:
        today = _today_ist()

        # Prevent double check-ins
        existing = attendance_collection.find_one({
            "employee_id": employee_id,
            "date": today,
        })

        if existing:
            return existing

        record = {
            "employee_id": employee_id,
            "date": today,
            "checkin_time": now_ist(),   # ⭐ stored in IST
            "checkout_time": None,
            "mood": mood,
        }

        attendance_collection.insert_one(record)
        return record

    except Exception as e:
        logging.error(f"Error during check-in: {e}")
        raise


def checkout(employee_id: str):
    """Record checkout in IST."""
    try:
        today = _today_ist()

        updated = attendance_collection.find_one_and_update(
            {"employee_id": employee_id, "date": today},
            {"$set": {"checkout_time": now_ist()}},  # ⭐ stored in IST
            return_document=True,
        )

        return updated

    except Exception as e:
        logging.error(f"Error during checkout: {e}")
        raise
