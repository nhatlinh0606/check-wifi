"""
WebSocket Service for broadcasting real-time scan events to frontend clients.
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketService:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        if not self.active_connections:
            return

        payload = json.dumps({"event": event_type, "data": data})
        disconnected = set()

        for conn in list(self.active_connections):
            try:
                await conn.send_text(payload)
            except Exception as e:
                logger.debug(f"Failed to send to client: {e}")
                disconnected.add(conn)

        for dead in disconnected:
            self.active_connections.discard(dead)


ws_manager = WebSocketService()
