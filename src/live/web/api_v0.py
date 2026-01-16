from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterator, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from ..monitoring import list_runs as monitoring_list_runs
from ..run_logging import load_run_events, load_run_metadata
from .models_v0 import (
    EquityPointV0,
    EventItemV02,
    EventsPollResponseV02,
    HealthResponse,
    HealthV02,
    OrderPointV0B,
    OrdersResponseV0B,
    PositionPointV0B,
    PositionsResponseV0B,
    RunDetailV0,
    RunDetailV02,
    RunMetaV0,
    RunMetadataResponse,
    RunMetricsV0,
    RunSnapshotResponse,
    RunSummaryV02,
    SignalPointV0B,
    SignalsResponseV0B,
)


def build_api_v0_router(
    *,
    runs_dir: Path,
    contract_version: str,
    health_check: Callable[[], Awaitable[HealthResponse]],
    get_runs: Callable[[], Awaitable[List[RunMetadataResponse]]],
    get_run_snapshot_endpoint: Callable[[str], Awaitable[RunSnapshotResponse]],
) -> APIRouter:
    """
    Builds the read-only API v0 router under /api/v0.

    Note: This router is watch-only / read-only. No mutating endpoints.
    """

    router = APIRouter(prefix="/api/v0")

    def _run_dir_for(run_id: str) -> Path:
        run_dir = runs_dir / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail=f"run_not_found: {run_id}")
        return run_dir

    def _load_meta_v0(run_id: str) -> RunMetaV0:
        run_dir = _run_dir_for(run_id)
        try:
            meta = load_run_metadata(run_dir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"meta_not_found: {run_id}")

        return RunMetaV0(
            run_id=meta.run_id,
            mode=meta.mode,
            strategy_name=meta.strategy_name,
            symbol=meta.symbol,
            timeframe=meta.timeframe,
            started_at=meta.started_at.isoformat() if meta.started_at else None,
            ended_at=meta.ended_at.isoformat() if meta.ended_at else None,
            config_snapshot=meta.config_snapshot or {},
            notes=meta.notes or "",
        )

    def _asof_utc() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _load_events_df_v0b(run_id: str) -> pd.DataFrame:
        run_dir = _run_dir_for(run_id)
        try:
            return load_run_events(run_dir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"events_not_available: {run_id}")

    def _events_tail_v0b(df: pd.DataFrame, limit: int) -> pd.DataFrame:
        if len(df) == 0:
            return df
        if "step" in df.columns:
            try:
                df = df.sort_values("step")
            except Exception:
                pass
        if limit and len(df) > limit:
            df = df.tail(limit)
        return df

    def _row_ts_v0b(row: Any) -> Optional[str]:
        try:
            ts_val = row.get("ts_event") if hasattr(row, "get") else None
        except Exception:
            ts_val = None
        if not ts_val:
            try:
                ts_val = row.get("ts_bar") if hasattr(row, "get") else None
            except Exception:
                ts_val = None
        if ts_val is None:
            return None
        return str(ts_val)

    def _int_or_none(val: Any) -> Optional[int]:
        try:
            if val is None or pd.isna(val):
                return None
            return int(val)
        except Exception:
            return None

    @router.get("/health", response_model=HealthResponse)
    async def api_v0_health() -> HealthResponse:
        return await health_check()

    @router.get("/runs", response_model=List[RunMetadataResponse])
    async def api_v0_runs() -> List[RunMetadataResponse]:
        return await get_runs()

    @router.get("/runs/{run_id}", response_model=RunDetailV0)
    async def api_v0_run_detail(run_id: str) -> RunDetailV0:
        meta = _load_meta_v0(run_id)
        snapshot = await get_run_snapshot_endpoint(run_id)
        return RunDetailV0(meta=meta, snapshot=snapshot)

    @router.get("/runs/{run_id}/metrics", response_model=RunMetricsV0)
    async def api_v0_run_metrics(run_id: str) -> RunMetricsV0:
        snapshot = await get_run_snapshot_endpoint(run_id)
        return RunMetricsV0(
            equity=snapshot.equity,
            realized_pnl=snapshot.realized_pnl,
            unrealized_pnl=snapshot.unrealized_pnl,
            drawdown=snapshot.drawdown,
            total_steps=snapshot.total_steps,
            total_orders=snapshot.total_orders,
            total_blocked_orders=snapshot.total_blocked_orders,
        )

    @router.get("/runs/{run_id}/equity", response_model=List[EquityPointV0])
    async def api_v0_run_equity(
        run_id: str,
        limit: int = Query(default=500, ge=1, le=5000),
    ) -> List[EquityPointV0]:
        run_dir = _run_dir_for(run_id)
        try:
            events_df = load_run_events(run_dir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"equity_not_available: {run_id}")

        if len(events_df) == 0:
            return []

        ts_col = (
            "ts_event"
            if "ts_event" in events_df.columns
            else "ts_bar"
            if "ts_bar" in events_df.columns
            else None
        )
        if ts_col is None:
            raise HTTPException(status_code=404, detail=f"equity_not_available: {run_id}")

        # Ensure chronological order if step exists, otherwise keep file order.
        if "step" in events_df.columns:
            try:
                events_df = events_df.sort_values("step")
            except Exception:
                pass

        if limit and len(events_df) > limit:
            events_df = events_df.tail(limit)

        equity_col = "equity" if "equity" in events_df.columns else None
        realized_col = (
            "realized_pnl"
            if "realized_pnl" in events_df.columns
            else ("pnl" if "pnl" in events_df.columns else None)
        )
        unrealized_col = "unrealized_pnl" if "unrealized_pnl" in events_df.columns else None
        drawdown_col = "drawdown" if "drawdown" in events_df.columns else None

        # Best-effort drawdown compute if missing and equity available.
        drawdown_series = None
        if drawdown_col is None and equity_col is not None:
            try:
                eq = events_df[equity_col].astype(float)
                running_max = eq.expanding().max()
                dd = (eq - running_max) / running_max
                drawdown_series = dd
            except Exception:
                drawdown_series = None

        def _to_float(val: Any) -> Optional[float]:
            try:
                if val is None:
                    return None
                if pd.isna(val):
                    return None
                return float(val)
            except Exception:
                return None

        points: List[EquityPointV0] = []
        for idx, row in events_df.iterrows():
            ts_val = row.get(ts_col)
            if ts_val is None:
                continue
            ts_str = str(ts_val)
            points.append(
                EquityPointV0(
                    ts=ts_str,
                    equity=_to_float(row.get(equity_col)) if equity_col else None,
                    realized_pnl=_to_float(row.get(realized_col)) if realized_col else None,
                    unrealized_pnl=_to_float(row.get(unrealized_col)) if unrealized_col else None,
                    drawdown=(
                        _to_float(row.get(drawdown_col))
                        if drawdown_col
                        else (
                            _to_float(drawdown_series.loc[idx])
                            if drawdown_series is not None
                            else None
                        )
                    ),
                )
            )

        return points

    @router.get("/runs/{run_id}/trades")
    async def api_v0_run_trades(run_id: str) -> Dict[str, Any]:
        # Optional v0: only if an explicit trades artifact exists.
        run_dir = _run_dir_for(run_id)
        trades_parquet = run_dir / "trades.parquet"
        trades_csv = run_dir / "trades.csv"
        if trades_parquet.exists() or trades_csv.exists():
            # Intentionally minimal: return raw records (best effort).
            try:
                if trades_parquet.exists():
                    df = pd.read_parquet(trades_parquet)
                else:
                    df = pd.read_csv(trades_csv)
                return {"run_id": run_id, "available": True, "rows": df.to_dict(orient="records")}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"trades_parse_error: {e}")

        raise HTTPException(status_code=404, detail=f"trades_not_available: {run_id}")

    @router.get("/runs/{run_id}/signals", response_model=SignalsResponseV0B)
    async def api_v0b_run_signals(
        run_id: str,
        limit: int = Query(default=200, ge=1, le=5000),
    ) -> SignalsResponseV0B:
        df = _events_tail_v0b(_load_events_df_v0b(run_id), limit=limit)
        items: List[SignalPointV0B] = []
        for _, row in df.iterrows():
            ts = _row_ts_v0b(row)
            if ts is None:
                continue
            items.append(
                SignalPointV0B(
                    ts=ts,
                    step=_int_or_none(row.get("step")),
                    signal=_int_or_none(row.get("signal")),
                    signal_changed=(
                        bool(row.get("signal_changed"))
                        if "signal_changed" in row and pd.notna(row.get("signal_changed"))
                        else None
                    ),
                )
            )
        return SignalsResponseV0B(run_id=run_id, asof=_asof_utc(), count=len(items), items=items)

    @router.get("/runs/{run_id}/positions", response_model=PositionsResponseV0B)
    async def api_v0b_run_positions(
        run_id: str,
        limit: int = Query(default=200, ge=1, le=5000),
    ) -> PositionsResponseV0B:
        df = _events_tail_v0b(_load_events_df_v0b(run_id), limit=limit)
        items: List[PositionPointV0B] = []
        for _, row in df.iterrows():
            ts = _row_ts_v0b(row)
            if ts is None:
                continue
            items.append(
                PositionPointV0B(
                    ts=ts,
                    step=_int_or_none(row.get("step")),
                    position_size=(
                        float(row.get("position_size"))
                        if "position_size" in row and pd.notna(row.get("position_size"))
                        else None
                    ),
                    cash=(float(row.get("cash")) if "cash" in row and pd.notna(row.get("cash")) else None),
                    equity=(
                        float(row.get("equity"))
                        if "equity" in row and pd.notna(row.get("equity"))
                        else None
                    ),
                )
            )
        return PositionsResponseV0B(run_id=run_id, asof=_asof_utc(), count=len(items), items=items)

    @router.get("/runs/{run_id}/orders", response_model=OrdersResponseV0B)
    async def api_v0b_run_orders(
        run_id: str,
        limit: int = Query(default=500, ge=1, le=5000),
        only_nonzero: bool = Query(
            default=True,
            description="Wenn true: filtert Events ohne Order-Aktivität heraus (best effort).",
        ),
    ) -> OrdersResponseV0B:
        df = _events_tail_v0b(_load_events_df_v0b(run_id), limit=limit)
        items: List[OrderPointV0B] = []
        for _, row in df.iterrows():
            ts = _row_ts_v0b(row)
            if ts is None:
                continue

            og = _int_or_none(row.get("orders_generated"))
            of = _int_or_none(row.get("orders_filled"))
            orj = _int_or_none(row.get("orders_rejected"))
            ob = _int_or_none(row.get("orders_blocked"))

            if only_nonzero:
                any_nonzero = any(v for v in [og, of, orj, ob] if v is not None and v != 0)
                if not any_nonzero:
                    continue

            items.append(
                OrderPointV0B(
                    ts=ts,
                    step=_int_or_none(row.get("step")),
                    orders_generated=og,
                    orders_filled=of,
                    orders_rejected=orj,
                    orders_blocked=ob,
                    risk_allowed=(
                        bool(row.get("risk_allowed"))
                        if "risk_allowed" in row and pd.notna(row.get("risk_allowed"))
                        else None
                    ),
                    risk_reasons=(
                        str(row.get("risk_reasons"))
                        if "risk_reasons" in row and pd.notna(row.get("risk_reasons"))
                        else None
                    ),
                )
            )
        return OrdersResponseV0B(run_id=run_id, asof=_asof_utc(), count=len(items), items=items)

    # =============================================================================
    # API v0.2 (Control Center, additive, read-only)
    # =============================================================================

    def _run_status_v02(meta: RunMetaV0, is_active: Optional[bool], last_event_time: Optional[str]) -> str:
        if is_active:
            return "active"
        if meta.ended_at:
            return "completed"
        if last_event_time:
            return "inactive"
        return "unknown"

    def _extract_tags(config_snapshot: Dict[str, Any]) -> List[str]:
        tags_val = config_snapshot.get("tags")
        if isinstance(tags_val, list):
            return [str(t) for t in tags_val if t is not None]
        return []

    def _build_run_summary_v02(run_id: str) -> RunSummaryV02:
        meta = _load_meta_v0(run_id)
        # Best-effort: derive "heartbeat" from last event time in monitoring snapshot (if available).
        last_event_time = None
        is_active = None
        try:
            snapshots = monitoring_list_runs(base_dir=runs_dir, include_inactive=True)
            for s in snapshots:
                if getattr(s, "run_id", None) == run_id:
                    is_active = bool(getattr(s, "is_active", False))
                    let = getattr(s, "last_event_time", None)
                    last_event_time = let.isoformat() if let else None
                    break
        except Exception:
            last_event_time = None

        status = _run_status_v02(meta, is_active=is_active, last_event_time=last_event_time)
        return RunSummaryV02(
            run_id=run_id,
            status=status,
            started_at=meta.started_at,
            last_heartbeat=last_event_time,
            strategy_id=meta.strategy_name,
            tags=_extract_tags(meta.config_snapshot),
            base_dir=str(runs_dir),
        )

    @router.get("/health_v02", response_model=HealthV02)
    async def api_v0_health_v02() -> HealthV02:
        now = datetime.now(timezone.utc).isoformat()
        components: Dict[str, Dict[str, Any]] = {
            "live_dashboard": {"status": "ok", "contract_version": contract_version},
            "runs_dir": {"status": "ok" if runs_dir.exists() else "missing", "path": str(runs_dir)},
        }
        return HealthV02(
            status="ok",
            contract_version=contract_version,
            server_time=now,
            last_update=now,
            components=components,
        )

    @router.get("/runs_v02", response_model=List[RunSummaryV02])
    async def api_v0_runs_v02(limit: int = Query(default=50, ge=1, le=200)) -> List[RunSummaryV02]:
        # Use existing runs listing and then enrich using meta.json.
        runs = await get_runs()
        out: List[RunSummaryV02] = []
        for r in runs[:limit]:
            try:
                meta = _load_meta_v0(r.run_id)
                status = _run_status_v02(meta, is_active=r.is_active, last_event_time=r.last_event_time)
                out.append(
                    RunSummaryV02(
                        run_id=r.run_id,
                        status=status,
                        started_at=meta.started_at,
                        last_heartbeat=r.last_event_time,
                        strategy_id=meta.strategy_name,
                        tags=_extract_tags(meta.config_snapshot),
                        base_dir=str(runs_dir),
                    )
                )
            except HTTPException:
                # If meta is missing, still return minimal info.
                out.append(
                    RunSummaryV02(
                        run_id=r.run_id,
                        status="unknown",
                        started_at=r.started_at,
                        last_heartbeat=r.last_event_time,
                        strategy_id=r.strategy_name,
                        tags=[],
                        base_dir=str(runs_dir),
                    )
                )
        return out

    def load_alerts_from_file(run_dir: Path, limit: int = 100) -> List[Dict[str, Any]]:
        alerts_path = run_dir / "alerts.jsonl"
        if not alerts_path.exists():
            return []

        alerts: List[Dict[str, Any]] = []
        try:
            with open(alerts_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        alert = json.loads(line)
                        alerts.append(alert)
                    except json.JSONDecodeError:
                        continue

            alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return alerts[:limit]
        except Exception:
            return []

    @router.get("/runs/{run_id}/detail_v02", response_model=RunDetailV02)
    async def api_v0_run_detail_v02(run_id: str) -> RunDetailV02:
        summary = _build_run_summary_v02(run_id)
        pointers = {
            "metrics": f"/api/v0/runs/{run_id}/metrics",
            "equity": f"/api/v0/runs/{run_id}/equity",
            "signals": f"/api/v0/runs/{run_id}/signals",
            "positions": f"/api/v0/runs/{run_id}/positions",
            "orders": f"/api/v0/runs/{run_id}/orders",
            "alerts": f"/runs/{run_id}/alerts",
            "events": f"/api/v0/runs/{run_id}/events",
        }
        alerts_summary: Dict[str, Any] = {"count": 0}
        try:
            run_dir = _run_dir_for(run_id)
            alerts = load_alerts_from_file(run_dir, limit=50)
            alerts_summary["count"] = len(alerts)
            if alerts:
                alerts_summary["last_severity"] = alerts[-1].get("severity")
        except Exception:
            pass
        meta = _load_meta_v0(run_id)
        return RunDetailV02(
            summary=summary,
            pointers=pointers,
            alerts_summary=alerts_summary,
            config_snapshot=meta.config_snapshot,
        )

    def _events_items_v02(run_id: str, since_seq: int, limit: int) -> EventsPollResponseV02:
        df = _load_events_df_v0b(run_id)
        if len(df) == 0:
            return EventsPollResponseV02(
                run_id=run_id,
                asof=_asof_utc(),
                next_seq=max(since_seq, 0),
                count=0,
                items=[],
            )
        if "step" in df.columns:
            try:
                df = df.sort_values("step")
            except Exception:
                pass

        start = max(int(since_seq), 0)
        end = start + int(limit)
        if start >= len(df):
            return EventsPollResponseV02(
                run_id=run_id,
                asof=_asof_utc(),
                next_seq=start,
                count=0,
                items=[],
            )

        slice_df = df.iloc[start:end]
        items: List[EventItemV02] = []
        for i, (_, row) in enumerate(slice_df.iterrows(), start=start):
            ts = _row_ts_v0b(row) or _asof_utc()
            step = _int_or_none(row.get("step"))
            signal = _int_or_none(row.get("signal"))
            pos = row.get("position_size")
            og = _int_or_none(row.get("orders_generated"))
            of = _int_or_none(row.get("orders_filled"))
            ob = _int_or_none(row.get("orders_blocked"))
            risk_allowed = row.get("risk_allowed")

            level = "info"
            if (risk_allowed is False) or (ob is not None and ob > 0):
                level = "warning"

            msg = (
                f"step={step} signal={signal} position_size={pos} "
                f"orders_generated={og} orders_filled={of} orders_blocked={ob}"
            )
            items.append(
                EventItemV02(
                    seq=i,
                    ts=ts,
                    level=level,
                    component="run",
                    msg=msg,
                    run_id=run_id,
                )
            )

        next_seq = start + len(items)
        return EventsPollResponseV02(
            run_id=run_id,
            asof=_asof_utc(),
            next_seq=next_seq,
            count=len(items),
            items=items,
        )

    def _sse_format_event(item: EventItemV02) -> str:
        data = item.model_dump()
        return f"event: pt_event\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    @router.get("/runs/{run_id}/events")
    async def api_v0_run_events(
        request: Request,
        run_id: str,
        since_seq: int = Query(default=0, ge=0),
        limit: int = Query(default=200, ge=1, le=2000),
        follow: bool = Query(default=False, description="If true: keep stream open (bounded)."),
        max_seconds: int = Query(default=30, ge=1, le=600),
        sse: bool = Query(default=False, description="If true: force SSE (text/event-stream)."),
    ) -> Any:
        wants_sse = sse or ("text/event-stream" in (request.headers.get("accept") or ""))
        if not wants_sse:
            return _events_items_v02(run_id=run_id, since_seq=since_seq, limit=limit).model_dump()

        def gen() -> Iterator[str]:
            start_t = time.monotonic()
            cur = int(since_seq)

            batch = _events_items_v02(run_id=run_id, since_seq=cur, limit=limit)
            for it in batch.items:
                yield _sse_format_event(it)
                cur = it.seq + 1

            if not follow:
                return

            last_ping = time.monotonic()
            while True:
                now = time.monotonic()
                if now - start_t >= float(max_seconds):
                    return

                if now - last_ping >= 5.0:
                    yield ": ping\n\n"
                    last_ping = now

                batch = _events_items_v02(run_id=run_id, since_seq=cur, limit=limit)
                if batch.items:
                    for it in batch.items:
                        yield _sse_format_event(it)
                        cur = it.seq + 1

                time.sleep(0.5)

        return StreamingResponse(gen(), media_type="text/event-stream")

    return router
