"""
Classe base abstrata para engines de reconhecimento de áudio.
Reduz duplicação de código entre GoogleEngine, WhisperEngine, etc.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional
import numpy as np


class BaseAudioEngine(ABC):
    """
    Classe base para todos os engines de reconhecimento de áudio.
    Implementa lógica comum de buffering e detecção de silêncio.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.buffer = bytearray()
        self.silence_frames = 0
        self.thinking = False

        # Configuráveis por subclasses
        self.silence_threshold_frames = 15  # ~450ms padrão
        self.max_buffer_seconds = 6  # Segurança

    @abstractmethod
    def recognize(self, audio_data_bytes: bytes) -> str:
        """
        Método abstrato: deve ser implementado por subclasses.
        Processa os bytes de áudio e retorna o texto reconhecido.
        """
        pass

    def process_audio(
        self, audio_bytes: bytes, is_speech: bool
    ) -> Tuple[Optional[str], Optional[bytes]]:
        """
        Processa um chunk de áudio e decide quando acionar o reconhecimento.

        Args:
            audio_bytes: Chunk de áudio em bytes
            is_speech: Estado atual do VAD

        Returns:
            Tupla (status, data):
            - status: String vazia se processando, ou None
            - data: Bytes do áudio para reconhecimento, ou None
        """
        if audio_bytes:
            self.buffer.extend(audio_bytes)

            # Proteção contra buffer muito grande
            max_bytes = self.sample_rate * 2 * self.max_buffer_seconds
            if len(self.buffer) > max_bytes:
                # Mantém apenas os últimos 2 segundos
                self.buffer = self.buffer[-(self.sample_rate * 2 * 2) :]

        if not is_speech:
            self.silence_frames += 1
        else:
            self.silence_frames = 0

        # Trigger: silêncio suficiente OU buffer muito cheio
        silence_trigger = (
            self.silence_frames >= self.silence_threshold_frames
            and len(self.buffer) > 0
        )
        safety_trigger = (
            len(self.buffer) > self.sample_rate * 2 * self.max_buffer_seconds
        )

        if silence_trigger or safety_trigger:
            data = bytes(self.buffer)
            duration_s = len(data) / (self.sample_rate * 2)

            # Reset
            self.buffer.clear()
            self.silence_frames = 0

            # Filtro de duração mínima (evita ruídos/clicks)
            if duration_s < 0.4:  # 400ms mínimo
                return None, None

            return ("", data)  # Status vazio = processando

        return None, None

    def normalize_audio(
        self, audio_np: np.ndarray, target_peak: float = 30000.0
    ) -> np.ndarray:
        """
        Normaliza o áudio para melhor reconhecimento.

        Args:
            audio_np: Array numpy com áudio
            target_peak: Valor de pico desejado (0-32767 para int16)

        Returns:
            Array numpy normalizado
        """
        max_val = np.max(np.abs(audio_np))
        if max_val > 0:
            return (audio_np / max_val) * target_peak
        return audio_np

    def apply_noise_reduction(self, audio_np: np.ndarray) -> np.ndarray:
        """
        Aplica redução de ruído se disponível.

        Args:
            audio_np: Array numpy com áudio

        Returns:
            Array com ruído reduzido ou original se biblioteca não disponível
        """
        try:
            import noisereduce as nr

            return nr.reduce_noise(y=audio_np, sr=self.sample_rate, prop_decrease=0.8)
        except ImportError:
            # noisereduce não instalado, retorna original
            return audio_np

    def bytes_to_numpy(
        self, audio_bytes: bytes, dtype: np.dtype = np.int16
    ) -> np.ndarray:
        """Converte bytes de áudio para array numpy."""
        return np.frombuffer(audio_bytes, dtype=dtype).astype(np.float32)

    def reset(self):
        """Reseta o estado do engine."""
        self.buffer.clear()
        self.silence_frames = 0
        self.thinking = False
