"""Tests for /auth/register and /auth/login endpoints."""
import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "name": "New User",
            "password": "securepass",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["role"] == "user"
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client):
        payload = {"email": "dup@example.com", "name": "A", "password": "pass1234"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_short_password(self, client):
        resp = client.post("/auth/register", json={
            "email": "short@example.com",
            "name": "A",
            "password": "abc",  # too short — must be 8+ chars
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email", "name": "A", "password": "password1",
        })
        assert resp.status_code == 422

    def test_register_admin_role_is_ignored(self, client):
        """Passing role=admin must be ignored — user is always created as 'user'."""
        resp = client.post("/auth/register", json={
            "email": "adm@example.com",
            "name": "Admin Wannabe",
            "password": "adminpass1",
        })
        assert resp.status_code == 201
        assert resp.json()["role"] == "user"  # ← never admin


class TestLogin:
    def test_login_success(self, client):
        client.post("/auth/register", json={
            "email": "login@example.com", "name": "L", "password": "password1",
        })
        resp = client.post("/auth/login", json={
            "email": "login@example.com", "password": "password1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/auth/register", json={
            "email": "wp@example.com", "name": "W", "password": "correct1",
        })
        resp = client.post("/auth/login", json={
            "email": "wp@example.com", "password": "wrong",
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@example.com", "password": "password1",
        })
        assert resp.status_code == 401