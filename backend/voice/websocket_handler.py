"""
WebSocket Voice Handler — Tharun AI Portfolio.
"""
import asyncio
import json
import logging
import uuid

from fastapi import WebSocket, WebSocketDisconnect

from agents.graph import process_query
from voice.language_detector import detect_language_from_text
from voice.stt import transcribe_audio
from voice.tts import get_tts_response

logger = logging.getLogger(__name__)

MIN_AUDIO_BYTES = 1000
RECEIVE_TIMEOUT_SEC = 120.0

WAKE_PREFIXES = [
    "hey tharun", "hi tharun", "hello tharun",
    "ok tharun", "okay tharun", "tharun",
    "hey taron", "hey thrown", "hey the run",
    "hey sharon", "hey tarun", "hey theron",
    "hay tharun", "hey ai",
]


def strip_wake_word(text: str) -> str:
    """Remove wake word prefix from transcript."""
    text_lower = text.lower().strip()
    for prefix in WAKE_PREFIXES:
        if text_lower.startswith(prefix):
            stripped = text[len(prefix):].strip(" ,.")

            return stripped if stripped else text
    return text


def _is_disconnect_error(exc: BaseException) -> bool:
    if isinstance(exc, WebSocketDisconnect):
        return True
    return "disconnect" in str(exc).lower()


async def _send_connected(websocket: WebSocket, session_id: str) -> None:
    await websocket.send_json({
        "type": "status",
        "status": "connected",
        "session_id": session_id,
    })


async def _receive_message(websocket: WebSocket) -> dict | None:
    """Receive one WS message; return None on clean client disconnect."""
    try:
        return await asyncio.wait_for(
            websocket.receive(),
            timeout=RECEIVE_TIMEOUT_SEC,
        )
    except asyncio.TimeoutError:
        try:
            await websocket.send_json({"type": "ping"})
        except Exception:
            return None
        return {}
    except (WebSocketDisconnect, RuntimeError) as exc:
        if _is_disconnect_error(exc):
            return None
        raise
    except Exception:
        return None


async def handle_voice_websocket(websocket: WebSocket) -> None:
    """Main WebSocket handler with clean disconnect handling."""
    await websocket.accept()

    session_id = str(uuid.uuid4())
    audio_buffer = bytearray()
    conversation_history: list[dict] = []
    is_processing = False

    await _send_connected(websocket, session_id)

    try:
        while True:
            message = await _receive_message(websocket)
            if message is None:
                break
            if not message:
                continue

            if message.get("type") == "websocket.disconnect":
                break

            if "bytes" in message:
                if not is_processing:
                    audio_buffer.extend(message["bytes"])
                continue

            if "text" not in message:
                continue

            try:
                data = json.loads(message["text"])
            except json.JSONDecodeError:
                continue

            event = data.get("event")

            if event == "init":
                client_session = data.get("session_id")
                if client_session:
                    session_id = client_session
                await _send_connected(websocket, session_id)
                continue

            if event == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if event == "end_of_speech":
                if is_processing:
                    continue

                if len(audio_buffer) < MIN_AUDIO_BYTES:
                    audio_buffer.clear()
                    await websocket.send_json({"type": "status", "status": "too_short"})
                    await asyncio.sleep(0.1)
                    await _send_connected(websocket, session_id)
                    continue

                is_processing = True
                await websocket.send_json({"type": "status", "status": "processing"})

                audio_bytes = bytes(audio_buffer)
                audio_buffer.clear()
                logger.info(
                    "Session %s: end_of_speech audio=%d bytes",
                    session_id,
                    len(audio_bytes),
                )

                try:
                    stt_result = transcribe_audio(audio_bytes)
                    transcript = stt_result.get("text", "").strip()

                    if stt_result.get("error") == "hallucination_filtered":
                        logger.info(
                            "Session %s: Hallucination filtered, raw was: '%s'",
                            session_id,
                            stt_result.get("raw_text"),
                        )
                        await websocket.send_json({
                            "type": "status",
                            "status": "no_transcript",
                        })
                        await asyncio.sleep(0.1)
                        await _send_connected(websocket, session_id)
                        continue

                    if not transcript:
                        if stt_result.get("error"):
                            logger.info(
                                "Session %s: STT skipped — %s (audio=%d bytes)",
                                session_id,
                                stt_result["error"],
                                len(audio_bytes),
                            )
                        await websocket.send_json({
                            "type": "status",
                            "status": "no_transcript",
                        })
                        await asyncio.sleep(0.1)
                        await _send_connected(websocket, session_id)
                        continue

                    transcript = strip_wake_word(transcript)

                    if not transcript or len(transcript) < 2:
                        await _send_connected(websocket, session_id)
                        continue

                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript,
                    })

                    language = detect_language_from_text(transcript)

                    agent_result = await asyncio.wait_for(
                        asyncio.to_thread(
                            process_query,
                            transcript,
                            session_id,
                            language,
                            conversation_history.copy(),
                        ),
                        timeout=120.0,
                    )

                    response_text = agent_result.get("final_response", "")

                    if not response_text:
                        await websocket.send_json({
                            "type": "error",
                            "message": "No response generated",
                        })
                        continue

                    conversation_history.append({"role": "user", "text": transcript})
                    conversation_history.append({"role": "assistant", "text": response_text})
                    conversation_history = conversation_history[-8:]

                    await websocket.send_json({
                        "type": "reply_text",
                        "text": response_text,
                        "intent": agent_result.get("intent"),
                        "response_source": agent_result.get("response_source"),
                        "processing_time_ms": agent_result.get("processing_time_ms"),
                        "agent_steps": agent_result.get("agent_steps"),
                        "tools_used": agent_result.get("tools_used"),
                    })

                    tts_result = get_tts_response(response_text)

                    if tts_result["provider"] == "elevenlabs" and tts_result["audio_bytes"]:
                        await websocket.send_bytes(tts_result["audio_bytes"])
                    else:
                        await websocket.send_json({
                            "type": "use_webspeech",
                            "text": response_text,
                        })

                except asyncio.TimeoutError:
                    logger.warning("Session %s: agent pipeline timed out", session_id)
                    await websocket.send_json({
                        "type": "error",
                        "message": "Processing took too long. Please try again.",
                    })
                except Exception:
                    logger.exception("Session %s: pipeline error", session_id)
                    await websocket.send_json({
                        "type": "error",
                        "message": "Something went wrong. Please try again.",
                    })
                finally:
                    is_processing = False
                    await _send_connected(websocket, session_id)

    except Exception as e:
        if not _is_disconnect_error(e):
            logger.warning("[voice-ws] Unexpected error: %s", e)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Session ended unexpectedly",
            })
        except Exception:
            pass
    finally:
        logger.info("[voice-ws] Session %s closed", session_id)
