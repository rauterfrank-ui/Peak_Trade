"""Single canonical browser-facing state aggregate (server-side composition)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import (
    DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
    OkxOhlcvReadmodelError,
    load_ohlcv_readmodel_v1,
    refresh_selected_okx_ohlcv_readmodel_from_archive_v1,
)
from src.ops.presentation_archive_root_v1.resolver_v1 import resolve_workflow_dashboard_archive_root
from src.webui.execution_watch_api_v0_2 import (
    api_execution_run_events_v0_2,
    api_execution_runs_v0_2,
)
from src.webui.r_and_d_api import compute_summary, load_experiments_from_dir

from .contracts_v1 import (
    MARKET_OBSERVATION_INTERVAL_SECONDS,
    POLL_INTERVAL_SECONDS,
    STATE_SCHEMA,
    SYSTEM_INSTRUMENTS_CACHE_SECONDS,
)
from .market_projection_v1 import project_market_state_from_ohlcv_doc
from .observation_cache_v1 import get_or_refresh_system_slice
from .system_projection_v1 import project_system_state


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _load_trade_events_for_latest_run() -> tuple[str | None, list[dict[str, Any]] | None]:
    try:
        runs_resp = await api_execution_runs_v0_2(limit=1)
    except Exception:  # noqa: BLE001 — observability only
        return None, None
    if not runs_resp.runs:
        return None, None
    run_id = runs_resp.runs[0].run_id
    try:
        ev_resp = await api_execution_run_events_v0_2(run_id, limit=500)
        events = [ev.model_dump() for ev in ev_resp.items]
        return run_id, events
    except Exception:  # noqa: BLE001
        return run_id, None


def _load_r_and_d_summary() -> dict[str, Any] | None:
    try:
        experiments = load_experiments_from_dir()
        return compute_summary(experiments)
    except Exception:  # noqa: BLE001
        return None


async def build_canonical_surface_state_v1(*, force_refresh: bool = False) -> dict[str, Any]:
    observed_at = _utc_now_iso()
    archive_root: Path | None = resolve_workflow_dashboard_archive_root()
    refresh_meta: dict[str, Any] | None = None
    ohlcv_doc: dict[str, Any] | None = None

    if archive_root is not None and archive_root.is_dir():
        try:
            refresh_meta = refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
                archive_root=archive_root,
                client=None,
                force=force_refresh,
                min_interval_seconds=0
                if force_refresh
                else DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
            )
        except OkxOhlcvReadmodelError as exc:
            if str(exc) == "REFRESH_IN_PROGRESS":
                refresh_meta = {
                    "status": "SKIPPED_IN_PROGRESS",
                    "refresh_attempted": False,
                    "refresh_error": str(exc),
                }
            else:
                refresh_meta = {
                    "status": "REFRESH_FAILED",
                    "refresh_attempted": True,
                    "refresh_error": str(exc),
                }
        loaded = load_ohlcv_readmodel_v1(archive_root)
        if loaded is not None:
            ohlcv_doc = dict(loaded)
        elif isinstance(refresh_meta, dict) and isinstance(refresh_meta.get("ohlcv"), dict):
            ohlcv_doc = dict(refresh_meta["ohlcv"])

    market = project_market_state_from_ohlcv_doc(
        ohlcv_doc, refresh_meta=refresh_meta, observed_at=observed_at
    )

    async def _build_system_payload() -> dict[str, Any]:
        run_id, events = await _load_trade_events_for_latest_run()
        r_and_d = _load_r_and_d_summary()
        system = project_system_state(
            archive_root=archive_root,
            trade_events=events,
            run_id=run_id,
            observed_at=observed_at,
            r_and_d_summary=r_and_d,
        )
        return {"system": system}

    system_payload, system_from_cache = await get_or_refresh_system_slice(
        builder=_build_system_payload,
        force=force_refresh,
    )
    system = system_payload["system"]

    try:
        from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.constants_v1 import (
            POST_ALLOWED,
            REAL_VENUE_POST_ALLOWED,
        )
    except ImportError:
        POST_ALLOWED = False  # type: ignore[misc, assignment]
        REAL_VENUE_POST_ALLOWED = False  # type: ignore[misc, assignment]

    safety = {
        "read_only_surface": True,
        "post_allowed": bool(POST_ALLOWED),
        "real_venue_post_allowed": bool(REAL_VENUE_POST_ALLOWED),
        "external_effect_authorized": False,
        "pt_mutation_routes": 0,
        "direct_browser_okx": False,
        "classification": "PROVEN_CURRENT",
    }

    return {
        "schema_name": STATE_SCHEMA,
        "schema_version": 1,
        "observed_at": observed_at,
        "poll_interval_seconds": POLL_INTERVAL_SECONDS,
        "observation": {
            "market_interval_seconds": MARKET_OBSERVATION_INTERVAL_SECONDS,
            "browser_poll_interval_seconds": POLL_INTERVAL_SECONDS,
            "system_instruments_cache_seconds": SYSTEM_INSTRUMENTS_CACHE_SECONDS,
            "system_slice_from_cache": system_from_cache,
            "okx_refresh_status": None if refresh_meta is None else refresh_meta.get("status"),
        },
        "market": market,
        "system": system,
        "safety": safety,
        "archive_root_configured": archive_root is not None,
    }
