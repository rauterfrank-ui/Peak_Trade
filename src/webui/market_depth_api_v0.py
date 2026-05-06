"""Market Depth read-model API v0 — read-only GET for `market_depth_readmodel_v0` (server-configured bundle only)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .market_depth_runtime_v0 import market_depth_json_payload_v0

_NO_STORE = {"Cache-Control": "no-store"}

router = APIRouter(prefix="/api/market", tags=["market-depth-api-v0"])


@router.get("/depth")
async def get_market_depth() -> JSONResponse:
    status_code, body = market_depth_json_payload_v0()
    return JSONResponse(status_code=status_code, content=body, headers=_NO_STORE)


__all__ = ["router"]
