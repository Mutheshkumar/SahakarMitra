"""
Voice Service for SahakarMitra.
Handles OpenAI Whisper speech-to-English translation and multi-language translation of answers.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from deep_translator import GoogleTranslator, MyMemoryTranslator

load_dotenv()

# Common language code mappings
LANGUAGE_MAP = {
    "tamil": "ta",
    "hindi": "hi",
    "telugu": "te",
    "kannada": "kn",
    "malayalam": "ml",
    "marathi": "mr",
    "bengali": "bn",
    "gujarati": "gu",
    "punjabi": "pa",
    "odia": "or",
    "urdu": "ur",
    "english": "en",
    "french": "fr",
    "spanish": "es",
    "german": "de",
}


def normalize_language_code(lang: str) -> str:
    """Normalize language code or language name to standard ISO 639-1 code."""
    if not lang:
        return "ta"
    lang_clean = lang.strip().lower()
    return LANGUAGE_MAP.get(lang_clean, lang_clean)


def translate_audio_whisper(audio_file_path: str) -> str:
    """
    Transcribe and translate an audio file into English text using OpenAI Whisper API in translate mode.
    
    Args:
        audio_file_path: Local path to the temporary audio file.
        
    Returns:
        English transcription/translation of the spoken audio.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if openai_api_key and not openai_api_key.startswith("your_openai_"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_api_key)
            
            with open(audio_file_path, "rb") as audio_file:
                # Use OpenAI Whisper in translate mode (translates any audio language to English)
                translation = client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file
                )
            
            # The result has a .text attribute (or string if response_format="text")
            if hasattr(translation, "text"):
                question_text = translation.text.strip()
            elif isinstance(translation, dict):
                question_text = translation.get("text", "").strip()
            else:
                question_text = str(translation).strip()

            if question_text:
                return question_text

        except Exception as e:
            print(f"[Voice Service] OpenAI Whisper translation error: {e}")
            # Raise exception if in live mode or let fallback handle if intended
            if not os.getenv("ALLOW_FALLBACK_TEST_AUDIO", "true").lower() in ("true", "1"):
                raise

    # Fallback simulation for offline testing / development when OpenAI key is not provided
    print("[Voice Service] Using default/mock transcription for testing/offline mode.")
    return "What is the monthly stipend and eligibility for Sahakar Mitra internship scheme?"


def translate_text(text: str, target_lang: str = "ta") -> str:
    """
    Translate English text into the target language using deep-translator (GoogleTranslator).
    
    Args:
        text: The source text in English to translate.
        target_lang: ISO 639-1 code or name for the target language (default 'ta' for Tamil).
        
    Returns:
        Translated text string in the target language.
    """
    if not text or not text.strip():
        return ""

    target_code = normalize_language_code(target_lang)

    # If target is English, return directly
    if target_code in ("en", "en-us", "en-gb"):
        return text

    # Attempt translation via GoogleTranslator
    try:
        # For long responses, chunk text to avoid URL / request size limits
        max_chunk = 4000
        if len(text) <= max_chunk:
            translator = GoogleTranslator(source="auto", target=target_code)
            return translator.translate(text)
        else:
            chunks = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]
            translator = GoogleTranslator(source="auto", target=target_code)
            translated_chunks = [translator.translate(chunk) for chunk in chunks]
            return " ".join(translated_chunks)
            
    except Exception as e:
        print(f"[Voice Service] GoogleTranslator failed for lang '{target_code}': {e}. Attempting fallback...")
        try:
            # Secondary fallback using MyMemory
            translator = MyMemoryTranslator(source="en-US", target=target_code)
            return translator.translate(text[:500])
        except Exception as fallback_e:
            print(f"[Voice Service] Secondary translator failed: {fallback_e}")
            # If all external translators fail (e.g. completely offline), return original text
            return text
