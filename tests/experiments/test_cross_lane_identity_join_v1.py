"""U-I82-R1 tests for dormant cross_lane_identity_join_v1 contract."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path
from types import MappingProxyType

import pytest

from src.experiments.cross_lane_identity_join_v1 import (
    CONTRACT_ID,
    CONTRACT_VERSION,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    JOIN_PLANES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    CrossLaneIdentityJoinError,
    PlanePresence,
    is_package_n_sha256_canonical_id,
    read_historical_provenance,
    validate_cross_lane_identity_join_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "src" / "experiments" / "cross_lane_identity_join_v1.py"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r1-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r1-other").hexdigest()
_MD5_12 = "abcdef012345"


def _absent_planes(**overrides: str) -> dict[str, str]:
    planes = {plane: PlanePresence.ABSENT_DECLARED.value for plane in JOIN_PLANES}
    planes.update(overrides)
    return planes


def _base_record(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": CONTRACT_VERSION,
        "contract_version": CONTRACT_VERSION,
        "contract_id": CONTRACT_ID,
        "plane_presence": _absent_planes(IDENTITY=PlanePresence.PRESENT.value),
        "experiment_identity_id": _PACKAGE_N_SHA256,
    }
    payload.update(overrides)
    return payload


def test_valid_package_n_sha256_id_accepted() -> None:
    assert is_package_n_sha256_canonical_id(_PACKAGE_N_SHA256)
    record = validate_cross_lane_identity_join_v1(_base_record())
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert len(record.experiment_identity_id or "") == 64


def test_present_state_supported() -> None:
    payload = _base_record(
        plane_presence=_absent_planes(
            IDENTITY=PlanePresence.PRESENT.value,
            RUN=PlanePresence.PRESENT.value,
        ),
        run_id="run-opaque-1",
    )
    record = validate_cross_lane_identity_join_v1(payload)
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert record.run_id == "run-opaque-1"


def test_absent_declared_state_supported() -> None:
    payload = _base_record(
        plane_presence=_absent_planes(),
    )
    del payload["experiment_identity_id"]
    record = validate_cross_lane_identity_join_v1(payload)
    assert record.plane_presence["IDENTITY"] == PlanePresence.ABSENT_DECLARED.value
    assert record.experiment_identity_id is None
    for plane in JOIN_PLANES:
        assert record.plane_presence[plane] == PlanePresence.ABSENT_DECLARED.value


def test_missing_status_rejected() -> None:
    payload = _base_record()
    planes = _absent_planes(IDENTITY=PlanePresence.PRESENT.value)
    del planes["RUN"]
    payload["plane_presence"] = planes
    with pytest.raises(CrossLaneIdentityJoinError, match="missing required plane status"):
        validate_cross_lane_identity_join_v1(payload)

    payload = _base_record()
    payload["plane_presence"] = _absent_planes(IDENTITY=PlanePresence.PRESENT.value, RUN="")
    with pytest.raises(CrossLaneIdentityJoinError, match="status is missing"):
        validate_cross_lane_identity_join_v1(payload)

    payload = _base_record()
    payload["plane_presence"] = _absent_planes(
        IDENTITY=PlanePresence.PRESENT.value, SESSION="ABSENT"
    )
    with pytest.raises(CrossLaneIdentityJoinError, match="PRESENT or ABSENT_DECLARED"):
        validate_cross_lane_identity_join_v1(payload)


def test_missing_canonical_id_when_present_rejected() -> None:
    payload = _base_record()
    del payload["experiment_identity_id"]
    with pytest.raises(CrossLaneIdentityJoinError, match="canonical Package-N SHA256 id missing"):
        validate_cross_lane_identity_join_v1(payload)

    payload = _base_record(experiment_identity_id=None)
    with pytest.raises(CrossLaneIdentityJoinError, match="canonical Package-N SHA256 id missing"):
        validate_cross_lane_identity_join_v1(payload)


def test_uuid_and_run_id_not_accepted_as_package_n_sha256() -> None:
    run_id = str(uuid.uuid4())
    assert is_package_n_sha256_canonical_id(run_id) is False
    payload = _base_record(experiment_identity_id=run_id)
    with pytest.raises(CrossLaneIdentityJoinError, match="UUID/run_id"):
        validate_cross_lane_identity_join_v1(payload)

    payload = _base_record(
        plane_presence=_absent_planes(
            IDENTITY=PlanePresence.PRESENT.value,
            RUN=PlanePresence.PRESENT.value,
        ),
        experiment_identity_id=run_id,
        run_id=run_id,
    )
    with pytest.raises(CrossLaneIdentityJoinError, match="UUID/run_id"):
        validate_cross_lane_identity_join_v1(payload)

    payload = _base_record(experiment_identity_id=_MD5_12)
    with pytest.raises(CrossLaneIdentityJoinError, match="MD5 alias"):
        validate_cross_lane_identity_join_v1(payload)


def test_conflicting_identities_rejected() -> None:
    payload = _base_record(experiment_id=str(uuid.uuid4()))
    with pytest.raises(CrossLaneIdentityJoinError, match="conflicting identities"):
        validate_cross_lane_identity_join_v1(payload)

    payload = _base_record(
        plane_presence=_absent_planes(
            IDENTITY=PlanePresence.PRESENT.value,
            RUN=PlanePresence.PRESENT.value,
        ),
        run_id=_PACKAGE_N_SHA256,
    )
    with pytest.raises(CrossLaneIdentityJoinError, match="conflicting identities"):
        validate_cross_lane_identity_join_v1(payload)

    payload = _base_record(
        historical_provenance={"experiment_identity_id": _OTHER_SHA256},
    )
    with pytest.raises(
        CrossLaneIdentityJoinError, match="historical provenance canonical id mismatch"
    ):
        validate_cross_lane_identity_join_v1(payload)


def test_historical_provenance_read_only_and_unmodified() -> None:
    original_provenance = {
        "legacy_experiment_id": "3f1a9c2e-4b8d-4e21-9c77-aaaaaaaaaaaa",
        "legacy_alias_md5_12": _MD5_12,
        "source_note": "pre-join explorer row",
    }
    payload = _base_record(
        plane_presence=_absent_planes(),
        historical_provenance=original_provenance,
    )
    del payload["experiment_identity_id"]
    snapshot = copy.deepcopy(original_provenance)
    record = validate_cross_lane_identity_join_v1(payload)
    original_provenance["legacy_experiment_id"] = "MUTATED"
    payload["historical_provenance"]["source_note"] = "MUTATED_PAYLOAD"  # type: ignore[index]
    assert dict(record.historical_provenance) == snapshot
    assert payload["historical_provenance"]["legacy_experiment_id"] == "MUTATED"  # type: ignore[index]
    with pytest.raises(TypeError):
        record.historical_provenance["legacy_experiment_id"] = "rewrite"  # type: ignore[index]
    frozen = read_historical_provenance(record)
    assert isinstance(frozen, MappingProxyType)
    assert dict(frozen) == snapshot
    round_trip = validate_cross_lane_identity_join_v1(record.to_canonical_mapping())
    assert dict(round_trip.historical_provenance) == snapshot


def test_unknown_plane_rejected() -> None:
    payload = _base_record()
    planes = _absent_planes(IDENTITY=PlanePresence.PRESENT.value)
    planes["ORDERS"] = PlanePresence.PRESENT.value
    payload["plane_presence"] = planes
    with pytest.raises(CrossLaneIdentityJoinError, match="unknown join plane"):
        validate_cross_lane_identity_join_v1(payload)


def test_invalid_record_cannot_serialize_as_valid_join() -> None:
    with pytest.raises(CrossLaneIdentityJoinError):
        validate_cross_lane_identity_join_v1({"contract_id": CONTRACT_ID})
    valid = validate_cross_lane_identity_join_v1(_base_record())
    serialized = valid.to_canonical_mapping()
    assert (
        validate_cross_lane_identity_join_v1(serialized).experiment_identity_id == _PACKAGE_N_SHA256
    )


def test_runtime_invariants_remain_unauthorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1
    payload = _base_record(
        safety={"MULTI_FUTURE_RUNTIME_AUTHORIZED": True},
    )
    with pytest.raises(CrossLaneIdentityJoinError, match="MULTI_FUTURE_RUNTIME_AUTHORIZED"):
        validate_cross_lane_identity_join_v1(payload)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_no_cap72_or_src_execution_import() -> None:
    modules = _imported_modules(CONTRACT_PATH)
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    assert "src.experiments.base" not in modules
    assert "src.analytics.explorer" not in modules
