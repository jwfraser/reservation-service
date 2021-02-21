from datetime import datetime

from pydantic import BaseModel, Json

class Reservation(BaseModel):
    start_time: datetime
    end_time: datetime
    employee_email: str
    employee_name: str
    resource_id: str