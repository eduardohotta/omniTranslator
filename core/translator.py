from deep_translator import GoogleTranslator
import threading

class Translator:
    def __init__(self, from_code='pt', to_code='en'):
        self.from_code = from_code
        self.to_code = to_code
        self._translator = GoogleTranslator(source=from_code, target=to_code)
        print(f"DEBUG: Translator initialized for {from_code} -> {to_code}")

    def translate(self, text):
        if not text or text.strip() == "":
            return ""
        
        try:
            # deep-translator is synchronous and uses requests internally
            translated = self._translator.translate(text)
            print(f"DEBUG: Translation result: '{text}' -> '{translated}'")
            return translated
        except Exception as e:
            print(f"DEBUG Translation error: {e}")
            return text

