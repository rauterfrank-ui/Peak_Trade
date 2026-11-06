"""U-I82-R3 tests for dormant cross_lane_identity_join_record_v1 primitive."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pytest

from src.experiments.cross_lane_identity_join_record_v1 import (
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    CrossLaneIdentityJoinRecordError,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    build_cross_lane_identity_join_record_v1,
)
from src.experiments.cross_lane_identity_join_v1 import (
    JOIN_PLANES,
    PlanePresence,
    is_package_n_sha256_canonical_id,
    validate_cross_lane_identity_join_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMITIVE_PATH = REPO_ROOT / "src" / "experiments" / "cross_lane_identity_join_record_v1.py"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r3-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r3-other").hexdigest()
_MD5_12 = "abcdef012345"
_RUN_ID = str(uuid.uuid4())


def _absent(plane: str) -> dict[str, str]:
    return {"plane": plane, "presence": PlanePresence.ABSENT_DECLARED.value}


def _present(plane: str, value: str, join_key: str = _PACKAGE_N_SHA256) -> dict[str, str]:
    return {
        "plane": plane,
        "presence": PlanePresence.PRESENT.value,
        "join_key": join_key,
        "value": value,
    }


def _complete(*overrides: dict[str, str]) -> list[dict[str, str]]:
    by_plane = {plane: _absent(plane) for plane in JOIN_PLANES}
    for item in overrides:
        by_plane[item["plane"]] = item
    return [by_plane[plane] for plane in JOIN_PLANES]


def test_two_present_planes_same_package_n_sha256_join() -> None:
    contributions = _complete(
        _present("IDENTITY", _PACKAGE_N_SHA256),
        _present("RUN", _RUN_ID),
    )
    record = build_cross_lane_identity_join_record_v1(contributions)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.run_id == _RUN_ID
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["RUN"] == PlanePresence.PRESENT.value


def test_present_plus_absent_declared_explicit_join() -> None:
    record = build_cross_lane_identity_join_record_v1(
        _complete(_present("IDENTITY", _PACKAGE_N_SHA256))
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.run_id is None


def test_conflicting_package_n_sha256_rejected() -> None:
    contributions = _complete(
        _present("IDENTITY", _PACKAGE_N_SHA256, join_key=_PACKAGE_N_SHA256),
        _present("RUN", _RUN_ID, join_key=_OTHER_SHA256),
    )
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="conflicting Package-N SHA256"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_missing_plane_status_rejected() -> None:
    contributions = _complete(_present("IDENTITY", _PACKAGE_N_SHA256))
    contributions[1] = {"plane": "ALIAS"}
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="status is missing"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_unknown_status_rejected() -> None:
    contributions = _complete(_present("IDENTITY", _PACKAGE_N_SHA256))
    contributions[1] = {"plane": "ALIAS", "presence": "ABSENT"}
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="unknown plane presence status"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_present_without_package_n_sha256_rejected() -> None:
    contributions = _complete(
        {
            "plane": "IDENTITY",
            "presence": PlanePresence.PRESENT.value,
            "value": _PACKAGE_N_SHA256,
        }
    )
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="missing Package-N SHA256 join_key"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_uuid_run_id_as_identity_rejected() -> None:
    assert is_package_n_sha256_canonical_id(_RUN_ID) is False
    contributions = _complete(_present("IDENTITY", _RUN_ID, join_key=_RUN_ID))
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="Package-N SHA256"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_legacy_experiment_id_as_identity_rejected() -> None:
    contributions = _complete(_present("IDENTITY", _PACKAGE_N_SHA256))
    contributions[0] = {
        "plane": "IDENTITY",
        "presence": PlanePresence.PRESENT.value,
        "join_key": _PACKAGE_N_SHA256,
        "value": _PACKAGE_N_SHA256,
        "experiment_id": _RUN_ID,
    }
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="forbidden join contribution key"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_md5_as_identity_rejected() -> None:
    contributions = _complete(_present("IDENTITY", _MD5_12, join_key=_MD5_12))
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="Package-N SHA256"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_absent_declared_with_synthetic_identity_rejected() -> None:
    contributions = _complete(
        {
            "plane": "IDENTITY",
            "presence": PlanePresence.ABSENT_DECLARED.value,
            "join_key": _PACKAGE_N_SHA256,
            "value": _PACKAGE_N_SHA256,
        }
    )
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="synthetic identity forbidden"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_join_is_deterministic_for_identical_input() -> None:
    contributions = _complete(
        _present("IDENTITY", _PACKAGE_N_SHA256),
        _present("RUN", _RUN_ID),
    )
    first = build_cross_lane_identity_join_record_v1(contributions).to_canonical_mapping()
    second = build_cross_lane_identity_join_record_v1(
        list(reversed(contributions))
    ).to_canonical_mapping()
    third = build_cross_lane_identity_join_record_v1(
        copy.deepcopy(contributions)
    ).to_canonical_mapping()
    assert first == second == third
    validate_cross_lane_identity_join_v1(first)


def test_join_does_not_mutate_inputs() -> None:
    contributions = _complete(
        _present("IDENTITY", _PACKAGE_N_SHA256),
        _present("RUN", _RUN_ID),
    )
    snapshot = copy.deepcopy(contributions)
    provenance = {"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID}
    provenance_snapshot = copy.deepcopy(provenance)
    build_cross_lane_identity_join_record_v1(contributions, historical_provenance=provenance)
    assert contributions == snapshot
    assert provenance == provenance_snapshot


def test_historical_provenance_non_authoritative() -> None:
    provenance = {
        "legacy_experiment_id": _RUN_ID,
        "run_id": _RUN_ID,
        "note": "historical I65 row",
    }
    record = build_cross_lane_identity_join_record_v1(
        _complete(_present("IDENTITY", _PACKAGE_N_SHA256)),
        historical_provenance=provenance,
    )
    provenance["legacy_experiment_id"] = "MUTATED"
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert record.experiment_identity_id != _RUN_ID


def test_duplicate_plane_rejected() -> None:
    contributions = _complete(_present("IDENTITY", _PACKAGE_N_SHA256))
    contributions.append(_present("IDENTITY", _PACKAGE_N_SHA256))
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="duplicate plane"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_incomplete_join_record_rejected() -> None:
    contributions = [
        item
        for item in _complete(_present("IDENTITY", _PACKAGE_N_SHA256))
        if item["plane"] != "SESSION"
    ]
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="incomplete join record"):
        build_cross_lane_identity_join_record_v1(contributions)


def test_package_n_manifest_id_match_and_mismatch() -> None:
    manifest = {"experiment_identity_id": _PACKAGE_N_SHA256}
    record = build_cross_lane_identity_join_record_v1(
        _complete(_present("IDENTITY", _PACKAGE_N_SHA256)),
        package_n_manifest=manifest,
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    with pytest.raises(CrossLaneIdentityJoinRecordError, match="conflicting Package-N SHA256"):
        build_cross_lane_identity_join_record_v1(
            _complete(_present("IDENTITY", _PACKAGE_N_SHA256)),
            package_n_manifest={"experiment_identity_id": _OTHER_SHA256},
        )


def test_forbidden_runtime_keys_rejected() -> None:
    for key in ("orders", "credentials", "promotion_authority"):
        contributions = _complete(_present("IDENTITY", _PACKAGE_N_SHA256))
        item = dict(contributions[0])
        item[key] = True
        contributions[0] = item
        with pytest.raises(
            CrossLaneIdentityJoinRecordError, match="forbidden join contribution key"
        ):
            build_cross_lane_identity_join_record_v1(contributions)


def test_runtime_invariants_remain_unauthorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_no_cap72_execution_or_runtime_registration_imports() -> None:
    modules = _imported_modules(PRIMITIVE_PATH)
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    assert "src.experiments.base" not in modules
    assert "src.experiments.experiment_identity_manifest_v1" not in modules
    assert "src.analytics.explorer" not in modules
    assert "src.core.experiments" not in modules
    source = PRIMITIVE_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "append_experiment_record" not in source
