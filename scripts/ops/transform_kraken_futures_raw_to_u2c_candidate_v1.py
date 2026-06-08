#!/usr/bin/env python3
"""U5D: offline Kraken Futures raw payload → U2c candidate validation (no network).

Reads durable U5C raw instruments/tickers + U5B probe report; emits validation artifact only.
Not snapshot intake, loader, readmodel write, dashboard wiring, truth-GO, or trading.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROBE_SCRIPT = _REPO_ROOT / "scripts/ops/probe_kraken_futures_public_market_data_v1.py"


def _load_probe_mod() -> Any:
    spec = importlib.util.spec_from_file_location("_kf_probe", _PROBE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load probe module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_PROBE = _load_probe_mod()
is_futures_eligible_instrument = _PROBE.is_futures_eligible_instrument
is_ineligible_spot_symbol = _PROBE.is_ineligible_spot_symbol

CONFIRM_TOKEN = "CONFIRM_U5D_OFFLINE_TRANSFORM_VALIDATION_V1"
SCHEMA = "u5d_u2c_candidate_validation_v1"
PROVIDER = "kraken_futures"
EXCHANGE = "kraken_futures"
SOURCE_STAGE = "market_data_view_only"
TOP_N = 20


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_num(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _die(f"ERR: cannot read JSON {path}: {exc}")
    if not isinstance(data, dict):
        _die(f"ERR: expected JSON object in {path}")
    return data


def _contract_type(inst: Mapping[str, Any]) -> str:
    raw = str(inst.get("type") or inst.get("contract_type") or "").lower()
    if "inverse" in raw:
        return "future"
    if "flexible" in raw or "perpetual" in raw:
        return "perpetual"
    return raw or "unknown"


def _map_instrument_row(
    inst: Mapping[str, Any],
    tick: Optional[Mapping[str, Any]],
    *,
    fetched_at: str,
) -> Dict[str, Any]:
    symbol = str(inst.get("symbol") or "")
    missing: List[str] = []
    degraded: List[str] = []

    last = _parse_num(tick.get("last")) if tick else None
    mark = _parse_num(tick.get("markPrice")) if tick else None
    index_px = _parse_num(tick.get("indexPrice")) if tick else None
    vol24h = _parse_num(tick.get("vol24h")) if tick else None
    bid = _parse_num(tick.get("bid")) if tick else None
    ask = _parse_num(tick.get("ask")) if tick else None
    funding = _parse_num(tick.get("fundingRate")) if tick else None
    oi = _parse_num(tick.get("openInterest")) if tick else None

    display_price = last
    price_source = "last"
    if display_price is None and mark is not None:
        display_price = mark
        price_source = "markPrice"
        degraded.append("last_missing_markPrice_fallback")
    elif display_price is None:
        missing.append("last_price")
        price_source = "unknown"

    if vol24h is None or vol24h <= 0:
        missing.append("vol24h")
    if bid is None or ask is None:
        missing.append("bid_ask")
    if funding is None:
        missing.append("funding_rate")
    if oi is None:
        missing.append("open_interest")

    expiry = inst.get("lastTradingTime")
    if expiry in (None, ""):
        expiry = None

    spread: Optional[float] = None
    if bid is not None and ask is not None:
        spread = ask - bid

    return {
        "provider": PROVIDER,
        "exchange": EXCHANGE,
        "instrument_id": symbol,
        "symbol": symbol,
        "contract_type": _contract_type(inst),
        "market_type": _contract_type(inst),
        "base_currency": inst.get("base"),
        "quote_currency": inst.get("quote"),
        "expiry": expiry,
        "active": bool(inst.get("tradeable", False)),
        "provider_tradable_display_only": bool(inst.get("tradeable", False)),
        "tick_size": inst.get("tickSize"),
        "contract_size": inst.get("contractSize"),
        "last_price": last,
        "mark_price": mark,
        "index_price": index_px,
        "display_price": display_price,
        "display_price_source": price_source,
        "vol24h": vol24h,
        "bid": bid,
        "ask": ask,
        "spread": spread,
        "funding_rate": funding,
        "open_interest": oi,
        "fetched_at": fetched_at,
        "missing_fields": missing,
        "degraded_fields": degraded,
        "not_selected": True,
        "not_signal": True,
        "not_truth_go": True,
        "not_tradable_authority": True,
    }


def _rank_key(row: Mapping[str, Any]) -> Tuple[int, float, str]:
    vol = row.get("vol24h")
    vol_sort = float(vol) if isinstance(vol, (int, float)) and vol > 0 else -1.0
    has_vol = 1 if vol_sort > 0 else 0
    return (-has_vol, -vol_sort, str(row.get("symbol") or ""))


def build_top20_ranking_candidate(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    eligible = [
        r
        for r in rows
        if r.get("active") and isinstance(r.get("vol24h"), (int, float)) and r["vol24h"] > 0
    ]
    ranked = sorted(eligible, key=_rank_key)
    out: List[Dict[str, Any]] = []
    for rank, row in enumerate(ranked[:TOP_N], start=1):
        out.append(
            {
                "rank": rank,
                "symbol": row.get("symbol"),
                "vol24h": row.get("vol24h"),
                "display_price": row.get("display_price"),
                "display_price_source": row.get("display_price_source"),
                "ranking_method": "vol24h_liquidity_desc_symbol_tiebreak",
                "preview_only": False,
                "validation_only": True,
                "not_selected": True,
                "not_signal": True,
                "not_truth_go": True,
                "not_tradable_authority": True,
                "not_alphabetical_preview": True,
            }
        )
    return out


def run_offline_transform_validation(
    *,
    confirm: str,
    raw_instruments: Path,
    raw_tickers: Path,
    probe_report: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    if confirm != CONFIRM_TOKEN:
        _die("ERR: confirm token required for offline transform validation")
    for path in (raw_instruments, raw_tickers, probe_report):
        if not path.is_file():
            _die(f"ERR: required input missing: {path}")

    inst_body = _load_json(raw_instruments)
    tick_body = _load_json(raw_tickers)
    report = _load_json(probe_report)

    if report.get("schema") != "kraken_futures_public_market_data_probe_report_v1":
        _die("ERR: probe report schema mismatch")

    fetched_at = str(report.get("fetched_at") or "")
    if not fetched_at:
        _die("ERR: probe report missing fetched_at")

    instruments = inst_body.get("instruments")
    tickers = tick_body.get("tickers")
    if not isinstance(instruments, list) or not instruments:
        _die("ERR: instruments[] missing or empty")
    if not isinstance(tickers, list) or not tickers:
        _die("ERR: tickers[] missing or empty")

    inst_by_symbol: Dict[str, Mapping[str, Any]] = {}
    rejected: List[Dict[str, str]] = []
    for inst in instruments:
        if not isinstance(inst, Mapping):
            continue
        sym = str(inst.get("symbol") or "")
        if not sym:
            rejected.append({"symbol": sym, "reason": "MISSING_SYMBOL"})
            continue
        if is_ineligible_spot_symbol(sym):
            rejected.append({"symbol": sym, "reason": "INELIGIBLE_SPOT_SYMBOL"})
            continue
        if not is_futures_eligible_instrument(inst):
            rejected.append({"symbol": sym, "reason": "NON_FUTURES_INSTRUMENT"})
            continue
        if inst.get("isExpired") is True:
            rejected.append({"symbol": sym, "reason": "EXPIRED_INSTRUMENT"})
            continue
        if not inst.get("tradeable", False):
            rejected.append({"symbol": sym, "reason": "NOT_TRADEABLE"})
            continue
        inst_by_symbol[sym] = inst

    tick_by_symbol: Dict[str, Mapping[str, Any]] = {}
    orphan_tickers: List[Dict[str, str]] = []
    for tick in tickers:
        if not isinstance(tick, Mapping):
            continue
        sym = str(tick.get("symbol") or tick.get("tag") or "")
        if not sym:
            continue
        tick_by_symbol[sym] = tick
        if sym not in inst_by_symbol:
            orphan_tickers.append({"symbol": sym, "reason": "ORPHAN_TICKER_NO_INSTRUMENT"})

    packet_candidates: List[Dict[str, Any]] = []
    unmatched_instruments: List[str] = []
    for sym, inst in sorted(inst_by_symbol.items()):
        tick = tick_by_symbol.get(sym)
        if tick is None:
            unmatched_instruments.append(sym)
        packet_candidates.append(_map_instrument_row(inst, tick, fetched_at=fetched_at))

    top20 = build_top20_ranking_candidate(packet_candidates)

    probe_preview = report.get("top20_candidate_preview") or []
    probe_preview_symbols = [
        str(p.get("symbol")) for p in probe_preview if isinstance(p, Mapping) and p.get("symbol")
    ]
    governed_symbols = [str(t.get("symbol")) for t in top20]

    artifact: Dict[str, Any] = {
        "schema": SCHEMA,
        "source_stage": SOURCE_STAGE,
        "provider": PROVIDER,
        "transform_validation_only": True,
        "GOVERNED_SNAPSHOT_ACCEPTED": False,
        "SNAPSHOT_INTAKE_EXECUTED": False,
        "LOADER_RUN_EXECUTED": False,
        "READMODEL_WRITE_EXECUTED": False,
        "DASHBOARD_WIRING_EXECUTED": False,
        "LIVE_AUTHORIZED": False,
        "PREFLIGHT_LIFT_AUTHORIZED": False,
        "OPERATOR_TRUTH_GO_GRANTED": False,
        "selected_tradable_future_created": False,
        "auth_used": False,
        "no_secrets": True,
        "no_orders": True,
        "fetched_at": fetched_at,
        "input_checksums": {
            "raw_instruments_sha256": _sha256_file(raw_instruments),
            "raw_tickers_sha256": _sha256_file(raw_tickers),
            "probe_report_sha256": _sha256_file(probe_report),
        },
        "input_paths": {
            "raw_instruments": str(raw_instruments.resolve()),
            "raw_tickers": str(raw_tickers.resolve()),
            "probe_report": str(probe_report.resolve()),
        },
        "join": {
            "join_key": "symbol",
            "instruments_eligible_count": len(inst_by_symbol),
            "tickers_count": len(tick_by_symbol),
            "matched_count": len(inst_by_symbol) - len(unmatched_instruments),
            "unmatched_instruments": unmatched_instruments,
            "orphan_tickers": orphan_tickers,
            "rejected_symbols": rejected,
        },
        "packet_candidates": packet_candidates,
        "top20_ranking_candidate": top20,
        "ranking_notes": {
            "primary_sort": "vol24h_desc",
            "price_fallback": "markPrice_when_last_missing",
            "tie_breaker": "symbol_asc",
            "alphabetical_preview_forbidden": True,
            "u5b_alphabetical_preview_not_reused": governed_symbols != probe_preview_symbols,
        },
        "safety_markers": {
            "TRANSFORM_VALIDATION_ONLY": True,
            "NOT_TRADING": True,
            "NOT_TRUTH_GO": True,
            "NOT_SELECTED_TRADABLE_FUTURE": True,
            "NOT_SNAPSHOT_INTAKE": True,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    out_json = output_dir / "u5d_u2c_candidate_validation.v1.json"
    out_json.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary_lines = [
        "# U5D Offline Transform Validation Summary",
        "",
        f"- schema: `{SCHEMA}`",
        f"- source_stage: `{SOURCE_STAGE}`",
        f"- eligible instruments: {len(inst_by_symbol)}",
        f"- matched tickers: {len(inst_by_symbol) - len(unmatched_instruments)}",
        f"- orphan tickers: {len(orphan_tickers)}",
        f"- rejected symbols: {len(rejected)}",
        f"- top20 candidate rows: {len(top20)}",
        f"- GOVERNED_SNAPSHOT_ACCEPTED: false",
        f"- transform_validation_only: true",
        "",
        "This artifact is validation-only — not governed snapshot acceptance.",
    ]
    (output_dir / "transform_summary.md").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )

    _emit_machine_lines(artifact)
    return artifact


def _emit_machine_lines(artifact: Mapping[str, Any]) -> None:
    join = artifact.get("join") or {}
    lines = [
        "TRANSFORM_VALIDATION_ONLY=true",
        "NOT_TRADING=true",
        "NOT_TRUTH_GO=true",
        "NOT_SELECTED_TRADABLE_FUTURE=true",
        "GOVERNED_SNAPSHOT_ACCEPTED=false",
        "SNAPSHOT_INTAKE_EXECUTED=false",
        "LOADER_RUN_EXECUTED=false",
        "READMODEL_WRITE_EXECUTED=false",
        "DASHBOARD_WIRING_EXECUTED=false",
        f"SOURCE_STAGE={SOURCE_STAGE}",
        f"INSTRUMENTS_ELIGIBLE={join.get('instruments_eligible_count', 0)}",
        f"MATCHED_COUNT={join.get('matched_count', 0)}",
        f"TOP20_COUNT={len(artifact.get('top20_ranking_candidate') or [])}",
        f"ORPHAN_TICKERS={len(join.get('orphan_tickers') or [])}",
    ]
    for line in lines:
        print(line)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="U5D offline Kraken raw → U2c candidate validation (no network)."
    )
    parser.add_argument("--raw-instruments", type=Path, required=True)
    parser.add_argument("--raw-tickers", type=Path, required=True)
    parser.add_argument("--probe-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--confirm-offline-transform-validation",
        required=True,
        choices=[CONFIRM_TOKEN],
        help=f"Must be {CONFIRM_TOKEN!r}.",
    )
    ns = parser.parse_args(argv)
    try:
        run_offline_transform_validation(
            confirm=ns.confirm_offline_transform_validation,
            raw_instruments=ns.raw_instruments,
            raw_tickers=ns.raw_tickers,
            probe_report=ns.probe_report,
            output_dir=ns.output_dir,
        )
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
