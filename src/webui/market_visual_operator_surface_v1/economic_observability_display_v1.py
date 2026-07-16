"""Economic observability display view model (read-only, honest zeros/FAIL).

Binds ``baseline_metrics.json``, ``cost_attribution.json`` and
``economic_validity_evaluation_v1.json`` from the offline evidence bundle. Shows real
zeros and FAIL verdicts honestly; never invents equity/drawdown curves.
"""

from __future__ import annotations

from typing import Any

from .contracts import (
    ENV_EVIDENCE_ROOT,
    ActivityState,
    load_json_or_none,
    resolve_economic_evidence_dir,
    resolved_dir_or_none,
)


def _metric(value: Any) -> dict[str, Any]:
    """Normalize a baseline-metric entry ({semantic, value}) or a raw scalar."""
    if isinstance(value, dict):
        semantic = str(value.get("semantic") or "").strip() or "UNKNOWN"
        raw = value.get("value")
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            return {"value": None, "semantic": semantic, "display": "—"}
        return {"value": float(raw), "semantic": semantic, "display": f"{float(raw):.6g}"}
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return {"value": None, "semantic": "NOT_COMPUTED", "display": "—"}
    return {"value": float(value), "semantic": "COMPUTED", "display": f"{float(value):.6g}"}


def _cost_component(value: Any) -> dict[str, Any]:
    """Normalize a cost-attribution component, preserving NOT_COMPUTED honestly."""
    if isinstance(value, dict):
        semantic = str(value.get("semantic") or "").strip() or "UNKNOWN"
        reason = str(value.get("reason_code") or "")
        raw = value.get("value")
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            return {"value": None, "semantic": semantic, "reason_code": reason, "display": semantic}
        return {
            "value": float(raw),
            "semantic": semantic,
            "reason_code": reason,
            "display": f"{float(raw):.6g}",
        }
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return {
            "value": None,
            "semantic": "NOT_COMPUTED",
            "reason_code": "",
            "display": "NOT_COMPUTED",
        }
    return {
        "value": float(value),
        "semantic": "COMPUTED",
        "reason_code": "",
        "display": f"{float(value):.6g}",
    }


def _base_vm(*, activity_state: str, economic_status: str = "unavailable") -> dict[str, Any]:
    return {
        "section_visible": True,
        "read_only": True,
        "non_authorizing": True,
        "activity_state": activity_state,
        "economic_status": economic_status,
        "gates_pass": False,
        "reason_codes": [],
        "gross_return": _metric(None),
        "net_return": _metric(None),
        "net_expectancy": _metric(None),
        "profit_factor": _metric(None),
        "max_drawdown": _metric(None),
        "sharpe": _metric(None),
        "sortino": _metric(None),
        "trade_count": _metric(None),
        "roundtrip_cost_bps": _cost_component(None),
        "fee_drag": _cost_component(None),
        "slippage_impact": _cost_component(None),
        "funding_drag": _cost_component(None),
        "equity_series_status": "MISSING_SOURCE",
        "drawdown_series_status": "MISSING_SOURCE",
        "equity_series": [],
        "drawdown_series": [],
        "source_id": "",
        "generated_at": "",
        "freshness": "",
        "quality": "missing_source",
        "manifest_ref": "",
        "recovery_hint": f"Set {ENV_EVIDENCE_ROOT} to an offline economic evidence bundle.",
    }


def build_economic_observability_display_v1() -> dict[str, Any]:
    """Build the economic observability display VM (fail closed by default)."""
    evidence_root = resolved_dir_or_none(ENV_EVIDENCE_ROOT)
    if evidence_root is None:
        return _base_vm(activity_state=ActivityState.NOT_AVAILABLE)

    economic_dir, binding_ref = resolve_economic_evidence_dir(evidence_root)
    baseline = load_json_or_none(economic_dir / "baseline_metrics.json")
    costs = load_json_or_none(economic_dir / "cost_attribution.json")
    validity = load_json_or_none(economic_dir / "economic_validity_evaluation_v1.json")

    if not any(isinstance(x, dict) for x in (baseline, costs, validity)):
        vm = _base_vm(activity_state=ActivityState.AVAILABLE_NOT_RUN)
        vm["source_id"] = str(economic_dir)
        vm["manifest_ref"] = binding_ref or ""
        return vm

    baseline = baseline if isinstance(baseline, dict) else {}
    costs = costs if isinstance(costs, dict) else {}
    validity = validity if isinstance(validity, dict) else {}

    economic_status = str(validity.get("evaluation_status") or "unavailable")
    reason_codes = [str(code) for code in (validity.get("reason_codes") or []) if str(code)]

    return {
        "section_visible": True,
        "read_only": True,
        "non_authorizing": True,
        "activity_state": ActivityState.PROCESSED,
        "economic_status": economic_status,
        "gates_pass": bool(validity.get("gates_pass") is True),
        "reason_codes": reason_codes,
        "gross_return": _metric(baseline.get("gross_return")),
        "net_return": _metric(baseline.get("net_return")),
        "net_expectancy": _metric(baseline.get("net_expectancy")),
        "profit_factor": _metric(baseline.get("profit_factor")),
        "max_drawdown": _metric(baseline.get("max_drawdown")),
        "sharpe": _metric(baseline.get("sharpe")),
        "sortino": _metric(baseline.get("sortino")),
        "trade_count": _metric(baseline.get("trade_count")),
        "roundtrip_cost_bps": _cost_component(costs.get("roundtrip_cost_bps")),
        "fee_drag": _cost_component(costs.get("fee_drag")),
        "slippage_impact": _cost_component(costs.get("slippage_impact")),
        "funding_drag": _cost_component(costs.get("funding_drag")),
        # No equity/drawdown series in offline evidence — do not invent curves.
        "equity_series_status": "MISSING_SOURCE",
        "drawdown_series_status": "MISSING_SOURCE",
        "equity_series": [],
        "drawdown_series": [],
        "source_id": str(economic_dir),
        "generated_at": str(validity.get("created_at_utc") or ""),
        "freshness": str(validity.get("created_at_utc") or ""),
        "quality": "loaded",
        "manifest_ref": binding_ref or "",
        "recovery_hint": "",
    }


__all__ = ["build_economic_observability_display_v1"]
