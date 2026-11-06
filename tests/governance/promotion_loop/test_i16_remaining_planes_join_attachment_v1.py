"""U-I82-R4 tests for dormant I16 remaining-plane join attachment."""

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
from src.governance.promotion_loop.i16_remaining_planes_join_attachment_v1 import (
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I16RemainingPlanesJoinAttachmentError,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    attach_i16_remaining_planes_join_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ATTACHMENT_PATH = (
    REPO_ROOT
    / "src"
    / "governance"
    / "promotion_loop"
    / "i16_remaining_planes_join_attachment_v1.py"
)

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r4-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r4-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r4-content").hexdigest()
_MD5_12 = "abcdef012345"
_RUN_ID = str(uuid.uuid4())
_SESSION_ID = "runtime-session-i16-r4"


def _i16_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "ref_id": _PACKAGE_N_SHA256,
        "digest": _CONTENT_SHA256,
        "artifact_path": "experiment_identity_manifest_v1.json",
    }
    payload.update(overrides)
    return payload


def test_canonical_package_n_sha256_run_join() -> None:
    record = attach_i16_remaining_planes_join_v1(_i16_payload(run_id=_RUN_ID))
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.run_id == _RUN_ID
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _RUN_ID


def test_campaign_and_session_absent_declared_by_default() -> None:
    record = attach_i16_remaining_planes_join_v1(_i16_payload())
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.campaign_id is None
    assert record.session_id is None
    assert record.run_id is None


def test_explicit_session_present_is_not_identity() -> None:
    record = attach_i16_remaining_planes_join_v1(_i16_payload(session_id=_SESSION_ID))
    assert record.session_id == _SESSION_ID
    assert record.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _SESSION_ID


def test_uuid_run_id_as_identity_rejected() -> None:
    assert is_package_n_sha256_canonical_id(_RUN_ID) is False
    with pytest.raises(I16RemainingPlanesJoinAttachmentError, match="Package-N SHA256"):
        attach_i16_remaining_planes_join_v1(
            _i16_payload(experiment_identity_id=_RUN_ID, ref_id=_RUN_ID)
        )


def test_md5_as_ref_id_rejected() -> None:
    with pytest.raises(I16RemainingPlanesJoinAttachmentError, match="must not be UUID/run_id/MD5"):
        attach_i16_remaining_planes_join_v1(_i16_payload(ref_id=_MD5_12))


def test_legacy_experiment_id_as_identity_rejected() -> None:
    with pytest.raises(I16RemainingPlanesJoinAttachmentError, match="forbidden I16 join field"):
        attach_i16_remaining_planes_join_v1(_i16_payload(experiment_id=_RUN_ID))


def test_conflicting_ref_id_and_identity_rejected() -> None:
    with pytest.raises(I16RemainingPlanesJoinAttachmentError, match="conflicting Package-N SHA256"):
        attach_i16_remaining_planes_join_v1(
            _i16_payload(experiment_identity_id=_PACKAGE_N_SHA256, ref_id=_OTHER_SHA256)
        )


def test_missing_identity_rejected() -> None:
    with pytest.raises(I16RemainingPlanesJoinAttachmentError, match="IDENTITY missing"):
        attach_i16_remaining_planes_join_v1({"run_id": _RUN_ID})


def test_run_id_must_not_substitute_identity() -> None:
    with pytest.raises(I16RemainingPlanesJoinAttachmentError, match="must not substitute"):
        attach_i16_remaining_planes_join_v1(_i16_payload(run_id=_PACKAGE_N_SHA256))


def test_session_id_must_not_substitute_identity() -> None:
    with pytest.raises(I16RemainingPlanesJoinAttachmentError, match="must not substitute"):
        attach_i16_remaining_planes_join_v1(_i16_payload(session_id=_PACKAGE_N_SHA256))


def test_join_is_deterministic() -> None:
    payload = _i16_payload(run_id=_RUN_ID, session_id=_SESSION_ID)
    first = attach_i16_remaining_planes_join_v1(payload).to_canonical_mapping()
    second = attach_i16_remaining_planes_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_attachment_does_not_mutate_inputs() -> None:
    payload = _i16_payload(
        run_id=_RUN_ID,
        historical_provenance={"legacy_experiment_id": _RUN_ID},
    )
    snapshot = copy.deepcopy(payload)
    record = attach_i16_remaining_planes_join_v1(payload)
    payload["run_id"] = "MUTATED"
    payload["historical_provenance"]["legacy_experiment_id"] = "MUTATED"  # type: ignore[index]
    assert record.run_id == snapshot["run_id"]
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert payload != snapshot


def test_historical_provenance_non_authoritative() -> None:
    payload = _i16_payload(
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID}
    )
    record = attach_i16_remaining_planes_join_v1(payload)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _RUN_ID
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID


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
    assert "src.governance.promotion_loop.experiment_lineage_ref_producer_v1" not in modules
    assert (
        "src.meta.learning_loop.comparison_promotion_candidate_identity_binding_v1" not in modules
    )
    assert "src.meta.learning_loop.experiment_durable_evidence_binding_v1" not in modules
    assert "src.experiments.base" not in modules
    source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "produce_experiment_lineage_ref_v1" not in source
    assert "append_experiment_record" not in source
