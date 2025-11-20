from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from app.database import db, users_collection
from app.services.jira_service import get_high_priority_tickets_for_user
from app.services.google_service import (
    get_month_events,
    get_daily_steps_from_google,
    get_daily_calories_from_google,
    get_daily_active_minutes_from_google,
)

def generate_recommendations(user_id: str):
    """Generate and return only the highest-priority AI recommendation."""
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user_id")

    user = users_collection.find_one({"_id": ObjectId(user_id)}) or {}

    # === Fetch live data ===
    try:
        jira_tasks = get_high_priority_tickets_for_user(user_id).get("tickets", [])
    except Exception:
        jira_tasks = []

    try:
        calendar_events = get_month_events(user_id)
    except Exception:
        calendar_events = []

    try:
        steps = get_daily_steps_from_google(user_id)
        calories = get_daily_calories_from_google(user_id)
        active_min = get_daily_active_minutes_from_google(user_id)
    except Exception:
        steps = calories = active_min = 0

    # === User goals ===
    step_goal = user.get("step_goal", 8000)
    calorie_goal = user.get("calorie_goal", 2000)
    active_min_goal = user.get("active_minute_goal", 60)

    recommendations = []

    # === Jira ===
    high = sum(1 for t in jira_tasks if "High" in t["priority"])
    med = sum(1 for t in jira_tasks if "Medium" in t["priority"])
    low = sum(1 for t in jira_tasks if "Low" in t["priority"])

    if high > 0:
        recommendations.append({
            "priority": 1,
            "type": "jira",
            "message": f"⚡ {high} high-priority task(s) pending — complete them first!"
        })
    elif med > 0:
        recommendations.append({
            "priority": 2,
            "type": "jira",
            "message": f"📋 {med} medium-priority task(s) left — plan before meetings."
        })
    elif low > 0:
        recommendations.append({
            "priority": 4,
            "type": "jira",
            "message": f"🧩 {low} low-priority tasks can wait till you have free time."
        })

    # === Calendar ===
    today = datetime.utcnow().date().isoformat()
    today_meetings = [e for e in calendar_events if e["start"].startswith(today)]
    meeting_count = len(today_meetings)

    if meeting_count > 6:
        recommendations.append({
            "priority": 1,
            "type": "calendar",
            "message": "📅 Too many meetings — block 1h for deep work."
        })
    elif 3 <= meeting_count <= 6:
        recommendations.append({
            "priority": 3,
            "type": "calendar",
            "message": "🗓 Balanced meeting day — schedule short recovery breaks."
        })
    else:
        recommendations.append({
            "priority": 4,
            "type": "calendar",
            "message": "🌤 Light meeting day — perfect for deep work."
        })

    # === Fitness ===
    if steps < 0.7 * step_goal:
        recommendations.append({
            "priority": 2,
            "type": "fitness",
            "message": f"🚶 Only {steps}/{step_goal} steps — take a 10-min walk."
        })

    if active_min < 0.7 * active_min_goal:
        recommendations.append({
            "priority": 2,
            "type": "fitness",
            "message": f"⏱️ Only {active_min}/{active_min_goal} active minutes — move a bit!"
        })

    # === Sort and select top ===
    recommendations.sort(key=lambda x: x["priority"])
    top_rec = recommendations[0] if recommendations else {
        "priority": 5,
        "type": "general",
        "message": "🌿 No major issues — stay consistent today!"
    }

    # === Return only top priority ===
    return {
        "user_id": user_id,
        "recommendation": top_rec,
        "generated_at": datetime.utcnow().isoformat(),
        "source": "fresh"
    }
