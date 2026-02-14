"""
Testes unitários para config_schema.py
"""

import pytest
import json
import tempfile
from pathlib import Path

from core.config_schema import ConfigSchema, VALID_LANGUAGES, VALID_MODELS


class TestConfigSchema:
    """Testes para validação de configuração."""

    def test_default_values(self):
        """Testa se valores padrão são aplicados corretamente."""
        config = ConfigSchema()
        assert config.source_lang == "pt"
        assert config.target_lang == "en"
        assert config.opacity == 0.69
        assert config.model_type == "google"
        assert config.font_size == 14

    def test_opacity_validation(self):
        """Testa validação de range de opacidade."""
        # Valor válido
        config = ConfigSchema(opacity=0.5)
        assert config.opacity == 0.5

        # Valor mínimo
        config = ConfigSchema(opacity=0.0)
        assert config.opacity == 0.0

        # Valor máximo
        config = ConfigSchema(opacity=1.0)
        assert config.opacity == 1.0

        # Valor inválido (deve lançar exceção)
        with pytest.raises(ValueError):
            ConfigSchema(opacity=1.5)

        with pytest.raises(ValueError):
            ConfigSchema(opacity=-0.1)

    def test_font_size_validation(self):
        """Testa validação de tamanho de fonte."""
        config = ConfigSchema(font_size=24)
        assert config.font_size == 24

        with pytest.raises(ValueError):
            ConfigSchema(font_size=5)  # Muito pequeno

        with pytest.raises(ValueError):
            ConfigSchema(font_size=100)  # Muito grande

    def test_model_type_validation(self):
        """Testa validação de tipos de modelo."""
        for model in VALID_MODELS:
            config = ConfigSchema(model_type=model)
            assert config.model_type == model

        # Tipo inválido
        with pytest.raises(ValueError):
            ConfigSchema(model_type="invalid_model")

    def test_language_normalization(self):
        """Testa normalização de códigos de idioma."""
        # Vários formatos devem normalizar para "en"
        config = ConfigSchema(target_lang="English")
        assert config.target_lang == "en"

        config = ConfigSchema(target_lang="INGLÊS")
        assert config.target_lang == "en"

        config = ConfigSchema(target_lang="EN")
        assert config.target_lang == "en"

    def test_color_validation(self):
        """Testa validação de cores."""
        # Cores nomeadas válidas
        config = ConfigSchema(text_color="white")
        assert config.text_color == "white"

        config = ConfigSchema(trans_color="#39FF14")
        assert config.trans_color == "#39FF14"

        # Cor inválida
        with pytest.raises(ValueError):
            ConfigSchema(text_color="not_a_color")

    def test_save_and_load(self):
        """Testa salvamento e carregamento de arquivo."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Cria e salva config
            config = ConfigSchema(opacity=0.8, font_size=20, target_lang="es")
            config.save_to_file(temp_path)

            # Verifica se arquivo foi criado
            assert temp_path.exists()

            # Carrega e verifica
            loaded = ConfigSchema.load_from_file(temp_path)
            assert loaded.opacity == 0.8
            assert loaded.font_size == 20
            assert loaded.target_lang == "es"
        finally:
            # Limpa
            if temp_path.exists():
                temp_path.unlink()

    def test_load_invalid_json(self):
        """Testa carregamento de JSON inválido."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_path = Path(f.name)

        try:
            # Deve retornar config padrão e criar backup
            config = ConfigSchema.load_from_file(temp_path)
            assert config.opacity == 0.69  # Valor padrão
            assert (temp_path.parent / f"{temp_path.stem}.json.backup").exists()
        finally:
            # Limpa
            for f in [temp_path, temp_path.parent / f"{temp_path.stem}.json.backup"]:
                if f.exists():
                    f.unlink()

    def test_window_dimensions_validation(self):
        """Testa validação de dimensões da janela."""
        # Valores válidos
        config = ConfigSchema(win_width=800, win_height=400)
        assert config.win_width == 800
        assert config.win_height == 400

        # Valores inválidos
        with pytest.raises(ValueError):
            ConfigSchema(win_width=200)  # Muito pequeno

        with pytest.raises(ValueError):
            ConfigSchema(win_height=50)  # Muito pequeno


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
