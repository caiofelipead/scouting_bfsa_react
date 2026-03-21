"""Tests for similarity service functions."""

import pytest
import pandas as pd
import numpy as np


class TestSafeFloat:
    """Test the _safe_float helper from main.py."""

    def test_normal_float(self):
        from main import _safe_float
        assert _safe_float(3.14) == 3.14

    def test_integer(self):
        from main import _safe_float
        assert _safe_float(42) == 42.0

    def test_string_number(self):
        from main import _safe_float
        assert _safe_float("3.14") == 3.14

    def test_string_comma_decimal(self):
        from main import _safe_float
        assert _safe_float("3,14") == 3.14

    def test_none(self):
        from main import _safe_float
        assert _safe_float(None) is None

    def test_nan(self):
        from main import _safe_float
        assert _safe_float(float("nan")) is None

    def test_invalid_string(self):
        from main import _safe_float
        assert _safe_float("not a number") is None


class TestResolveActualLeague:
    """Test league resolution logic."""

    def test_known_club(self):
        from main import resolve_actual_league
        from config.mappings import CLUB_LEAGUE_MAP
        # Pick any mapped club
        if CLUB_LEAGUE_MAP:
            club = next(iter(CLUB_LEAGUE_MAP))
            result = resolve_actual_league(club)
            assert result == CLUB_LEAGUE_MAP[club]

    def test_fallback_to_liga_tier(self):
        from main import resolve_actual_league
        result = resolve_actual_league("UnknownClubXYZ999", fallback_liga_tier="Brasil | 2")
        assert result == "Brasil | 2"

    def test_none_team(self):
        from main import resolve_actual_league
        result = resolve_actual_league(None)
        assert result is None

    def test_nan_team(self):
        from main import resolve_actual_league
        result = resolve_actual_league(float("nan"))
        assert result is None


class TestSimilarityService:
    """Test similarity computation functions."""

    def test_position_weights_exist(self):
        from services.similarity import POSITION_WEIGHTS
        assert isinstance(POSITION_WEIGHTS, dict)
        assert len(POSITION_WEIGHTS) > 0

    def test_inverted_metrics_exist(self):
        from services.similarity import INVERTED_METRICS
        assert isinstance(INVERTED_METRICS, (set, frozenset))

    def test_calculate_overall_score_returns_number(self):
        from services.similarity import calculate_overall_score, POSITION_WEIGHTS
        # Create a minimal DataFrame with some metrics
        positions = list(POSITION_WEIGHTS.keys())
        if not positions:
            pytest.skip("No position weights configured")

        pos = positions[0]
        weights = POSITION_WEIGHTS[pos]
        metrics = list(weights.keys())[:5]

        # Build a simple row and df
        data = {m: [np.random.uniform(0, 100) for _ in range(10)] for m in metrics}
        data["Posição"] = [pos] * 10
        df = pd.DataFrame(data)
        row = df.iloc[0]

        score = calculate_overall_score(row, pos, df)
        # Score can be None if insufficient data, but should not raise
        if score is not None:
            assert isinstance(score, (int, float))
            assert 0 <= score <= 100


@pytest.mark.asyncio
async def test_rankings_requires_auth(client):
    """POST /api/rankings without token → 403."""
    resp = await client.post("/api/rankings", json={
        "position": "Meia",
        "top_n": 10,
    })
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_similarity_requires_auth(client):
    """POST /api/similarity without token → 403."""
    resp = await client.post("/api/similarity", json={
        "player_display_name": "Test Player",
        "position": "Meia",
    })
    assert resp.status_code in (401, 403)
