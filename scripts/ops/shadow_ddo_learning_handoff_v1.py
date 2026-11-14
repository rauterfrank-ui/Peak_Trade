"""Consume a verified I17 O4 receipt through the offline DDO owners."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from scripts.ops.run_integrated_paper_shadow_observation_wallclock_session_v1 import (
    reverify_shadow_outcome_receipt_v1,
)
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
)
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1, publish_v1, read_v1
from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.common_v0 import require_event_time_utc
from src.learning.deterministic_decision_outcome_v0.current_decision_consumer_v1 import (
    require_current_double_play_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
    persist_evaluation_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_runtime_productive_host_v1 import (
    derive_productive_n_bars_evaluation_identity_v1,
    ledger_records_index_v1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
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
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
    validate_n_bars_measurement_artifacts_v1,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    O4_SNAPSHOT_SCHEMA_NAME,
    O4_SNAPSHOT_SCHEMA_VERSION,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_bindings_v1 import (
    ProvenanceBindingContextV1,
    ProvenanceProducerBindingV1,
)

_REPO = Path(__file__).resolve().parents[2]


def _original_records(evidence_root: Path, selection: dict):
    manifest_path = evidence_root / "evidence_manifest.sha256"
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != selection["shadow_manifest_sha256"]:
        raise ValueError("SHADOW_HANDOFF_MANIFEST_CHANGED")
    pins = {}
    for line in manifest_bytes.decode().splitlines():
        if line:
            digest, name = line.split("  ", 1)
            pins[name] = digest

    def check(path: Path):
        raw = path.read_bytes()
        if path.is_symlink() or hashlib.sha256(raw).hexdigest() != pins.get(path.name):
            raise ValueError("SHADOW_HANDOFF_SOURCE_CHANGED:" + path.name)
        return raw

    ledger_path = evidence_root / LEDGER_FILENAME_DEFAULT
    check(ledger_path)
    records = ledger_records_index_v1(AppendOnlyDdoLedgerV0(ledger_path))
    check(ledger_path)
    fixture = json.loads(check(evidence_root / "prereg.json"))["fixture_non_authoritative"]
    if type(fixture) is not bool:
        raise ValueError("SHADOW_HANDOFF_FIXTURE_CLASS_REQUIRED")
    if not fixture:
        config = json.loads(check(evidence_root / "config_snapshot.json"))
        if (
            config.get("schema") != "productive_wallclock_runtime_v1"
            or config.get("use_real_network") is not True
        ):
            raise ValueError("SHADOW_HANDOFF_RECORDED_NETWORK_SOURCE_REQUIRED")

    ref = selection["decision_event_ref"]
    bundle = require_current_double_play_bundle_v1(records_by_id=records, decision_event_ref=ref)
    if (
        bundle.semantic_digest != selection["decision_semantic_digest"]
        or bundle.input_digest != selection["decision_input_digest"]
        or bundle.observation_ref != selection["observation_ref"]
        or bundle.input_evidence_ref != selection["input_evidence_ref"]
    ):
        raise ValueError("SHADOW_HANDOFF_DECISION_BUNDLE_CHANGED")
    refs = {ref, bundle.observation_ref, bundle.input_evidence_ref}
    pending = list(refs)
    while pending:
        record = records[pending.pop()]
        parents = set(record["causal_parent_ids"]) - refs
        pending.extend(parents)
        refs.update(parents)
    return {ref: record for ref, record in records.items() if ref in refs}, bundle, fixture


def _evaluate(receipt: dict, records: dict, *, trading_epoch: int):
    selected = receipt["shadow_decision"]
    market = receipt["market_observation"]
    ref = selected["decision_event_ref"]
    decision = records[ref]
    if UNKNOWN in (decision["code_sha"], decision["config_hash"]):
        raise ValueError("SHADOW_HANDOFF_DECISION_CONFIGURATION_REQUIRED")
    request = market["request"]
    snapshot = {
        "schema_name": O4_SNAPSHOT_SCHEMA_NAME,
        "schema_version": O4_SNAPSHOT_SCHEMA_VERSION,
        "decision_event_ref": ref,
        "horizon_start_time_utc": request["horizon_start_time_utc"],
        "o4_interval_id": request["o4_interval_id"],
        "n_bars": request["n_bars"],
        "o4_bars": [json.loads(row["original_bar_json"]) for row in market["source_receipts"]],
    }
    pipeline = run_offline_n_bars_horizon_pipeline_v1(
        decision, snapshot, outcome_scalar_kind="LOG_RETURN"
    )
    observation = pipeline["evaluation_observation"]
    materialization = pipeline["materialization"]
    measurement = dict(materialization.measurement_evidence_artifact)
    info = dict(materialization.evaluation_time_information_set_artifact)
    validate_n_bars_measurement_artifacts_v1(observation, measurement, info)
    if any(measurement.get(key) != value for key, value in market["measurement"].items()):
        raise ValueError("SHADOW_HANDOFF_DDO_MEASUREMENT_MISMATCH")

    # Keep the verified evaluation clock without dropping sub-microsecond digits.
    known_at_utc = require_event_time_utc(
        market["evaluated_at_utc"].removesuffix("+00:00") + "Z"
        if market["evaluated_at_utc"].endswith("+00:00")
        else market["evaluated_at_utc"],
        "shadow_evaluated_at_utc",
    )
    # Keep the market window in the evaluation identity as well as the receipt clock.
    horizon = digest_v1({key: request[key] for key in ("horizon_start_time_utc", "n_bars")})
    identity = derive_productive_n_bars_evaluation_identity_v1(
        decision_record_id=ref,
        evaluation_time_utc=known_at_utc,
        correlation_id=f"ddo.sl.i17.{horizon}",
        code_sha=decision["code_sha"],
        config_hash=decision["config_hash"],
    )
    evaluation = evaluate_offline_bundle_v0(
        decision,
        observation,
        identity=identity,
        records_by_id=records,
        provenance_binding=ProvenanceProducerBindingV1.I17_SHADOW_COUNTERFACTUAL,
        provenance_context=ProvenanceBindingContextV1(
            decision_event_ref=ref,
            producer_id=__name__,
            instrument_id=selected["canonical_instrument_id"],
            venue_native_id=selected["venue_instrument_id"],
            cycle_id=decision["cycle_id"],
            trading_epoch=str(trading_epoch),
            outcome_scalar_kind="LOG_RETURN",
            evaluation_horizon="N_BARS",
            decision_timestamp_utc=decision["event_time_utc"],
            evaluation_timestamp_utc=observation["evaluation_time_utc"],
            ddo_ledger_environment=ExecutionEnvironment.DEV,
            lineage_digest=receipt["exact_content_digest"],
        ),
    )
    bundle = {
        role: evaluation[f"{role}_record"] for role in ("outcome", "attribution", "counterfactual")
    }
    return bundle, identity, measurement, info


def shadow_ddo_learning_handoff_v1(
    *,
    root: Path,
    cycle_key: str,
    evidence_root: Path,
    o4_mark_archive: Path,
    outcome_receipt: Path,
    expected_digest: str | None = None,
    verified_receipt_sink: list[dict] | None = None,
):
    """Ingest once or reverify a completed transition using both source archives."""
    if (
        not root.is_absolute()
        or root.resolve() != root
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", cycle_key)
    ):
        raise ValueError("SHADOW_HANDOFF_OFFLINE_WORKSPACE_REQUIRED")
    source_roots = (_REPO, evidence_root.resolve(), o4_mark_archive.resolve())
    if outcome_receipt.resolve().is_relative_to(root) or any(
        root.is_relative_to(path) or path.is_relative_to(root) for path in source_roots
    ):
        raise ValueError("SHADOW_HANDOFF_SOURCE_AND_WORKSPACE_MUST_BE_SEPARATE")
    receipt = reverify_shadow_outcome_receipt_v1(
        evidence_root=evidence_root,
        o4_mark_archive=o4_mark_archive,
        outcome_receipt=outcome_receipt,
    )
    selected = receipt["shadow_decision"]
    records, decision_bundle, fixture = _original_records(evidence_root.resolve(), selected)
    bundle, identity, measurement, info = _evaluate(
        receipt, records, trading_epoch=decision_bundle.trading_epoch
    )
    outcome = bundle["outcome"]
    scope_id = derive_learning_state_scope_id_v1(
        session_id=selected["session_id"],
        config_hash=outcome["config_hash"],
        code_sha=outcome["code_sha"],
    )
    fingerprint = compute_evaluation_bundle_fingerprint_v1(
        outcome_content_hash=outcome["content_hash"],
        attribution_content_hash=bundle["attribution"]["content_hash"],
        counterfactual_content_hash=bundle["counterfactual"]["content_hash"],
    )
    state_ref = derive_learning_state_record_id_v1(state_scope_id=scope_id, fingerprint=fingerprint)
    binding = {
        "schema_version": "i17_shadow_ddo_learning_binding_v1",
        "cycle_key": cycle_key,
        "authority": "NONE",
        "source_class": "TEST_ONLY_SYNTHETIC" if fixture else "DECLARED_OFFLINE_DATA",
        "outcome_receipt_digest": receipt["exact_content_digest"],
        "shadow_manifest_sha256": selected["shadow_manifest_sha256"],
        "original_record_hashes": {ref: row["content_hash"] for ref, row in records.items()},
        "measurement": measurement,
        "evaluation_information_set": info,
        "learning_state_record_ref": state_ref,
        "evaluation_bundle_fingerprint": fingerprint,
    }

    # A single case per workspace key also fences conflicts after a partial write.
    workspace = EvaluationReceiptArchiveV1(
        EvaluationReceiptArchiveV1(root).safe_path_v1(Path("shadow-ddo-learning") / cycle_key)
    )
    binding_path = workspace.safe_path_v1("binding.json")
    result_path = workspace.safe_path_v1("result.json")
    ledger = AppendOnlyDdoLedgerV0(workspace.safe_path_v1(LEDGER_FILENAME_DEFAULT))
    digest = digest_v1(binding)

    if expected_digest is None:
        with workspace.lease_v1():
            publish_v1(binding_path, binding)
            for row in records.values():
                ledger.append(row)
            persist_evaluation_bundle_v0(ledger, **bundle)
            state = ingest_evaluation_bundle_into_learning_state_v1(
                ledger,
                state_scope_id=scope_id,
                **bundle,
                event_time_utc=identity["event_time_utc"],
                correlation_id=identity["correlation_id"],
                cycle_id=outcome["cycle_id"],
                expected_prior_state_record_ref=None,
            )["learning_state_record"]
            publish_v1(result_path, _result(binding, digest, state))
    elif digest != expected_digest:
        raise ValueError("SHADOW_HANDOFF_DIGEST_MISMATCH")

    if read_v1(binding_path) != binding:
        raise ValueError("SHADOW_HANDOFF_BINDING_MISMATCH")
    stored = ledger_records_index_v1(ledger)
    for original in (*records.values(), *bundle.values()):
        if stored[original["record_id"]]["content_hash"] != original["content_hash"]:
            raise ValueError("SHADOW_HANDOFF_LEDGER_MISMATCH")
    state = stored[state_ref]
    if (
        state["state_scope_id"] != scope_id
        or state["state_version"] != 1
        or state["decision_event_ref"] != selected["decision_event_ref"]
        or state["outcome_record_ref"] != outcome["record_id"]
        or state["evaluation_bundle_fingerprint"] != fingerprint
        or state["outcome_evidence_provenance"] != outcome["outcome_evidence_provenance"]
    ):
        raise ValueError("SHADOW_HANDOFF_STATE_MISMATCH")
    result = _result(binding, digest, state)
    if read_v1(result_path) != result:
        raise ValueError("SHADOW_HANDOFF_RESULT_MISMATCH")
    if verified_receipt_sink is not None:
        verified_receipt_sink.append(receipt)
    return result


def _result(binding, digest, state):
    return {
        "schema_version": "i17_shadow_ddo_learning_result_v1",
        "authority": "NONE",
        "handoff_digest": digest,
        "outcome_receipt_digest": binding["outcome_receipt_digest"],
        "source_class": binding["source_class"],
        "learning_evidence": export_learning_evidence_from_state_v1(state),
    }
