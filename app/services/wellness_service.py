from datetime import date, datetime, timedelta
from fastapi import HTTPException
import logging
from statistics import mean
from app.database import wellness_collection, tokens_collection
from app.services.google_service import (
    get_daily_steps_from_google,
    get_daily_calories_from_google,
    get_daily_active_minutes_from_google,
    get_month_events,
)
from app.services.jira_service import get_high_priority_tickets_for_user


# ✅ Weightage Configuration
WEIGHTS = {
    "fitness": 0.4,
    "jira": 0.4,
    "calendar": 0.2
}


# ----------------------- FITNESS SCORING -----------------------

def calculate_fitness_score(user_doc: dict, user_id: str):
    """Calculate fitness score based on Google Fit data vs goals."""
    try:
        steps = get_daily_steps_from_google(user_id)
        calories = get_daily_calories_from_google(user_id)
        active_minutes = get_daily_active_minutes_from_google(user_id)

        step_goal = user_doc.get("step_goal", 8000)
        calorie_goal = user_doc.get("calorie_goal", 2200)
        active_goal = user_doc.get("active_minute_goal", 30)

        steps_ratio = min(steps / step_goal, 1.0)
        calories_ratio = min(calories / calorie_goal, 1.0)
        active_ratio = min(active_minutes / active_goal, 1.0)

        score = round((steps_ratio * 0.5 + calories_ratio * 0.3 + active_ratio * 0.2) * 100, 2)

        return {
            "steps": steps,
            "calories": calories,
            "active_minutes": active_minutes,
            "score": score
        }

    except Exception as e:
        logging.error(f"Error calculating fitness score for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating fitness score: {e}")


# ----------------------- JIRA SCORING -----------------------

def calculate_jira_score(user_id: str):
    """Calculate Jira productivity score based on high-priority tickets."""
    try:
        jira_data = get_high_priority_tickets_for_user(user_id)
        tickets = jira_data.get("tickets", [])

        total_tickets = len(tickets)
        if total_tickets == 0:
            return {"tickets": [], "score": 100.0}

        completed_tickets = sum(1 for t in tickets if t["status"].lower() in ["done", "resolved"])
        in_progress = sum(1 for t in tickets if t["status"].lower() in ["in progress", "in-review"])

        completion_ratio = completed_tickets / total_tickets
        progress_ratio = in_progress / total_tickets

        score = round((completion_ratio * 0.8 + progress_ratio * 0.2) * 100, 2)

        return {
            "total_tickets": total_tickets,
            "completed_tickets": completed_tickets,
            "in_progress_tickets": in_progress,
            "score": score
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error calculating Jira score for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Jira score: {e}")


# ----------------------- CALENDAR SCORING -----------------------

def calculate_calendar_score(user_id: str):
    """Calculate calendar score based on user's meeting balance."""
    try:
        events = get_month_events(user_id)
        today_str = date.today().isoformat()
        today_events = [e for e in events if e["start"].startswith(today_str)]

        total_meetings = len(today_events)
        if total_meetings == 0:
            return {"meetings": 0, "score": 100.0}

        # 4–6 meetings/day ideal
        if total_meetings <= 2:
            score = 70.0
        elif 3 <= total_meetings <= 6:
            score = 100.0
        else:
            score = max(60.0, 120 - total_meetings * 10)

        return {"meetings": total_meetings, "score": round(score, 2)}

    except Exception as e:
        logging.error(f"Error calculating calendar score for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating calendar score: {e}")


# ----------------------- DAILY AGGREGATION -----------------------

async def compute_and_store_daily_score(user_id: str):
    """Compute or reuse wellness score (only recompute after 6 hours)."""
    try:
        user_doc = tokens_collection.find_one({"user_id": user_id})
        print(user_doc)
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        today_str = date.today().isoformat()
        existing_record = wellness_collection.find_one({"user_id": user_id, "date": today_str})

        if existing_record:
            last_updated = existing_record.get("last_updated")
            if last_updated:
                last_updated_dt = datetime.fromisoformat(last_updated)
                if datetime.utcnow() - last_updated_dt < timedelta(hours=6):
                    # ⏳ Reuse existing score if within 6 hours
                    return existing_record

        # 🔄 Compute fresh scores
        fitness_data = calculate_fitness_score(user_doc, user_id)
        jira_data = calculate_jira_score(user_id)
        calendar_data = calculate_calendar_score(user_id)

        total_score = round(
            fitness_data["score"] * WEIGHTS["fitness"]
            + jira_data["score"] * WEIGHTS["jira"]
            + calendar_data["score"] * WEIGHTS["calendar"],
            2,
        )

        record = {
            "user_id": user_id,
            "date": today_str,
            "fitness": fitness_data,
            "jira": jira_data,
            "calendar": calendar_data,
            "total_score": total_score,
            "last_updated": datetime.utcnow().isoformat(),
        }

        wellness_collection.update_one(
            {"user_id": user_id, "date": today_str},
            {"$set": record},
            upsert=True,
        )

        return record

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error computing wellness score: {e}")
        raise HTTPException(status_code=500, detail=f"Error computing wellness score: {e}")


# ----------------------- OVERALL WELLNESS SCORE -----------------------

async def compute_overall_wellness_score(user_id: str):
    """Compute the user's overall average wellness score."""
    try:
        records = list(wellness_collection.find({"user_id": user_id}))
        if not records:
            raise HTTPException(status_code=404, detail="No wellness data found for user")

        fitness_scores = [r["fitness"]["score"] for r in records if "fitness" in r]
        jira_scores = [r["jira"]["score"] for r in records if "jira" in r]
        calendar_scores = [r["calendar"]["score"] for r in records if "calendar" in r]
        total_scores = [r["total_score"] for r in records if "total_score" in r]

        result = {
            "user_id": user_id,
            "days_recorded": len(records),
            "average_scores": {
                "fitness": round(mean(fitness_scores), 2) if fitness_scores else 0,
                "jira": round(mean(jira_scores), 2) if jira_scores else 0,
                "calendar": round(mean(calendar_scores), 2) if calendar_scores else 0,
            },
            "overall_wellness_score": round(mean(total_scores), 2) if total_scores else 0,
        }

        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error computing overall wellness score: {e}")
        raise HTTPException(status_code=500, detail=f"Error computing overall wellness score: {e}")
