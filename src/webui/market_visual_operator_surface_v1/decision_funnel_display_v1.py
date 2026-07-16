"""Decision funnel display view model (read-only, no invented counts).

Reads the offline economic evidence ``compact_decision_funnel.json`` (or the
``DECISION_FUNNEL`` block of ``final_report.json``) and renders a fixed-stage funnel.
Intermediate stages without concrete evidence stay ``None`` — never fabricated.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import (
    ENV_EVIDENCE_ROOT,
    ActivityState,
    load_json_or_none,
    resolve_economic_evidence_dir,
    resolved_dir_or_none,
)

# Canonical funnel stage order (exact).
FUNNEL_STAGES: tuple[str, ...] = (
    "market_epochs",
    "directional_candidates",
    "confirmed",
    "survival_pass",
    "suitability_pass",
    "double_play_eligible",
    "entry_preconditions",
    "risk_sizing_admissible",
    "portfolio_admissible",
    "trades_opened",
)

STAGE_LABELS: dict[str, str] = {
    "market_epochs": "Market epochs",
    "directional_candidates": "Directional candidates",
    "confirmed": "Confirmed",
    "survival_pass": "Survival pass",
    "suitability_pass": "Suitability pass",
    "double_play_eligible": "Double-play eligible",
    "entry_preconditions": "Entry preconditions",
    "risk_sizing_admissible": "Risk sizing admissible",
    "portfolio_admissible": "Portfolio admissible",
    "trades_opened": "Trades opened",
}


def _empty_stages(status: str) -> list[dict[str, Any]]:
    return [
        {
            "stage_id": stage,
            "label": STAGE_LABELS[stage],
            "count": None,
            "status": status,
        }
        for stage in FUNNEL_STAGES
    ]


def _base_vm(*, activity_state: str, stage_status: str) -> dict[str, Any]:
    return {
        "section_visible": True,
        "read_only": True,
        "non_authorizing": True,
        "activity_state": activity_state,
        "stages": _empty_stages(stage_status),
        "bar_count": None,
        "trade_count": None,
        "zero_trade_degeneration": None,
        "zero_trade_degeneration_explicit": False,
        "trade_count_computed": False,
        "most_frequent_block_reasons": [],
        "source_id": "",
        "generated_at": "",
        "freshness": "",
        "quality": "missing_source",
        "manifest_ref": "",
        "recovery_hint": f"Set {ENV_EVIDENCE_ROOT} to an offline economic evidence bundle.",
    }


def _funnel_from_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the decision-funnel block from compact funnel or final_report payloads."""
    if "bar_count" in payload or "trade_count" in payload:
        return payload
    nested = payload.get("DECISION_FUNNEL")
    if isinstance(nested, dict):
        return nested
    return None


def _as_int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def build_decision_funnel_display_v1() -> dict[str, Any]:
    """Build the decision funnel display VM (fail closed by default)."""
    evidence_root = resolved_dir_or_none(ENV_EVIDENCE_ROOT)
    if evidence_root is None:
        return _base_vm(
            activity_state=ActivityState.NOT_AVAILABLE,
            stage_status=ActivityState.NOT_AVAILABLE,
        )

    economic_dir, binding_ref = resolve_economic_evidence_dir(evidence_root)
    funnel_path = economic_dir / "compact_decision_funnel.json"
    if funnel_path.is_file():
        payload = load_json_or_none(funnel_path)
        if payload is None:
            # File present but unparseable: honest parse failure.
            vm = _base_vm(
                activity_state=ActivityState.FAILED,
                stage_status=ActivityState.FAILED,
            )
            vm["source_id"] = str(funnel_path)
            vm["quality"] = "parse_error"
            return vm
    else:
        final_report = load_json_or_none(economic_dir / "final_report.json")
        payload = final_report if isinstance(final_report, dict) else None

    if payload is None:
        # Configured but nothing loadable: honest AVAILABLE_NOT_RUN (not a parse failure).
        vm = _base_vm(
            activity_state=ActivityState.AVAILABLE_NOT_RUN,
            stage_status=ActivityState.AVAILABLE_NOT_RUN,
        )
        vm["source_id"] = str(economic_dir)
        vm["manifest_ref"] = binding_ref or ""
        return vm

    if not isinstance(payload, dict):
        vm = _base_vm(
            activity_state=ActivityState.FAILED,
            stage_status=ActivityState.FAILED,
        )
        vm["source_id"] = str(economic_dir)
        vm["quality"] = "parse_error"
        return vm

    funnel = _funnel_from_payload(payload)
    if funnel is None:
        vm = _base_vm(
            activity_state=ActivityState.FAILED,
            stage_status=ActivityState.FAILED,
        )
        vm["source_id"] = str(economic_dir)
        vm["quality"] = "parse_error"
        return vm

    bar_count = _as_int_or_none(funnel.get("bar_count"))
    trade_count = _as_int_or_none(funnel.get("trade_count"))
    ztd_raw = funnel.get("zero_trade_degeneration")
    ztd_explicit = isinstance(ztd_raw, bool)
    zero_trade_degeneration = ztd_raw if ztd_explicit else None

    block_reasons_raw = funnel.get("most_frequent_block_reasons")
    block_reasons: list[dict[str, Any]] = []
    if isinstance(block_reasons_raw, list):
        for item in block_reasons_raw:
            if isinstance(item, dict):
                label = str(
                    item.get("reason") or item.get("block_reason") or item.get("label") or ""
                )
                count = _as_int_or_none(item.get("count"))
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                label = str(item[0])
                count = _as_int_or_none(item[1])
            else:
                label = str(item)
                count = None
            if label:
                block_reasons.append({"label": label, "count": count})

    # Stage counts: only leaf stages carry evidence; the rest stay None (not invented).
    stages: list[dict[str, Any]] = []
    for stage in FUNNEL_STAGES:
        if stage == "market_epochs" and bar_count is not None:
            stages.append(
                {
                    "stage_id": stage,
                    "label": STAGE_LABELS[stage],
                    "count": bar_count,
                    "status": ActivityState.PROCESSED,
                }
            )
        elif stage == "trades_opened" and trade_count is not None:
            stages.append(
                {
                    "stage_id": stage,
                    "label": STAGE_LABELS[stage],
                    "count": trade_count,
                    "status": ActivityState.PROCESSED,
                }
            )
        else:
            stages.append(
                {
                    "stage_id": stage,
                    "label": STAGE_LABELS[stage],
                    "count": None,
                    "status": ActivityState.AVAILABLE_NOT_RUN,
                }
            )

    return {
        "section_visible": True,
        "read_only": True,
        "non_authorizing": True,
        "activity_state": ActivityState.PROCESSED,
        "stages": stages,
        "bar_count": bar_count,
        "trade_count": trade_count,
        "zero_trade_degeneration": zero_trade_degeneration,
        "zero_trade_degeneration_explicit": ztd_explicit,
        "trade_count_computed": trade_count is not None,
        "most_frequent_block_reasons": block_reasons,
        "source_id": str(funnel_path if funnel_path.is_file() else economic_dir),
        "generated_at": str(payload.get("created_at_utc") or ""),
        "freshness": str(payload.get("created_at_utc") or ""),
        "quality": "loaded",
        "manifest_ref": binding_ref or "",
        "recovery_hint": "",
    }


__all__ = [
    "FUNNEL_STAGES",
    "STAGE_LABELS",
    "build_decision_funnel_display_v1",
]
