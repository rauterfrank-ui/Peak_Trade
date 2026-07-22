"""Evidence-surface schema for VEPC v1 development evaluation entry point."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.constants_v1 import (
    REQUIRED_EVIDENCE_METRIC_KEYS,
    TIME_SEGMENT_COUNT,
    TIME_SEGMENT_DEFINITION_ID,
    TIME_SEGMENT_IDS,
)


class EvidenceSchemaError(ValueError):
    """Fail-closed evidence schema error."""


def required_evidence_keys() -> tuple[str, ...]:
    return REQUIRED_EVIDENCE_METRIC_KEYS


def empty_evidence_surface_template(
    *,
    config_digest: str,
    strategy_params_digest: str,
    dataset_id: str,
    dataset_digest: str | None = None,
    segment_boundaries: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    segments = list(segment_boundaries or [])
    if not segments:
        segments = [
            {
                "segment_id": seg_id,
                "range": "NOT_EXECUTED",
                "evaluable_treatment_breakout_events": "NOT_EXECUTED",
                "result": "NOT_EXECUTED",
            }
            for seg_id in TIME_SEGMENT_IDS
        ]
    return {
        "schema_version": "evaluate_volatility_expansion_pullback_continuation_development_summary.v1",
        "evaluation_executed": False,
        "runner_started": False,
        "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
        "time_segment_count": TIME_SEGMENT_COUNT,
        "config_digest": config_digest,
        "strategy_params_digest": strategy_params_digest,
        "dataset_id": dataset_id,
        "dataset_digest": dataset_digest or "NOT_RESOLVED_PANEL_NOT_OPENED",
        "gross_return": "NOT_EXECUTED",
        "net_return": "NOT_EXECUTED",
        "gross_profit_factor": "NOT_EXECUTED",
        "net_profit_factor": "NOT_EXECUTED",
        "max_drawdown": "NOT_EXECUTED",
        "trade_count": "NOT_EXECUTED",
        "evaluable_treatment_breakout_events": "NOT_EXECUTED",
        "segment_boundaries": segments,
        "segment_results": [
            {"segment_id": s.get("segment_id"), "result": s.get("result", "NOT_EXECUTED")}
            for s in segments
        ],
        "passing_segments": "NOT_EXECUTED",
        "time_segment_robustness_pass_ratio": "NOT_EXECUTED",
        "economic_gate_pass": False,
        "holdout_accessed": False,
        "development_dataset_loaded": False,
    }


def validate_evidence_surface_complete(payload: Mapping[str, Any]) -> None:
    missing = [k for k in REQUIRED_EVIDENCE_METRIC_KEYS if k not in payload]
    if missing:
        raise EvidenceSchemaError(f"EVIDENCE_KEYS_MISSING:{','.join(missing)}")
    if payload.get("time_segment_count") != TIME_SEGMENT_COUNT:
        raise EvidenceSchemaError("TIME_SEGMENT_COUNT_DRIFT")
    if payload.get("time_segment_definition_id") != TIME_SEGMENT_DEFINITION_ID:
        raise EvidenceSchemaError("TIME_SEGMENT_DEFINITION_DRIFT")
