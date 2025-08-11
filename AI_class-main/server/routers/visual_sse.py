from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import time
from typing import Dict, Any

router = APIRouter()

class SSEManager:
    def __init__(self):
        self.connections: Dict[str, asyncio.Queue] = {}

    async def add_connection(self, session_id: str, queue: asyncio.Queue):
        self.connections[session_id] = queue
        print(f"SSE connection established: {session_id}")

    async def remove_connection(self, session_id: str):
        if session_id in self.connections:
            del self.connections[session_id]
            print(f"SSE connection closed: {session_id}")

    async def send_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        if session_id in self.connections:
            event = {
                "type": event_type,
                "data": data,
                "timestamp": time.time()
            }
            await self.connections[session_id].put(event)

sse_manager = SSEManager()

@router.get("/sse/{session_id}")
async def sse_endpoint(request: Request, session_id: str):
    
    async def event_generator():
        queue = asyncio.Queue()
        await sse_manager.add_connection(session_id, queue)
        try:
            yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
                except Exception:
                    break
        finally:
            await sse_manager.remove_connection(session_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

