from deep_translator import GoogleTranslator

class Translator:
    @staticmethod
    def translate(text,source_language = "auto"):
        try:
            translated_text = GoogleTranslator(source=source_language, target="en").translate(text)
            return translated_text
        except Exception as e:
            print(f"Translation error: {e}")
            raise e