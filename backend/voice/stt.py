"""
Speech-to-Text — Groq Whisper.
Filters known hallucination phrases that Whisper produces
on silent or low-quality audio input.
"""
import io
import logging
import time

from groq import Groq

from config import STT_MODEL
from core.provider_keys import get_groq_keys, try_with_keys

logger = logging.getLogger(__name__)

MIN_VALID_AUDIO_BYTES = 1000
MAX_AUDIO_BYTES = 25_000_000
WEBM_HEADER = b"\x1a\x45\xdf\xa3"

# Known Whisper hallucination phrases on silence/noise
HALLUCINATION_PHRASES = {
    "thank you",
    "thank you.",
    "thanks for watching",
    "thanks for watching!",
    "thank you for watching",
    "please subscribe",
    "bye",
    "bye.",
    "okay",
    "ok.",
    "you",
    "the",
    "uh",
    "um",
    "hmm",
    ".",
    "...",
}


def is_likely_hallucination(text: str, audio_duration: float | None) -> bool:
    """
    Detect if transcription is likely a Whisper hallucination
    rather than real speech.
    """
    normalized = text.lower().strip()

    if normalized in HALLUCINATION_PHRASES:
        return True

    if audio_duration is not None and audio_duration < 1.0:
        if len(normalized.split()) <= 3:
            return True

    return False


def transcribe_audio(
    audio_bytes: bytes,
    language: str = "en",
    retry: bool = True,
) -> dict:
    """
    Transcribe audio bytes using Groq Whisper.
    Filters hallucinated phrases from silent/short audio.
    """
    audio_size = len(audio_bytes or b"")

    if audio_size < MIN_VALID_AUDIO_BYTES:
        return {
            "text": "",
            "language": language,
            "error": f"Audio too small ({audio_size} bytes)",
        }

    if audio_size < 1000 and not audio_bytes.startswith(WEBM_HEADER):
        return {
            "text": "",
            "language": language,
            "error": "Invalid audio format from browser",
        }

    if audio_size > MAX_AUDIO_BYTES:
        return {
            "text": "",
            "language": language,
            "error": f"Audio too large ({audio_size} bytes)",
        }

    if not get_groq_keys():
        return {"text": "", "language": language, "error": "Missing API key"}

    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.webm"

        def transcribe_with_key(api_key: str):
            audio_file.seek(0)
            client = Groq(api_key=api_key)
            return client.audio.transcriptions.create(
                model=STT_MODEL,
                file=audio_file,
                language=language if language != "auto" else None,
                response_format="verbose_json",
                timeout=30.0,
            )

        transcription = try_with_keys(get_groq_keys(), "groq-stt", transcribe_with_key)
        if not transcription:
            return {
                "text": "",
                "language": language,
                "error": "All Groq keys failed for STT",
            }

        text = (transcription.text or "").strip()
        duration = getattr(transcription, "duration", None)

        if is_likely_hallucination(text, duration):
            logger.info(
                "[stt] Filtered likely hallucination: '%s' "
                "(duration=%s, audio_bytes=%s)",
                text,
                duration,
                audio_size,
            )
            return {
                "text": "",
                "language": language,
                "error": "hallucination_filtered",
                "raw_text": text,
            }

        return {
            "text": text,
            "language": getattr(transcription, "language", language),
            "duration": duration,
        }

    except Exception as e:
        error_str = str(e).lower()

        if "timeout" in error_str and retry:
            logger.info("[stt] Timeout — retrying once...")
            time.sleep(1)
            return transcribe_audio(audio_bytes, language, retry=False)

        if "valid media file" in error_str or "format" in error_str:
            return {
                "text": "",
                "language": language,
                "error": "Invalid audio format from browser",
            }

        return {
            "text": "",
            "language": language,
            "error": str(e),
        }
