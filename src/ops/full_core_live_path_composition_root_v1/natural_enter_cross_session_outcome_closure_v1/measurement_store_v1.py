"""Retain existing supplier artifacts under the existing Pending store owner."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import require_event_time_utc
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    validate_n_bars_measurement_artifacts_v1,
)
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    mint_ddo_content_ref_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
    EVIDENCE_CLASS_REAL_PUBLIC,
    EVENT_BAR_INGESTED,
    O4_STATE_DIRNAME,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.id_v1 import (
    pending_outcome_id_from_decision_event_ref_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
    NaturalEnterPendingOutcomeStoreError,
    _atomic_write_json_v1,
    _writer_v2,
    lane_pending_lane_dir_v1,
    load_pending_outcome_by_decision_ref_v1,
    load_pending_outcome_events_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.types_v1 import (
    NaturalEnterPendingOutcomeRecordV1,
)

SCHEMA = "pending_n_bars_measurement_artifacts.v1"


def _path(root: Path, pending: NaturalEnterPendingOutcomeRecordV1) -> Path:
    if pending.pending_outcome_id != pending_outcome_id_from_decision_event_ref_v1(
        pending.decision_event_ref
    ):
        raise DdoValidationError("PENDING_ARTIFACT_IDENTITY_INVALID")
    path = (
        lane_pending_lane_dir_v1(root)
        / O4_STATE_DIRNAME
        / pending.pending_outcome_id
        / "measurement_artifacts_v1.json"
    )
    if any(parent.is_symlink() for parent in (path.parent, path.parent.parent)):
        raise DdoValidationError("PENDING_ARTIFACT_SYMLINK_FORBIDDEN")
    return path


def _validate(bundle: Mapping[str, Any], pending: NaturalEnterPendingOutcomeRecordV1) -> None:
    if set(bundle) != {
        "schema_version",
        "pending_outcome_id",
        "decision_event_ref",
        "evidence_class",
        "producer_observed_at_unix",
        "evaluation_observation",
        "measurement_evidence_artifact",
        "evaluation_time_information_set_artifact",
    }:
        raise DdoValidationError("PENDING_ARTIFACT_SHAPE_INVALID")
    if (
        bundle["schema_version"] != SCHEMA
        or bundle["pending_outcome_id"] != pending.pending_outcome_id
        or bundle["decision_event_ref"] != pending.decision_event_ref
        or bundle["evidence_class"] != EVIDENCE_CLASS_REAL_PUBLIC
    ):
        raise DdoValidationError("PENDING_ARTIFACT_CONTEXT_MISMATCH")
    observed = bundle["producer_observed_at_unix"]
    if (
        isinstance(observed, bool)
        or not isinstance(observed, (int, float))
        or not math.isfinite(observed)
        or observed < pending.decision_timestamp_unix
    ):
        raise DdoValidationError("PENDING_ARTIFACT_KNOWLEDGE_TIME_INVALID")
    observation = bundle["evaluation_observation"]
    measurement = bundle["measurement_evidence_artifact"]
    information = bundle["evaluation_time_information_set_artifact"]
    if not all(isinstance(item, Mapping) for item in (observation, measurement, information)):
        raise DdoValidationError("PENDING_ARTIFACT_PAIR_MISSING")
    validate_n_bars_measurement_artifacts_v1(observation, measurement, information)
    if (
        observation.get("decision_event_ref") != pending.decision_event_ref
        or observation.get("n_bars") != pending.n_bars_required
        or observation.get("horizon_observation_status") != "OK"
    ):
        raise DdoValidationError("PENDING_ARTIFACT_DECISION_MISMATCH")
    instrument_ref = mint_ddo_content_ref_v1(
        prefix="ddo.o4.inst.",
        payload={
            "canonical_instrument_id": pending.canonical_instrument_id,
            "venue": "okx_eea",
            "venue_instrument_id": pending.native_id,
        },
    )
    provenance = information.get("o4_provenance")
    if (
        observation.get("instrument_ref") != instrument_ref
        or not isinstance(provenance, Mapping)
        or provenance.get("session_id") != pending.pending_outcome_id
    ):
        raise DdoValidationError("PENDING_ARTIFACT_INSTRUMENT_MISMATCH")
    start = datetime.fromisoformat(
        require_event_time_utc(
            observation.get("horizon_start_time_utc"), "horizon_start_time_utc"
        ).replace("Z", "+00:00")
    ).timestamp()
    end = datetime.fromisoformat(
        require_event_time_utc(
            observation.get("evaluation_time_utc"), "evaluation_time_utc"
        ).replace("Z", "+00:00")
    ).timestamp()
    if start < pending.decision_timestamp_unix or end > observed:
        raise DdoValidationError("PENDING_ARTIFACT_WINDOW_MISMATCH")


def load_pending_measurement_artifacts_v1(
    lane_state_root: Path,
    pending: NaturalEnterPendingOutcomeRecordV1,
    *,
    expected_ref: str,
) -> dict[str, Any]:
    path = _path(lane_state_root, pending)
    if path.is_symlink():
        raise DdoValidationError("PENDING_ARTIFACT_SYMLINK_FORBIDDEN")
    data = path.read_bytes()
    ref = "pending.nbars.bundle." + hashlib.sha256(data).hexdigest()
    if not expected_ref or ref != expected_ref:
        raise DdoValidationError("PENDING_ARTIFACT_DIGEST_MISMATCH")
    bundle = json.loads(data)
    if not isinstance(bundle, dict):
        raise DdoValidationError("PENDING_ARTIFACT_SHAPE_INVALID")
    _validate(bundle, pending)
    if pending.status == "CLOSED" and (
        pending.closure_refs.get("measurement_ref")
        != bundle["measurement_evidence_artifact"]["actual_outcome_ref"]
        or pending.closure_refs.get("evaluation_information_set_ref")
        != bundle["evaluation_time_information_set_artifact"]["evaluation_time_information_set_ref"]
    ):
        raise DdoValidationError("PENDING_ARTIFACT_CLOSURE_REFS_MISMATCH")
    return bundle


def persist_pending_measurement_artifacts_v1(
    *,
    lane_state_root: Path,
    pending: NaturalEnterPendingOutcomeRecordV1,
    horizon_result: Mapping[str, Any],
    producer_observed_at_unix: float,
) -> dict[str, str]:
    bundle = {
        "schema_version": SCHEMA,
        "pending_outcome_id": pending.pending_outcome_id,
        "decision_event_ref": pending.decision_event_ref,
        "evidence_class": EVIDENCE_CLASS_REAL_PUBLIC,
        "producer_observed_at_unix": producer_observed_at_unix,
        "evaluation_observation": horizon_result.get("evaluation_observation"),
        "measurement_evidence_artifact": horizon_result.get("measurement_evidence_artifact"),
        "evaluation_time_information_set_artifact": horizon_result.get(
            "evaluation_time_information_set_artifact"
        ),
    }
    _validate(bundle, pending)
    path = _path(lane_state_root, pending)
    with _writer_v2(lane_state_root):
        if (
            load_pending_outcome_by_decision_ref_v1(lane_state_root, pending.decision_event_ref)
            != pending
        ):
            raise NaturalEnterPendingOutcomeStoreError("PENDING_STORE_EXPECTED_RECORD_MISMATCH")
        sources = {
            event["detail"].get("evidence_class")
            for event in load_pending_outcome_events_v1(lane_state_root)
            if event["pending_outcome_id"] == pending.pending_outcome_id
            and event["event_type"] == EVENT_BAR_INGESTED
        }
        if sources != {EVIDENCE_CLASS_REAL_PUBLIC}:
            raise DdoValidationError("PENDING_ARTIFACT_SOURCE_NOT_BOUND")
        if path.is_symlink():
            raise DdoValidationError("PENDING_ARTIFACT_SYMLINK_FORBIDDEN")
        if path.exists():
            previous_bytes = path.read_bytes()
            previous = load_pending_measurement_artifacts_v1(
                lane_state_root,
                pending,
                expected_ref="pending.nbars.bundle." + hashlib.sha256(previous_bytes).hexdigest(),
            )
            # Repeated evaluation may know the same measurement later. Preserve
            # the original publication time and immutable artifact bytes.
            current_body = {k: v for k, v in bundle.items() if k != "producer_observed_at_unix"}
            prior_body = {k: v for k, v in previous.items() if k != "producer_observed_at_unix"}
            if (
                current_body != prior_body
                or producer_observed_at_unix < previous["producer_observed_at_unix"]
            ):
                raise DdoValidationError("PENDING_ARTIFACT_CONTENT_CONFLICT")
        else:
            _atomic_write_json_v1(path, bundle, fsync=True)
        data = path.read_bytes()
        ref = "pending.nbars.bundle." + hashlib.sha256(data).hexdigest()
        saved = load_pending_measurement_artifacts_v1(lane_state_root, pending, expected_ref=ref)
    return {
        "measurement_bundle_ref": ref,
        "measurement_ref": saved["measurement_evidence_artifact"]["actual_outcome_ref"],
        "evaluation_information_set_ref": saved["evaluation_time_information_set_artifact"][
            "evaluation_time_information_set_ref"
        ],
    }
