"""Offline candidate for source/time-safe N_BARS composition; no productive wiring.

The source receipt schema and synthetic binding here are a research proposal,
not a new productive authority. Existing supplier/record/learning contracts do
the calculation. No automatic productive provenance binding is invoked.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    ingest_evaluation_bundle_into_learning_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_bindings_v1 import (
    ProvenanceBindingContextV1,
    ProvenanceProducerBindingV1,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_v1 import (
    build_outcome_evidence_provenance_v1,
    provenance_implies_productive_truth_v1,
)
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import build_outcome_record_v0
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_materialization_v1 import (
    build_o4_n_bars_bar_evidence_snapshot_v1,
)

SYNTHETIC = "SYNTHETIC_OFFLINE"
RECORDED = "RECORDED_PUBLIC_MD"
SYNTHETIC_USE = "OFFLINE_SYNTHETIC_RESEARCH"
OBSERVED_USE = "OFFLINE_OBSERVED_RESEARCH"


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _time(value: str) -> float:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("EXPLICIT_UTC_REQUIRED")
    return parsed.timestamp()


def _write(path: Path, payload: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")


def inspect_source(
    request: Mapping[str, Any], source: Mapping[str, Any], *, as_of_utc: str
) -> dict[str, Any]:
    """Validate immutable bar receipts before minting any measurement or state.

    available_at_utc means the completed bar was available to the consumer,
    not the last price sample time. Both are required and remain distinct.
    Integrity of a receipt does not independently attest its market origin.
    """
    decision = validate_decision_event_v0(request["decision"])
    as_of = _time(as_of_utc)
    decision_time = _time(decision["event_time_utc"])
    start = _time(request["horizon_start_time_utc"])
    n_bars = request["n_bars"]
    if isinstance(n_bars, bool) or not isinstance(n_bars, int) or n_bars < 2:
        raise ValueError("LAB_EXPLICIT_N_AT_LEAST_TWO_REQUIRED")
    if start < decision_time or as_of < decision_time:
        raise ValueError("HORIZON_OR_AS_OF_PRECEDES_DECISION")
    if request["interval"] != "PT1H" or start % 3600 != 0:
        raise ValueError("LAB_EXPLICIT_PT1H_GRID_REQUIRED")
    source_kind = source["source_kind"]
    if source_kind not in {SYNTHETIC, RECORDED}:
        raise ValueError("EXPLICIT_SOURCE_KIND_REQUIRED")
    if request["requested_use"] not in {SYNTHETIC_USE, OBSERVED_USE}:
        raise ValueError("EXPLICIT_OFFLINE_USE_REQUIRED")
    if (source_kind == SYNTHETIC) != (request["requested_use"] == SYNTHETIC_USE):
        raise ValueError("SOURCE_KIND_USE_MISMATCH")
    if not source.get("price_unit") or source.get("price_basis") != "EXPLICIT_BAR_CLOSE":
        raise ValueError("EXPLICIT_PRICE_UNIT_AND_BASIS_REQUIRED")
    if decision["selected_instrument_ref"] != source["canonical_instrument_id"]:
        raise ValueError("DECISION_INSTRUMENT_BINDING_MISMATCH")
    if source["clock_domain"] != ("SIMULATED_UTC" if source_kind == SYNTHETIC else "CAPTURE_UTC"):
        raise ValueError("CLOCK_DOMAIN_SOURCE_MISMATCH")

    seen: set[float] = set()
    selected: dict[float, Mapping[str, Any]] = {}
    end = start + n_bars * 3600
    for receipt in source["bar_receipts"]:
        if receipt["source_kind"] != source_kind:
            raise ValueError("MIXED_SOURCE_ORIGIN")
        bar = receipt["bar"]
        identity = bar["last_observation_identity"]
        for field in ("canonical_instrument_id", "venue_instrument_id", "venue"):
            if bar[field] != source[field] or identity[field] != source[field]:
                raise ValueError(f"BAR_IDENTITY_MISMATCH:{field}")
        opened, closed = float(bar["bar_open_time"]), float(bar["bar_close_time"])
        observed, available = (
            float(identity["venue_event_time"]),
            _time(receipt["available_at_utc"]),
        )
        if bar["interval"] != request["interval"] or closed - opened != 3600 or opened % 3600:
            raise ValueError("ORIGINAL_BAR_INTERVAL_MISMATCH")
        if not opened <= observed <= closed:
            raise ValueError("OBSERVATION_OUTSIDE_ORIGINAL_BAR")
        if available < max(observed, closed):
            raise ValueError("BAR_AVAILABLE_BEFORE_OBSERVATION_OR_CLOSE")
        if opened in seen:
            raise ValueError("DUPLICATE_OR_CONFLICTING_BAR")
        seen.add(opened)
        if bar["config_digest"] == "ddo-handoff-o4-seed-v1":
            raise ValueError("KNOWN_RETIMED_SEED_NOT_ORIGINAL_BAR_EVIDENCE")
        if start <= opened < end:
            if (
                bar["finalization_state"] != "FINALIZED_BAR"
                or bar["quality_state"] != "FINALIZED_BAR"
            ):
                raise ValueError("FINALIZED_COMPLETE_BAR_REQUIRED")
            if available <= as_of and closed <= as_of:
                selected[opened] = bar
    expected = [start + i * 3600 for i in range(n_bars)]
    if any(t not in selected for t in expected):
        return {
            "status": "WAITING_FOR_COMPLETE_AVAILABLE_HORIZON",
            "bars_available": len(selected),
            "n_bars_required": n_bars,
            "source_kind": source_kind,
            "clock_domain": source["clock_domain"],
            "measurement_created": False,
        }
    return {
        "status": "READY",
        "bars": [dict(selected[t]) for t in expected],
        "source_kind": source_kind,
        "clock_domain": source["clock_domain"],
    }


def _provenance(
    decision: Mapping[str, Any],
    source: Mapping[str, Any],
    measurement: Mapping[str, Any],
    lineage: str,
) -> dict[str, Any]:
    synthetic = source["source_kind"] == SYNTHETIC
    # Candidate binding expressed with existing orthogonal contract vocabulary.
    # No simulated fills/accounting or productive truth is inferred from prices.
    return dict(
        build_outcome_evidence_provenance_v1(
            {
                "decision_event_ref": decision["record_id"],
                "producer_id": __name__,
                "producer_version": "offline-candidate-v1",
                "instrument_id": source["canonical_instrument_id"],
                "venue_native_id": source["venue_instrument_id"],
                "cycle_id": decision["cycle_id"],
                "trading_epoch": source["source_epoch"],
                "lineage_digest": lineage,
                "market_observation_source": SYNTHETIC if synthetic else "REPLAY_HISTORICAL",
                "ddo_ledger_environment": "dev",
                "order_environment_label": "NOT_APPLICABLE",
                "decision_source": "DDO_OBSERVATION" if synthetic else "REPLAY_SEMANTIC",
                "execution_mode_label": "NO_EXECUTION",
                "fill_source_type": "NO_FILL",
                "position_truth_source": "NOT_APPLICABLE",
                "reconciliation_source": "NOT_APPLICABLE",
                "accounting_source": "NOT_APPLICABLE",
                "outcome_source": "OFFLINE_PRICE_MEASUREMENT_CANDIDATE",
                "outcome_semantic_class": "INTERNAL_SIMULATED_OUTCOME"
                if synthetic
                else "REPLAY_HISTORICAL",
                "outcome_realization_kind": "SIMULATED" if synthetic else "REPLAYED",
                "outcome_scalar_kind": "LOG_RETURN",
                "external_capital_flow_class": "NONE",
                "market_timestamp_utc": measurement["evaluation_time_utc"],
                "decision_timestamp_utc": decision["event_time_utc"],
                "evaluation_timestamp_utc": measurement["evaluation_time_utc"],
                "evaluation_horizon": "N_BARS",
                "provenance_status": "KNOWN",
            }
        )
    )


def require_consumer_origin(
    evidence: Mapping[str, Any],
    *,
    source: Mapping[str, Any],
    lineage: str,
    requested_use: str,
    expected_measurement: Mapping[str, Any],
) -> None:
    """Lab consumer check, additional to the existing canonical intake.

    Compare against source lineage, not just a caller-selected evidence label.
    Source receipts remain required evidence at a real integration boundary.
    """
    prov = evidence["outcome_evidence_provenance"]
    synthetic = source["source_kind"] == SYNTHETIC
    expected_class = "INTERNAL_SIMULATED_OUTCOME" if synthetic else "REPLAY_HISTORICAL"
    if synthetic and requested_use != SYNTHETIC_USE:
        raise ValueError("SYNTHETIC_EVIDENCE_NOT_OBSERVED_RESEARCH")
    if prov["market_observation_source"] != (SYNTHETIC if synthetic else "REPLAY_HISTORICAL"):
        raise ValueError("CONSUMER_ORIGIN_CHANGED")
    if prov["lineage_digest"] != lineage:
        raise ValueError("CONSUMER_SOURCE_LINEAGE_CHANGED")
    if evidence["actual_outcome_ref"] != expected_measurement["actual_outcome_ref"]:
        raise ValueError("CONSUMER_MEASUREMENT_REF_CHANGED")
    if (
        prov["instrument_id"] != source["canonical_instrument_id"]
        or prov["venue_native_id"] != source["venue_instrument_id"]
    ):
        raise ValueError("CONSUMER_INSTRUMENT_CHANGED")
    if prov["evaluation_timestamp_utc"] != expected_measurement["evaluation_time_utc"]:
        raise ValueError("CONSUMER_EVALUATION_TIME_CHANGED")
    if (
        evidence["outcome_semantic_class"] != expected_class
        or prov["outcome_semantic_class"] != expected_class
    ):
        raise ValueError("CONSUMER_SEMANTIC_CLASS_CHANGED")
    if evidence["evidence_pool_class"] != expected_class:
        raise ValueError("CONSUMER_POOL_CHANGED")
    if provenance_implies_productive_truth_v1(prov):
        raise ValueError("OFFLINE_INPUT_UPGRADED_TO_PRODUCTIVE_TRUTH")


def run_candidate(
    request: Mapping[str, Any],
    *,
    source_path: Path,
    source_sha256: str,
    as_of_utc: str,
    output: Path,
) -> dict[str, Any]:
    """Run exclusively on a new private ledger after source/time validation."""
    source_path, output = source_path.resolve(strict=True), output.resolve()
    if output == source_path.parent or output.is_relative_to(source_path.parent):
        raise ValueError("OUTPUT_WITHIN_SOURCE_DIRECTORY")
    raw = source_path.read_bytes()
    if digest_bytes(raw) != source_sha256:
        raise ValueError("SOURCE_SHA256_MISMATCH")
    source = json.loads(raw)
    readiness = inspect_source(request, source, as_of_utc=as_of_utc)
    if readiness["status"] != "READY":
        return readiness
    decision = dict(validate_decision_event_v0(request["decision"]))
    snapshot = build_o4_n_bars_bar_evidence_snapshot_v1(
        decision_event_ref=decision["record_id"],
        o4_bars=readiness["bars"],
        n_bars=request["n_bars"],
        decision_event=decision,
    )
    pipe = run_offline_n_bars_horizon_pipeline_v1(
        decision, snapshot, outcome_scalar_kind="LOG_RETURN"
    )
    obs, mat = pipe["evaluation_observation"], pipe["materialization"]
    lineage = digest_bytes(canonical({"request": request, "source_sha256": source_sha256}))
    ids = {
        "outcome_record_id": "out.candidate." + lineage[:40],
        "attribution_record_id": "attr.candidate." + lineage[:40],
        "counterfactual_record_id": "cf.candidate." + lineage[:40],
        "correlation_id": decision["correlation_id"],
        "event_time_utc": obs["evaluation_time_utc"],
        "code_sha": digest_bytes(Path(__file__).read_bytes()),
        "config_hash": lineage,
    }
    # Explicit nonproductive assembly. Synthetic binding is proposed here only;
    # production implementation should add it to the existing binding owner.
    bundle = evaluate_offline_bundle_v0(
        decision,
        obs,
        identity=ids,
        provenance_binding=ProvenanceProducerBindingV1.REPLAY_HISTORICAL,
        provenance_context=ProvenanceBindingContextV1(
            decision_event_ref=decision["record_id"],
            producer_id=__name__,
            ddo_ledger_environment=ExecutionEnvironment.DEV,
        ),
    )
    payload = {k: v for k, v in dict(bundle["outcome_record"]).items() if k != "content_hash"}
    payload["outcome_evidence_provenance"] = _provenance(
        decision, source, mat.measurement_evidence_artifact, lineage
    )
    outcome = dict(build_outcome_record_v0(payload))
    output.mkdir(parents=True, exist_ok=False)
    (output / "source_snapshot.json").write_bytes(raw)
    _write(
        output / "request.json",
        {"request": request, "as_of_utc": as_of_utc, "source_sha256": source_sha256},
    )
    ledger = AppendOnlyDdoLedgerV0(output / "candidate_ledger.jsonl")
    ledger.append(decision)
    for record in (outcome, bundle["attribution_record"], bundle["counterfactual_record"]):
        ledger.append(record)
    state = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id="ddo.lscope.semantic-repair." + lineage[:32],
        outcome=outcome,
        attribution=bundle["attribution_record"],
        counterfactual=bundle["counterfactual_record"],
        event_time_utc=obs["evaluation_time_utc"],
        correlation_id=decision["correlation_id"],
    )["learning_state_record"]
    evidence = export_learning_evidence_from_state_v1(state)
    require_consumer_origin(
        evidence,
        source=source,
        lineage=lineage,
        requested_use=request["requested_use"],
        expected_measurement=mat.measurement_evidence_artifact,
    )
    intake = dict(
        validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
        )
    )
    provenance = outcome["outcome_evidence_provenance"]
    if (
        dict(state["outcome_evidence_provenance"]) != provenance
        or evidence["outcome_evidence_provenance"] != provenance
    ):
        raise ValueError("PROVENANCE_CHANGED_IN_LEARNING_EXPORT")
    ledger.verify_integrity()
    if source_path.read_bytes() != raw:
        raise ValueError("SOURCE_CHANGED_DURING_CASE")
    for name, value in {
        "measurement": mat.measurement_evidence_artifact,
        "measurement_origin": {
            "source_kind": source["source_kind"],
            "clock_domain": source["clock_domain"],
            "source_sha256": source_sha256,
            "lineage_digest": lineage,
            "price_unit": source["price_unit"],
            "price_basis": source["price_basis"],
            "scalar_unit": "dimensionless natural logarithm",
            "measurement_payload_sha256": digest_bytes(
                canonical(mat.measurement_evidence_artifact)
            ),
            "actual_outcome_ref": mat.measurement_evidence_artifact["actual_outcome_ref"],
            "productive_authority": "NONE",
        },
        "evaluation_information_set": mat.evaluation_time_information_set_artifact,
        "evaluation_observation": obs,
        "outcome": outcome,
        "learning_state": dict(state),
        "learning_evidence": evidence,
        "intake": intake,
    }.items():
        _write(output / f"{name}.json", value)
    report = {
        "status": "COMPLETED_OFFLINE_CANDIDATE",
        "source_kind": source["source_kind"],
        "clock_domain": source["clock_domain"],
        "provenance_preserved": True,
        "outcome_semantic_class": evidence["outcome_semantic_class"],
        "market_observation_source": provenance["market_observation_source"],
        "source_lineage_digest": lineage,
        "source_unchanged": True,
        "economic_score_label": evidence["economic_score_label"],
        "intake_status": intake["status"],
        "productive_truth_claim": False,
        "real_market_origin_independently_proven": False,
        "productive_code_wired": False,
        "external_effect_authorized": False,
        "bar_times_preserved": snapshot["o4_bars"] == readiness["bars"],
    }
    _write(output / "report.json", report)
    return report
