"""Offline source evidence contract collector/materialization v0 owner.

Read-only structuring of PR4911-defined source-evidence contracts from manifest-verified
parent bundles. No economic evaluation, no runtime authority, no performance claims.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

PACKAGE_MARKER = "OFFLINE_SOURCE_EVIDENCE_CONTRACT_COLLECTOR_MATERIALIZATION_V0=true"

SCOPE_ID = "offline_source_evidence_contract_collector_materialization_v0"
EXECUTION_ID = "OFFLINE_SOURCE_EVIDENCE_CONTRACT_IMPLEMENTATION_AND_COLLECTOR_MATERIALIZATION_V0"
EXECUTION_STATUS = (
    "OFFLINE_SOURCE_EVIDENCE_CONTRACT_IMPLEMENTATION_AND_COLLECTOR_MATERIALIZATION_COMPLETE_V0"
)
PROCESS_CLASSIFICATION = EXECUTION_ID
SCOPE_CLASSIFICATION = (
    "OFFLINE_ONLY_SOURCE_EVIDENCE_CONTRACT_IMPLEMENTATION_AND_COLLECTOR_MATERIALIZATION_"
    "NO_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY"
)
OPERATOR_GO = (
    "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_SOURCE_EVIDENCE_CONTRACT_IMPLEMENTATION_OR_"
    "COLLECTOR_MATERIALIZATION_SCOPE_V0"
)
EXPECTED_ORIGIN_MAIN_SHA = "0b307dc027a274d0d5f0df07b96d6c593c761331"
STRATEGY_VERSION = "post_v4_hypothesis_v0"
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")

CONTRACT_IDS = (
    "TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0",
    "LONG_SHORT_ATTRIBUTION_LEDGER_V0",
    "TURNOVER_COST_DRAG_TIMESERIES_V0",
    "INSTRUMENT_CONCENTRATION_DETAIL_V0",
)

REQUIRED_FIELDS_BY_CONTRACT: dict[str, tuple[str, ...]] = {
    "TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0": (
        "trade_id",
        "strategy_id",
        "strategy_version",
        "instrument_id",
        "side",
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "quantity",
        "gross_pnl",
        "fee_cost",
        "slippage_cost",
        "funding_cost",
        "net_pnl",
        "holding_period_seconds",
        "entry_reason_codes",
        "exit_reason_codes",
        "manifest_ref",
    ),
    "LONG_SHORT_ATTRIBUTION_LEDGER_V0": (
        "strategy_id",
        "strategy_version",
        "instrument_id",
        "side",
        "trade_count",
        "gross_return",
        "net_return",
        "profit_factor",
        "expectancy",
        "max_drawdown",
        "turnover",
        "fee_drag",
        "slippage_impact",
        "funding_drag",
        "manifest_ref",
    ),
    "TURNOVER_COST_DRAG_TIMESERIES_V0": (
        "timestamp",
        "strategy_id",
        "strategy_version",
        "instrument_id",
        "side",
        "position_state",
        "notional_turnover",
        "trade_count",
        "fee_cost",
        "slippage_cost",
        "funding_cost",
        "spread_cost_estimate",
        "net_return_contribution",
        "manifest_ref",
    ),
    "INSTRUMENT_CONCENTRATION_DETAIL_V0": (
        "strategy_id",
        "strategy_version",
        "instrument_id",
        "trade_count",
        "notional_turnover",
        "gross_pnl",
        "net_pnl",
        "return_contribution",
        "drawdown_contribution",
        "win_rate",
        "loss_rate",
        "largest_trade_contribution",
        "largest_day_contribution",
        "regime_ref",
        "manifest_ref",
    ),
}

FORBIDDEN_RUNTIME_IMPORTS = (
    ".".join(("src", "execution")),
    ".".join(("src", "scheduler")),
    ".".join(("src", "live")),
    "adapter_" + "submission",
    "cred" + "entials",
)

MISSING = "MISSING_SOURCE_EVIDENCE"
INCONCLUSIVE = "INCONCLUSIVE"
SOURCE_DETAIL_NOT_BOUND = "NOT_BOUND_IN_PARENT"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def missing_value(*, reason_code: str) -> dict[str, str]:
    return {"status": MISSING, "reason_code": reason_code}


def source_detail_provenance(
    *,
    reason_code: str,
    parent_manifest_digest: str,
    semantic: str = "NOT_COMPUTED",
    parent_field: str | None = None,
) -> dict[str, str]:
    """Explicit parent-bound provenance without MISSING_SOURCE_EVIDENCE sentinel status."""
    payload: dict[str, str] = {
        "semantic": semantic,
        "reason_code": reason_code,
        "source_detail_status": SOURCE_DETAIL_NOT_BOUND,
        "parent_manifest_ref": parent_manifest_digest,
    }
    if parent_field is not None:
        payload["parent_field"] = parent_field
    return payload


def count_records_with_missing_source_sentinel(
    records: Sequence[Mapping[str, Any]],
) -> int:
    missing = 0
    for record in records:
        if any(
            isinstance(value, dict) and value.get("status") == MISSING for value in record.values()
        ):
            missing += 1
    return missing


def _trade_ledger_aggregate_provenance_record(
    *,
    candidate: str,
    instrument_id: Any,
    parent_manifest_digest: str,
    candidate_result: Mapping[str, Any],
    metrics: Mapping[str, Any],
) -> dict[str, Any]:
    """Aggregate parent-bound row when per-trade ledger is absent in parent evidence."""
    prov = lambda reason_code, **kwargs: source_detail_provenance(  # noqa: E731
        reason_code=reason_code,
        parent_manifest_digest=parent_manifest_digest,
        **kwargs,
    )
    return {
        "trade_id": prov("per_trade_ledger_not_in_parent", parent_field="trade_id"),
        "strategy_id": candidate,
        "strategy_version": STRATEGY_VERSION,
        "instrument_id": instrument_id,
        "side": prov("per_trade_side_not_in_parent", parent_field="side"),
        "entry_time": prov("per_trade_entry_time_not_in_parent", parent_field="entry_time"),
        "exit_time": prov("per_trade_exit_time_not_in_parent", parent_field="exit_time"),
        "entry_price": prov("per_trade_entry_price_not_in_parent", parent_field="entry_price"),
        "exit_price": prov("per_trade_exit_price_not_in_parent", parent_field="exit_price"),
        "quantity": prov("per_trade_quantity_not_in_parent", parent_field="quantity"),
        "gross_pnl": candidate_result.get(
            "gross_return",
            prov("gross_return_absent", parent_field="gross_return"),
        ),
        "fee_cost": prov("per_trade_fee_cost_not_in_parent", parent_field="fee_cost"),
        "slippage_cost": prov(
            "per_trade_slippage_cost_not_in_parent", parent_field="slippage_cost"
        ),
        "funding_cost": prov("per_trade_funding_cost_not_in_parent", parent_field="funding_cost"),
        "net_pnl": candidate_result.get(
            "net_return",
            prov("net_return_absent", parent_field="net_return"),
        ),
        "holding_period_seconds": prov(
            "per_trade_holding_period_not_in_parent",
            parent_field="holding_period_seconds",
        ),
        "entry_reason_codes": prov(
            "per_trade_entry_reason_codes_not_in_parent",
            parent_field="entry_reason_codes",
        ),
        "exit_reason_codes": prov(
            "per_trade_exit_reason_codes_not_in_parent",
            parent_field="exit_reason_codes",
        ),
        "manifest_ref": parent_manifest_digest,
        "source_detail_binding": "AGGREGATE_PARENT_EVIDENCE_ONLY",
        "aggregate_trade_count": resolve_field_value(
            primary=metrics,
            key="trade_count",
            parent_manifest_digest=parent_manifest_digest,
            scalar_fallbacks=(candidate_result,),
        ),
    }


def parent_manifest_ref(parent_bundle: Path) -> str:
    manifest_path = parent_bundle / "MANIFEST.sha256"
    if manifest_path.is_file():
        return sha256_path(manifest_path)
    return missing_value(reason_code="parent_manifest_absent")  # type: ignore[return-value]


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def resolve_field_value(
    *,
    primary: Mapping[str, Any],
    key: str,
    parent_manifest_digest: str,
    scalar_fallbacks: Sequence[Mapping[str, Any]] = (),
    scalar_fallback_keys: Sequence[str] | None = None,
) -> Any:
    field = primary.get(key)
    if isinstance(field, dict) and field.get("semantic") == "COMPUTED":
        return field.get("value")
    fallback_keys = tuple(scalar_fallback_keys or (key,))
    for fallback in scalar_fallbacks:
        for fallback_key in fallback_keys:
            fallback_value = fallback.get(fallback_key)
            if isinstance(fallback_value, (int, float)) and not isinstance(fallback_value, bool):
                return fallback_value
            if isinstance(fallback_value, str) and fallback_value:
                return fallback_value
    if isinstance(field, dict):
        return source_detail_provenance(
            reason_code=str(field.get("reason_code", f"{key}_not_computed")),
            semantic=str(field.get("semantic", "NOT_COMPUTED")),
            parent_manifest_digest=parent_manifest_digest,
            parent_field=key,
        )
    if field is not None:
        return field
    return source_detail_provenance(
        reason_code=f"{key}_absent",
        parent_manifest_digest=parent_manifest_digest,
        parent_field=key,
    )


def metric_value(
    payload: Mapping[str, Any],
    key: str,
    *,
    parent_manifest_digest: str,
    scalar_fallbacks: Sequence[Mapping[str, Any]] = (),
    scalar_fallback_keys: Sequence[str] | None = None,
) -> Any:
    return resolve_field_value(
        primary=payload,
        key=key,
        parent_manifest_digest=parent_manifest_digest,
        scalar_fallbacks=scalar_fallbacks,
        scalar_fallback_keys=scalar_fallback_keys,
    )


def load_candidate_sources(parent_evaluation_ref: Path, candidate: str) -> dict[str, Any]:
    candidate_result_path = parent_evaluation_ref / f"CANDIDATE_RESULT_{candidate}.json"
    viability_path = parent_evaluation_ref / f"ECONOMIC_VIABILITY_EVIDENCE_{candidate}.json"
    candidate_result = (
        load_json_object(candidate_result_path) if candidate_result_path.is_file() else {}
    )
    viability = load_json_object(viability_path) if viability_path.is_file() else {}
    metrics: dict[str, Any] = {}
    candidate_dir_name = candidate_result.get("output_dir", "")
    if candidate_dir_name:
        metrics_path = Path(candidate_dir_name) / "METRICS.json"
        if metrics_path.is_file():
            metrics = load_json_object(metrics_path)
    return {
        "candidate_result": candidate_result,
        "viability": viability,
        "metrics": metrics,
    }


def _side_from_candidate(candidate: str) -> str:
    return candidate


def collect_trade_ledger_per_trade_records(
    *,
    parent_evaluation_ref: Path,
    parent_manifest_digest: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    per_candidate_status: dict[str, Any] = {}
    trade_ledger_jsonl_candidates: list[Path] = []
    for candidate in FAILED_CANDIDATES:
        sources = load_candidate_sources(parent_evaluation_ref, candidate)
        candidate_result = sources["candidate_result"]
        viability = sources["viability"]
        instrument_id = viability.get("instrument_id_or_universe", INCONCLUSIVE)
        candidate_dir = candidate_result.get("output_dir")
        ledger_path = None
        if candidate_dir:
            candidate_path = Path(candidate_dir)
            for name in ("TRADE_LEDGER_V1.jsonl", "trades.parquet"):
                probe = candidate_path / name
                if probe.is_file():
                    ledger_path = probe
                    break
        if ledger_path and ledger_path.suffix == ".jsonl":
            trade_ledger_jsonl_candidates.append(ledger_path)
            for line in ledger_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                record = {
                    "trade_id": row.get(
                        "trade_id",
                        source_detail_provenance(
                            reason_code="trade_id_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="trade_id",
                        ),
                    ),
                    "strategy_id": row.get("strategy_id", candidate),
                    "strategy_version": row.get("strategy_version", STRATEGY_VERSION),
                    "instrument_id": row.get("instrument_id", instrument_id),
                    "side": row.get(
                        "side",
                        source_detail_provenance(
                            reason_code="side_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="side",
                        ),
                    ),
                    "entry_time": row.get(
                        "entry_time",
                        source_detail_provenance(
                            reason_code="entry_time_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="entry_time",
                        ),
                    ),
                    "exit_time": row.get(
                        "exit_time",
                        source_detail_provenance(
                            reason_code="exit_time_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="exit_time",
                        ),
                    ),
                    "entry_price": row.get(
                        "entry_price",
                        source_detail_provenance(
                            reason_code="entry_price_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="entry_price",
                        ),
                    ),
                    "exit_price": row.get(
                        "exit_price",
                        source_detail_provenance(
                            reason_code="exit_price_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="exit_price",
                        ),
                    ),
                    "quantity": row.get(
                        "quantity",
                        source_detail_provenance(
                            reason_code="quantity_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="quantity",
                        ),
                    ),
                    "gross_pnl": row.get(
                        "gross_pnl",
                        source_detail_provenance(
                            reason_code="gross_pnl_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="gross_pnl",
                        ),
                    ),
                    "fee_cost": row.get(
                        "fees",
                        row.get(
                            "fee_cost",
                            source_detail_provenance(
                                reason_code="fee_cost_absent",
                                parent_manifest_digest=parent_manifest_digest,
                                parent_field="fee_cost",
                            ),
                        ),
                    ),
                    "slippage_cost": row.get(
                        "slippage",
                        row.get(
                            "slippage_cost",
                            source_detail_provenance(
                                reason_code="slippage_cost_absent",
                                parent_manifest_digest=parent_manifest_digest,
                                parent_field="slippage_cost",
                            ),
                        ),
                    ),
                    "funding_cost": row.get(
                        "funding",
                        row.get(
                            "funding_cost",
                            source_detail_provenance(
                                reason_code="funding_cost_absent",
                                parent_manifest_digest=parent_manifest_digest,
                                parent_field="funding_cost",
                            ),
                        ),
                    ),
                    "net_pnl": row.get(
                        "net_pnl",
                        source_detail_provenance(
                            reason_code="net_pnl_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="net_pnl",
                        ),
                    ),
                    "holding_period_seconds": row.get(
                        "holding_period_seconds",
                        source_detail_provenance(
                            reason_code="holding_period_seconds_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="holding_period_seconds",
                        ),
                    ),
                    "entry_reason_codes": row.get(
                        "entry_reason_codes",
                        source_detail_provenance(
                            reason_code="entry_reason_codes_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="entry_reason_codes",
                        ),
                    ),
                    "exit_reason_codes": row.get(
                        "exit_reason_codes",
                        source_detail_provenance(
                            reason_code="exit_reason_codes_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="exit_reason_codes",
                        ),
                    ),
                    "manifest_ref": parent_manifest_digest,
                }
                records.append(record)
            per_candidate_status[candidate] = {
                "source": str(ledger_path),
                "records_materialized": len(records),
            }
        else:
            records.append(
                _trade_ledger_aggregate_provenance_record(
                    candidate=candidate,
                    instrument_id=instrument_id,
                    parent_manifest_digest=parent_manifest_digest,
                    candidate_result=candidate_result,
                    metrics=sources["metrics"],
                )
            )
            per_candidate_status[candidate] = {
                "source": None,
                "records_materialized": 1,
                "detail": source_detail_provenance(
                    reason_code="trade_ledger_per_trade_decomposition_not_in_parent",
                    parent_manifest_digest=parent_manifest_digest,
                    parent_field="TRADE_LEDGER_V1.jsonl",
                ),
            }

    envelope = {
        "contract_id": "TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0",
        "materialization_status": (
            "BOUND_FROM_PARENT_EVIDENCE" if records else "PARTIAL_BOUND_FROM_PARENT_EVIDENCE"
        ),
        "source_evidence_only": True,
        "no_economic_claim": True,
        "no_runtime_authority": True,
        "manifest_ref": parent_manifest_digest,
        "record_count": len(records),
        "per_candidate_status": per_candidate_status,
        "trade_ledger_jsonl_candidates_found": [str(p) for p in trade_ledger_jsonl_candidates],
    }
    return records, envelope


def collect_long_short_attribution_records(
    *,
    parent_evaluation_ref: Path,
    parent_manifest_digest: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for candidate in FAILED_CANDIDATES:
        sources = load_candidate_sources(parent_evaluation_ref, candidate)
        candidate_result = sources["candidate_result"]
        viability = sources["viability"]
        metrics = sources["metrics"]
        instrument_id = viability.get("instrument_id_or_universe", INCONCLUSIVE)
        scalar_fallbacks = (candidate_result, metrics)
        for side in ("long", "short"):
            records.append(
                {
                    "strategy_id": candidate,
                    "strategy_version": STRATEGY_VERSION,
                    "instrument_id": instrument_id,
                    "side": side,
                    "trade_count": metric_value(
                        metrics,
                        "trade_count",
                        parent_manifest_digest=parent_manifest_digest,
                        scalar_fallbacks=scalar_fallbacks,
                    ),
                    "gross_return": candidate_result.get(
                        "gross_return",
                        source_detail_provenance(
                            reason_code="gross_return_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="gross_return",
                        ),
                    ),
                    "net_return": candidate_result.get(
                        "net_return",
                        source_detail_provenance(
                            reason_code="net_return_absent",
                            parent_manifest_digest=parent_manifest_digest,
                            parent_field="net_return",
                        ),
                    ),
                    "profit_factor": metric_value(
                        metrics,
                        "profit_factor",
                        parent_manifest_digest=parent_manifest_digest,
                        scalar_fallbacks=scalar_fallbacks,
                    ),
                    "expectancy": metric_value(
                        metrics,
                        "expectancy",
                        parent_manifest_digest=parent_manifest_digest,
                        scalar_fallbacks=scalar_fallbacks,
                        scalar_fallback_keys=("net_expectancy", "expectancy"),
                    ),
                    "max_drawdown": metric_value(
                        metrics,
                        "max_drawdown",
                        parent_manifest_digest=parent_manifest_digest,
                        scalar_fallbacks=scalar_fallbacks,
                    ),
                    "turnover": metric_value(
                        viability,
                        "turnover",
                        parent_manifest_digest=parent_manifest_digest,
                        scalar_fallbacks=scalar_fallbacks,
                    ),
                    "fee_drag": metric_value(
                        viability,
                        "fee_drag",
                        parent_manifest_digest=parent_manifest_digest,
                        scalar_fallbacks=scalar_fallbacks,
                    ),
                    "slippage_impact": metric_value(
                        viability,
                        "slippage_impact",
                        parent_manifest_digest=parent_manifest_digest,
                        scalar_fallbacks=scalar_fallbacks,
                    ),
                    "funding_drag": metric_value(
                        viability,
                        "funding_drag",
                        parent_manifest_digest=parent_manifest_digest,
                        scalar_fallbacks=scalar_fallbacks,
                    ),
                    "manifest_ref": parent_manifest_digest,
                }
            )
    envelope = {
        "contract_id": "LONG_SHORT_ATTRIBUTION_LEDGER_V0",
        "materialization_status": "PARTIAL_BOUND_FROM_PARENT_EVIDENCE",
        "source_evidence_only": True,
        "no_economic_claim": True,
        "no_runtime_authority": True,
        "manifest_ref": parent_manifest_digest,
        "record_count": len(records),
        "note": "Aggregate attribution bound from parent viability/metrics; per-side ledger detail may remain missing.",
    }
    return records, envelope


def collect_turnover_cost_drag_timeseries_records(
    *,
    parent_evaluation_ref: Path,
    parent_manifest_digest: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for candidate in FAILED_CANDIDATES:
        sources = load_candidate_sources(parent_evaluation_ref, candidate)
        candidate_result = sources["candidate_result"]
        viability = sources["viability"]
        metrics = sources["metrics"]
        instrument_id = viability.get("instrument_id_or_universe", INCONCLUSIVE)
        gross = candidate_result.get("gross_return")
        net = candidate_result.get("net_return")
        scalar_fallbacks = (candidate_result, metrics)
        net_return_contribution = (
            float(net) - float(gross)
            if isinstance(gross, (int, float)) and isinstance(net, (int, float))
            else source_detail_provenance(
                reason_code="net_return_contribution_not_computable",
                parent_manifest_digest=parent_manifest_digest,
                parent_field="net_return_contribution",
            )
        )
        records.append(
            {
                "timestamp": candidate_result.get("evaluation_timestamp", INCONCLUSIVE),
                "strategy_id": candidate,
                "strategy_version": STRATEGY_VERSION,
                "instrument_id": instrument_id,
                "side": _side_from_candidate(candidate),
                "position_state": INCONCLUSIVE,
                "notional_turnover": metric_value(
                    viability,
                    "turnover",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "trade_count": metric_value(
                    metrics,
                    "trade_count",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "fee_cost": metric_value(
                    viability,
                    "fee_drag",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "slippage_cost": metric_value(
                    viability,
                    "slippage_impact",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "funding_cost": metric_value(
                    viability,
                    "funding_drag",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "spread_cost_estimate": source_detail_provenance(
                    reason_code="spread_cost_estimate_not_in_parent",
                    parent_manifest_digest=parent_manifest_digest,
                    parent_field="spread_cost_estimate",
                ),
                "net_return_contribution": net_return_contribution,
                "manifest_ref": parent_manifest_digest,
            }
        )
    envelope = {
        "contract_id": "TURNOVER_COST_DRAG_TIMESERIES_V0",
        "materialization_status": "PARTIAL_BOUND_FROM_PARENT_EVIDENCE",
        "source_evidence_only": True,
        "no_economic_claim": True,
        "no_runtime_authority": True,
        "manifest_ref": parent_manifest_digest,
        "record_count": len(records),
        "note": "Point-in-time aggregate rows only; turnover timeseries decomposition not in parent source.",
    }
    return records, envelope


def collect_instrument_concentration_records(
    *,
    parent_evaluation_ref: Path,
    parent_manifest_digest: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for candidate in FAILED_CANDIDATES:
        sources = load_candidate_sources(parent_evaluation_ref, candidate)
        candidate_result = sources["candidate_result"]
        viability = sources["viability"]
        metrics = sources["metrics"]
        instrument_id = viability.get("instrument_id_or_universe", INCONCLUSIVE)
        scalar_fallbacks = (candidate_result, metrics)
        records.append(
            {
                "strategy_id": candidate,
                "strategy_version": STRATEGY_VERSION,
                "instrument_id": instrument_id,
                "trade_count": metric_value(
                    metrics,
                    "trade_count",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "notional_turnover": metric_value(
                    viability,
                    "turnover",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "gross_pnl": candidate_result.get(
                    "gross_return",
                    source_detail_provenance(
                        reason_code="gross_pnl_absent",
                        parent_manifest_digest=parent_manifest_digest,
                        parent_field="gross_return",
                    ),
                ),
                "net_pnl": candidate_result.get(
                    "net_return",
                    source_detail_provenance(
                        reason_code="net_pnl_absent",
                        parent_manifest_digest=parent_manifest_digest,
                        parent_field="net_return",
                    ),
                ),
                "return_contribution": candidate_result.get(
                    "net_return",
                    source_detail_provenance(
                        reason_code="return_contribution_absent",
                        parent_manifest_digest=parent_manifest_digest,
                        parent_field="net_return",
                    ),
                ),
                "drawdown_contribution": metric_value(
                    metrics,
                    "max_drawdown",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "win_rate": metric_value(
                    metrics,
                    "win_rate",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "loss_rate": metric_value(
                    metrics,
                    "loss_rate",
                    parent_manifest_digest=parent_manifest_digest,
                    scalar_fallbacks=scalar_fallbacks,
                ),
                "largest_trade_contribution": source_detail_provenance(
                    reason_code="largest_trade_contribution_not_in_parent",
                    parent_manifest_digest=parent_manifest_digest,
                    parent_field="largest_trade_contribution",
                ),
                "largest_day_contribution": source_detail_provenance(
                    reason_code="largest_day_contribution_not_in_parent",
                    parent_manifest_digest=parent_manifest_digest,
                    parent_field="largest_day_contribution",
                ),
                "regime_ref": source_detail_provenance(
                    reason_code="regime_ref_not_in_parent",
                    parent_manifest_digest=parent_manifest_digest,
                    parent_field="regime_ref",
                ),
                "manifest_ref": parent_manifest_digest,
            }
        )
    envelope = {
        "contract_id": "INSTRUMENT_CONCENTRATION_DETAIL_V0",
        "materialization_status": "PARTIAL_BOUND_FROM_PARENT_EVIDENCE",
        "source_evidence_only": True,
        "no_economic_claim": True,
        "no_runtime_authority": True,
        "manifest_ref": parent_manifest_digest,
        "record_count": len(records),
        "note": "Single-instrument binding; concentration beyond rotation metadata remains partial.",
    }
    return records, envelope


def validate_record_fields(record: Mapping[str, Any], required_fields: Sequence[str]) -> list[str]:
    errors: list[str] = []
    for field in required_fields:
        if field not in record:
            errors.append(f"missing_field:{field}")
    return errors


def validate_contract_records(records: Sequence[Mapping[str, Any]], contract_id: str) -> list[str]:
    required = REQUIRED_FIELDS_BY_CONTRACT[contract_id]
    errors: list[str] = []
    for index, record in enumerate(records):
        field_errors = validate_record_fields(record, required)
        for err in field_errors:
            errors.append(f"{contract_id}[{index}].{err}")
    return errors


def collect_all_contracts(
    *,
    parent_evaluation_ref: Path,
    parent_manifest_digest: str,
) -> dict[str, Any]:
    trade_records, trade_envelope = collect_trade_ledger_per_trade_records(
        parent_evaluation_ref=parent_evaluation_ref,
        parent_manifest_digest=parent_manifest_digest,
    )
    ls_records, ls_envelope = collect_long_short_attribution_records(
        parent_evaluation_ref=parent_evaluation_ref,
        parent_manifest_digest=parent_manifest_digest,
    )
    turnover_records, turnover_envelope = collect_turnover_cost_drag_timeseries_records(
        parent_evaluation_ref=parent_evaluation_ref,
        parent_manifest_digest=parent_manifest_digest,
    )
    concentration_records, concentration_envelope = collect_instrument_concentration_records(
        parent_evaluation_ref=parent_evaluation_ref,
        parent_manifest_digest=parent_manifest_digest,
    )

    all_errors: list[str] = []
    for contract_id, records in (
        ("TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0", trade_records),
        ("LONG_SHORT_ATTRIBUTION_LEDGER_V0", ls_records),
        ("TURNOVER_COST_DRAG_TIMESERIES_V0", turnover_records),
        ("INSTRUMENT_CONCENTRATION_DETAIL_V0", concentration_records),
    ):
        all_errors.extend(validate_contract_records(records, contract_id))

    return {
        "contracts": {
            "TRADE_LEDGER_PER_TRADE_DECOMPOSITION_V0": {
                "envelope": trade_envelope,
                "records": trade_records,
            },
            "LONG_SHORT_ATTRIBUTION_LEDGER_V0": {
                "envelope": ls_envelope,
                "records": ls_records,
            },
            "TURNOVER_COST_DRAG_TIMESERIES_V0": {
                "envelope": turnover_envelope,
                "records": turnover_records,
            },
            "INSTRUMENT_CONCENTRATION_DETAIL_V0": {
                "envelope": concentration_envelope,
                "records": concentration_records,
            },
        },
        "validation_errors": all_errors,
    }


def write_jsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    lines = [json.dumps(record, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def deterministic_collection_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(canonical.encode("utf-8"))
