from pydantic import BaseModel
from datetime import date
from typing import Optional

class WellnessScore(BaseModel):
    user_id: str
    date: date
    fitness_score: float
    jira_score: float
    calendar_score: float
    total_score: float
