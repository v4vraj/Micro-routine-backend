from bson import ObjectId

def attendance_entity(att):
    if not att:
        return None

    return {
        "id": str(att["_id"]) if "_id" in att else None,
        "employee_id": att.get("employee_id"),
        "date": att.get("date"),
        "checkin_time": att.get("checkin_time"),
        "checkout_time": att.get("checkout_time"),
        "mood": att.get("mood"),
    }
