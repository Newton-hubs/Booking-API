from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")  # "user" | "admin"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bookings = relationship("Booking", back_populates="user", lazy="select")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"


class FitnessClass(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    instructor = Column(String(255), nullable=False)
    available_slots = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("available_slots >= 0", name="ck_classes_slots_non_negative"),
        # Index("ix_classes_scheduled_at", "scheduled_at"),
    )

    bookings = relationship("Booking", back_populates="fitness_class", lazy="select")

    def __repr__(self):
        return f"<FitnessClass id={self.id} name={self.name} slots={self.available_slots}>"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    booked_at = Column(DateTime(timezone=True), server_default=func.now())
    idempotency_key = Column(String(255), unique=True, nullable=True)  # client-supplied dedup key

    __table_args__ = (
        # One booking per user per class — enforced at DB level
        UniqueConstraint("class_id", "user_id", name="uq_bookings_class_user"),
        # Index("ix_bookings_user_id", "user_id"),
        # Index("ix_bookings_class_id", "class_id"),
    )

    fitness_class = relationship("FitnessClass", back_populates="bookings")
    user = relationship("User", back_populates="bookings")

    def __repr__(self):
        return f"<Booking id={self.id} class_id={self.class_id} user_id={self.user_id}>"
