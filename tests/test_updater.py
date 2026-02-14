"""
Testes unitários para updater.py (validação de segurança)
"""

import pytest
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from core.updater import AppUpdater, SecurityError


class TestAppUpdater:
    """Testes para o sistema de atualização."""

    def test_version_comparison(self):
        """Testa comparação de versões."""
        updater = AppUpdater("1.0.0")

        # Versões mais novas
        assert updater._is_newer("1.1.0", "1.0.0") == True
        assert updater._is_newer("2.0.0", "1.0.0") == True
        assert updater._is_newer("1.0.1", "1.0.0") == True

        # Versões iguais ou mais antigas
        assert updater._is_newer("1.0.0", "1.0.0") == False
        assert updater._is_newer("0.9.0", "1.0.0") == False
        assert updater._is_newer("1.0.0", "1.1.0") == False

    def test_calculate_sha256(self):
        """Testa cálculo de hash SHA256."""
        updater = AppUpdater("1.0.0")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Hello World")
            temp_path = f.name

        try:
            hash_result = updater._calculate_sha256(temp_path)

            # Verifica se é hash SHA256 válido (64 caracteres hex)
            assert len(hash_result) == 64
            assert all(c in "0123456789abcdef" for c in hash_result.lower())

            # Verifica valor esperado
            expected = hashlib.sha256(b"Hello World").hexdigest()
            assert hash_result.lower() == expected.lower()
        finally:
            Path(temp_path).unlink()

    def test_verify_checksum_valid(self):
        """Testa verificação de checksum válido."""
        updater = AppUpdater("1.0.0")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            expected_hash = hashlib.sha256(b"Test content").hexdigest()

            # Deve retornar True para checksum válido
            assert updater._verify_checksum(temp_path, expected_hash) == True

            # Deve retornar False para checksum inválido
            assert updater._verify_checksum(temp_path, "invalid_hash") == False
        finally:
            Path(temp_path).unlink()

    def test_verify_checksum_missing(self):
        """Testa verificação quando checksum não está disponível."""
        updater = AppUpdater("1.0.0")

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test")
            temp_path = f.name

        try:
            # Sem checksum deve retornar False
            assert updater._verify_checksum(temp_path, None) == False
            assert updater._verify_checksum(temp_path, "") == False
        finally:
            Path(temp_path).unlink()

    @patch("core.updater.requests.get")
    def test_check_for_updates(self, mock_get):
        """Testa verificação de atualizações."""
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v1.1.0",
            "assets": [
                {
                    "name": "OmniTranslator.exe",
                    "browser_download_url": "http://example.com/exe",
                },
                {
                    "name": "OmniTranslator.exe.sha256",
                    "browser_download_url": "http://example.com/checksum",
                },
            ],
        }
        mock_get.return_value = mock_response

        updater = AppUpdater("1.0.0")
        has_update, version, url, checksum_url = updater.check_for_updates()

        assert has_update == True
        assert version == "1.1.0"
        assert url == "http://example.com/exe"
        assert checksum_url == "http://example.com/checksum"

    @patch("core.updater.requests.get")
    def test_check_for_updates_no_update(self, mock_get):
        """Testa quando não há atualização disponível."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tag_name": "v1.0.0", "assets": []}
        mock_get.return_value = mock_response

        updater = AppUpdater("1.0.0")
        has_update, version, url, checksum_url = updater.check_for_updates()

        assert has_update == False
        assert version == "1.0.0"
        assert url is None

    @patch("core.updater.requests.get")
    def test_download_checksum(self, mock_get):
        """Testa download de arquivo de checksum."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "abc123def456 OmniTranslator.exe"
        mock_get.return_value = mock_response

        updater = AppUpdater("1.0.0")
        checksum = updater._download_checksum("http://example.com/checksum")

        assert checksum == "abc123def456"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
