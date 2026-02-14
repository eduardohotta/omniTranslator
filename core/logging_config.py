"""
Logging estruturado para o OmniTranslator.
Substitui prints por logs com níveis apropriados.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Formatter com cores para terminal."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 3,
) -> logging.Logger:
    """
    Configura logging estruturado para a aplicação.

    Args:
        log_file: Caminho do arquivo de log (None = apenas console)
        level: Nível mínimo de log
        max_bytes: Tamanho máximo do arquivo antes de rotacionar
        backup_count: Número de arquivos de backup

    Returns:
        Logger configurado
    """
    logger = logging.getLogger("OmniTranslator")
    logger.setLevel(level)

    # Evita duplicar handlers
    if logger.handlers:
        return logger

    # Formatos
    file_format = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_format = ColoredFormatter("%(levelname)-8s | %(message)s")

    # Handler de arquivo com rotação
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(file_format)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    # Handler de console com cores
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_format)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger filho do logger principal."""
    return logging.getLogger(f"OmniTranslator.{name}")
