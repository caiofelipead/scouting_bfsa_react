"""Testes para similarity.py"""
import pytest
import pandas as pd
import numpy as np
from similarity import (
    _safe_float,
    _percentile_rank,
    _is_inverted,
    calculate_weighted_index,
    calculate_all_indices,
    calculate_overall_score,
    get_top_metrics_for_position,
    calculate_metric_percentiles,
    POSITION_WEIGHTS,
    INVERTED_METRICS,
)


class TestSafeFloat:
    def test_float_input(self):
        assert _safe_float(3.14) == pytest.approx(3.14)

    def test_string_input(self):
        assert _safe_float("3.14") == pytest.approx(3.14)

    def test_comma_decimal(self):
        assert _safe_float("3,14") == pytest.approx(3.14)

    def test_none_input(self):
        assert _safe_float(None) is None

    def test_nan_input(self):
        assert _safe_float(float("nan")) is None

    def test_invalid_string(self):
        assert _safe_float("abc") is None


class TestPercentileRank:
    def test_basic_percentile(self):
        series = pd.Series([10, 20, 30, 40, 50])
        assert _percentile_rank(30, series) == pytest.approx(40.0)

    def test_max_value(self):
        series = pd.Series([10, 20, 30])
        assert _percentile_rank(30, series) == pytest.approx(66.67, abs=0.1)

    def test_min_value(self):
        series = pd.Series([10, 20, 30])
        assert _percentile_rank(10, series) == pytest.approx(0.0)

    def test_empty_series(self):
        series = pd.Series([], dtype=float)
        assert _percentile_rank(10, series) == 50.0


class TestIsInverted:
    def test_known_inverted(self):
        assert _is_inverted("Faltas/90") is True
        assert _is_inverted("Cartões amarelos/90") is True
        assert _is_inverted("Golos sofridos/90") is True

    def test_not_inverted(self):
        assert _is_inverted("Golos/90") is False
        assert _is_inverted("Assistências/90") is False
        assert _is_inverted("Passes certos, %") is False

    def test_inverted_via_set(self):
        for m in INVERTED_METRICS:
            assert _is_inverted(m) is True


class TestPositionWeights:
    def test_all_positions_have_weights(self):
        expected_positions = ['Atacante', 'Extremo', 'Meia', 'Volante', 'Lateral', 'Zagueiro', 'Goleiro']
        for pos in expected_positions:
            assert pos in POSITION_WEIGHTS, f"Missing position: {pos}"
            assert len(POSITION_WEIGHTS[pos]) > 0

    def test_weights_are_positive(self):
        for pos, weights in POSITION_WEIGHTS.items():
            for metric, w in weights.items():
                assert w >= 0, f"Negative weight for {pos}/{metric}: {w}"


class TestCalculateWeightedIndex:
    @pytest.fixture
    def sample_data(self):
        df = pd.DataFrame({
            'Golos/90': [0.5, 0.3, 0.7, 0.2, 0.6],
            'Remates/90': [3.0, 2.0, 4.0, 1.5, 3.5],
        })
        player = df.iloc[2]  # Best scorer
        return player, df

    def test_returns_value_0_to_100(self, sample_data):
        player, df = sample_data
        result = calculate_weighted_index(player, ['Golos/90', 'Remates/90'], df, 'Atacante')
        assert 0 <= result <= 100

    def test_no_metrics_returns_50(self, sample_data):
        player, df = sample_data
        result = calculate_weighted_index(player, ['NonExistent'], df, 'Atacante')
        assert result == 50.0


class TestGetTopMetrics:
    def test_returns_correct_count(self):
        result = get_top_metrics_for_position('Atacante', top_n=5)
        assert len(result) == 5

    def test_sorted_by_weight_desc(self):
        result = get_top_metrics_for_position('Atacante', top_n=10)
        weights = [w for _, w in result]
        assert weights == sorted(weights, reverse=True)

    def test_unknown_position_returns_empty(self):
        result = get_top_metrics_for_position('Unknown', top_n=5)
        assert len(result) == 0
