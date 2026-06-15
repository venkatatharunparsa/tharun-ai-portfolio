"""
Text-to-Speech Cascade — Tharun AI Portfolio.
"""
import logging

from elevenlabs import ElevenLabs
from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    TTS_ELEVENLABS_CHAR_LIMIT,
)

logger = logging.getLogger(__name__)

client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None


def should_use_elevenlabs(text: str) -> bool:
    """Determine if response is short enough for ElevenLabs."""
    return len(text.strip()) <= TTS_ELEVENLABS_CHAR_LIMIT


def synthesize_elevenlabs(text: str) -> bytes | None:
    """
    Generate audio using ElevenLabs.
    Returns audio bytes or None on failure.
    """
    try:
        if not client or not ELEVENLABS_VOICE_ID:
            return None

        audio_generator = client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id="eleven_turbo_v2",
            output_format="mp3_44100_128",
        )
        audio_bytes = b"".join(chunk for chunk in audio_generator)
        return audio_bytes

    except Exception as e:
        logger.warning("ElevenLabs TTS error: %s", e)
        return None


def get_tts_response(text: str) -> dict:
    """
    Main TTS entry point.
    Decides provider and returns audio or web speech signal.

    Returns dict:
    {
        "provider": "elevenlabs" | "webspeech",
        "audio_bytes": bytes | None,
        "text": str
    }
    """
    if should_use_elevenlabs(text):
        audio = synthesize_elevenlabs(text)
        if audio:
            return {
                "provider": "elevenlabs",
                "audio_bytes": audio,
                "text": text,
            }

    return {
        "provider": "webspeech",
        "audio_bytes": None,
        "text": text,
    }
