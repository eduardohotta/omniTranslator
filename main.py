import sys
import queue
import json
import keyboard
from PySide6.QtWidgets import QApplication
from ui.overlay import OverlayWindow
from core.audio import AudioCapture
from core.transcriber import Transcriber
try:
    from core.translator import Translator 
    HAS_TRANSLATOR = True
except Exception as e:
    print(f"Translator import failed: {e}")
    HAS_TRANSLATOR = False
from core.pipeline import DownloadWorker, LoaderWorker, ProcessingThread
from download_models import is_model_installed
import os

VERSION = "1.0.0"


def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create default config with Google model and default microphone
        default_config = {
            "source_lang": "pt",
            "target_lang": "en",
            "font_size": 14,
            "font_color": "white",
            "opacity": 0.69,
            "always_on_top": True,
            "x_pos": None,
            "y_pos": 50,
            "audio_device_index": None,  # None = default microphone
            "model_type": "google",
            "text_color": "white",
            "trans_color": "#39FF14",
            "trans_font_size": 19,
            "vad_threshold": 300,
            "text_align": "center"
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        print("Created default config.json with Google model and default microphone")
        return default_config
    except Exception as e:
        print(f"Config load failed: {e}")
        return {}

def main():
    app = QApplication(sys.argv)
    config = load_config()
    
    # Function to restart everything (model/language change)
    def restart_all_modules():
        print("Performing full restart of modules...")
        thread.pause_audio()
        
        m_type = config.get("model_type", "small")
        actual_path = is_model_installed(m_type)
        
        apply_restart()

    def download_model(model_type):
        window.show_loading(0)
        worker = DownloadWorker(model_type)
        worker.progress_signal.connect(window.show_loading)
        worker.finished_signal.connect(on_download_finished)
        # Keep reference to avoid GC
        window.dl_worker = worker
        worker.start()

    def on_download_finished(path, error_msg):
        if path:
            print(f"Download finished: {path}")
            apply_restart()
        else:
            print(f"Download failed: {error_msg}")
            window.update_text("Erro no download.", f"{error_msg}\nTente novamente nas configurações.")


    def apply_restart():
        m_type = config.get("model_type", "small")
        m_path = is_model_installed(m_type)
        
        window.update_text("Carregando...", f"Iniciando motor {m_type}...", to_history=False)
        
        # Use LoaderWorker to avoid freezing UI
        loader = LoaderWorker(m_path, config.get("target_lang", "en"), HAS_TRANSLATOR)
        loader.finished_signal.connect(on_load_finished)
        loader.error_signal.connect(on_load_error)
        window.loader_worker = loader # Prevent GC
        loader.start()


    def on_load_finished(new_transcriber, new_translator):
        print("Model and translator loaded successfully.")
        thread.transcriber = new_transcriber
        thread.translator = new_translator
        window.update_text("Concluído", "Modelo carregado com sucesso.", to_history=False)
        thread.resume_audio()
        
        # Reset text back to waiting after 3 seconds
        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: window.update_text("", ""))

    def on_load_error(error_msg):
        print(f"Load error: {error_msg}")
        window.update_text("Erro ao carregar", f"{error_msg}\nTente baixar novamente o modelo.", to_history=False)
        thread.resume_audio()



    # Function to restart audio logic
    def restart_audio_capture(device_index):
        print(f"Restarting audio on device {device_index}")
        thread.pause_audio() 
        audio.change_device(device_index)
        thread.resume_audio()
        
        # Save config
        config['audio_device_index'] = device_index
        with open('config.json', 'w') as f:
            json.dump(config, f)

    print("Initializing modules...")
    try:
        # Load correct model on startup
        m_type = config.get("model_type", "small")
        actual_path = is_model_installed(m_type)


        if not actual_path:
            print(f"Preferred model {m_type} is missing or broken.")
            # Fallback to small if we wanted big
            if m_type == "big":
                actual_path = is_model_installed("small")
                if actual_path:
                    print("Falling back to model_small for startup.")
                else:
                    print("No valid local models found.")

        
        # If still no path, we can't init Transcriber normally.
        # We will initialize with a placeholder OR just let it try and we catch it.
        # But we MUST have a Transcriber object for the thread.
        transcriber = Transcriber(actual_path if actual_path else "missing")
        
        # Init Audio
        dev_idx = config.get("audio_device_index")
        vad_th = config.get("vad_threshold", 300)
        
        audio = AudioCapture(
            device_index=dev_idx, 
            energy_threshold=vad_th
        )
        
        translator = None
        if HAS_TRANSLATOR:
            try:
                translator = Translator(
                    from_code="pt",
                    to_code=config.get("target_lang", "en")
                )
            except Exception as e:
                print(f"Translator init failed: {e}") 
                pass
    except Exception as e:
        print(f"Silent initialization failure: {e}")
        # Ensure we have at least standard objects to avoid crash
        # If transcription failed, thread will just wait.
        if 'audio' not in locals(): audio = AudioCapture(device_index=config.get("audio_device_index"))
        if 'transcriber' not in locals(): transcriber = Transcriber("missing")
        if 'translator' not in locals(): translator = None


    # Initialize UI
    window = OverlayWindow(config, audio_handler=audio)
    window.set_version(VERSION)
    
    # Initialize Worker Thread
    thread = ProcessingThread(audio, transcriber, translator)
    thread.update_text_signal.connect(window.update_text)
    thread.update_status_signal.connect(window.update_status)
    thread.update_thinking_signal.connect(window.set_thinking)
    thread.update_pause_signal.connect(window.update_pause)
    window.request_restart_audio.connect(restart_audio_capture)
    window.request_full_restart.connect(restart_all_modules)
    
    # Ensure clean exit
    def on_close():
        print("Closing application...")
        thread.stop()
        app.quit()
        
    window.closed_signal.connect(on_close)
    
    window.show()
    
    # Hotkeys
    print("Registering hotkeys...")
    # Ctrl+Alt+S to toggle
    keyboard.add_hotkey('ctrl+alt+s', lambda: thread.toggle_pause())
    # Ctrl+Alt+C to clear
    keyboard.add_hotkey('ctrl+alt+c', lambda: window.clear_history())


    print("Starting application...")
    thread.start()
    
    # Automatic download/repair on startup removed to avoid intrusive behavior.
    # Users should manage models via Settings.

    ret = app.exec()

    print("Shutting down...")
    thread.stop()
    sys.exit(ret)


if __name__ == "__main__":
    main()
