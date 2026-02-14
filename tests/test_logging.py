"""
Testes unitários para logging_config.py
"""

import pytest
import logging
import tempfile
from pathlib import Path

from core.logging_config import setup_logging, get_logger, ColoredFormatter


class TestLoggingConfig:
    """Testes para configuração de logging."""

    def setup_method(self):
        """Limpa handlers antes de cada teste."""
        logger = logging.getLogger("OmniTranslator")
        # Remove todos os handlers existentes
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    def test_setup_logging_console_only(self):
        """Testa setup sem arquivo (apenas console)."""
        logger = setup_logging(log_file=None, level=logging.DEBUG)

        assert logger.name == "OmniTranslator"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) >= 1  # Pelo menos console
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_setup_logging_with_file(self):
        """Testa setup com arquivo de log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            logger = setup_logging(log_file=log_file, level=logging.INFO)

            # Deve ter pelo menos console + arquivo
            assert len(logger.handlers) >= 1

            # Testa se arquivo foi criado
            logger.info("Test message")

            # Força flush e fecha handlers para liberar arquivo (Windows)
            for handler in logger.handlers:
                handler.flush()
                handler.close()
            logger.handlers.clear()

            # Verifica se arquivo existe e contém mensagem
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content

    def test_get_logger(self):
        """Testa obtenção de logger filho."""
        child_logger = get_logger("TestModule")

        assert child_logger.name == "OmniTranslator.TestModule"
        assert child_logger.parent is not None

    def test_colored_formatter(self):
        """Testa formatter com cores."""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")

        # Cria registro de log
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # Deve conter código de cor ANSI
        assert "\033[" in formatted
        assert "INFO" in formatted

    def test_log_levels(self):
        """Testa diferentes níveis de log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_levels.log"

            logger = setup_logging(log_file=log_file, level=logging.DEBUG)

            # Log em todos os níveis
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            # Força flush e fecha handlers para liberar arquivo (Windows)
            for handler in logger.handlers:
                handler.flush()
                handler.close()
            logger.handlers.clear()

            # Verifica conteúdo
            content = log_file.read_text()
            assert "DEBUG" in content
            assert "INFO" in content
            assert "WARNING" in content
            assert "ERROR" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
