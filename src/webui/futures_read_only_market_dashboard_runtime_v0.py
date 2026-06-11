"""F5 Futures Read-only Market Dashboard runtime (SSR-only, offline/fixture)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ENV_ENABLED = "PEAK_TRADE_F5_MARKET_DASHBOARD_ENABLED"
ENV_BUNDLE_ROOT = "PEAK_TRADE_F5_MARKET_DASHBOARD_BUNDLE_ROOT"

READMODEL_ID = "futures_read_only_market_dashboard_v0"

STATUS_MODEL_VALUES: tuple[str, ...] = (
    "spot_only",
    "generic_market",
    "metadata_label_only",
    "futures_metadata_missing",
    "futures_metadata_partial",
    "provenance_missing",
    "provenance_partial",
    "backtest_realism_incomplete",
    "risk_safety_incomplete",
    "testnet_candidate_only",
    "unsupported_for_live",
)

KRAKEN_FUTURES_TESTNET_ENV_NAME = "kraken_futures_testnet"

F1_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "exchange",
    "market_type",
    "symbol",
    "base_currency",
    "quote_currency",
    "settle_currency",
    "contract_type",
    "perpetual",
    "contract_size",
    "tick_size",
    "lot_size",
    "max_leverage",
    "margin_modes",
    "liquidation_model_status",
    "metadata_source",
    "provenance_reference",
)

F2_FIELDS: tuple[str, ...] = (
    "data_source",
    "fetch_mode",
    "cache_status",
    "last_price_availability",
    "mark_price_availability",
    "index_price_availability",
    "funding_rate_availability",
    "freshness_status",
    "provenance_reference",
)

F3_FIELDS: tuple[str, ...] = (
    "realism_status",
    "fee_model_status",
    "slippage_model_status",
    "funding_model_status",
    "margin_model_status",
    "liquidation_model_status",
    "notional_exposure_status",
    "stress_coverage_status",
)

F4_FIELDS: tuple[str, ...] = (
    "risk_gate_status",
    "safety_guard_status",
    "kill_switch_status",
    "live_risk_limits_status",
    "notional_exposure_status",
    "leverage_status",
    "margin_usage_status",
    "liquidation_distance_status",
    "funding_risk_status",
)


def enabled_explicitly_on() -> bool:
    raw = os.environ.get(ENV_ENABLED)
    return raw is not None and raw.strip() == "1"


def resolved_bundle_root_or_none() -> Path | None:
    raw = os.environ.get(ENV_BUNDLE_ROOT)
    if raw is None or not str(raw).strip():
        return None
    path = Path(raw).expanduser()
    try:
        path = path.resolve(strict=True)
    except OSError:
        return None
    if not path.is_dir():
        return None
    return path


def _authority_boundaries() -> dict[str, bool]:
    return {
        "provider_truth": False,
        "dashboard_truth": False,
        "trading_readiness": False,
        "selected_future_truth": False,
        "execution_readiness": False,
        "liquidity_truth": False,
        "slippage_truth": False,
        "depth_truth": False,
    }


def _missing_field_rows(fields: tuple[str, ...]) -> list[dict[str, str]]:
    return [{"field": name, "value": "missing", "display_status": "missing"} for name in fields]


def _normalize_section(
    raw: object,
    *,
    fields: tuple[str, ...],
    default_status: str,
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {
            "status": default_status,
            "rows": _missing_field_rows(fields),
        }
    status = str(raw.get("status") or default_status)
    rows: list[dict[str, str]] = []
    for name in fields:
        value = raw.get(name)
        if value is None or str(value).strip() == "":
            display = "missing"
            cell = "missing"
        else:
            display = "present"
            cell = str(value)
        rows.append({"field": name, "value": cell, "display_status": display})
    return {"status": status, "rows": rows}


def _fail_closed_context(
    *, gate_enabled: bool, display_status: str, summary: str
) -> dict[str, Any]:
    ctx: dict[str, Any] = {
        "gate_enabled": gate_enabled,
        "display_status": display_status,
        "readmodel_id": READMODEL_ID,
        "non_authorizing": True,
        "summary_line": summary,
        "overall_status": "futures_metadata_missing",
        "env_name": "",
        "kraken_futures_testnet_label": False,
        "status_model_values": list(STATUS_MODEL_VALUES),
        "authority": _authority_boundaries(),
        "f1": _normalize_section(None, fields=F1_FIELDS, default_status="futures_metadata_missing"),
        "f2": _normalize_section(None, fields=F2_FIELDS, default_status="provenance_missing"),
        "f3": _normalize_section(
            None, fields=F3_FIELDS, default_status="backtest_realism_incomplete"
        ),
        "f4": _normalize_section(None, fields=F4_FIELDS, default_status="risk_safety_incomplete"),
    }
    return ctx


def _load_dashboard_json(bundle_root: Path) -> dict[str, Any] | None:
    path = bundle_root / "dashboard.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def build_futures_read_only_market_dashboard_display_context() -> dict[str, Any]:
    """SSR-only F5 dashboard context for GET /market/futures (fail closed by default)."""
    if not enabled_explicitly_on():
        return _fail_closed_context(
            gate_enabled=False,
            display_status="disabled",
            summary="F5 futures dashboard disabled (env gate off).",
        )

    bundle_root = resolved_bundle_root_or_none()
    if bundle_root is None:
        return _fail_closed_context(
            gate_enabled=True,
            display_status="unconfigured",
            summary="F5 futures dashboard bundle root unconfigured.",
        )

    payload = _load_dashboard_json(bundle_root)
    if payload is None:
        return _fail_closed_context(
            gate_enabled=True,
            display_status="builder_error",
            summary="F5 futures dashboard fixture could not be loaded.",
        )

    env_name = str(payload.get("env_name") or "").strip()
    overall_status = str(payload.get("overall_status") or "futures_metadata_partial")

    ctx: dict[str, Any] = {
        "gate_enabled": True,
        "display_status": str(payload.get("display_status") or "ready"),
        "readmodel_id": str(payload.get("readmodel_id") or READMODEL_ID),
        "non_authorizing": bool(payload.get("non_authorizing") is True),
        "summary_line": str(
            payload.get("summary_line") or "Offline fixture display — read-only, non-authorizing."
        ),
        "overall_status": overall_status,
        "env_name": env_name,
        "kraken_futures_testnet_label": env_name == KRAKEN_FUTURES_TESTNET_ENV_NAME,
        "status_model_values": list(payload.get("status_model_values") or STATUS_MODEL_VALUES),
        "authority": _authority_boundaries(),
        "f1": _normalize_section(
            payload.get("f1"),
            fields=F1_FIELDS,
            default_status="futures_metadata_partial",
        ),
        "f2": _normalize_section(
            payload.get("f2"),
            fields=F2_FIELDS,
            default_status="provenance_missing",
        ),
        "f3": _normalize_section(
            payload.get("f3"),
            fields=F3_FIELDS,
            default_status="backtest_realism_incomplete",
        ),
        "f4": _normalize_section(
            payload.get("f4"),
            fields=F4_FIELDS,
            default_status="risk_safety_incomplete",
        ),
    }
    return ctx


__all__ = [
    "ENV_BUNDLE_ROOT",
    "ENV_ENABLED",
    "KRAKEN_FUTURES_TESTNET_ENV_NAME",
    "READMODEL_ID",
    "STATUS_MODEL_VALUES",
    "build_futures_read_only_market_dashboard_display_context",
    "enabled_explicitly_on",
    "resolved_bundle_root_or_none",
]
