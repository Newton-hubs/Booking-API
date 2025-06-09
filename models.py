from pydantic import EmailStr
from datetime import datetime
from typing import List

# In-memory data models for demonstration (replace with DB models in production)

class FitnessClass:
    def __init__(self, id: int, name: str, datetime: datetime, instructor: str, available_slots: int):
        self.id = id
        self.name = name
        self.datetime = datetime  # Should be timezone-aware (IST)
        self.instructor = instructor
        self.available_slots = available_slots

class Booking:
    def __init__(self, id: int, class_id: int, client_name: str, client_email: EmailStr, booked_at: datetime):
        self.id = id
        self.class_id = class_id
        self.client_name = client_name
        self.client_email = client_email
        self.booked_at = booked_at
