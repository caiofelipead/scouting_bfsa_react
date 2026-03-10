"""Testes para data_loader.py"""
import pytest
import pandas as pd
import numpy as np
from data_loader import (
    load_skillcorner_csv,
    safe_numeric_cast,
    validate_url,
    TM_PATTERN,
    OGOL_PATTERN,
)


class TestValidateUrl:
    def test_valid_transfermarkt_url(self):
        url = "https://www.transfermarkt.com.br/jogador/profil/spieler/12345"
        assert validate_url(url, TM_PATTERN) is True

    def test_valid_tm_without_www(self):
        url = "https://transfermarkt.com/jogador/profil/spieler/99999"
        assert validate_url(url, TM_PATTERN) is True

    def test_invalid_tm_url_no_id(self):
        url = "https://www.transfermarkt.com.br/jogador/profil/spieler/"
        assert validate_url(url, TM_PATTERN) is False

    def test_invalid_tm_wrong_domain(self):
        url = "https://evil.com/profil/spieler/12345"
        assert validate_url(url, TM_PATTERN) is False

    def test_valid_ogol_url(self):
        url = "https://www.ogol.com.br/jogador/fulano"
        assert validate_url(url, OGOL_PATTERN) is True

    def test_valid_zerozero_url(self):
        url = "https://www.zerozero.pt/jogador/fulano"
        assert validate_url(url, OGOL_PATTERN) is True

    def test_empty_url(self):
        assert validate_url("", TM_PATTERN) is False
        assert validate_url(None, TM_PATTERN) is False

    def test_non_string_url(self):
        assert validate_url(123, TM_PATTERN) is False


class TestSafeNumericCast:
    def test_already_numeric(self):
        series = pd.Series([1.0, 2.0, 3.0])
        result = safe_numeric_cast(series)
        assert result.dtype in [np.float64, np.int64, float, int]

    def test_string_with_commas(self):
        series = pd.Series(["1,5", "2,3", "3,7"])
        result = safe_numeric_cast(series)
        assert result.iloc[0] == pytest.approx(1.5)
        assert result.iloc[1] == pytest.approx(2.3)

    def test_string_with_invalid(self):
        series = pd.Series(["abc", "2.0", "N/A"])
        result = safe_numeric_cast(series)
        assert pd.isna(result.iloc[0])
        assert result.iloc[1] == pytest.approx(2.0)
        assert pd.isna(result.iloc[2])
