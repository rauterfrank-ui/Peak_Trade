"""Import one verified simulated Paper episode into the offline learning ledger."""

from pathlib import Path

from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.experiments.canonical_research_prepared_execution_v1 import publish_v1, read_v1
from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    NET_PNL_QUOTE_CURRENCY_V1,
    SIMULATED_POSITION_LIFECYCLE_V1,
    UNKNOWN,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
    persist_evaluation_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
    compute_evaluation_bundle_fingerprint_v1,
    derive_learning_state_record_id_v1,
    derive_learning_state_scope_id_v1,
    ingest_evaluation_bundle_into_learning_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    LEDGER_FILENAME_DEFAULT,
    AppendOnlyDdoLedgerV0,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_bindings_v1 import (
    ProvenanceBindingContextV1,
    ProvenanceProducerBindingV1,
)
from src.ops.bounded_peaktrade_system_composition_v1.paper_episode_outcome_v1 import (
    read_paper_episode_outcome_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_core_entry_assessment_frame_v1 import (
    read_current_core_entry_assessment_frame_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    parse_current_productive_sidestate_confirmation_cursor_v1,
)

_REPO = Path(__file__).resolve().parents[2]


def _evaluation(measurement):
    opening = measurement["fill_bindings"][0]
    digest = measurement["outcome_digest"]
    observed = measurement["observed_at_utc"]
    decision_id = opening["decision_id"]
    decision_digest = opening["decision_sha256"]
    correlation_id = f"paper.episode:{digest}"
    code_sha = measurement["source_tree_sha256"]
    config_hash = opening["decision_config_sha256"]
    evidence_refs = [f"paper.archive.decision:{decision_digest}"]
    market_ref = None
    if "decision_evidence" in opening:
        original = opening["decision_evidence"]
        if (
            original["schema"] != "paper_original_decision_cursor.v1"
            or original["scope"] != "ORIGINAL_ASSESSMENT_AND_POST_DECISION_CURSOR"
        ):
            raise ValueError("PAPER_LEARNING_DECISION_EVIDENCE_SCOPE_MISMATCH")
        cursor = parse_current_productive_sidestate_confirmation_cursor_v1(original["cursor"])
        bodies = read_current_core_entry_assessment_frame_v1(cursor)
        frame = cursor.entry_assessment_frame
        if (
            (cursor.instrument_id, cursor.venue_native_id)
            != (measurement["instrument_id"], measurement["venue_native_id"])
            or bodies["parent"]["decision_id"] != decision_id
            or bodies["parent"]["config_digest"] != config_hash
            or str(bodies["parent"]["trading_epoch"]) != opening["trading_epoch"]
            or bodies["parent"]["decision_outcome"] != opening["decision_outcome"]
            or frame["components"]["parent"]["semantic_digest"] != decision_digest
        ):
            raise ValueError("PAPER_LEARNING_ORIGINAL_DECISION_MISMATCH")
        evidence_refs.append(f"paper.archive.assessment:{frame['digest']}")
        market_ref = f"paper.archive.market:{frame['market_context']['input_digest']}"
        evidence_refs.append(market_ref)
    # Project the archived Core decision. Fields requiring a decision-time DDO
    # snapshot remain unknown on historical Paper runs.
    decision = build_decision_event_v0(
        {
            "schema_name": "decision_event",
            "schema_version": "decision_event_v0",
            "record_id": decision_id,
            "event_id": f"paper.decision:{decision_digest}",
            "event_time_utc": opening["decision_observed_at_utc"],
            "correlation_id": f"paper.decision:{decision_digest}",
            "cycle_id": opening["cycle_id"],
            "decision_type": UNKNOWN,
            "decision_result": UNKNOWN,
            "reason_codes": [],
            "hard_block_reasons": [],
            "authority_owner": UNKNOWN,
            "producer_id": __name__,
            "code_sha": code_sha,
            "config_hash": config_hash,
            "evidence_hash": decision_digest,
            "evidence_source_refs": evidence_refs,
            **({"market_snapshot_ref": market_ref} if market_ref is not None else {}),
        }
    )
    outcome_ref = f"paper.outcome.measurement:{digest}"
    identity = {
        "outcome_record_id": f"out.paper.{digest}",
        "attribution_record_id": f"attr.paper.{digest}",
        "counterfactual_record_id": f"cf.paper.{digest}",
        "correlation_id": correlation_id,
        "event_time_utc": observed,
        "code_sha": code_sha,
        "config_hash": config_hash,
    }
    result = evaluate_offline_bundle_v0(
        decision,
        {
            "decision_event_ref": decision_id,
            "evaluation_horizon": SIMULATED_POSITION_LIFECYCLE_V1,
            "evaluation_time_utc": observed,
            "actual_outcome_ref": outcome_ref,
            "evaluation_time_information_set_ref": outcome_ref,
            "declared_decision_score": UNKNOWN,
        },
        identity=identity,
        provenance_binding=ProvenanceProducerBindingV1.BOUNDED_PAPER_POSITION,
        provenance_context=ProvenanceBindingContextV1(
            decision_event_ref=decision_id,
            producer_id=__name__,
            instrument_id=measurement["instrument_id"],
            venue_native_id=measurement["venue_native_id"],
            cycle_id=opening["cycle_id"],
            trading_epoch=opening["trading_epoch"],
            outcome_scalar_kind=NET_PNL_QUOTE_CURRENCY_V1,
            evaluation_horizon=SIMULATED_POSITION_LIFECYCLE_V1,
            decision_timestamp_utc=opening["decision_observed_at_utc"],
            evaluation_timestamp_utc=observed,
            ddo_ledger_environment=ExecutionEnvironment.DEV,
            lineage_digest=digest,
        ),
    )
    bundle = {
        role: result[f"{role}_record"] for role in ("outcome", "attribution", "counterfactual")
    }
    scope = derive_learning_state_scope_id_v1(
        session_id=measurement["episode_id"],
        account_identity=measurement["session_id"],
        code_sha=code_sha,
        config_hash=config_hash,
    )
    return decision, bundle, scope


def _read_result(ledger, decision, bundle, scope, measurement):
    for expected in (decision, *bundle.values()):
        if ledger.get(expected["record_id"])["content_hash"] != expected["content_hash"]:
            raise ValueError("PAPER_LEARNING_LEDGER_MISMATCH")
    fingerprint = compute_evaluation_bundle_fingerprint_v1(
        outcome_content_hash=bundle["outcome"]["content_hash"],
        attribution_content_hash=bundle["attribution"]["content_hash"],
        counterfactual_content_hash=bundle["counterfactual"]["content_hash"],
    )
    state = ledger.get(
        derive_learning_state_record_id_v1(state_scope_id=scope, fingerprint=fingerprint)
    )
    outcome = bundle["outcome"]
    if (
        state["state_scope_id"] != scope
        or state["state_version"] != 1
        or state["prior_state_record_ref"] is not None
        or state["decision_event_ref"] != decision["record_id"]
        or state["evaluation_bundle_fingerprint"] != fingerprint
        or state["outcome_record_ref"] != outcome["record_id"]
        or state["last_actual_outcome_ref"] != outcome["actual_outcome_ref"]
        or state["outcome_evidence_provenance"] != outcome["outcome_evidence_provenance"]
    ):
        raise ValueError("PAPER_LEARNING_STATE_MISMATCH")
    evidence = export_learning_evidence_from_state_v1(state)
    admission = dict(
        validate_canonical_optimization_universe_learning_input_v1(
            CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
        )
    )
    if (
        admission["status"] != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
        or admission["learning_evidence_digest"] != evidence["content_hash"]
    ):
        raise ValueError("PAPER_OPTIMIZATION_INPUT_REJECTED")
    return {
        "schema": "paper_episode_learning_handoff.v1",
        "authority": "NONE",
        "measurement": measurement,
        "learning_evidence": evidence,
        "optimization_admission": admission,
    }


def paper_episode_learning_handoff_v1(
    *,
    archive_root: Path,
    episode_id: str,
    output_root: Path,
    verify: bool = False,
    expected_lane_id: str | None = None,
    require_measurement=None,
) -> dict:
    """Persist or reverify a Paper episode using the original archive and DDO."""
    source = archive_root.resolve()
    if (
        not output_root.is_absolute()
        or output_root != output_root.resolve()
        or output_root.is_relative_to(source)
        or source.is_relative_to(output_root)
        or output_root.is_relative_to(_REPO)
        or _REPO.is_relative_to(output_root)
    ):
        raise ValueError("PAPER_LEARNING_SEPARATE_OFFLINE_WORKSPACE_REQUIRED")
    workspace = EvaluationReceiptArchiveV1(output_root)
    folder = Path("paper-episodes") / episode_id
    measurement_path = workspace.safe_path_v1(folder / "measurement.json")
    result_path = workspace.safe_path_v1(folder / "result.json")
    # Existing imported episodes retain their original measurement and ledger
    # identities. Fresh XPERP imports carry the already archived decision data.
    # Never retrofit an append-only record or silently downgrade an enriched one.
    include_decision_evidence = True
    if measurement_path.exists() or measurement_path.is_symlink():
        stored = read_v1(measurement_path)
        include_decision_evidence = any(
            "decision_evidence" in binding for binding in stored["fill_bindings"]
        )
    measurement = read_paper_episode_outcome_v1(
        archive_root,
        episode_id,
        expected_lane_id=expected_lane_id,
        include_decision_evidence=include_decision_evidence,
    )
    if require_measurement is not None:
        require_measurement(measurement)
    decision, bundle, scope = _evaluation(measurement)
    ledger = AppendOnlyDdoLedgerV0(workspace.safe_path_v1(folder / LEDGER_FILENAME_DEFAULT))
    if verify:
        result = _read_result(ledger, decision, bundle, scope, measurement)
    else:
        with workspace.lease_v1():
            publish_v1(measurement_path, measurement)
            ledger.append(decision)
            persist_evaluation_bundle_v0(ledger, **bundle)
            ingest_evaluation_bundle_into_learning_state_v1(
                ledger,
                state_scope_id=scope,
                **bundle,
                event_time_utc=measurement["observed_at_utc"],
                correlation_id=bundle["outcome"]["correlation_id"],
                cycle_id=decision["cycle_id"],
                expected_prior_state_record_ref=None,
            )
            result = _read_result(ledger, decision, bundle, scope, measurement)
            publish_v1(result_path, result)
    if read_v1(measurement_path) != measurement or read_v1(result_path) != result:
        raise ValueError("PAPER_LEARNING_STORED_HANDOFF_MISMATCH")
    return result
