from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CheckinRequest(BaseModel):
    mood: int  # 1-5


class CheckoutRequest(BaseModel):
    pass


class AttendanceResponse(BaseModel):
    employee_id: str
    date: str
    checkin_time: Optional[datetime]
    checkout_time: Optional[datetime]
    mood: Optional[int]
