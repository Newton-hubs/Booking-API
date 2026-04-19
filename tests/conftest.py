"""
Test fixtures.
Uses an in-memory SQLite database so tests run without a real PostgreSQL
instance. The app's `get_db` dependency is overridden with a test session.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import User, FitnessClass
from app.core.security import hash_password

SQLITE_URL = "sqlite:///./test.db"

engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
# Disable ALL startup and shutdown events during tests
import app.main as main_module
main_module.engine = engine
app.router.on_startup.clear()
app.router.on_shutdown.clear()


@pytest.fixture(autouse=True)
def setup_database():
    """Recreate all tables before each test, drop after."""
    Base.metadata.drop_all(bind=engine)   # ← drop first to clear any stale indexes
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def sample_class(db):
    """A fitness class with 5 available slots."""
    from datetime import datetime, timedelta, timezone
    fc = FitnessClass(
        name="Test Yoga",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
        instructor="Test Instructor",
        available_slots=5,
    )
    db.add(fc)
    db.commit()
    db.refresh(fc)
    return fc


@pytest.fixture()
def sample_class_full(db):
    """A fitness class with 0 available slots."""
    from datetime import datetime, timedelta, timezone
    fc = FitnessClass(
        name="Full Class",
        scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
        instructor="Test Instructor",
        available_slots=0,
    )
    db.add(fc)
    db.commit()
    db.refresh(fc)
    return fc


def _register_and_login(client, email, password, role="user"):
    client.post("/auth/register", json={
        "email": email, "name": "Test User",
        "password": password, "role": role,
    })
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


@pytest.fixture()
def user_token(client):
    return _register_and_login(client, "user@test.com", "password123", role="user")


@pytest.fixture()
def admin_token(client):
    return _register_and_login(client, "admin@test.com", "password123", role="admin")


@pytest.fixture()
def auth_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
