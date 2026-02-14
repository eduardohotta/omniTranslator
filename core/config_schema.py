"""
Schema de configuração com validação usando Pydantic.
Garante que todas as configurações estejam dentro dos ranges válidos.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from pathlib import Path


class ConfigSchema(BaseModel):
    """Schema validado para configurações do OmniTranslator."""

    # Idiomas
    source_lang: str = Field(default="pt", min_length=2, max_length=5)
    target_lang: str = Field(default="en", min_length=2, max_length=5)

    # Fonte
    font_size: int = Field(default=14, ge=8, le=72)
    font_color: str = Field(default="white", pattern=r"^[a-zA-Z]+$|^#[0-9A-Fa-f]{6}$")

    # Visual
    opacity: float = Field(default=0.69, ge=0.0, le=1.0)
    always_on_top: bool = Field(default=True)

    # Posição da janela
    x_pos: Optional[int] = Field(default=None, ge=0, le=3840)
    y_pos: int = Field(default=50, ge=0, le=2160)

    # Dimensões da janela
    win_width: int = Field(default=1000, ge=400, le=1920)
    win_height: int = Field(default=240, ge=100, le=600)

    # Áudio
    audio_device_index: Optional[int] = Field(default=None, ge=-1)
    vad_threshold: int = Field(default=300, ge=100, le=5000)

    # Modelo
    model_type: Literal["small", "big", "google", "whisper"] = Field(default="google")

    # Cores
    text_color: str = Field(default="white", pattern=r"^[a-zA-Z]+$|^#[0-9A-Fa-f]{6}$")
    trans_color: str = Field(
        default="#39FF14", pattern=r"^[a-zA-Z]+$|^#[0-9A-Fa-f]{6}$"
    )
    orig_color: Optional[str] = Field(
        default=None, pattern=r"^[a-zA-Z]+$|^#[0-9A-Fa-f]{6}$"
    )

    # Tamanhos de fonte
    trans_font_size: int = Field(default=19, ge=14, le=72)
    orig_font_size: Optional[int] = Field(default=None, ge=8, le=72)

    # Alinhamento
    text_align: Literal["top", "center", "bottom"] = Field(default="center")

    @field_validator(
        "font_color", "text_color", "trans_color", "orig_color", mode="before"
    )
    @classmethod
    def validate_color_format(cls, v):
        """Valida que a cor está em formato válido."""
        if v is None:
            return v
        if isinstance(v, str):
            # Cores nomeadas válidas
            valid_colors = {
                "white",
                "black",
                "red",
                "green",
                "blue",
                "yellow",
                "orange",
                "cyan",
                "magenta",
                "gray",
                "grey",
            }
            if v.lower() in valid_colors or v.startswith("#"):
                return v
        raise ValueError(f"Cor inválida: {v}. Use nome da cor ou hexadecimal (#RRGGBB)")

    @field_validator("target_lang", mode="before")
    @classmethod
    def validate_target_lang(cls, v):
        """Normaliza código do idioma alvo."""
        lang_map = {
            "en": "en",
            "english": "en",
            "inglês": "en",
            "es": "es",
            "spanish": "es",
            "espanhol": "es",
            "fr": "fr",
            "french": "fr",
            "francês": "fr",
            "de": "de",
            "german": "de",
            "alemão": "de",
            "it": "it",
            "italian": "it",
            "italiano": "it",
            "ja": "ja",
            "japanese": "ja",
            "japonês": "ja",
            "zh": "zh",
            "zh-cn": "zh-CN",
            "chinese": "zh-CN",
            "chinês": "zh-CN",
            "pt": "pt",
            "portuguese": "pt",
            "português": "pt",
        }
        return lang_map.get(str(v).lower(), v)

    def save_to_file(self, path: Path = Path("config.json")) -> None:
        """Salva configuração em arquivo JSON."""
        import json

        path.write_text(
            json.dumps(self.model_dump(), indent=2, default=str), encoding="utf-8"
        )

    @classmethod
    def load_from_file(cls, path: Path = Path("config.json")) -> "ConfigSchema":
        """Carrega configuração de arquivo JSON com valores padrão como fallback."""
        import json

        if not path.exists():
            config = cls()
            config.save_to_file(path)
            return config

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**data)
        except (json.JSONDecodeError, Exception) as e:
            # Se houver erro, cria backup e retorna config padrão
            backup_path = path.with_suffix(".json.backup")
            path.rename(backup_path)
            config = cls()
            config.save_to_file(path)
            return config


# Constantes de validação
VALID_LANGUAGES = ["en", "es", "fr", "de", "it", "ja", "zh-CN", "pt"]
VALID_MODELS = ["small", "big", "google", "whisper"]
VALID_ALIGNMENTS = ["top", "center", "bottom"]
