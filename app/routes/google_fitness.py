from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import pytz
import logging
from app.utils.auth_utils import get_current_user
from app.services.google_service import (
    get_daily_steps_from_google,
    get_daily_calories_from_google,
    get_daily_active_minutes_from_google
)
# Assuming you have a users_collection in your database.py
from app.database import users_collection

router = APIRouter(prefix="/api/google/fitness", tags=["Google Fit"])

# --- Pydantic Model for Goal Input ---
class StepGoal(BaseModel):
    goal: int

@router.get("/steps")
def get_daily_steps(current_user=Depends(get_current_user)):
    """
    Fetch today's Google Fit steps and the user's custom goal.
    """
    try:
        user_id = str(current_user["_id"])
        
        # Call the service function to get steps
        total_steps = get_daily_steps_from_google(user_id)

        # Fetch goal from user's record (default to 8000 if not set)
        step_goal = current_user.get("step_goal", 8000)

        return {
            "steps_completed": total_steps,
            "step_goal": step_goal,
            "date": datetime.utcnow().date().isoformat(),
        }

    except Exception as e:
        logging.exception("Error fetching Google Fit steps data")
        raise HTTPException(status_code=500, detail=f"Error fetching steps: {e}")


@router.get("/calories")
def get_daily_calories(current_user=Depends(get_current_user)):
    """
    Fetch today's calories burned from Google Fit.
    """
    try:
        user_id = str(current_user["_id"])
        
        # Call the service function to get calories
        total_calories = get_daily_calories_from_google(user_id)

        # You can also add a calorie goal
        calorie_goal = current_user.get("calorie_goal", 2000) # Example default

        return {
            "calories_burned": total_calories,
            "calorie_goal": calorie_goal,
            "date": datetime.utcnow().date().isoformat(),
        }

    except Exception as e:
        logging.exception("Error fetching Google Fit calories data")
        raise HTTPException(status_code=500, detail=f"Error fetching calories: {e}")


@router.get("/active_minutes")
def get_daily_active_minutes(current_user=Depends(get_current_user)):
    """
    Fetch today's active minutes from Google Fit.
    """
    try:
        user_id = str(current_user["_id"])
        
        # Call the service function to get active minutes
        total_minutes = get_daily_active_minutes_from_google(user_id)

        # You can also add an active minute goal
        minute_goal = current_user.get("active_minute_goal", 30) # Example default

        return {
            "active_minutes": total_minutes,
            "active_minute_goal": minute_goal,
            "date": datetime.utcnow().date().isoformat(),
        }

    except Exception as e:
        logging.exception("Error fetching Google Fit active minutes data")
        raise HTTPException(status_code=500, detail=f"Error fetching active minutes: {e}")


@router.post("/steps/goal")
def set_daily_step_goal(
    step_goal: StepGoal,
    current_user=Depends(get_current_user)
):
    """
    Set or update the user's daily step goal in the database.
    """
    try:
        if step_goal.goal <= 0:
            raise HTTPException(status_code=400, detail="Goal must be a positive number")

        # Update the user's document in MongoDB
        result = users_collection.update_one(
            {"_id": current_user["_id"]},
            {"$set": {"step_goal": step_goal.goal}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "Step goal updated successfully", "new_goal": step_goal.goal}

    except HTTPException as he:
        # Re-raise HTTPExceptions to avoid them being caught as 500
        raise he
    except Exception as e:
        logging.exception("Error updating step goal")
        raise HTTPException(status_code=500, detail=f"Error updating goal: {e}")

