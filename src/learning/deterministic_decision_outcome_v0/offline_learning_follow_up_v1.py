"""Schedule and remeasure a DDO decision class from the previous offline learning state."""

from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from collections.abc import Mapping
from contextlib import contextmanager
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_OUTCOME_RECORD,
)
from src.learning.deterministic_decision_outcome_v0.current_decision_consumer_v1 import (
    is_double_play_decision_event_v0,
    require_current_double_play_bundle_v1,
)
from src.learning.deterministic_decision_outcome_v0.durable_evidence_path_v0 import (
    DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
    resolve_ddo_durable_evidence_path_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
    persist_evaluation_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.evaluation_runtime_productive_host_v1 import (
    derive_productive_n_bars_evaluation_identity_v1,
    ledger_records_index_v1,
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
from src.learning.deterministic_decision_outcome_v0.learning_scope_guard_v1 import (
    require_learning_scope_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_state_record_v0 import (
    learning_event_time_key_v0,
    learning_state_head_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
    validate_n_bars_measurement_artifacts_v1,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    unix_seconds_to_event_time_utc,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_bindings_v1 import (
    ProvenanceBindingContextV1,
    ProvenanceProducerBindingV1,
)

_PLAN = "ddo_offline_follow_up_plan_v1"
_MEASUREMENT = "ddo_offline_follow_up_measurement_v1"
_RESULT = "ddo_offline_follow_up_result_v1"
_SOURCE = "SYNTHETIC_OFFLINE"
_CLASS = "INTERNAL_SIMULATED_OUTCOME"
_SCOPE_FIELDS = {
    "session_id",
    "account_scope",
    "code_sha",
    "config_hash",
    "instrument_id",
    "native_instrument_id",
    "venue",
    "n_bars",
}


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(value: Any) -> str:
    return sha256(_json_bytes(value)).hexdigest()


def _read(path: Path, schema: str, expected_digest: str | None = None) -> dict[str, Any]:
    if path.is_symlink():
        raise DdoValidationError("SL_FOLLOW_UP_SYMLINK")
    packet = json.loads(path.read_bytes())
    body = packet["body"]
    if (
        body["schema_version"] != schema
        or packet["sha256"] != _digest(body)
        or (expected_digest is not None and packet["sha256"] != expected_digest)
    ):
        raise DdoValidationError("SL_FOLLOW_UP_RECEIPT_DIGEST")
    return body


def _publish(path: Path, body: dict[str, Any]) -> str:
    digest = _digest(body)
    raw = _json_bytes({"body": body, "sha256": digest}) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent) as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
        try:
            os.link(stream.name, path)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes() != raw:
                raise DdoValidationError("SL_FOLLOW_UP_IMMUTABLE_CONFLICT") from None
        for parent in (path.parent, *path.parent.parents):
            fd = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    return digest


def _scoped_path(root: Path, path: Path) -> Path:
    if path.resolve() != path or not path.is_relative_to(root):
        raise DdoValidationError("SL_FOLLOW_UP_UNSAFE_PATH")
    return path


def _cycle_directory(root: Path, cycle_key: str) -> Path:
    if (
        not root.is_absolute()
        or root.resolve() != root
        or root.is_relative_to(Path(__file__).resolve().parents[3])
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", cycle_key)
    ):
        raise DdoValidationError("SL_FOLLOW_UP_OFFLINE_WORKSPACE_REQUIRED")
    return _scoped_path(root, root / "sl-follow-up" / cycle_key)


def _read_plan(directory: Path, expected_digest: str | None = None) -> dict[str, Any]:
    plan = _read(directory / "plan.json", _PLAN, expected_digest)
    if plan["cycle_key"] != directory.name or plan["authority"] != "NONE":
        raise DdoValidationError("SL_FOLLOW_UP_PLAN_SCOPE_MISMATCH")
    return plan


def offline_learning_ledger_path_v1(root: Path, account_scope: str) -> Path:
    """Address the existing DDO owner inside the explicit DEV workspace."""
    path = resolve_ddo_durable_evidence_path_v1(
        runtime_state_root=root,
        environment="dev",
        account_scope=account_scope,
        system_scope=DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
    )
    _scoped_path(root, path.with_name(path.name + ".writer.lock"))
    return _scoped_path(root, path)


def _scope_id(scope: Mapping[str, Any]) -> str:
    if (
        scope.keys() != _SCOPE_FIELDS
        or type(scope["n_bars"]) is not int
        or scope["n_bars"] < 2
        or any(
            not isinstance(scope[key], str) or scope[key] in {"", "UNKNOWN"}
            for key in _SCOPE_FIELDS - {"n_bars"}
        )
    ):
        raise DdoValidationError("SL_FOLLOW_UP_SCOPE_UNBOUND")
    return derive_learning_state_scope_id_v1(
        session_id=_digest({"scope": dict(scope), "source": _SOURCE}),
        account_identity=scope["account_scope"],
        config_hash=scope["config_hash"],
        code_sha=scope["code_sha"],
    )


def _require_scoped_outcome(outcome: Mapping[str, Any], scope: Mapping[str, Any]) -> None:
    target = {
        "instrument_id": scope["instrument_id"],
        "native_instrument_id": scope["native_instrument_id"],
        "venue": scope["venue"],
        "n_bars": scope["n_bars"],
    }
    require_learning_scope_v1(
        outcome=outcome,
        scope={
            "account_identity": scope["account_scope"],
            "code_sha": scope["code_sha"],
            "config_hash": scope["config_hash"],
            "outcome_semantic_class": _CLASS,
            "market_observation_source": _SOURCE,
            "external_capital_flow_class": "NONE",
            "outcome_scalar_kind": "LOG_RETURN",
            "evaluation_horizon": "N_BARS",
            "metric_version": "FIRST_LAST_CLOSE_LOG_RETURN_V1",
            "evidence_pool_class": _CLASS,
            "target": target,
        },
        target=target,
    )
    provenance = outcome["outcome_evidence_provenance"]
    if (
        provenance["instrument_id"] != scope["instrument_id"]
        or provenance["venue_native_id"] != scope["native_instrument_id"]
        or not str(outcome["actual_outcome_ref"]).startswith("ddo.outcome.measure.")
    ):
        raise DdoValidationError("SL_FOLLOW_UP_OUTCOME_SCOPE_MISMATCH")


def _candidate(records: Mapping[str, Any], decision_ref: str, scope: Mapping[str, Any]) -> dict:
    decision = records[decision_ref]
    if not is_double_play_decision_event_v0(decision) or any(
        decision[key] != scope[key] for key in ("code_sha", "config_hash")
    ):
        raise DdoValidationError("SL_FOLLOW_UP_DECISION_SCOPE_MISMATCH")
    bundle = require_current_double_play_bundle_v1(
        records_by_id=records, decision_event_ref=decision_ref
    )
    if bundle.instrument_id != scope["instrument_id"] or bundle.input_evidence_ref is None:
        raise DdoValidationError("SL_FOLLOW_UP_ORIGINAL_DECISION_UNBOUND")
    return {
        "decision_ref": decision_ref,
        "decision_hash": decision["content_hash"],
        "decision_class": bundle.authoritative_decision_outcome,
        "decision_time_utc": decision["event_time_utc"],
        "observation_ref": bundle.observation_ref,
        "observation_hash": records[bundle.observation_ref]["content_hash"],
        "input_evidence_ref": bundle.input_evidence_ref,
        "input_evidence_hash": records[bundle.input_evidence_ref]["content_hash"],
        "available_at_utc": max(
            (
                records[ref]["event_time_utc"]
                for ref in (decision_ref, bundle.observation_ref, bundle.input_evidence_ref)
            ),
            key=learning_event_time_key_v0,
        ),
    }


def prepare_offline_learning_follow_up_v1(
    root: Path, cycle_key: str, request: dict[str, Any]
) -> dict[str, Any]:
    """Read the last learned state and freeze the choice before seeing its outcome."""
    if request.keys() != {"scope", "planned_at_utc", "candidate_decision_refs"}:
        raise DdoValidationError("SL_FOLLOW_UP_PLAN_REQUEST_SHAPE")
    directory = _cycle_directory(root, cycle_key)
    path = directory / "plan.json"
    if path.exists():
        plan = _read_plan(directory)
        if plan["request"] != request:
            raise DdoValidationError("SL_FOLLOW_UP_IMMUTABLE_CONFLICT")
        return {"plan_digest": _digest(plan), "plan": plan}
    scope = request["scope"]
    state_scope_id = _scope_id(scope)
    planned_at = learning_event_time_key_v0(request["planned_at_utc"])
    ledger = AppendOnlyDdoLedgerV0(offline_learning_ledger_path_v1(root, scope["account_scope"]))
    records = ledger_records_index_v1(ledger)
    prior = learning_state_head_v0(records.values(), state_scope_id=state_scope_id)
    prior_choice = None
    if prior is not None:
        if learning_event_time_key_v0(prior["event_time_utc"]) >= planned_at:
            raise DdoValidationError("SL_FOLLOW_UP_PRIOR_NOT_YET_KNOWN")
        _require_scoped_outcome(records[prior["outcome_record_ref"]], scope)
        prior_choice = _candidate(records, prior["decision_event_ref"], scope)

    refs = request["candidate_decision_refs"]
    if not isinstance(refs, list) or not refs or len(refs) != len(set(refs)):
        raise DdoValidationError("SL_FOLLOW_UP_DISTINCT_CANDIDATES_REQUIRED")
    already_evaluated = {
        row["decision_event_ref"]
        for row in records.values()
        if row["schema_name"] == SCHEMA_NAME_OUTCOME_RECORD
    }
    candidates = [_candidate(records, ref, scope) for ref in refs]
    for item in candidates:
        if (
            item["decision_ref"] in already_evaluated
            or learning_event_time_key_v0(item["available_at_utc"]) > planned_at
            or (
                prior is not None
                and learning_event_time_key_v0(item["decision_time_utc"])
                <= learning_event_time_key_v0(prior["event_time_utc"])
            )
        ):
            raise DdoValidationError("SL_FOLLOW_UP_CANDIDATE_NOT_PROSPECTIVE")
    candidates.sort(
        key=lambda item: (
            learning_event_time_key_v0(item["decision_time_utc"]),
            item["decision_ref"],
        )
    )
    chosen = next(
        (
            item
            for item in candidates
            if prior_choice is not None and item["decision_class"] == prior_choice["decision_class"]
        ),
        candidates[0],
    )
    instant, fraction = planned_at
    horizon_start = instant.replace(minute=0, second=0)
    if horizon_start != instant or int(fraction):
        horizon_start += timedelta(hours=1)
    plan = {
        "schema_version": _PLAN,
        "authority": "NONE",
        "cycle_key": cycle_key,
        "request": request,
        "state_scope_id": state_scope_id,
        "prior_state_record_ref": None if prior is None else prior["record_id"],
        "prior_state_content_hash": None if prior is None else prior["content_hash"],
        "prior_decision_class": None if prior_choice is None else prior_choice["decision_class"],
        "chronological_first_ref": candidates[0]["decision_ref"],
        "horizon_start_time_utc": horizon_start.isoformat() + "Z",
        "selected": chosen,
        "candidates": candidates,
    }
    return {"plan_digest": _publish(path, plan), "plan": plan}


def _materialize_measurement(
    plan: dict[str, Any], records: Mapping[str, Any], source: dict[str, Any]
) -> dict[str, Any]:
    request = plan["request"]
    scope = request["scope"]
    ref = plan["selected"]["decision_ref"]
    if _candidate(records, ref, scope) != plan["selected"]:
        raise DdoValidationError("SL_FOLLOW_UP_SELECTED_DECISION_MISMATCH")
    if source.keys() != {"snapshot", "known_at_utc"}:
        raise DdoValidationError("SL_FOLLOW_UP_MEASUREMENT_SOURCE_SHAPE")
    snapshot = source["snapshot"]
    bars = snapshot["o4_bars"]
    if (
        snapshot["n_bars"] != scope["n_bars"]
        or snapshot["horizon_start_time_utc"] != plan["horizon_start_time_utc"]
        or not bars
        or unix_seconds_to_event_time_utc(
            min(bar["bar_open_time"] for bar in bars), "first_bar_open"
        )
        != plan["horizon_start_time_utc"]
        or any(
            (bar["canonical_instrument_id"], bar["venue_instrument_id"], bar["venue"])
            != (scope["instrument_id"], scope["native_instrument_id"], scope["venue"])
            for bar in bars
        )
    ):
        raise DdoValidationError("SL_FOLLOW_UP_MEASUREMENT_SCOPE_MISMATCH")
    pipeline = run_offline_n_bars_horizon_pipeline_v1(
        records[ref], snapshot, outcome_scalar_kind="LOG_RETURN"
    )
    observation = dict(pipeline["evaluation_observation"])
    artifacts = pipeline["materialization"]
    measured = dict(artifacts.measurement_evidence_artifact)
    information = dict(artifacts.evaluation_time_information_set_artifact)
    if observation["horizon_observation_status"] != "OK":
        raise DdoValidationError("SL_FOLLOW_UP_MEASUREMENT_UNAVAILABLE")
    validate_n_bars_measurement_artifacts_v1(observation, measured, information)
    time_key = learning_event_time_key_v0
    if not (
        time_key(request["planned_at_utc"])
        < time_key(observation["bar_close_times_utc"][0])
        <= time_key(observation["evaluation_time_utc"])
        <= time_key(source["known_at_utc"])
    ):
        raise DdoValidationError("SL_FOLLOW_UP_MEASUREMENT_TIME_MISMATCH")
    return {
        "schema_version": _MEASUREMENT,
        "plan_digest": _digest(plan),
        "source": source,
        "observation": observation,
        "measurement": measured,
        "evaluation_information_set": information,
    }


@contextmanager
def _completion_lock(path: Path):
    # All completion callers in the isolated workspace share this lock. The
    # DDO owner's predecessor check also protects against an external writer.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DdoValidationError("SL_FOLLOW_UP_COMPLETION_BUSY") from exc
        yield
    finally:
        os.close(fd)


def complete_offline_learning_follow_up_v1(
    root: Path, cycle_key: str, *, plan_digest: str, source: dict[str, Any]
) -> dict[str, Any]:
    """Reevaluate the frozen case, then append one state transition through the DDO owner."""
    directory = _cycle_directory(root, cycle_key)
    plan = _read_plan(directory, plan_digest)
    with _completion_lock(directory.parent / ".completion.lock"):
        return _complete(root, directory, plan, plan_digest, source)


def _complete(
    root: Path,
    directory: Path,
    plan: dict[str, Any],
    plan_digest: str,
    source: dict[str, Any],
) -> dict[str, Any]:
    scope = plan["request"]["scope"]
    ledger = AppendOnlyDdoLedgerV0(offline_learning_ledger_path_v1(root, scope["account_scope"]))
    records = ledger_records_index_v1(ledger)
    parent_ref = plan["prior_state_record_ref"]
    if (
        parent_ref is not None
        and records[parent_ref]["content_hash"] != plan["prior_state_content_hash"]
    ):
        raise DdoValidationError("SL_FOLLOW_UP_PARENT_MISMATCH")
    measurement = _materialize_measurement(plan, records, source)
    observation = measurement["observation"]
    ref = plan["selected"]["decision_ref"]
    identity = derive_productive_n_bars_evaluation_identity_v1(
        decision_record_id=ref,
        evaluation_time_utc=source["known_at_utc"],
        correlation_id=f"ddo.sl.{plan_digest}",
        code_sha=scope["code_sha"],
        config_hash=scope["config_hash"],
    )
    bundle = evaluate_offline_bundle_v0(
        records[ref],
        observation,
        identity=identity,
        records_by_id=records,
        provenance_binding=ProvenanceProducerBindingV1.EXPLICIT_OFFLINE_SYNTHETIC_N_BARS,
        provenance_context=ProvenanceBindingContextV1(
            decision_event_ref=ref,
            producer_id=__name__,
            instrument_id=scope["instrument_id"],
            venue_native_id=scope["native_instrument_id"],
            cycle_id=records[ref]["cycle_id"],
            outcome_scalar_kind="LOG_RETURN",
            evaluation_horizon="N_BARS",
            decision_timestamp_utc=plan["selected"]["decision_time_utc"],
            evaluation_timestamp_utc=observation["evaluation_time_utc"],
            lineage_digest=_digest(measurement),
        ),
    )
    outcome, attribution, counterfactual = (
        bundle[f"{role}_record"] for role in ("outcome", "attribution", "counterfactual")
    )
    _require_scoped_outcome(outcome, scope)
    fingerprint = compute_evaluation_bundle_fingerprint_v1(
        outcome_content_hash=outcome["content_hash"],
        attribution_content_hash=attribution["content_hash"],
        counterfactual_content_hash=counterfactual["content_hash"],
    )
    state_id = derive_learning_state_record_id_v1(
        state_scope_id=plan["state_scope_id"], fingerprint=fingerprint
    )
    head = learning_state_head_v0(records.values(), state_scope_id=plan["state_scope_id"])
    if state_id not in records and (None if head is None else head["record_id"]) != parent_ref:
        raise DdoValidationError("LEARNING_STATE_PREDECESSOR_CHANGED")
    measurement_digest = _publish(directory / "measurement.json", measurement)
    persist_evaluation_bundle_v0(
        ledger, outcome=outcome, attribution=attribution, counterfactual=counterfactual
    )
    state = ingest_evaluation_bundle_into_learning_state_v1(
        ledger,
        state_scope_id=plan["state_scope_id"],
        outcome=outcome,
        attribution=attribution,
        counterfactual=counterfactual,
        event_time_utc=source["known_at_utc"],
        correlation_id=identity["correlation_id"],
        cycle_id=records[ref]["cycle_id"],
        expected_prior_state_record_ref=parent_ref,
    )["learning_state_record"]
    result = {
        "schema_version": _RESULT,
        "authority": "NONE",
        "source_profile": _SOURCE,
        "plan_digest": plan_digest,
        "measurement_digest": measurement_digest,
        "decision_ref": ref,
        "decision_class": plan["selected"]["decision_class"],
        "decision_score": outcome["decision_score"],
        "actual_outcome_ref": outcome["actual_outcome_ref"],
        "log_return": measurement["measurement"]["log_return"],
        "learning_state_record_ref": state["record_id"],
        "learning_state_content_hash": state["content_hash"],
        "learning_state_version": state["state_version"],
        "prior_state_record_ref": state["prior_state_record_ref"],
    }
    _publish(directory / "result.json", result)
    return read_offline_learning_follow_up_v1(root, plan["cycle_key"], plan_digest=plan_digest)


def read_offline_learning_follow_up_v1(
    root: Path, cycle_key: str, *, plan_digest: str
) -> dict[str, Any]:
    """Verify the stored choice, O4 measurement and corresponding DDO ledger state."""
    directory = _cycle_directory(root, cycle_key)
    plan = _read_plan(directory, plan_digest)
    result = _read(directory / "result.json", _RESULT)
    measurement = _read(directory / "measurement.json", _MEASUREMENT, result["measurement_digest"])
    ledger = AppendOnlyDdoLedgerV0(
        offline_learning_ledger_path_v1(root, plan["request"]["scope"]["account_scope"])
    )
    records = ledger_records_index_v1(ledger)
    state = records[result["learning_state_record_ref"]]
    outcome = records[state["outcome_record_ref"]]
    parent_ref = plan["prior_state_record_ref"]
    _require_scoped_outcome(outcome, plan["request"]["scope"])
    validate_n_bars_measurement_artifacts_v1(
        measurement["observation"],
        measurement["measurement"],
        measurement["evaluation_information_set"],
    )
    if (
        result["authority"] != "NONE"
        or result["source_profile"] != _SOURCE
        or measurement["plan_digest"] != result["plan_digest"]
        or result["plan_digest"] != plan_digest
        or result["decision_ref"] != plan["selected"]["decision_ref"]
        or _candidate(records, result["decision_ref"], plan["request"]["scope"]) != plan["selected"]
        or state["content_hash"] != result["learning_state_content_hash"]
        or state["state_scope_id"] != plan["state_scope_id"]
        or state["state_version"] != result["learning_state_version"]
        or state["decision_event_ref"] != result["decision_ref"]
        or state["prior_state_record_ref"] != parent_ref
        or result["prior_state_record_ref"] != parent_ref
        or (
            parent_ref is not None
            and records[parent_ref]["content_hash"] != plan["prior_state_content_hash"]
        )
        or result["decision_class"] != plan["selected"]["decision_class"]
        or result["decision_score"] != outcome["decision_score"]
        or outcome["outcome_evidence_provenance"]["lineage_digest"] != result["measurement_digest"]
        or result["actual_outcome_ref"] != outcome["actual_outcome_ref"]
        or result["actual_outcome_ref"] != measurement["observation"]["actual_outcome_ref"]
        or result["log_return"] != measurement["measurement"]["log_return"]
    ):
        raise DdoValidationError("SL_FOLLOW_UP_READBACK_MISMATCH")
    return result


def export_completed_offline_learning_evidence_v1(
    root: Path, cycle_key: str, *, plan_digest: str
) -> dict[str, Any]:
    """Export only the exact learning state verified by the completed offline cycle."""
    result = read_offline_learning_follow_up_v1(root, cycle_key, plan_digest=plan_digest)
    plan = _read_plan(_cycle_directory(root, cycle_key), plan_digest)
    ledger = AppendOnlyDdoLedgerV0(
        offline_learning_ledger_path_v1(root, plan["request"]["scope"]["account_scope"])
    )
    state = ledger.get(result["learning_state_record_ref"])
    if state["content_hash"] != result["learning_state_content_hash"]:
        raise DdoValidationError("SL_FOLLOW_UP_EXPORT_STATE_MISMATCH")
    return export_learning_evidence_from_state_v1(state)
