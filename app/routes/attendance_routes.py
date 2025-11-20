from fastapi import APIRouter, Depends, HTTPException
import logging
from app.utils.auth_utils import get_current_user
from app.utils.serializers import attendance_entity
from app.models.attendance_model import (
    CheckinRequest,
    AttendanceResponse,
)
from app.services.attendance_service import (
    get_today_attendance,
    checkin,
    checkout,
)

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


# ✅ GET TODAY'S ATTENDANCE
@router.get("/today", response_model=AttendanceResponse)
def fetch_today_attendance(current_user=Depends(get_current_user)):
    try:
        employee_id = current_user["employee_id"]
        record = get_today_attendance(employee_id)

        if not record:
            return {
                "id": None,
                "employee_id": employee_id,
                "date": None,
                "checkin_time": None,
                "checkout_time": None,
                "mood": None,
            }

        return attendance_entity(record)

    except Exception as e:
        logging.exception("Error getting today's attendance")
        raise HTTPException(status_code=500, detail=f"Error fetching attendance: {e}")


# ✅ CHECK-IN
@router.post("/checkin")
def check_in(data: CheckinRequest, current_user=Depends(get_current_user)):
    try:
        employee_id = current_user["employee_id"]
        record = checkin(employee_id, data.mood)
        return {
            "message": "Checked in",
            "log": attendance_entity(record)
        }

    except Exception as e:
        logging.exception("Error during check-in")
        raise HTTPException(status_code=500, detail=f"Check-in failed: {e}")


# ✅ CHECK-OUT
@router.post("/checkout")
def check_out(current_user=Depends(get_current_user)):
    try:
        employee_id = current_user["employee_id"]
        record = checkout(employee_id)

        if not record:
            raise HTTPException(status_code=404, detail="No check-in found")

        return {
            "message": "Checked out",
            "log": attendance_entity(record)
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Error during checkout")
        raise HTTPException(status_code=500, detail=f"Checkout failed: {e}")
