"""
Speech-to-Text — Groq Whisper.
Validates audio before sending. Retries once on timeout.
"""
import io
import logging
import time

from groq import Groq

from config import STT_MODEL
from core.provider_keys import get_groq_keys, try_with_keys

logger = logging.getLogger(__name__)

MIN_VALID_AUDIO_BYTES = 300
MAX_AUDIO_BYTES = 25_000_000
WEBM_HEADER = b"\x1a\x45\xdf\xa3"


def transcribe_audio(
    audio_bytes: bytes,
    language: str = "en",
    retry: bool = True,
) -> dict:
    """Transcribe audio bytes using Groq Whisper."""
    audio_size = len(audio_bytes or b"")

    if audio_size < MIN_VALID_AUDIO_BYTES:
        return {
            "text": "",
            "language": language,
            "error": (
                f"Audio too small ({audio_size} bytes) "
                f"— likely empty recording"
            ),
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

        return {
            "text": (transcription.text or "").strip(),
            "language": getattr(transcription, "language", language),
            "duration": getattr(transcription, "duration", None),
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
