"""
Suite de testes principal para o OmniTranslator.
Execute com: pytest tests/ -v
"""

import pytest
import sys
from pathlib import Path

# Adiciona diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """Executa todos os testes."""
    exit_code = pytest.main(
        [
            str(Path(__file__).parent),
            "-v",
            "--tb=short",
            "-x",  # Para no primeiro erro
        ]
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(run_all_tests())
