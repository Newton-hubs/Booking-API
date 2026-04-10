from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import FitnessClass
from app.schemas import FitnessClassCreate, FitnessClassOut
from app.core.security import get_current_user, require_role
from app.core.logging import logger

router = APIRouter(prefix="/classes", tags=["Classes"])


@router.get("/", response_model=List[FitnessClassOut])
def list_classes(db: Session = Depends(get_db)):
    """
    Public endpoint — returns all upcoming classes ordered by schedule time.
    No authentication required.
    """
    now = datetime.now(timezone.utc)
    classes = (
        db.query(FitnessClass)
        .filter(FitnessClass.scheduled_at > now)
        .order_by(FitnessClass.scheduled_at.asc())
        .all()
    )
    return classes


@router.get("/{class_id}", response_model=FitnessClassOut)
def get_class(class_id: int, db: Session = Depends(get_db)):
    """
    Public endpoint — returns a single class by ID.
    """
    fitness_class = db.query(FitnessClass).filter(FitnessClass.id == class_id).first()
    if not fitness_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")
    return fitness_class


@router.post(
    "/",
    response_model=FitnessClassOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def create_class(
    payload: FitnessClassCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Admin only — create a new fitness class.
    Requires a valid JWT with role='admin'.
    """
    fitness_class = FitnessClass(
        name=payload.name,
        scheduled_at=payload.scheduled_at,
        instructor=payload.instructor,
        available_slots=payload.available_slots,
    )
    db.add(fitness_class)
    db.commit()
    db.refresh(fitness_class)

    logger.info(
        f"Class created | id={fitness_class.id} name={fitness_class.name} "
        f"by admin={current_user.get('sub')}"
    )
    return fitness_class


@router.delete(
    "/{class_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
def delete_class(class_id: int, db: Session = Depends(get_db)):
    """
    Admin only — delete a class. Cascades to all related bookings.
    """
    fitness_class = db.query(FitnessClass).filter(FitnessClass.id == class_id).first()
    if not fitness_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")
    db.delete(fitness_class)
    db.commit()
    logger.info(f"Class deleted | id={class_id}")
