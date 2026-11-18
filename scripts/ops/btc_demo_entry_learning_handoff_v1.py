"""Join a retained BTC Demo first fill to its original Double-Play decision offline."""

from datetime import datetime
from pathlib import Path

from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
)
from src.experiments.canonical_research_prepared_execution_v1 import publish_v1, read_v1
from src.learning.deterministic_decision_outcome_v0.current_decision_consumer_v1 import (
    is_double_play_decision_event_v0,
    require_current_double_play_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
    persist_evaluation_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1 import (
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


def btc_demo_entry_learning_handoff_v1(*, measurement, decision_ledger: Path, output_root: Path):
    if not decision_ledger.is_absolute() or decision_ledger.resolve() != decision_ledger:
        raise ValueError("BTC_DEMO_ORIGINAL_DECISION_LEDGER_REQUIRED")
    if not decision_ledger.is_file():
        raise FileNotFoundError(decision_ledger)
    rows = AppendOnlyDdoLedgerV0(decision_ledger).read_all()
    records = {row["record_id"]: row for row in rows}
    matches = [
        row["decision_event_ref"]
        for row in rows
        if row["schema_name"] == "double_play_entry_exit_observation"
        and (row.get("producer_canonical_payload") or {}).get("policy_decision_id")
        == measurement["decision_id"]
    ]
    if len(matches) != 1:
        raise ValueError("BTC_DEMO_ORIGINAL_DOUBLE_PLAY_DECISION_NOT_UNIQUE")
    (decision_ref,) = matches
    decision = records[decision_ref]
    dp = require_current_double_play_bundle_v1(
        records_by_id=records, decision_event_ref=decision_ref
    )
    if (
        not is_double_play_decision_event_v0(decision)
        or dp.policy_decision_id != measurement["decision_id"]
        or dp.instrument_id != measurement["instrument_id"]
        or dp.authoritative_decision_outcome.upper() != measurement["decision_outcome"]
        or decision["config_hash"] != measurement["config_digest"]
        or datetime.fromisoformat(decision["event_time_utc"].replace("Z", "+00:00"))
        > datetime.fromisoformat(measurement["envelope_created_utc"].replace("Z", "+00:00"))
    ):
        raise ValueError("BTC_DEMO_ORIGINAL_DOUBLE_PLAY_DECISION_MISMATCH")

    evaluated_at = measurement["confirmed_at_utc"]
    digest = measurement["source_digest"]
    ref = "btc.demo.confirmed-entry:" + digest
    horizon = "IMMEDIATE_POST_EVENT"
    identity = {
        "outcome_record_id": "out.demo." + digest,
        "attribution_record_id": "attr.demo." + digest,
        "counterfactual_record_id": "cf.demo." + digest,
        "correlation_id": ref,
        "event_time_utc": evaluated_at,
        "code_sha": decision["code_sha"],
        "config_hash": decision["config_hash"],
    }
    evaluation = evaluate_offline_bundle_v0(
        decision,
        {
            "decision_event_ref": decision_ref,
            "evaluation_horizon": horizon,
            "evaluation_time_utc": evaluated_at,
            "evaluation_time_information_set_ref": ref,
        },
        identity=identity,
        records_by_id=records,
        provenance_binding=ProvenanceProducerBindingV1.TESTNET_CONFIRMED_ENTRY,
        provenance_context=ProvenanceBindingContextV1(
            decision_event_ref=decision_ref,
            producer_id=__name__,
            instrument_id=measurement["instrument_id"],
            venue_native_id=measurement["venue_native_id"],
            cycle_id=decision["cycle_id"],
            trading_epoch=str(dp.trading_epoch),
            evaluation_horizon=horizon,
            decision_timestamp_utc=decision["event_time_utc"],
            evaluation_timestamp_utc=evaluated_at,
            order_environment_label="TESTNET",
            lineage_digest=digest,
        ),
    )
    bundle = {
        role: evaluation[f"{role}_record"] for role in ("outcome", "attribution", "counterfactual")
    }
    refs = {decision_ref, dp.observation_ref, dp.input_evidence_ref} - {None}
    pending = list(refs)
    while pending:
        parents = set(records[pending.pop()]["causal_parent_ids"]) - refs
        pending.extend(parents)
        refs.update(parents)

    parent = EvaluationReceiptArchiveV1(output_root)
    workspace = EvaluationReceiptArchiveV1(parent.safe_path_v1(Path("demo-learning") / digest))
    scope = derive_learning_state_scope_id_v1(
        session_id=measurement["session_id"],
        account_identity=measurement["episode_id"],
        code_sha=decision["code_sha"],
        config_hash=decision["config_hash"],
    )
    with workspace.lease_v1():
        publish_v1(workspace.safe_path_v1("measurement.json"), measurement)
        ledger = AppendOnlyDdoLedgerV0(workspace.safe_path_v1(LEDGER_FILENAME_DEFAULT))
        for row in rows:
            if row["record_id"] in refs:
                ledger.append(row)
        persist_evaluation_bundle_v0(ledger, **bundle)
        state = ingest_evaluation_bundle_into_learning_state_v1(
            ledger,
            state_scope_id=scope,
            **bundle,
            event_time_utc=evaluated_at,
            correlation_id=ref,
            cycle_id=decision["cycle_id"],
            expected_prior_state_record_ref=None,
        )["learning_state_record"]
        result = {
            "schema": "btc_demo_entry_learning_handoff.v1",
            "authority": "NONE",
            "decision_event_ref": decision_ref,
            "measurement": measurement,
            "learning_evidence": export_learning_evidence_from_state_v1(state),
        }
        path = workspace.safe_path_v1("result.json")
        publish_v1(path, result)
        return read_v1(path)
