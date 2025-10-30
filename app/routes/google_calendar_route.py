from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth_utils import get_current_user
from app.services.google_service import get_month_events

router = APIRouter(prefix="/api/google", tags=["Google Calendar"])

@router.get("/events")
def fetch_google_events(current_user=Depends(get_current_user)):
    """
    Fetch current month's Google Calendar events for authenticated user.
    """
    try:
        user_id = str(current_user["_id"])
        events = get_month_events(user_id)
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
