"""Quick WebSocket /voice connectivity test."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import websockets


async def main():
    uri = "ws://127.0.0.1:8000/voice"
    async with websockets.connect(uri) as ws:
        msg = json.loads(await ws.recv())
        print("connected:", msg)
        await ws.send(json.dumps({"event": "ping"}))
        pong = json.loads(await ws.recv())
        print("pong:", pong)


if __name__ == "__main__":
    asyncio.run(main())
