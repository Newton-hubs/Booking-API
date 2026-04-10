from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from typing import List

from app.database import get_db
from app.models import Booking, FitnessClass
from app.schemas import BookingRequest, BookingOut
from app.core.security import get_current_user
from app.core.logging import logger

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def book_class(
    payload: BookingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Book a fitness class for the authenticated user.

    Race condition safety: slot decrement uses an atomic UPDATE with a
    WHERE available_slots > 0 guard. If two requests arrive simultaneously
    for the last slot, only one UPDATE will match (rowcount=1); the other
    receives a 409 without ever committing.

    Idempotency: supply an idempotency_key to safely retry this request.
    Retrying with the same key returns the existing booking instead of
    creating a duplicate.
    """
    user_id = current_user["user_id"]

    # ── Idempotency check ────────────────────────────────────────────────────
    if payload.idempotency_key:
        existing = (
            db.query(Booking)
            .filter(Booking.idempotency_key == payload.idempotency_key)
            .first()
        )
        if existing:
            logger.info(
                f"Idempotent booking returned | key={payload.idempotency_key} "
                f"booking_id={existing.id}"
            )
            return existing

    # ── Verify class exists ──────────────────────────────────────────────────
    fitness_class = (
        db.query(FitnessClass)
        .filter(FitnessClass.id == payload.class_id)
        .first()
    )
    if not fitness_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")

    if fitness_class.available_slots <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No slots available for this class.",
        )

    # ── Atomic slot decrement (race condition safe) ──────────────────────────
    # The WHERE available_slots > 0 means only one concurrent transaction
    # wins the last slot. rowcount=0 means we lost the race.
    result = db.execute(
        text(
            "UPDATE classes SET available_slots = available_slots - 1 "
            "WHERE id = :class_id AND available_slots > 0"
        ),
        {"class_id": payload.class_id},
    )

    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No slots available for this class.",
        )

    # ── Insert booking ───────────────────────────────────────────────────────
    booking = Booking(
        class_id=payload.class_id,
        user_id=user_id,
        idempotency_key=payload.idempotency_key,
    )
    db.add(booking)

    try:
        db.commit()
    except IntegrityError:
        # UniqueConstraint(class_id, user_id) fired — user already booked
        db.rollback()
        # Undo slot decrement since booking failed
        db.execute(
            text("UPDATE classes SET available_slots = available_slots + 1 WHERE id = :class_id"),
            {"class_id": payload.class_id},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already booked this class.",
        )

    db.refresh(booking)
    logger.info(
        f"Booking confirmed | booking_id={booking.id} class_id={payload.class_id} "
        f"user_id={user_id}"
    )
    return booking


@router.get("/me", response_model=List[BookingOut])
def my_bookings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns all bookings for the currently authenticated user.
    """
    user_id = current_user["user_id"]
    bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
    return bookings


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Cancel a booking. Only the booking owner can cancel their own booking.
    Slot is returned to the class on successful cancellation.
    """
    user_id = current_user["user_id"]
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == user_id,
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or does not belong to you.",
        )

    class_id = booking.class_id
    db.delete(booking)

    # Return the slot
    db.execute(
        text("UPDATE classes SET available_slots = available_slots + 1 WHERE id = :class_id"),
        {"class_id": class_id},
    )
    db.commit()

    logger.info(f"Booking cancelled | booking_id={booking_id} user_id={user_id}")
