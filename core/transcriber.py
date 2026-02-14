import os
import json
import vosk
import sys
import speech_recognition as sr

try:
    import whisper

    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False


class Transcriber:
    def __init__(self, engine_type="small", sample_rate=16000):
        """
        engine_type can be: "small", "big", "google", "whisper"
        """
        self.engine_type = engine_type
        self.sample_rate = sample_rate
        self.engine = None

        if engine_type == "google":
            self.engine = GoogleEngine(sample_rate)
        elif engine_type == "whisper":
            self.engine = WhisperEngine(sample_rate)
        else:
            # Vosk path (small/big)
            self.engine = VoskEngine(engine_type, sample_rate)

    def process_audio(self, audio_bytes, is_speech=False):
        """
        is_speech: Current VAD state from main thread.
        """
        return self.engine.process_audio(audio_bytes, is_speech)


class VoskEngine:
    def __init__(self, model_path, sample_rate):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.model = None
        self.recognizer = None
        self._initialize()

    def _initialize(self):
        if not self.model_path or self.model_path == "missing":
            return

        def try_load(path):
            try:
                vosk.SetLogLevel(-1)
                m = vosk.Model(path)
                r = vosk.KaldiRecognizer(m, self.sample_rate)
                return m, r
            except:
                return None, None

        # 1. Try base path
        self.model, self.recognizer = try_load(self.model_path)

        # 2. If failed, search one level deep (FalaBrasil often extracts into a subfolder)
        if not self.model and os.path.isdir(self.model_path):
            for item in os.listdir(self.model_path):
                sub_path = os.path.join(self.model_path, item)
                if os.path.isdir(sub_path):
                    self.model, self.recognizer = try_load(sub_path)
                    if self.model:
                        print(f"Vosk: Auto-located model in {sub_path}")
                        break

        if not self.model:
            print(
                f"Vosk Init Error: Failed to load model from {self.model_path} or subfolders."
            )

    def process_audio(self, audio_bytes, is_speech):
        if not self.recognizer:
            return None, None

        if not hasattr(self, "silence_frames"):
            self.silence_frames = 0

        if not is_speech:
            self.silence_frames += 1
        else:
            self.silence_frames = 0

        # If Vosk naturally accepts the waveform (inner silence detection)
        if self.recognizer.AcceptWaveform(audio_bytes):
            res = json.loads(self.recognizer.Result())
            self.silence_frames = 0
            return None, res.get("text", "")

        # Optimization: If our OWN VAD detects silence long enough, force a result
        # This makes the "Big" model feel much faster as it doesn't wait for its internal timeout
        if self.silence_frames >= 20:  # ~600ms
            res = json.loads(self.recognizer.PartialResult())
            partial = res.get("partial", "")
            if partial:
                # We stop the current result and return it as final
                self.recognizer.Result()  # Clear internal buffer
                self.silence_frames = 0
                return None, partial
            self.silence_frames = 0

        # Regular partial result
        res = json.loads(self.recognizer.PartialResult())
        return res.get("partial", ""), None


class GoogleEngine:
    def __init__(self, sample_rate):
        self.recognizer = sr.Recognizer()
        self.sample_rate = sample_rate
        self.buffer = bytearray()
        self.is_processing = False
        self.silence_frames = 0
        self.silence_threshold_frames = (
            1  # ~30ms (instant trigger after AudioCapture says ok)
        )
        self.thinking = False

    def process_audio(self, audio_bytes, is_speech):
        if audio_bytes:
            self.buffer.extend(audio_bytes)

        if not is_speech:
            self.silence_frames += 1
        else:
            self.silence_frames = 0

        # Trigger on sustained silence OR if buffer is very long
        trigger = (
            self.silence_frames >= self.silence_threshold_frames
            and len(self.buffer) > 0
        )
        safety_trigger = len(self.buffer) > self.sample_rate * 2 * 2  # 2s max

        if trigger or safety_trigger:
            data = bytes(self.buffer)
            # Filter out very short segments (noise/clicks)
            duration_s = len(data) / (self.sample_rate * 2)

            # Reset for next segment
            self.buffer.clear()
            self.silence_frames = 0

            if duration_s < 0.4:  # 400ms min
                return None, None

            print(
                f"LOG: Segmento pronto para reconhecimento ({duration_s:.2f}s). Enviando para Google..."
            )
            # Return empty status + raw data for async pipeline (UI shows icon instead of text)
            return ("", data)

        return None, None

    def recognize(self, audio_data_bytes):
        """This method is called in the background thread (Executor)."""
        try:
            # Verificações de segurança
            if not audio_data_bytes or len(audio_data_bytes) == 0:
                print("LOG: Empty audio data received")
                return ""

            if not hasattr(self, "sample_rate") or self.sample_rate <= 0:
                print("LOG: Invalid sample rate")
                return ""

            import numpy as np

            audio_np = np.frombuffer(audio_data_bytes, dtype=np.int16).astype(
                np.float32
            )

            # Verifica se o array não está vazio
            if len(audio_np) == 0:
                print("LOG: Empty audio array")
                return ""

            # 1. Noise Reduction (Studio Quality)
            try:
                import noisereduce as nr

                # Apply stationary noise reduction
                # This removes fans, clicks and background hiss
                audio_np = nr.reduce_noise(
                    y=audio_np, sr=self.sample_rate, prop_decrease=0.8
                )
            except Exception as e:
                # Log only once to avoid spam
                if not hasattr(self, "_nr_warned"):
                    print(f"LOG: Noise reduction inactive (using raw audio): {e}")
                    self._nr_warned = True

            # 2. Normalization: significantly improves recognition for quiet mic inputs
            max_val = np.max(np.abs(audio_np))
            if max_val > 0:
                audio_np = (
                    audio_np / max_val
                ) * 30000.0  # Normalize to near-peak 16-bit

            normalized_bytes = audio_np.astype(np.int16).tobytes()

            # Verifica se o recognizer existe
            if not hasattr(self, "recognizer") or self.recognizer is None:
                print("LOG: Recognizer not initialized")
                return ""

            audio_data = sr.AudioData(normalized_bytes, self.sample_rate, 2)
            text = self.recognizer.recognize_google(audio_data, language="pt-BR")
            return text
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"Google API Error: {e}")
            import traceback

            traceback.print_exc()
            return ""


class WhisperEngine:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.model = None
        self.buffer = bytearray()
        self.silence_frames = 0
        self.silence_threshold_frames = 15  # ~450ms
        self.thinking = False

        if HAS_WHISPER:
            print("Loading Whisper model (base)...")
            self.model = whisper.load_model("base")
        else:
            raise RuntimeError("Whisper not installed")

    def process_audio(self, audio_bytes, is_speech):
        if audio_bytes:
            self.buffer.extend(audio_bytes)

        if not is_speech:
            self.silence_frames += 1
        else:
            self.silence_frames = 0

        trigger = (
            self.silence_frames >= self.silence_threshold_frames
            and len(self.buffer) > 0
        )
        safety_trigger = len(self.buffer) > self.sample_rate * 2 * 6  # 6s max

        if trigger or safety_trigger:
            data = bytes(self.buffer)
            self.buffer.clear()
            self.silence_frames = 0
            # Return empty status + raw data for async pipeline (UI shows icon instead of text)
            return ("", data)

        return None, None

    def recognize(self, audio_data_bytes):
        """This method is called in the background thread (Executor)."""
        if not HAS_WHISPER:
            return ""
        try:
            import numpy as np

            audio_np = (
                np.frombuffer(audio_data_bytes, dtype=np.int16).astype(np.float32)
                / 32768.0
            )
            result = self.model.transcribe(audio_np, language="pt")
            return result.get("text", "").strip()
        except Exception as e:
            print(f"Whisper Error: {e}")
            return ""
