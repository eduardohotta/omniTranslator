import queue
import time
import numpy as np
import logging

logger = logging.getLogger("Pipeline")
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QThread, Signal
from core.transcriber import Transcriber
from download_models import setup_vosk


class DownloadWorker(QThread):
    progress_signal = Signal(int)
    finished_signal = Signal(str, str)  # path, error_msg

    def __init__(self, model_type):
        super().__init__()
        self.model_type = model_type

    def run(self):
        try:
            path, msg = setup_vosk(
                self.model_type, progress_callback=self.progress_signal.emit
            )
            self.finished_signal.emit(path if path else "", msg)
        except Exception as e:
            logger.error(f"DownloadWorker thread error: {e}")
            self.finished_signal.emit("", str(e))


class LoaderWorker(QThread):
    finished_signal = Signal(object, object)  # transcriber, translator
    error_signal = Signal(str)

    def __init__(self, m_path, target_lang, has_translator):
        super().__init__()
        self.m_path = m_path
        self.target_lang = target_lang
        self.has_translator = has_translator

    def run(self):
        try:
            print(f"Loading model in background: {self.m_path}")
            new_transcriber = Transcriber(self.m_path)
            new_translator = None
            if self.has_translator:
                from core.translator import Translator

                new_translator = Translator(from_code="pt", to_code=self.target_lang)
            self.finished_signal.emit(new_transcriber, new_translator)
        except Exception as e:
            self.error_signal.emit(str(e))


class ProcessingThread(QThread):
    update_text_signal = Signal(str, str)
    update_status_signal = Signal(bool)
    update_thinking_signal = Signal(bool)
    update_pause_signal = Signal(bool)

    def __init__(
        self, audio_capture, transcriber, translator, has_translator_plugin=True
    ):
        super().__init__()
        self.audio_capture = audio_capture
        self.transcriber = transcriber
        self.translator = translator
        self.has_translator_plugin = has_translator_plugin
        self._running = True
        self._paused = False
        self._last_speech_status = False
        self.context_buffer = (
            ""  # Store last few words/sentences for better translation context
        )
        self.executor = ThreadPoolExecutor(max_workers=3)
        # Fila thread-safe para resultados do processamento assíncrono
        self._result_queue = queue.Queue()

    def run(self):
        print("Starting processing thread...")
        self.audio_capture.start()

        while self._running:
            if self._paused:
                self.msleep(100)
                continue

            # Processa resultados pendentes da fila (thread-safe)
            try:
                while not self._result_queue.empty():
                    result = self._result_queue.get_nowait()
                    result_type = result.get("type")

                    if result_type == "thinking":
                        self.update_thinking_signal.emit(result["value"])
                    elif result_type == "text":
                        self.update_text_signal.emit(
                            result["text"], result["translation"]
                        )
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Error processing result queue: {e}")

            try:
                # Get audio chunk
                item = self.audio_capture.audio_queue.get(timeout=0.1)
                audio_bytes, is_speech, energy = item if len(item) == 3 else (*item, 0)

                # Emit status
                if self._last_speech_status != is_speech:
                    self.update_status_signal.emit(bool(is_speech))
                    self._last_speech_status = is_speech

                if audio_bytes:
                    # Verifica se o transcriber e engine existem
                    if not self.transcriber or not hasattr(self.transcriber, "engine"):
                        print("Warning: Transcriber or engine not available")
                        continue

                    if hasattr(self.transcriber.engine, "recognize"):
                        # Online/Heavy engine
                        try:
                            status, data = self.transcriber.process_audio(
                                audio_bytes, is_speech=is_speech
                            )
                            if status is not None:
                                self.update_thinking_signal.emit(True)
                                if status:
                                    self.update_text_signal.emit(status, "")

                            if data:
                                self.update_thinking_signal.emit(True)
                                self.executor.submit(self._async_pipeline, data)
                        except Exception as e:
                            print(f"Error in online engine processing: {e}")
                    else:
                        # Standard offline logic
                        try:
                            partial, final = self.transcriber.process_audio(
                                audio_bytes, is_speech=is_speech
                            )
                            if final:
                                self._sync_pipeline(final)
                            elif partial:
                                self.update_text_signal.emit(partial, "")
                        except Exception as e:
                            print(f"Error in offline engine processing: {e}")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in processing loop: {e}")

    def _async_pipeline(self, data):
        """Processa reconhecimento em thread separada e coloca resultados na fila."""
        start_t = time.time()
        try:
            # Verificações de segurança
            if not self.transcriber or not hasattr(self.transcriber, "engine"):
                print("Warning: Transcriber/engine not available in async pipeline")
                self._result_queue.put({"type": "thinking", "value": False})
                return

            if not hasattr(self.transcriber.engine, "recognize"):
                print("Warning: Engine does not have recognize method")
                self._result_queue.put({"type": "thinking", "value": False})
                return

            # 1. Recognize
            text = (
                self.transcriber.engine.recognize(data)
                if isinstance(data, (bytes, bytearray))
                else data
            )
            if not text:
                # Coloca na fila em vez de emitir sinal diretamente (thread-safe)
                self._result_queue.put({"type": "thinking", "value": False})
                return

            # Coloca resultado intermediário na fila
            self._result_queue.put({"type": "text", "text": text, "translation": ""})

            # 2. Translate
            translation = (
                self.translator.translate(text)
                if self.has_translator_plugin and self.translator
                else text
            )

            # Coloca resultados finais na fila
            self._result_queue.put({"type": "thinking", "value": False})
            self._result_queue.put(
                {"type": "text", "text": text, "translation": translation}
            )
        except Exception as e:
            print(f"Async pipeline error: {e}")
            import traceback

            traceback.print_exc()
            # Coloca erro na fila
            self._result_queue.put({"type": "thinking", "value": False})

    def _sync_pipeline(self, text):
        translation = (
            self.translator.translate(text)
            if self.has_translator_plugin and self.translator
            else text
        )
        self.update_text_signal.emit(text, translation)

    def toggle_pause(self):
        self._paused = not self._paused
        if self._paused:
            self.audio_capture.stop()
        else:
            self.audio_capture.start()
        self.update_pause_signal.emit(self._paused)
        # Se pausar, forçamos o status de escuta para falso
        if self._paused:
            self.update_status_signal.emit(False)

    def pause_audio(self):
        self._paused = True
        self.audio_capture.stop()
        self.update_pause_signal.emit(True)
        self.update_status_signal.emit(False)

    def resume_audio(self):
        self._paused = False
        self.audio_capture.start()
        self.update_pause_signal.emit(False)

    def stop(self):
        """Para a thread de processamento de forma segura."""
        print("Stopping processing thread...")
        self._running = False
        self.audio_capture.stop()

        # Aguarda processamento de resultados pendentes
        try:
            while not self._result_queue.empty():
                result = self._result_queue.get_nowait()
                result_type = result.get("type")
                if result_type == "thinking":
                    self.update_thinking_signal.emit(result["value"])
                elif result_type == "text":
                    self.update_text_signal.emit(result["text"], result["translation"])
        except:
            pass

        # Desliga o executor de threads
        self.executor.shutdown(wait=False)

        # Aguarda a thread terminar
        if not self.wait(3000):  # Aguarda até 3 segundos
            print("Warning: Processing thread did not stop in time")
            self.terminate()  # Força terminação se necessário
