"""Shared fixtures for backend tests."""

import os

# Set env vars BEFORE importing any app modules
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "")  # use SQLite fallback
os.environ.setdefault("ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("ADMIN_PASSWORD", "TestPass123")
os.environ.setdefault("ADMIN_NAME", "Test Admin")

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
def auth_db(tmp_path):
    """Use a temp SQLite DB for auth tests."""
    db_path = str(tmp_path / "test_users.db")
    os.environ["AUTH_DB_PATH"] = db_path
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest_asyncio.fixture
async def client():
    """Async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def admin_token():
    """Create a valid admin JWT token for authenticated requests."""
    from auth import create_access_token
    return create_access_token({"sub": "admin@test.com", "role": "admin", "name": "Test Admin"})


@pytest.fixture
def analyst_token():
    """Create a valid analyst JWT token."""
    from auth import create_access_token
    return create_access_token({"sub": "analyst@test.com", "role": "analyst", "name": "Test Analyst"})
