"""Tests for /classes endpoints."""
import pytest
from datetime import datetime, timedelta, timezone


FUTURE_DT = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()


class TestListClasses:
    def test_list_classes_public(self, client, sample_class):
        """No auth required to list classes."""
        resp = client.get("/classes/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert any(c["id"] == sample_class.id for c in data)

    def test_list_classes_empty(self, client):
        resp = client.get("/classes/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_single_class(self, client, sample_class):
        resp = client.get(f"/classes/{sample_class.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == sample_class.name

    def test_get_nonexistent_class(self, client):
        resp = client.get("/classes/99999")
        assert resp.status_code == 404


class TestCreateClass:
    def test_create_class_as_admin(self, client, admin_headers):
        resp = client.post("/classes/", json={
            "name": "Spin Class",
            "scheduled_at": FUTURE_DT,
            "instructor": "Coach K",
            "available_slots": 10,
        }, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Spin Class"
        assert data["available_slots"] == 10

    def test_create_class_as_user_forbidden(self, client, auth_headers):
        resp = client.post("/classes/", json={
            "name": "Spin Class",
            "scheduled_at": FUTURE_DT,
            "instructor": "Coach K",
            "available_slots": 10,
        }, headers=auth_headers)
        assert resp.status_code == 403

    def test_create_class_unauthenticated(self, client):
        resp = client.post("/classes/", json={
            "name": "Spin Class",
            "scheduled_at": FUTURE_DT,
            "instructor": "Coach K",
            "available_slots": 10,
        })
        assert resp.status_code == 401

    def test_create_class_zero_slots_rejected(self, client, admin_headers):
        resp = client.post("/classes/", json={
            "name": "Empty Class",
            "scheduled_at": FUTURE_DT,
            "instructor": "Coach K",
            "available_slots": 0,  # must be > 0
        }, headers=admin_headers)
        assert resp.status_code == 422


class TestDeleteClass:
    def test_delete_class_as_admin(self, client, admin_headers, sample_class):
        resp = client.delete(f"/classes/{sample_class.id}", headers=admin_headers)
        assert resp.status_code == 204
        assert client.get(f"/classes/{sample_class.id}").status_code == 404

    def test_delete_class_as_user_forbidden(self, client, auth_headers, sample_class):
        resp = client.delete(f"/classes/{sample_class.id}", headers=auth_headers)
        assert resp.status_code == 403
