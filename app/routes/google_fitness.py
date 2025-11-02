from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging
from app.utils.auth_utils import get_current_user
from app.services.google_service import (
    get_daily_steps_from_google,
    get_daily_calories_from_google,
    get_daily_active_minutes_from_google,
    set_user_goal,
    get_user_goal,
)
from app.database import users_collection

router = APIRouter(prefix="/api/google/fitness", tags=["Google Fit"])

# --- Pydantic Models ---
class GoalBase(BaseModel):
    goal: float


# ✅ --- STEPS ---
@router.get("/steps")
def get_daily_steps(current_user=Depends(get_current_user)):
    """Fetch today's Google Fit steps and user's custom goal."""
    try:
        user_id = str(current_user["_id"])
        total_steps = get_daily_steps_from_google(user_id)
        step_goal = get_user_goal(current_user, "step_goal", 8000)
        return {
            "steps_completed": total_steps,
            "step_goal": step_goal,
            "date": datetime.utcnow().date().isoformat(),
        }
    except Exception as e:
        logging.exception("Error fetching Google Fit steps data")
        raise HTTPException(status_code=500, detail=f"Error fetching steps: {e}")


@router.post("/steps/goal")
def set_daily_step_goal(goal: GoalBase, current_user=Depends(get_current_user)):
    """Set or update the user's daily step goal."""
    return set_user_goal(str(current_user["_id"]), "step_goal", goal.goal)


# ✅ --- CALORIES ---
@router.get("/calories")
def get_daily_calories(current_user=Depends(get_current_user)):
    """Fetch today's calories burned and user's calorie goal."""
    try:
        user_id = str(current_user["_id"])
        total_calories = get_daily_calories_from_google(user_id)
        calorie_goal = get_user_goal(current_user, "calorie_goal", 2000)
        return {
            "calories_burned": total_calories,
            "calorie_goal": calorie_goal,
            "date": datetime.utcnow().date().isoformat(),
        }
    except Exception as e:
        logging.exception("Error fetching Google Fit calories data")
        raise HTTPException(status_code=500, detail=f"Error fetching calories: {e}")


@router.post("/calories/goal")
def set_daily_calorie_goal(goal: GoalBase, current_user=Depends(get_current_user)):
    """Set or update the user's daily calorie goal."""
    return set_user_goal(str(current_user["_id"]), "calorie_goal", goal.goal)


# ✅ --- ACTIVE MINUTES ---
@router.get("/active_minutes")
def get_daily_active_minutes(current_user=Depends(get_current_user)):
    """Fetch today's active minutes and user's goal."""
    try:
        user_id = str(current_user["_id"])
        total_minutes = get_daily_active_minutes_from_google(user_id)
        minute_goal = get_user_goal(current_user, "active_minute_goal", 30)
        return {
            "active_minutes": total_minutes,
            "active_minute_goal": minute_goal,
            "date": datetime.utcnow().date().isoformat(),
        }
    except Exception as e:
        logging.exception("Error fetching Google Fit active minutes data")
        raise HTTPException(status_code=500, detail=f"Error fetching active minutes: {e}")


@router.post("/active_minutes/goal")
def set_daily_active_minute_goal(goal: GoalBase, current_user=Depends(get_current_user)):
    """Set or update the user's daily active minutes goal."""
    return set_user_goal(str(current_user["_id"]), "active_minute_goal", goal.goal)