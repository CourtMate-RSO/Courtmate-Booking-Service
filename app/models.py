from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReservationCreate(BaseModel):
    court_id: UUID
    starts_at: datetime
    ends_at: datetime

class Reservation(BaseModel):
    id: UUID
    court_id: UUID
    user_id: UUID
    starts_at: datetime
    ends_at: datetime
    total_price: float
    created_at: datetime
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None