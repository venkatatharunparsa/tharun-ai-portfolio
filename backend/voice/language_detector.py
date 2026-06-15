"""
Language Detector — detects input language to route STT and TTS correctly.
Phase 2: English only.
Phase 5: Bhashini for Indian languages (Hindi, Telugu, Tamil etc.)
"""

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "mr": "Marathi",
}

INDIAN_LANGUAGES = {"hi", "te", "ta", "kn", "mr"}


def detect_language_from_text(text: str) -> str:
    """
    Basic language detection from transcribed text.
    Phase 3: returns 'en' always.
    Phase 5: integrate Bhashini language detection.
    """
    _ = text
    return "en"


def is_indian_language(language_code: str) -> bool:
    """Check if language should be routed to Bhashini."""
    return language_code in INDIAN_LANGUAGES


def get_tts_provider_for_language(language_code: str, text_length: int) -> str:
    """
    Determine TTS provider based on language and text length.

    Returns: 'elevenlabs' | 'webspeech' | 'bhashini'
    """
    if is_indian_language(language_code):
        return "bhashini"
    if text_length <= 200:
        return "elevenlabs"
    return "webspeech"
