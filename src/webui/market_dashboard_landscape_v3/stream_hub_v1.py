"""Peak_Trade-hosted WebSocket presentation hub for Landscape V3."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from src.webui.market_dashboard_landscape_v3.constants_v1 import STREAM_SCHEMA_VERSION
from src.webui.market_dashboard_landscape_v3.presentation_adapter_v1 import (
    LandscapeV3PresentationAdapterV1,
    LandscapeV3UpstreamObservationV1,
)


@dataclass
class LandscapeV3StreamHubV1:
    adapter: LandscapeV3PresentationAdapterV1 = field(
        default_factory=LandscapeV3PresentationAdapterV1
    )
    observation: LandscapeV3UpstreamObservationV1 = field(
        default_factory=lambda: LandscapeV3UpstreamObservationV1("ETH-USDT-SWAP")
    )
    _clients: list[WebSocket] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _loop: Optional[asyncio.AbstractEventLoop] = None
    heartbeat_seconds: float = 15.0

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def get_snapshot(self) -> dict[str, Any]:
        snap = self.adapter.build_snapshot(self.observation)
        return {"type": "snapshot", "stream_schema": STREAM_SCHEMA_VERSION, **snap}

    async def handle_client(self, websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_text(json.dumps(self.get_snapshot()))
        async with self._lock:
            self._clients.append(websocket)
        try:
            while True:
                msg = await websocket.receive_text()
                if msg.strip().lower() in {"ping", '{"op":"ping"}'}:
                    await websocket.send_text(json.dumps({"type": "heartbeat", "op": "pong"}))
                elif msg.strip().lower() == "resync":
                    await websocket.send_text(json.dumps(self.get_snapshot()))
        except WebSocketDisconnect:
            pass
        finally:
            async with self._lock:
                if websocket in self._clients:
                    self._clients.remove(websocket)

    async def broadcast_json(self, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload)
        async with self._lock:
            clients = list(self._clients)
        dead: list[WebSocket] = []
        for ws in clients:
            try:
                await ws.send_text(raw)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    if ws in self._clients:
                        self._clients.remove(ws)

    def publish_from_thread(self, payload: dict[str, Any]) -> None:
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast_json(payload), self._loop)


_GLOBAL_HUB: LandscapeV3StreamHubV1 | None = None


def get_landscape_v3_stream_hub_v1() -> LandscapeV3StreamHubV1:
    global _GLOBAL_HUB
    if _GLOBAL_HUB is None:
        _GLOBAL_HUB = LandscapeV3StreamHubV1()
    return _GLOBAL_HUB
