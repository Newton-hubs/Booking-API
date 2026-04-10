from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    role: Literal["user", "admin"] = "user"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Classes ───────────────────────────────────────────────────────────────────

class FitnessClassCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scheduled_at: datetime
    instructor: str = Field(..., min_length=1, max_length=255)
    available_slots: int = Field(..., gt=0)


class FitnessClassOut(BaseModel):
    id: int
    name: str
    scheduled_at: datetime
    instructor: str
    available_slots: int

    model_config = {"from_attributes": True}


# ── Bookings ──────────────────────────────────────────────────────────────────

class BookingRequest(BaseModel):
    class_id: int
    idempotency_key: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional client-supplied key for deduplication. "
                    "Send the same key to safely retry without double-booking.",
    )


class BookingOut(BaseModel):
    id: int
    class_id: int
    user_id: int
    booked_at: datetime
    idempotency_key: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Generic responses ─────────────────────────────────────────────────────────

class MessageOut(BaseModel):
    message: str
