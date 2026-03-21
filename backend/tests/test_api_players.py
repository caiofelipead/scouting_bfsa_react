"""Tests for player-related API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_players_requires_auth(client):
    """GET /api/players without token → 401/403."""
    resp = await client.get("/api/players")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_players_with_auth(client, analyst_token):
    """GET /api/players with valid token returns player list or 503 (data loading)."""
    resp = await client.get(
        "/api/players",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    # 200 if data loaded, 503 if still loading — both are acceptable
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert "total" in data
        assert "players" in data
        assert isinstance(data["players"], list)


@pytest.mark.asyncio
async def test_players_pagination(client, analyst_token):
    """GET /api/players supports limit and offset."""
    headers = {"Authorization": f"Bearer {analyst_token}"}
    resp = await client.get("/api/players?limit=5&offset=0", headers=headers)
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert len(data["players"]) <= 5


@pytest.mark.asyncio
async def test_players_search_filter(client, analyst_token):
    """GET /api/players?search=xyz applies name filter."""
    headers = {"Authorization": f"Bearer {analyst_token}"}
    resp = await client.get("/api/players?search=NonExistentPlayerXYZ", headers=headers)
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_player_profile_not_found(client, analyst_token):
    """GET /api/players/<name>/profile with bad name → 404 or 503."""
    headers = {"Authorization": f"Bearer {analyst_token}"}
    resp = await client.get("/api/players/NonExistentPlayer999/profile", headers=headers)
    assert resp.status_code in (404, 503)


@pytest.mark.asyncio
async def test_config_positions(client, analyst_token):
    """GET /api/config/positions returns position mappings."""
    headers = {"Authorization": f"Bearer {analyst_token}"}
    resp = await client.get("/api/config/positions", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "positions" in data
    assert "position_map" in data
    assert "indices" in data


@pytest.mark.asyncio
async def test_config_mappings(client, analyst_token):
    """GET /api/config/mappings returns static mappings."""
    headers = {"Authorization": f"Bearer {analyst_token}"}
    resp = await client.get("/api/config/mappings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "country_flags" in data
    assert "club_logos" in data
