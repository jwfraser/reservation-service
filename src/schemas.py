from datetime import datetime

from pydantic import BaseModel, Json, EmailStr, validator


class Reservation(BaseModel):
    start_time: datetime
    end_time: datetime
    employee_email: EmailStr
    employee_name: str
    workplace: str

class ReservationResponse(BaseModel):
    status: str
    message: str