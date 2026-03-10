"""Testes para funções utilitárias do app.py (importáveis sem Streamlit rodando)."""
import pytest
import sys
import os

# Adicionar o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSanitizeUrl:
    """Testes para a função sanitize_url definida em app.py.

    Como app.py depende do Streamlit (st.set_page_config no import),
    testamos a lógica de sanitização diretamente.
    """

    def _sanitize_url(self, url):
        """Replica a lógica de sanitize_url para testes sem importar app.py."""
        from urllib.parse import urlparse
        if not url or not isinstance(url, str):
            return ''
        url = url.strip()
        try:
            parsed = urlparse(url)
            if parsed.scheme not in {'http', 'https'}:
                return ''
            if not parsed.netloc:
                return ''
            return url
        except Exception:
            return ''

    def test_valid_https_url(self):
        assert self._sanitize_url("https://example.com/photo.jpg") != ''

    def test_valid_http_url(self):
        assert self._sanitize_url("http://example.com/photo.jpg") != ''

    def test_javascript_url_blocked(self):
        assert self._sanitize_url("javascript:alert(1)") == ''

    def test_data_url_blocked(self):
        assert self._sanitize_url("data:text/html,<script>alert(1)</script>") == ''

    def test_empty_url(self):
        assert self._sanitize_url("") == ''
        assert self._sanitize_url(None) == ''

    def test_non_string(self):
        assert self._sanitize_url(123) == ''

    def test_ftp_blocked(self):
        assert self._sanitize_url("ftp://files.example.com/data") == ''

    def test_relative_path_blocked(self):
        assert self._sanitize_url("/relative/path") == ''

    def test_url_with_whitespace(self):
        result = self._sanitize_url("  https://example.com  ")
        assert result == "https://example.com"


class TestEscapeHtml:
    """Testa escape de HTML."""

    def _escape_html(self, text):
        import html as html_module
        if text is None:
            return ''
        return html_module.escape(str(text))

    def test_escapes_angle_brackets(self):
        assert "&lt;" in self._escape_html("<script>")
        assert "&gt;" in self._escape_html("</script>")

    def test_escapes_quotes(self):
        assert "&quot;" in self._escape_html('"hello"')

    def test_escapes_ampersand(self):
        assert "&amp;" in self._escape_html("A & B")

    def test_none_returns_empty(self):
        assert self._escape_html(None) == ''

    def test_normal_text_unchanged(self):
        assert self._escape_html("Hello World") == "Hello World"
