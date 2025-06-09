from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class FitnessClass(BaseModel):
    id: int
    name: str
    datetime: datetime  # Scheduled in IST
    instructor: str
    available_slots: int

class BookingRequest(BaseModel):
    class_id: int
    client_name: str
    client_email: EmailStr

class Booking(BaseModel):
    id: int
    class_id: int
    client_name: str
    client_email: EmailStr
    booked_at: datetime
