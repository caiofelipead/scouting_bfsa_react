"""Tests for authentication: login, token validation, user roles."""

import pytest
from auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
    create_user,
    authenticate_user,
    init_db,
)


# ── Unit tests (no HTTP) ─────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_and_verify(self):
        plain = "MySecure123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("Correct123")
        assert not verify_password("Wrong456", hashed)


class TestJWT:
    def test_create_and_decode(self):
        payload = {"sub": "user@test.com", "role": "admin", "name": "Test"}
        token = create_access_token(payload)
        decoded = decode_token(token)
        assert decoded["sub"] == "user@test.com"
        assert decoded["role"] == "admin"
        assert "exp" in decoded

    def test_invalid_token_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")
        assert exc_info.value.status_code == 401


class TestUserCRUD:
    def test_create_user_validates_identifier(self, auth_db):
        init_db()
        # Spaces are invalid for both username and email patterns.
        err = create_user("not an email", "ValidPass1", "Test")
        assert err is not None
        assert "inv" in err.lower()

    def test_create_user_validates_password_length(self, auth_db):
        init_db()
        err = create_user("user@test.com", "Short1", "Test")
        assert err is not None
        assert "8 caracteres" in err

    def test_create_user_validates_password_uppercase(self, auth_db):
        init_db()
        err = create_user("user@test.com", "nouppercase1", "Test")
        assert err is not None
        assert "maiúscula" in err

    def test_create_user_validates_password_digit(self, auth_db):
        init_db()
        err = create_user("user@test.com", "NoDigitsHere", "Test")
        assert err is not None
        assert "número" in err

    def test_create_user_success(self, auth_db):
        init_db()
        err = create_user("newuser@test.com", "ValidPass1", "New User")
        assert err is None

    def test_create_user_duplicate(self, auth_db):
        init_db()
        create_user("dup@test.com", "ValidPass1", "User")
        err = create_user("dup@test.com", "ValidPass1", "User")
        assert err is not None
        assert "cadastrado" in err

    def test_authenticate_user_success(self, auth_db):
        init_db()
        create_user("auth@test.com", "AuthPass1", "Auth User")
        user = authenticate_user("auth@test.com", "AuthPass1")
        assert user is not None
        assert user["email"] == "auth@test.com"

    def test_authenticate_user_wrong_password(self, auth_db):
        init_db()
        create_user("auth2@test.com", "AuthPass1", "Auth User 2")
        user = authenticate_user("auth2@test.com", "WrongPass1")
        assert user is None

    def test_authenticate_user_nonexistent(self, auth_db):
        init_db()
        user = authenticate_user("nobody@test.com", "SomePass1")
        assert user is None

    def test_create_user_invalid_role(self, auth_db):
        init_db()
        err = create_user("role@test.com", "ValidPass1", "Test", role="superadmin")
        assert err is not None
        assert "inválido" in err.lower()


# ── Integration tests (HTTP) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client, auth_db):
    """POST /api/auth/login with valid admin credentials."""
    init_db()
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "TestPass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client, auth_db):
    """POST /api/auth/login with wrong password → 401."""
    init_db()
    resp = await client.post("/api/auth/login", json={
        "email": "admin@test.com",
        "password": "WrongPass999",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client, admin_token):
    """GET /api/auth/me with valid token returns user info."""
    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_without_token(client):
    """GET /api/auth/me without token → 401/403."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """GET /api/health should always respond."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "data_loaded" in data
