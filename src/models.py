import uuid

from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from db import Base


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    start_time = Column(DateTime())
    end_time = Column(DateTime())
    employee_email = Column(String(256))
    employee_name = Column(String(256))
    workplace = Column(String(36))