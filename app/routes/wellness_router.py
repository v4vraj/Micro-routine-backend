from fastapi import APIRouter, Query
from app.services.wellness_service import (
    compute_and_store_daily_score,
    compute_overall_wellness_score,
)
from bson import ObjectId

router = APIRouter(prefix="/api/wellness", tags=["Wellness"])


def convert_objectid(obj):
    """Recursively convert ObjectIds to strings for JSON response."""
    if isinstance(obj, list):
        return [convert_objectid(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj


@router.get("/daily")
async def get_daily_wellness(user_id: str = Query(...)):
    result = await compute_and_store_daily_score(user_id)
    return {"message": "Wellness score computed successfully", "data": convert_objectid(result)}


@router.get("/overall")
async def get_overall_wellness(user_id: str = Query(...)):
    result = await compute_overall_wellness_score(user_id)
    return {"message": "Overall wellness score computed successfully", "data": convert_objectid(result)}
