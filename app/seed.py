"""
Run once to seed sample classes and an admin user.
Usage: python -m app.seed
"""
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal, engine
from app.models import Base, User, FitnessClass
from app.core.security import hash_password
from app.core.logging import logger


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ── Admin user ────────────────────────────────────────────────────────
        if not db.query(User).filter(User.email == "admin@fitnessstudio.com").first():
            admin = User(
                email="admin@fitnessstudio.com",
                name="Studio Admin",
                hashed_password=hash_password("admin1234"),
                role="admin",
            )
            db.add(admin)
            logger.info("Seeded admin user | email=admin@fitnessstudio.com password=admin1234")

        # ── Sample classes ────────────────────────────────────────────────────
        if db.query(FitnessClass).count() == 0:
            now = datetime.now(timezone.utc)
            sample_classes = [
                FitnessClass(
                    name="Morning Yoga",
                    scheduled_at=now + timedelta(days=1, hours=7),
                    instructor="Amit Sharma",
                    available_slots=15,
                ),
                FitnessClass(
                    name="Zumba Blast",
                    scheduled_at=now + timedelta(days=1, hours=18),
                    instructor="Priya Singh",
                    available_slots=20,
                ),
                FitnessClass(
                    name="HIIT Power",
                    scheduled_at=now + timedelta(days=2, hours=6),
                    instructor="Rahul Verma",
                    available_slots=12,
                ),
                FitnessClass(
                    name="Pilates Core",
                    scheduled_at=now + timedelta(days=3, hours=9),
                    instructor="Sunita Rao",
                    available_slots=10,
                ),
            ]
            db.add_all(sample_classes)
            logger.info(f"Seeded {len(sample_classes)} fitness classes")

        db.commit()
        logger.info("Database seeding complete.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
