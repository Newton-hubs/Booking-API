"""
Tests for /bookings endpoints.

Covers: happy path, duplicate prevention, full-class rejection,
idempotency key deduplication, cancellation with slot return,
and a simulated concurrent booking race condition.
"""
import pytest
import threading
from app.models import FitnessClass


class TestBookClass:
    def test_book_class_success(self, client, auth_headers, sample_class):
        resp = client.post("/bookings/", json={"class_id": sample_class.id}, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["class_id"] == sample_class.id
        assert "booked_at" in data

    def test_book_class_unauthenticated(self, client, sample_class):
        resp = client.post("/bookings/", json={"class_id": sample_class.id})
        assert resp.status_code == 401

    def test_book_nonexistent_class(self, client, auth_headers):
        resp = client.post("/bookings/", json={"class_id": 99999}, headers=auth_headers)
        assert resp.status_code == 404

    def test_book_full_class_rejected(self, client, auth_headers, sample_class_full):
        resp = client.post("/bookings/", json={"class_id": sample_class_full.id}, headers=auth_headers)
        assert resp.status_code == 409
        assert "No slots available" in resp.json()["detail"]

    def test_duplicate_booking_rejected(self, client, auth_headers, sample_class):
        """Same user cannot book the same class twice."""
        client.post("/bookings/", json={"class_id": sample_class.id}, headers=auth_headers)
        resp = client.post("/bookings/", json={"class_id": sample_class.id}, headers=auth_headers)
        assert resp.status_code == 409
        assert "already booked" in resp.json()["detail"]

    def test_slot_count_decrements_on_booking(self, client, auth_headers, sample_class, db):
        initial_slots = sample_class.available_slots
        client.post("/bookings/", json={"class_id": sample_class.id}, headers=auth_headers)
        db.refresh(sample_class)
        assert sample_class.available_slots == initial_slots - 1


class TestIdempotency:
    def test_idempotent_booking_returns_same_record(self, client, auth_headers, sample_class):
        """
        Sending the same idempotency_key twice must return the same booking,
        not create a second one.
        """
        payload = {"class_id": sample_class.id, "idempotency_key": "idem-key-001"}
        resp1 = client.post("/bookings/", json=payload, headers=auth_headers)
        resp2 = client.post("/bookings/", json=payload, headers=auth_headers)

        assert resp1.status_code == 201
        assert resp2.status_code == 200
        assert resp1.json()["id"] == resp2.json()["id"]

    def test_idempotent_booking_does_not_decrement_slot_twice(
        self, client, auth_headers, sample_class, db
    ):
        initial_slots = sample_class.available_slots
        payload = {"class_id": sample_class.id, "idempotency_key": "idem-key-002"}

        client.post("/bookings/", json=payload, headers=auth_headers)
        client.post("/bookings/", json=payload, headers=auth_headers)

        db.refresh(sample_class)
        # Slot should only have gone down by 1, not 2
        assert sample_class.available_slots == initial_slots - 1


class TestMyBookings:
    def test_list_my_bookings(self, client, auth_headers, sample_class):
        client.post("/bookings/", json={"class_id": sample_class.id}, headers=auth_headers)
        resp = client.get("/bookings/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["class_id"] == sample_class.id

    def test_my_bookings_empty_for_new_user(self, client, auth_headers):
        resp = client.get("/bookings/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_my_bookings_isolated_from_other_users(self, client, sample_class):
        """User A's bookings should not appear in User B's list."""
        from tests.conftest import _register_and_login
        token_a = _register_and_login(client, "a@test.com", "password1")
        token_b = _register_and_login(client, "b@test.com", "password1")

        client.post("/bookings/", json={"class_id": sample_class.id},
                    headers={"Authorization": f"Bearer {token_a}"})

        resp_b = client.get("/bookings/me", headers={"Authorization": f"Bearer {token_b}"})
        assert resp_b.json() == []


class TestCancelBooking:
    def test_cancel_booking_success(self, client, auth_headers, sample_class, db):
        book_resp = client.post(
            "/bookings/", json={"class_id": sample_class.id}, headers=auth_headers
        )
        booking_id = book_resp.json()["id"]
        slots_after_booking = db.query(FitnessClass).get(sample_class.id).available_slots

        cancel_resp = client.delete(f"/bookings/{booking_id}", headers=auth_headers)
        assert cancel_resp.status_code == 204

        db.refresh(sample_class)
        assert sample_class.available_slots == slots_after_booking + 1

    def test_cancel_nonexistent_booking(self, client, auth_headers):
        resp = client.delete("/bookings/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_cancel_other_users_booking_denied(self, client, sample_class):
        """User B cannot cancel User A's booking."""
        from tests.conftest import _register_and_login
        token_a = _register_and_login(client, "ca@test.com", "password1")
        token_b = _register_and_login(client, "cb@test.com", "password1")

        book_resp = client.post(
            "/bookings/", json={"class_id": sample_class.id},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        booking_id = book_resp.json()["id"]

        resp = client.delete(
            f"/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404


class TestRaceCondition:
    def test_concurrent_bookings_respect_slot_limit(self, client, db):
        """
        Create a class with 1 slot and fire 5 concurrent booking requests
        from 5 different users. Exactly 1 must succeed; the rest must get 409.
        This validates the atomic UPDATE WHERE available_slots > 0 guard.
        """
        from datetime import datetime, timedelta, timezone
        from tests.conftest import _register_and_login

        fc = FitnessClass(
            name="One Slot Class",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            instructor="Tester",
            available_slots=1,
        )
        db.add(fc)
        db.commit()
        db.refresh(fc)

        tokens = [
            _register_and_login(client, f"racer{i}@test.com", "password1")
            for i in range(5)
        ]

        results = []

        def book(token):
            resp = client.post(
                "/bookings/", json={"class_id": fc.id},
                headers={"Authorization": f"Bearer {token}"},
            )
            results.append(resp.status_code)

        threads = [threading.Thread(target=book, args=(t,)) for t in tokens]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = results.count(201)
        conflicts = results.count(409)

        assert successes == 1, f"Expected exactly 1 success, got {successes}. Results: {results}"
        assert conflicts == 4, f"Expected 4 conflicts, got {conflicts}. Results: {results}"

        db.refresh(fc)
        assert fc.available_slots == 0
