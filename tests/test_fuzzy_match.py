"""Testes para fuzzy_match.py"""
import pytest
import pandas as pd
from fuzzy_match import (
    _normalize,
    _levenshtein,
    _similarity_ratio,
    SkillCornerIndex,
    build_skillcorner_index,
    find_skillcorner_player,
)


class TestNormalize:
    def test_removes_accents(self):
        assert _normalize("José") == "jose"
        assert _normalize("São Paulo") == "sao paulo"
        assert _normalize("André") == "andre"

    def test_lowercases(self):
        assert _normalize("JOGADOR") == "jogador"

    def test_strips_special_chars(self):
        assert _normalize("O'Brien-Smith") == "obriensmith"

    def test_none_and_nan(self):
        assert _normalize(None) == ""
        assert _normalize(float("nan")) == ""

    def test_empty_string(self):
        assert _normalize("") == ""


class TestLevenshtein:
    def test_same_strings(self):
        assert _levenshtein("abc", "abc") == 0

    def test_empty_strings(self):
        assert _levenshtein("", "") == 0
        assert _levenshtein("abc", "") == 3

    def test_single_edit(self):
        assert _levenshtein("cat", "car") == 1

    def test_completely_different(self):
        assert _levenshtein("abc", "xyz") == 3


class TestSimilarityRatio:
    def test_identical(self):
        assert _similarity_ratio("abc", "abc") == pytest.approx(1.0)

    def test_empty(self):
        # Both empty returns 0.0 since function checks `if not s1 or not s2`
        assert _similarity_ratio("", "") == pytest.approx(0.0)
        assert _similarity_ratio("abc", "") == pytest.approx(0.0)

    def test_partial(self):
        ratio = _similarity_ratio("kitten", "sitting")
        assert 0.0 < ratio < 1.0


class TestSkillCornerIndex:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'player_name': ['Neymar Jr', 'Lionel Messi', 'Cristiano Ronaldo'],
            'short_name': ['Neymar', 'Messi', 'Ronaldo'],
            'team_name': ['Al Hilal', 'Inter Miami', 'Al Nassr'],
        })

    def test_build_and_exact_match(self, sample_df):
        idx = SkillCornerIndex()
        idx.build(sample_df)
        result = idx.query("Neymar Jr")
        assert result is not None
        assert result['player_name'] == 'Neymar Jr'

    def test_short_name_match(self, sample_df):
        idx = SkillCornerIndex()
        idx.build(sample_df)
        result = idx.query("Messi")
        assert result is not None
        assert result['player_name'] == 'Lionel Messi'

    def test_fuzzy_match(self, sample_df):
        idx = SkillCornerIndex()
        idx.build(sample_df)
        result = idx.query("Cristiano Ronaldo", threshold=0.65)
        assert result is not None
        assert result['player_name'] == 'Cristiano Ronaldo'

    def test_no_match_below_threshold(self, sample_df):
        idx = SkillCornerIndex()
        idx.build(sample_df)
        result = idx.query("Xyzabc Unknown", threshold=0.90)
        assert result is None

    def test_team_boost(self, sample_df):
        idx = SkillCornerIndex()
        idx.build(sample_df)
        result = idx.query("Neymar", team="Al Hilal", threshold=0.50)
        assert result is not None
        assert result['team_name'] == 'Al Hilal'


class TestFindSkillCornerPlayer:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'player_name': ['Neymar Jr', 'Lionel Messi'],
            'short_name': ['Neymar', 'Messi'],
            'team_name': ['Al Hilal', 'Inter Miami'],
        })

    def test_finds_player(self, sample_df):
        result = find_skillcorner_player("Neymar Jr", sample_df)
        assert result is not None

    def test_returns_none_for_nan(self, sample_df):
        result = find_skillcorner_player(float("nan"), sample_df)
        assert result is None

    def test_returns_none_for_empty(self, sample_df):
        result = find_skillcorner_player("", sample_df)
        assert result is None
