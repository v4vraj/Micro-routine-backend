from fastapi import APIRouter, HTTPException, Query
from app.services.ai_agent_service import generate_recommendations

router = APIRouter(prefix="/api/ai", tags=["AI Agent"])

@router.get("/recommendations")
def get_ai_recommendations(user_id: str = Query(..., description="User ID")):
    """
    Generate real-time, intelligent AI recommendations for a user.
    Combines Google Fit + Jira + Calendar + Goal data.
    Always computes fresh results.
    Example: GET /api/ai/recommendations?user_id=abc123
    """
    try:
        result = generate_recommendations(user_id)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
