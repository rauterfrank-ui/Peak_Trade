"""EG-I82-JOIN U-I82-R2 — dormant historical I65 identity row reader.

Interprets existing I65 registry/explorer rows without rewriting them.
Legacy experiment_id/run_id remain RUN provenance. Canonical identity is
Package-N SHA256 only, via the R1 join contract. No synthesis, no migration.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from src.experiments.cross_lane_identity_join_v1 import (
    CONTRACT_ID as JOIN_CONTRACT_ID,
    CONTRACT_VERSION,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    JOIN_PLANES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PlanePresence,
    RUNTIME_AUTHORITY_IMPACT,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    CrossLaneIdentityJoinError,
    CrossLaneIdentityJoinV1,
    is_package_n_sha256_canonical_id,
    validate_cross_lane_identity_join_v1,
)

CONTRACT_ID = "legacy_identity_row_interpretation_v1"
LEGACY_EXPERIMENT_ID_CLASSIFICATION = "RUN_PROVENANCE_ALIAS"

_IDENTITY_SOURCE_KEYS = (
    "run_id",
    "experiment_id",
    "experiment_identity_id",
    "legacy_alias_md5_12",
    "legacy_experiment_id_md5_12",
)


class IdentityRequestMode(str, Enum):
    PROVENANCE = "PROVENANCE"
    IDENTITY_CANONICAL = "IDENTITY_CANONICAL"


class LegacyIdentityRowInterpretationError(ValueError):
    """Fail-closed historical I65 identity-row interpretation error."""


def _reject(message: str) -> None:
    raise LegacyIdentityRowInterpretationError(message)


def _optional_present_str(row: Mapping[str, Any], key: str) -> str | None:
    if key not in row:
        return None
    value = row[key]
    if value is None:
        return None
    if not isinstance(value, str):
        _reject(f"{key} must be a string when present")
    if not value.strip() or value != value.strip():
        _reject(f"{key} is present but empty or whitespace-padded (ambiguous)")
    return value


def _snapshot_identity_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for key in _IDENTITY_SOURCE_KEYS:
        if key in row:
            snapshot[key] = copy.deepcopy(row[key])
    return snapshot


def _alias_md5_12(row: Mapping[str, Any]) -> str | None:
    primary = _optional_present_str(row, "legacy_alias_md5_12")
    secondary = _optional_present_str(row, "legacy_experiment_id_md5_12")
    if primary is not None and secondary is not None and primary != secondary:
        _reject("conflicting identities: MD5 alias fields disagree")
    return primary if primary is not None else secondary


def _build_join_record(
    *,
    run_id: str | None,
    alias_md5_12: str | None,
    experiment_identity_id: str | None,
    historical_provenance: Mapping[str, Any],
) -> CrossLaneIdentityJoinV1:
    plane_presence = {plane: PlanePresence.ABSENT_DECLARED.value for plane in JOIN_PLANES}
    payload: dict[str, Any] = {
        "schema_version": CONTRACT_VERSION,
        "contract_version": CONTRACT_VERSION,
        "contract_id": JOIN_CONTRACT_ID,
        "plane_presence": plane_presence,
        "historical_provenance": dict(historical_provenance),
        "safety": {
            "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
            "evidence_does_not_authorize_runtime": True,
            "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
            "SECOND_EXECUTION_AUTHORITY_AUTHORIZED": SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
            "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS": (
                CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS
            ),
        },
    }
    if experiment_identity_id is not None:
        plane_presence["IDENTITY"] = PlanePresence.PRESENT.value
        payload["experiment_identity_id"] = experiment_identity_id
    if run_id is not None:
        plane_presence["RUN"] = PlanePresence.PRESENT.value
        payload["run_id"] = run_id
    if alias_md5_12 is not None:
        plane_presence["ALIAS"] = PlanePresence.PRESENT.value
        payload["legacy_alias_md5_12"] = alias_md5_12
    try:
        return validate_cross_lane_identity_join_v1(payload)
    except CrossLaneIdentityJoinError as exc:
        raise LegacyIdentityRowInterpretationError(
            f"R1 join contract rejected historical interpretation: {exc}"
        ) from exc


@dataclass(frozen=True)
class LegacyIdentityRowInterpretationV1:
    contract_id: str
    identity_request_mode: str
    run_id: str | None
    legacy_experiment_id: str | None
    legacy_experiment_id_classification: str | None
    legacy_alias_md5_12: str | None
    experiment_identity_id: str | None
    identity_status: str
    identity_canonical: bool
    join_record: CrossLaneIdentityJoinV1
    historical_provenance: Mapping[str, Any]

    def to_canonical_mapping(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "identity_request_mode": self.identity_request_mode,
            "run_id": self.run_id,
            "legacy_experiment_id": self.legacy_experiment_id,
            "legacy_experiment_id_classification": self.legacy_experiment_id_classification,
            "legacy_alias_md5_12": self.legacy_alias_md5_12,
            "experiment_identity_id": self.experiment_identity_id,
            "identity_status": self.identity_status,
            "identity_canonical": self.identity_canonical,
            "join_record": self.join_record.to_canonical_mapping(),
            "historical_provenance": copy.deepcopy(dict(self.historical_provenance)),
        }


def interpret_legacy_identity_row_v1(
    row: Mapping[str, Any],
    *,
    identity_request: IdentityRequestMode | str = IdentityRequestMode.PROVENANCE,
) -> LegacyIdentityRowInterpretationV1:
    """Read an I65 row as provenance. Never mutates `row` and never synthesizes SHA256."""
    if not isinstance(row, Mapping):
        _reject("historical I65 row must be an object")

    if isinstance(identity_request, IdentityRequestMode):
        request_mode = identity_request
    elif identity_request in {
        IdentityRequestMode.PROVENANCE.value,
        IdentityRequestMode.IDENTITY_CANONICAL.value,
    }:
        request_mode = IdentityRequestMode(identity_request)
    else:
        _reject(f"unknown identity_request mode: {identity_request!r}")

    provenance_snapshot = _snapshot_identity_fields(row)
    frozen_provenance = MappingProxyType(copy.deepcopy(provenance_snapshot))

    run_id = _optional_present_str(row, "run_id")
    legacy_experiment_id = _optional_present_str(row, "experiment_id")
    raw_identity = _optional_present_str(row, "experiment_identity_id")
    alias_md5_12 = _alias_md5_12(row)

    if run_id is None and legacy_experiment_id is None and raw_identity is None:
        _reject("historical I65 row has no run_id, experiment_id, or experiment_identity_id")

    if run_id is not None and legacy_experiment_id is not None and legacy_experiment_id != run_id:
        _reject("conflicting identities: experiment_id disagrees with run_id")

    legacy_classification: str | None = None
    if legacy_experiment_id is not None:
        if is_package_n_sha256_canonical_id(legacy_experiment_id):
            _reject(
                "legacy experiment_id must not be treated as Package-N SHA256; "
                "canonical identity requires experiment_identity_id"
            )
        legacy_classification = LEGACY_EXPERIMENT_ID_CLASSIFICATION

    canonical_id: str | None = None
    if raw_identity is not None:
        if not is_package_n_sha256_canonical_id(raw_identity):
            _reject("experiment_identity_id is present but is not a Package-N SHA256 canonical id")
        if run_id is not None and raw_identity == run_id:
            _reject("conflicting identities: experiment_identity_id equals run_id")
        if legacy_experiment_id is not None and raw_identity == legacy_experiment_id:
            _reject("conflicting identities: experiment_identity_id equals legacy experiment_id")
        canonical_id = raw_identity

    if request_mode is IdentityRequestMode.IDENTITY_CANONICAL and canonical_id is None:
        _reject("IDENTITY_CANONICAL requested but Package-N SHA256 identity is ABSENT_DECLARED")

    join_record = _build_join_record(
        run_id=run_id,
        alias_md5_12=alias_md5_12,
        experiment_identity_id=canonical_id,
        historical_provenance=frozen_provenance,
    )

    identity_status = (
        PlanePresence.PRESENT.value
        if canonical_id is not None
        else PlanePresence.ABSENT_DECLARED.value
    )
    return LegacyIdentityRowInterpretationV1(
        contract_id=CONTRACT_ID,
        identity_request_mode=request_mode.value,
        run_id=run_id,
        legacy_experiment_id=legacy_experiment_id,
        legacy_experiment_id_classification=legacy_classification,
        legacy_alias_md5_12=alias_md5_12,
        experiment_identity_id=canonical_id,
        identity_status=identity_status,
        identity_canonical=canonical_id is not None,
        join_record=join_record,
        historical_provenance=join_record.historical_provenance,
    )


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "IdentityRequestMode",
    "LEGACY_EXPERIMENT_ID_CLASSIFICATION",
    "LegacyIdentityRowInterpretationError",
    "LegacyIdentityRowInterpretationV1",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "interpret_legacy_identity_row_v1",
]
