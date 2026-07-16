#!/usr/bin/env python3
"""Materialize offline read-only bundles for the market visual operator surface v1.

Reads a real offline historical futures panel (OKX linear perpetual, non-Bitcoin) and
materializes deterministic, non-authorizing read-model bundles consumed by the SSR
``/market`` dashboard:

* ``futures_ohlcv/futures_ohlcv.json``   — ``market_futures_ohlcv_readmodel.v0``
* ``ranking_funnel/ranking_funnel.json`` — ``market_ranking_funnel_readmodel.v0``
* ``f5_dashboard/dashboard.json``        — ``futures_read_only_market_dashboard_v0``
* ``SOURCE_PROVENANCE.json``             — documents sources, digests, generated_at
* ``economic_evidence_binding.json``     — absolute pointers + digests for PR5242 evidence
* ``MANIFEST.sha256``                    — sha256 of every emitted file

This is a READ-ONLY display materialization. It never invents metrics, never emits spot
or synthetic fallbacks, and excludes Bitcoin instruments. Missing economic evidence files
are recorded honestly as ``provenance_missing`` rather than fabricated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

READMODEL_OHLCV_ID = "market_futures_ohlcv_readmodel.v0"
READMODEL_RANKING_ID = "market_ranking_funnel_readmodel.v0"
READMODEL_F5_ID = "futures_read_only_market_dashboard_v0"

DEFAULT_TIMEFRAME = "1h"
MAX_BARS_PER_SYMBOL = 120
SHORTLIST_TOP_N = 50
SELECTED_TOP_N = 50

ENV_PANEL_PATH = "PEAK_TRADE_MARKET_VISUAL_OPERATOR_PANEL_PATH"
ENV_ECONOMIC_EVIDENCE_DIR = "PEAK_TRADE_MARKET_VISUAL_OPERATOR_ECONOMIC_EVIDENCE_DIR"

_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_PANEL_PATH = (
    _ARCHIVE_ROOT
    / "datasets/admissible_futures"
    / "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_historical_2024_v1"
    / "v1/panel/normalized_panel_bars.json"
)
DEFAULT_ECONOMIC_EVIDENCE_DIR = (
    _ARCHIVE_ROOT
    / "research"
    / "full_canonical_system_economic_evidence_generation_v1_offline_execution_v0_20260716T015033Z"
)

ECONOMIC_EVIDENCE_KEY_FILES = (
    "compact_decision_funnel.json",
    "baseline_metrics.json",
    "cost_attribution.json",
    "economic_validity_evaluation_v1.json",
    "final_report.json",
    "economic_viability_evidence_v1.json",
)

_BITCOIN_TOKENS = ("BTC", "XBT")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    parts = instrument_id.upper().split(":")
    base = parts[2] if len(parts) >= 3 else instrument_id.upper()
    return any(token in base for token in _BITCOIN_TOKENS)


def _parse_instrument_id(instrument_id: str) -> dict[str, str]:
    """Parse ``okx:linear_perpetual:ETH:USDT:USDT:perp`` into honest partial metadata."""
    parts = instrument_id.split(":")
    exchange = parts[0] if len(parts) >= 1 else ""
    market_type = parts[1] if len(parts) >= 2 else ""
    base = parts[2] if len(parts) >= 3 else ""
    quote = parts[3] if len(parts) >= 4 else ""
    settle = parts[4] if len(parts) >= 5 else ""
    return {
        "instrument_id": instrument_id,
        "exchange": exchange,
        "market_type": market_type,
        "symbol": f"{base}{quote}",
        "base_currency": base,
        "quote_currency": quote,
        "settle_currency": settle,
    }


def _symbol_from_instrument_id(instrument_id: str) -> str:
    return _parse_instrument_id(instrument_id)["symbol"]


def _to_float(value: Any) -> float:
    return float(value)


def _write_json_deterministic(path: Path, payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return _sha256_bytes(text.encode("utf-8"))


def _load_panel(panel_path: Path) -> list[dict[str, Any]]:
    raw = json.loads(panel_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"panel payload must be a list of bar records: {panel_path}")
    return [row for row in raw if isinstance(row, dict)]


def _group_bars_by_symbol(
    records: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], int, int]:
    """Group panel bar records by governed symbol, dropping Bitcoin instruments."""
    by_symbol: dict[str, list[dict[str, Any]]] = {}
    dropped_bitcoin = 0
    for record in records:
        instrument_id = str(record.get("instrument_id") or "")
        if not instrument_id:
            continue
        if _is_bitcoin_instrument(instrument_id):
            dropped_bitcoin += 1
            continue
        symbol = _symbol_from_instrument_id(instrument_id)
        if not symbol:
            continue
        by_symbol.setdefault(symbol, []).append(record)

    normalized: dict[str, list[dict[str, Any]]] = {}
    for symbol, rows in by_symbol.items():
        rows_sorted = sorted(rows, key=lambda r: str(r.get("timestamp_utc") or ""))
        bars = [
            {
                "ts": str(r.get("timestamp_utc") or ""),
                "open": _to_float(r.get("open")),
                "high": _to_float(r.get("high")),
                "low": _to_float(r.get("low")),
                "close": _to_float(r.get("close")),
                "volume": _to_float(r.get("volume")),
            }
            for r in rows_sorted
        ]
        normalized[symbol] = bars[-MAX_BARS_PER_SYMBOL:]
    return normalized, dropped_bitcoin, len(records)


def _build_futures_ohlcv_payload(
    series_by_symbol: dict[str, list[dict[str, Any]]],
    *,
    generated_at: str,
    source_identifier: str,
) -> dict[str, Any]:
    series = {
        symbol: {"timeframe": DEFAULT_TIMEFRAME, "bars": series_by_symbol[symbol]}
        for symbol in sorted(series_by_symbol)
    }
    return {
        "readmodel_id": READMODEL_OHLCV_ID,
        "generated_at_iso": generated_at,
        "source": source_identifier,
        "stale": False,
        "stale_reason": None,
        "non_authorizing": True,
        "series": series,
    }


def _build_ranking_rows(
    series_by_symbol: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Rank symbols by last-bar volume (display-only), with normalized display_score."""
    volume_by_symbol: dict[str, float] = {}
    for symbol, bars in series_by_symbol.items():
        if not bars:
            continue
        volume_by_symbol[symbol] = float(bars[-1].get("volume") or 0.0)

    if not volume_by_symbol:
        return []

    max_vol = max(volume_by_symbol.values())
    min_vol = min(volume_by_symbol.values())
    span = max_vol - min_vol

    # Deterministic ordering: volume descending, then symbol ascending as tie-breaker.
    ordered = sorted(volume_by_symbol.items(), key=lambda kv: (-kv[1], kv[0]))
    rows: list[dict[str, Any]] = []
    for rank, (symbol, volume) in enumerate(ordered, start=1):
        display_score = 1.0 if span == 0 else round((volume - min_vol) / span, 6)
        rows.append(
            {
                "row_id": f"rank_{rank:03d}_{symbol}",
                "symbol": symbol,
                "rank": rank,
                "display_score": display_score,
            }
        )
    return rows


def _build_ranking_funnel_payload(
    ranking_rows: list[dict[str, Any]],
    *,
    generated_at: str,
    source_identifier: str,
) -> dict[str, Any]:
    universe = list(ranking_rows)
    shortlist = ranking_rows[:SHORTLIST_TOP_N]
    selected = ranking_rows[:SELECTED_TOP_N]
    return {
        "readmodel_id": READMODEL_RANKING_ID,
        "generated_at_iso": generated_at,
        "source": source_identifier,
        "stale": False,
        "stale_reason": None,
        "non_authorizing": True,
        "stages": {
            "universe": universe,
            "shortlist": shortlist,
            "selected": selected,
        },
    }


def _build_f5_dashboard_payload(
    primary_instrument_id: str,
    *,
    generated_at: str,
    source_identifier: str,
) -> dict[str, Any]:
    meta = _parse_instrument_id(primary_instrument_id)
    f1 = {
        "status": "futures_metadata_partial",
        "instrument_id": meta["instrument_id"],
        "exchange": meta["exchange"],
        "market_type": meta["market_type"],
        "symbol": meta["symbol"],
        "base_currency": meta["base_currency"],
        "quote_currency": meta["quote_currency"],
        "settle_currency": meta["settle_currency"],
        "contract_type": "linear_perpetual",
        "perpetual": "true",
        "metadata_source": source_identifier,
        "provenance_reference": source_identifier,
    }
    return {
        "schema_version": "futures_read_only_market_dashboard.v0",
        "readmodel_id": READMODEL_F5_ID,
        "non_authorizing": True,
        "display_status": "ready",
        "summary_line": (
            "Offline historical panel metadata (futures perpetual OKX) — read-only, "
            "non-authorizing; provenance/backtest/risk sections incomplete."
        ),
        "overall_status": "futures_metadata_partial",
        "env_name": "okx_linear_perpetual_offline_panel",
        "generated_at_iso": generated_at,
        "f1": f1,
        "f2": {"status": "provenance_missing"},
        "f3": {"status": "backtest_realism_incomplete"},
        "f4": {"status": "risk_safety_incomplete"},
    }


def _build_economic_evidence_binding(
    economic_dir: Path,
    *,
    generated_at: str,
) -> dict[str, Any]:
    files: dict[str, Any] = {}
    any_present = False
    for name in ECONOMIC_EVIDENCE_KEY_FILES:
        candidate = economic_dir / name
        if candidate.is_file():
            any_present = True
            files[name] = {
                "path": str(candidate),
                "sha256": _sha256_file(candidate),
                "status": "present",
            }
        else:
            files[name] = {
                "path": str(candidate),
                "sha256": None,
                "status": "provenance_missing",
            }
    return {
        "binding_id": "market_visual_operator_economic_evidence_binding_v1",
        "generated_at": generated_at,
        "economic_evidence_dir": str(economic_dir),
        "economic_evidence_dir_present": economic_dir.is_dir(),
        "provenance_status": "present" if any_present else "provenance_missing",
        "non_authorizing": True,
        "note": (
            "Absolute pointers and digests only — no economic metrics are copied or "
            "invented. Consumers read the referenced files directly (read-only)."
        ),
        "files": files,
    }


def _write_manifest(output_root: Path, digests: dict[str, str]) -> None:
    lines = [f"{digests[name]}  {name}" for name in sorted(digests)]
    (output_root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def materialize(output_root: Path, *, panel_path: Path, economic_dir: Path) -> dict[str, Any]:
    if not panel_path.is_file():
        raise FileNotFoundError(f"panel path not found: {panel_path}")

    generated_at = _utc_now_iso()
    panel_digest = _sha256_file(panel_path)
    source_identifier = f"historical_panel_offline:{panel_digest[:16]}"

    records = _load_panel(panel_path)
    series_by_symbol, dropped_bitcoin, total_records = _group_bars_by_symbol(records)
    if not series_by_symbol:
        raise ValueError("no eligible (non-Bitcoin) instruments found in panel")

    ranking_rows = _build_ranking_rows(series_by_symbol)
    primary_symbol = ranking_rows[0]["symbol"] if ranking_rows else ""
    primary_instrument_id = ""
    for record in records:
        instrument_id = str(record.get("instrument_id") or "")
        if instrument_id and _symbol_from_instrument_id(instrument_id) == primary_symbol:
            primary_instrument_id = instrument_id
            break

    output_root.mkdir(parents=True, exist_ok=True)

    digests: dict[str, str] = {}

    futures_payload = _build_futures_ohlcv_payload(
        series_by_symbol,
        generated_at=generated_at,
        source_identifier=source_identifier,
    )
    futures_path = output_root / "futures_ohlcv" / "futures_ohlcv.json"
    digests["futures_ohlcv/futures_ohlcv.json"] = _write_json_deterministic(
        futures_path, futures_payload
    )

    ranking_payload = _build_ranking_funnel_payload(
        ranking_rows,
        generated_at=generated_at,
        source_identifier=source_identifier,
    )
    ranking_path = output_root / "ranking_funnel" / "ranking_funnel.json"
    digests["ranking_funnel/ranking_funnel.json"] = _write_json_deterministic(
        ranking_path, ranking_payload
    )

    f5_payload = _build_f5_dashboard_payload(
        primary_instrument_id,
        generated_at=generated_at,
        source_identifier=source_identifier,
    )
    f5_path = output_root / "f5_dashboard" / "dashboard.json"
    digests["f5_dashboard/dashboard.json"] = _write_json_deterministic(f5_path, f5_payload)

    economic_binding = _build_economic_evidence_binding(economic_dir, generated_at=generated_at)
    economic_path = output_root / "economic_evidence_binding.json"
    digests["economic_evidence_binding.json"] = _write_json_deterministic(
        economic_path, economic_binding
    )

    provenance = {
        "generated_at": generated_at,
        "non_authorizing": True,
        "read_only": True,
        "bitcoin_excluded": True,
        "sources": {
            "historical_panel": {
                "path": str(panel_path),
                "sha256": panel_digest,
                "records_total": total_records,
                "records_dropped_bitcoin": dropped_bitcoin,
            },
            "economic_evidence_dir": {
                "path": str(economic_dir),
                "present": economic_dir.is_dir(),
            },
        },
        "materialized_bundles": {
            "futures_ohlcv": "futures_ohlcv/futures_ohlcv.json",
            "ranking_funnel": "ranking_funnel/ranking_funnel.json",
            "f5_dashboard": "f5_dashboard/dashboard.json",
            "economic_evidence_binding": "economic_evidence_binding.json",
        },
        "symbol_count": len(series_by_symbol),
        "primary_symbol": primary_symbol,
        "primary_instrument_id": primary_instrument_id,
        "timeframe": DEFAULT_TIMEFRAME,
        "source_identifier": source_identifier,
    }
    provenance_path = output_root / "SOURCE_PROVENANCE.json"
    digests["SOURCE_PROVENANCE.json"] = _write_json_deterministic(provenance_path, provenance)

    _write_manifest(output_root, digests)

    bar_counts = {symbol: len(bars) for symbol, bars in series_by_symbol.items()}
    return {
        "output_root": str(output_root),
        "symbol_count": len(series_by_symbol),
        "primary_symbol": primary_symbol,
        "bar_counts": bar_counts,
        "dropped_bitcoin": dropped_bitcoin,
        "digests": digests,
        "futures_ohlcv_path": str(futures_path),
        "ranking_funnel_path": str(ranking_path),
        "f5_dashboard_path": str(f5_path),
        "economic_binding_path": str(economic_path),
        "provenance_path": str(provenance_path),
    }


def _resolve_path(env_name: str, default: Path) -> Path:
    raw = os.environ.get(env_name)
    if raw is not None and raw.strip():
        return Path(raw).expanduser()
    return default


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", required=True, help="Directory to write bundles into.")
    args = parser.parse_args(argv)

    panel_path = _resolve_path(ENV_PANEL_PATH, DEFAULT_PANEL_PATH)
    economic_dir = _resolve_path(ENV_ECONOMIC_EVIDENCE_DIR, DEFAULT_ECONOMIC_EVIDENCE_DIR)
    output_root = Path(args.output_root).expanduser()

    result = materialize(output_root, panel_path=panel_path, economic_dir=economic_dir)

    bar_counts = result["bar_counts"]
    min_bars = min(bar_counts.values()) if bar_counts else 0
    max_bars = max(bar_counts.values()) if bar_counts else 0

    print(f"output_root: {result['output_root']}")
    print(f"symbols: {result['symbol_count']} (bitcoin dropped bars: {result['dropped_bitcoin']})")
    print(f"primary_symbol: {result['primary_symbol']}")
    print(f"bars per symbol: min={min_bars} max={max_bars}")
    print(f"futures_ohlcv: {result['futures_ohlcv_path']}")
    print(f"ranking_funnel: {result['ranking_funnel_path']}")
    print(f"f5_dashboard: {result['f5_dashboard_path']}")
    print(f"economic_evidence_binding: {result['economic_binding_path']}")
    print(f"provenance: {result['provenance_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
