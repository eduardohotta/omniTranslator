"""
Testes unitários para base_engine.py
"""

import pytest
import numpy as np
from unittest.mock import Mock

from core.base_engine import BaseAudioEngine


class MockAudioEngine(BaseAudioEngine):
    """Engine mock para testes."""

    def recognize(self, audio_data_bytes: bytes) -> str:
        return "recognized text"


class TestBaseAudioEngine:
    """Testes para a classe base de engines."""

    def test_initialization(self):
        """Testa inicialização padrão."""
        engine = MockAudioEngine()

        assert engine.sample_rate == 16000
        assert len(engine.buffer) == 0
        assert engine.silence_frames == 0
        assert engine.silence_threshold_frames == 15

    def test_process_audio_accumulation(self):
        """Testa acumulação de áudio no buffer."""
        engine = MockAudioEngine()

        # Simula chunks de áudio
        audio_chunk = b"\x00\x01" * 100

        # Processa com is_speech=True (não deve acionar ainda)
        result = engine.process_audio(audio_chunk, is_speech=True)
        assert result == (None, None)
        assert len(engine.buffer) > 0

    def test_process_audio_trigger_on_silence(self):
        """Testa trigger quando há silêncio suficiente."""
        engine = MockAudioEngine()
        engine.silence_threshold_frames = 2  # Reduzido para teste

        # Adiciona áudio suficiente (mais que 400ms = 12800 bytes em 16kHz)
        # sample_rate * 2 bytes * 0.5s = 16000 bytes
        audio_chunk = b"\x00\x01" * 10000

        # Processa com fala
        engine.process_audio(audio_chunk, is_speech=True)

        # Agora processa com silêncio até atingir threshold
        result = None
        for _ in range(3):
            result = engine.process_audio(b"", is_speech=False)
            if result[0] is not None:  # Se acionou, paramos
                break

        # Deve ter acionado (retornado dados)
        assert result[0] == ""  # Status vazio indica processamento
        assert result[1] is not None  # Dados presentes

    def test_buffer_size_limit(self):
        """Testa limite de tamanho do buffer."""
        engine = MockAudioEngine()
        engine.max_buffer_seconds = 1  # 1 segundo para teste rápido

        # Adiciona muito áudio
        large_chunk = b"\x00" * (engine.sample_rate * 2 * 10)  # 10 segundos

        engine.process_audio(large_chunk, is_speech=True)

        # Buffer deve ter sido limitado
        max_bytes = engine.sample_rate * 2 * engine.max_buffer_seconds
        assert len(engine.buffer) <= max_bytes * 1.1  # 10% tolerância

    def test_duration_filter(self):
        """Testa filtro de duração mínima."""
        engine = MockAudioEngine()
        engine.silence_threshold_frames = 1

        # Adiciona áudio muito curto (menos de 400ms)
        short_chunk = b"\x00\x01" * 100  # Muito curto

        engine.process_audio(short_chunk, is_speech=True)
        result = engine.process_audio(b"", is_speech=False)

        # Deve retornar None, None por ser muito curto
        assert result == (None, None)

    def test_normalize_audio(self):
        """Testa normalização de áudio."""
        engine = MockAudioEngine()

        # Cria áudio com amplitude baixa
        audio = np.array([100, 200, 300], dtype=np.float32)

        normalized = engine.normalize_audio(audio, target_peak=1000.0)

        # Valor máximo deve ser próximo do target_peak
        max_val = np.max(np.abs(normalized))
        assert max_val == pytest.approx(1000.0, rel=0.01)

    def test_normalize_audio_empty(self):
        """Testa normalização de áudio silencioso."""
        engine = MockAudioEngine()

        audio = np.array([0, 0, 0], dtype=np.float32)

        # Não deve lançar exceção
        normalized = engine.normalize_audio(audio)

        assert np.array_equal(normalized, audio)

    def test_bytes_to_numpy(self):
        """Testa conversão de bytes para numpy."""
        engine = MockAudioEngine()

        # Cria bytes de int16
        original = np.array([100, -100, 1000, -1000], dtype=np.int16)
        audio_bytes = original.tobytes()

        # Converte de volta
        result = engine.bytes_to_numpy(audio_bytes, dtype=np.int16)

        assert result.dtype == np.float32
        assert len(result) == 4

    def test_reset(self):
        """Testa reset do engine."""
        engine = MockAudioEngine()

        # Preenche com dados
        engine.buffer.extend(b"test data")
        engine.silence_frames = 10
        engine.thinking = True

        # Reseta
        engine.reset()

        assert len(engine.buffer) == 0
        assert engine.silence_frames == 0
        assert engine.thinking == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
