"""Voice WebSocket multi-turn backend test (session continuity)."""
import asyncio
import json
import uuid

import websockets

WS_URL = "ws://127.0.0.1:8000/voice"
SID = f"voice-smoke-{uuid.uuid4().hex[:8]}"


async def run():
    results = []
    async with websockets.connect(WS_URL) as ws:
        msg = json.loads(await ws.recv())
        assert msg.get("status") == "connected", msg

        await ws.send(json.dumps({"event": "init", "session_id": SID}))

        # Turn 1: too_short → should reset to connected
        await ws.send(json.dumps({"event": "end_of_speech"}))
        statuses = []
        for _ in range(3):
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            if m.get("type") == "status":
                statuses.append(m.get("status"))
        results.append(("turn1_reset", "connected" in statuses, statuses))

        # Ping keeps connection alive
        await ws.send(json.dumps({"event": "ping"}))
        pong = json.loads(await ws.recv())
        results.append(("ping_pong", pong.get("type") == "pong", pong))

    for name, ok, detail in results:
        print(f"{name}: {'PASS' if ok else 'FAIL'} — {detail}")


if __name__ == "__main__":
    asyncio.run(run())
