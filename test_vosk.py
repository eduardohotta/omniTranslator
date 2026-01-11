import vosk
import os
import sys

def test_vosk():
    print(f"Python: {sys.version}")
    print(f"Vosk Path: {vosk.__file__}")
    
    model_path = "model"
    if not os.path.exists(model_path):
        print("Model folder not found!")
        return

    print(f"Testing Model Load from: {os.path.abspath(model_path)}")
    print(f"Folder contents: {os.listdir(model_path)}")
    
    try:
        vosk.SetLogLevel(0)
        model = vosk.Model(model_path)
        print("SUCCESS: Model loaded!")
        
        rec = vosk.KaldiRecognizer(model, 16000)
        print("SUCCESS: Recognizer created!")
    except Exception as e:
        print("FAILURE: Critical Error loading Vosk.")
        print(f"Error details: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vosk()
