"""Phase 3 verification — STT fallback and TTS cascade."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from voice.stt import transcribe_audio
from voice.tts import should_use_elevenlabs, get_tts_response

short_text = "Hi! I'm Tharun AI."
long_text = (
    "Tharun is an Agentic AI Engineer who has built multiple production-grade "
    "systems including TaxSetu, InfraGenie, NINA, and VisionSync. His approach "
    "combines deep systems thinking with business understanding."
)

print("STT fallback test:", transcribe_audio(b"test"))
print("Short text uses ElevenLabs:", should_use_elevenlabs(short_text))
print("Long text uses ElevenLabs:", should_use_elevenlabs(long_text))
print("Long text provider:", get_tts_response(long_text)["provider"])
