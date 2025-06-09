import pytest
from fastapi.testclient import TestClient
from main import app
from db import init_db, seed_data
init_db()
seed_data()

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"].startswith("Welcome")

def test_get_classes():
    response = client.get("/classes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all("name" in c and "datetime" in c and "instructor" in c and "available_slots" in c for c in data)
    # Check that all classes are in the future (optional, based on seed)
    from datetime import datetime
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(IST)
    for c in data:
        dt = datetime.fromisoformat(c["datetime"])
        assert dt > now_ist

def test_get_bookings_empty():
    response = client.get("/bookings?email=notfound@example.com")
    assert response.status_code == 200
    assert response.json() == []

def test_get_bookings_after_booking():
    # Always reset DB and seed before this test to ensure slots are available
    init_db()
    seed_data()
    import uuid
    unique_email = f"testuser_{uuid.uuid4()}@example.com"
    # Use a class with more available slots (e.g., class_id 2 or 3)
    book_response = client.post(
        "/book",
        json={
            "class_id": 2,
            "client_name": "Test User",
            "client_email": unique_email
        }
    )
    assert book_response.status_code == 200
    # Now get bookings for that email
    response = client.get(f"/bookings?email={unique_email}")
    assert response.status_code == 200
    bookings = response.json()
    assert isinstance(bookings, list)
    assert any(b["client_email"] == unique_email for b in bookings)
