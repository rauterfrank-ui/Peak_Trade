"""U-I82-R6 tests for dormant I52 Level-Up join attachment."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pytest

from src.experiments.cross_lane_identity_join_v1 import (
    PlanePresence,
    is_package_n_sha256_canonical_id,
)
from src.levelup.i52_levelup_join_attachment_v1 import (
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I52LevelUpJoinAttachmentError,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    attach_i52_levelup_join_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTACHMENT_PATH = REPO_ROOT / "src" / "levelup" / "i52_levelup_join_attachment_v1.py"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r6-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r6-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r6-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_SLICE_ID = "S1-R3"
_RELATIVE_DIR = "out/ops/slice_demo_001/"


def _i52_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "slice_id": _SLICE_ID,
        "relative_dir": _RELATIVE_DIR,
    }
    payload.update(overrides)
    return payload


def test_canonical_package_n_sha256_happy_path() -> None:
    record = attach_i52_levelup_join_v1(_i52_payload())
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.evidence_ref == _RELATIVE_DIR
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _SLICE_ID
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True


def test_alias_run_campaign_session_absent_declared_by_default() -> None:
    record = attach_i52_levelup_join_v1(_i52_payload())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.run_id is None
    assert record.campaign_id is None
    assert record.session_id is None


def test_explicit_absent_declared_without_relative_dir() -> None:
    payload = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "slice_id": _SLICE_ID,
    }
    record = attach_i52_levelup_join_v1(payload)
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.evidence_ref is None
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value


def test_explicit_content_sha256_is_content_hash_not_identity() -> None:
    record = attach_i52_levelup_join_v1(_i52_payload(content_sha256=_CONTENT_SHA256))
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.content_sha256 == _CONTENT_SHA256
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.content_sha256 != record.experiment_identity_id


def test_missing_identity_rejected() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="IDENTITY missing"):
        attach_i52_levelup_join_v1({"slice_id": _SLICE_ID, "relative_dir": _RELATIVE_DIR})


def test_uuid_run_id_as_identity_rejected() -> None:
    assert is_package_n_sha256_canonical_id(_RUN_ID) is False
    with pytest.raises(I52LevelUpJoinAttachmentError, match="Package-N SHA256"):
        attach_i52_levelup_join_v1(_i52_payload(experiment_identity_id=_RUN_ID, run_id=_RUN_ID))


def test_legacy_experiment_id_as_identity_rejected() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="forbidden I52 join field"):
        attach_i52_levelup_join_v1(_i52_payload(experiment_id=_RUN_ID))


def test_md5_as_identity_rejected() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="Package-N SHA256"):
        attach_i52_levelup_join_v1(_i52_payload(experiment_identity_id=_MD5_12))
    with pytest.raises(I52LevelUpJoinAttachmentError, match="Package-N SHA256"):
        attach_i52_levelup_join_v1(_i52_payload(experiment_identity_id=_MD5_32))


def test_slice_id_as_identity_rejected() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="Package-N SHA256"):
        attach_i52_levelup_join_v1(_i52_payload(experiment_identity_id=_SLICE_ID))


def test_slice_id_must_not_substitute_identity() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="must not substitute"):
        attach_i52_levelup_join_v1(_i52_payload(slice_id=_PACKAGE_N_SHA256))


def test_relative_dir_outside_out_ops_rejected() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="must start with"):
        attach_i52_levelup_join_v1(_i52_payload(relative_dir="out/evidence/x"))


def test_relative_dir_path_traversal_rejected() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="path traversal"):
        attach_i52_levelup_join_v1(_i52_payload(relative_dir="out/ops/../other"))


def test_conflicting_evidence_values_rejected() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="conflicting EVIDENCE"):
        attach_i52_levelup_join_v1(
            _i52_payload(evidence_ref="out/ops/slice_a/", relative_dir="out/ops/slice_b/")
        )


def test_conflicting_identity_values_rejected() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="forbidden I52 join field"):
        attach_i52_levelup_join_v1(_i52_payload(ref_id=_OTHER_SHA256))
    with pytest.raises(I52LevelUpJoinAttachmentError, match="conflicting identities"):
        attach_i52_levelup_join_v1(
            _i52_payload(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )


def test_unknown_join_field_extra_forbid_rejected() -> None:
    with pytest.raises(I52LevelUpJoinAttachmentError, match="unknown I52 join field"):
        attach_i52_levelup_join_v1(_i52_payload(authorization_id="not-in-i52-join"))


def test_join_is_deterministic() -> None:
    payload = _i52_payload(content_sha256=_CONTENT_SHA256, run_id=_RUN_ID)
    first = attach_i52_levelup_join_v1(payload).to_canonical_mapping()
    second = attach_i52_levelup_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_attachment_does_not_mutate_inputs() -> None:
    payload = _i52_payload(
        historical_provenance={"legacy_experiment_id": _RUN_ID, "slice_id": _SLICE_ID}
    )
    snapshot = copy.deepcopy(payload)
    record = attach_i52_levelup_join_v1(payload)
    payload["slice_id"] = "MUTATED"
    payload["historical_provenance"]["legacy_experiment_id"] = "MUTATED"  # type: ignore[index]
    assert dict(record.historical_provenance)["slice_id"] == _SLICE_ID
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert payload != snapshot


def test_historical_provenance_non_authoritative() -> None:
    payload = _i52_payload(
        historical_provenance={"legacy_experiment_id": _RUN_ID, "slice_id": _SLICE_ID}
    )
    record = attach_i52_levelup_join_v1(payload)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _SLICE_ID
    assert record.experiment_identity_id != _RUN_ID
    assert dict(record.historical_provenance)["slice_id"] == _SLICE_ID


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


def test_no_runtime_registration_or_forbidden_imports() -> None:
    modules = _imported_modules(ATTACHMENT_PATH)
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    assert "src.levelup.v0_models" not in modules
    assert "src.levelup.v0_io" not in modules
    assert "src.levelup.cli" not in modules
    assert "src.experiments.base" not in modules
    source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "write_manifest" not in source
    assert "read_manifest" not in source
    assert "model_validate" not in source
