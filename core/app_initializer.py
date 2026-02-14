"""
Inicializador da aplicação - separa lógica de inicialização da UI.
Implementa padrão de inicialização em fases.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from core.logging_config import setup_logging, get_logger
from core.config_schema import ConfigSchema
from core.audio import AudioCapture
from core.transcriber import Transcriber
from core.translator import Translator
from download_models import is_model_installed

logger = get_logger("AppInitializer")


@dataclass
class AppComponents:
    """Container para todos os componentes inicializados."""

    config: ConfigSchema
    audio: AudioCapture
    transcriber: Transcriber
    translator: Optional[Translator]
    has_translator: bool


class AppInitializer:
    """
    Gerencia a inicialização da aplicação em fases bem definidas.
    Separa a lógica complexa de inicialização do main.py.
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.config: Optional[ConfigSchema] = None
        self.components: Optional[AppComponents] = None
        self._has_translator_plugin = True

    def initialize(self) -> AppComponents:
        """
        Inicializa todos os componentes da aplicação.

        Returns:
            AppComponents com todos os componentes prontos

        Raises:
            RuntimeError: Se inicialização crítica falhar
        """
        logger.info(f"=== Iniciando OmniTranslator v{self.VERSION} ===")

        # Fase 1: Configuração
        self.config = self._init_config()
        logger.info(f"Configuração carregada: {self.config.model_dump_json()}")

        # Fase 2: Logging avançado
        setup_logging(
            log_file=Path("logs/omnitranslator.log"),
            level=10,  # DEBUG
        )

        # Fase 3: Verificar modelo
        model_path = self._resolve_model_path()

        # Fase 4: Inicializar componentes
        audio = self._init_audio()
        transcriber = self._init_transcriber(model_path)
        translator = self._init_translator()

        self.components = AppComponents(
            config=self.config,
            audio=audio,
            transcriber=transcriber,
            translator=translator,
            has_translator=self._has_translator_plugin,
        )

        logger.info("✓ Inicialização concluída com sucesso")
        return self.components

    def _init_config(self) -> ConfigSchema:
        """Carrega ou cria configuração padrão."""
        try:
            return ConfigSchema.load_from_file()
        except Exception as e:
            logger.warning(f"Erro ao carregar config: {e}. Criando padrão.")
            config = ConfigSchema()
            config.save_to_file()
            return config

    def _resolve_model_path(self) -> str:
        """Resolve o caminho do modelo com fallback."""
        model_type = self.config.model_type
        actual_path = is_model_installed(model_type)

        if not actual_path:
            logger.warning(f"Modelo {model_type} não encontrado. Tentando fallback...")
            # Fallback para small se big foi solicitado
            if model_type == "big":
                actual_path = is_model_installed("small")
                if actual_path:
                    logger.info("Usando modelo small como fallback")

            # Se ainda não encontrou, tenta google
            if not actual_path and model_type != "google":
                actual_path = is_model_installed("google")
                if actual_path:
                    logger.info("Usando Google como fallback")
                    self.config.model_type = "google"

        if not actual_path:
            logger.error("Nenhum modelo válido encontrado!")
            actual_path = "missing"

        return actual_path

    def _init_audio(self) -> AudioCapture:
        """Inicializa captura de áudio."""
        try:
            device_idx = self.config.audio_device_index
            vad_th = self.config.vad_threshold

            audio = AudioCapture(device_index=device_idx, energy_threshold=vad_th)
            logger.info(
                f"✓ Áudio inicializado (device={device_idx}, threshold={vad_th})"
            )
            return audio

        except Exception as e:
            logger.error(f"Falha ao inicializar áudio: {e}")
            # Retorna instância padrão como fallback
            return AudioCapture()

    def _init_transcriber(self, model_path: str) -> Transcriber:
        """Inicializa o transcritor com o modelo especificado."""
        try:
            transcriber = Transcriber(model_path)
            logger.info(f"✓ Transcritor inicializado: {model_path}")
            return transcriber
        except Exception as e:
            logger.error(f"Falha ao inicializar transcritor: {e}")
            # Retorna instância placeholder
            return Transcriber("missing")

    def _init_translator(self) -> Optional[Translator]:
        """Inicializa o tradutor se disponível."""
        try:
            translator = Translator(
                from_code=self.config.source_lang, to_code=self.config.target_lang
            )
            logger.info(
                f"✓ Tradutor inicializado: {self.config.source_lang} -> {self.config.target_lang}"
            )
            return translator
        except Exception as e:
            logger.warning(f"Tradutor não disponível: {e}")
            self._has_translator_plugin = False
            return None

    def get_version(self) -> str:
        """Retorna a versão da aplicação."""
        return self.VERSION
