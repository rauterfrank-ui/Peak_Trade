"""U-I82-R5 tests for dormant I17 paper-shadow join attachment."""

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
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_join_attachment_v1 import (
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I17PaperShadowJoinAttachmentError,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    attach_i17_paper_shadow_join_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTACHMENT_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "i17_paper_shadow_join_attachment_v1.py"
)

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r5-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r5-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r5-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_SESSION_ID = "pso_fixture_session_non_auth_v1"
_GIT_SHA = "cd1bd6fa40d664c22b3f6abeef3cc00cdda72688"


def _i17_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "session_id": _SESSION_ID,
        "evidence_root": "evidence/fixtures/paper_shadow_observation_non_authoritative_v1",
        "config_identity": "config/ops/integrated_paper_shadow_observation_session_v1.toml",
        "code_identity": "src/ops/integrated_paper_shadow_observation_session_v1/",
        "expected_repository_sha": _GIT_SHA,
    }
    payload.update(overrides)
    return payload


def test_canonical_package_n_sha256_happy_path() -> None:
    record = attach_i17_paper_shadow_join_v1(_i17_payload())
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.session_id == _SESSION_ID
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _SESSION_ID
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True


def test_alias_run_campaign_absent_declared_by_default() -> None:
    record = attach_i17_paper_shadow_join_v1(_i17_payload())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.run_id is None
    assert record.campaign_id is None


def test_content_hash_absent_declared_without_explicit_sha256() -> None:
    record = attach_i17_paper_shadow_join_v1(_i17_payload())
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert record.content_sha256 is None


def test_explicit_content_sha256_is_content_hash_not_identity() -> None:
    record = attach_i17_paper_shadow_join_v1(_i17_payload(content_sha256=_CONTENT_SHA256))
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.content_sha256 == _CONTENT_SHA256
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.content_sha256 != record.experiment_identity_id


def test_missing_identity_rejected() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="IDENTITY missing"):
        attach_i17_paper_shadow_join_v1({"session_id": _SESSION_ID})


def test_missing_session_id_rejected() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="SESSION missing"):
        attach_i17_paper_shadow_join_v1({"experiment_identity_id": _PACKAGE_N_SHA256})


def test_uuid_run_id_as_identity_rejected() -> None:
    assert is_package_n_sha256_canonical_id(_RUN_ID) is False
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="Package-N SHA256"):
        attach_i17_paper_shadow_join_v1(
            _i17_payload(experiment_identity_id=_RUN_ID, run_id=_RUN_ID)
        )


def test_legacy_experiment_id_as_identity_rejected() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="forbidden I17 join field"):
        attach_i17_paper_shadow_join_v1(_i17_payload(experiment_id=_RUN_ID))


def test_md5_as_identity_rejected() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="Package-N SHA256"):
        attach_i17_paper_shadow_join_v1(_i17_payload(experiment_identity_id=_MD5_12))
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="Package-N SHA256"):
        attach_i17_paper_shadow_join_v1(_i17_payload(experiment_identity_id=_MD5_32))


def test_git_sha_as_identity_rejected() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="Package-N SHA256"):
        attach_i17_paper_shadow_join_v1(_i17_payload(experiment_identity_id=_GIT_SHA))


def test_session_id_must_not_substitute_identity() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="must not substitute"):
        attach_i17_paper_shadow_join_v1(_i17_payload(session_id=_PACKAGE_N_SHA256))


def test_expected_repository_sha_must_not_substitute_identity() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="must not substitute"):
        attach_i17_paper_shadow_join_v1(_i17_payload(expected_repository_sha=_PACKAGE_N_SHA256))


def test_campaign_id_extra_forbid_rejected() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="forbidden I17 join field"):
        attach_i17_paper_shadow_join_v1(_i17_payload(campaign_id="cap11-campaign"))


def test_conflicting_content_hash_values_rejected() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="conflicting CONTENT_HASH"):
        attach_i17_paper_shadow_join_v1(
            _i17_payload(content_sha256=_CONTENT_SHA256, scope_digest=_OTHER_SHA256)
        )


def test_conflicting_evidence_values_rejected() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="conflicting EVIDENCE"):
        attach_i17_paper_shadow_join_v1(
            _i17_payload(evidence_ref="evidence/a", evidence_root="evidence/b")
        )


def test_conflicting_identity_values_rejected() -> None:
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="forbidden I17 join field"):
        attach_i17_paper_shadow_join_v1(_i17_payload(ref_id=_OTHER_SHA256))
    with pytest.raises(I17PaperShadowJoinAttachmentError, match="conflicting identities"):
        attach_i17_paper_shadow_join_v1(
            _i17_payload(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )


def test_join_is_deterministic() -> None:
    payload = _i17_payload(content_sha256=_CONTENT_SHA256)
    first = attach_i17_paper_shadow_join_v1(payload).to_canonical_mapping()
    second = attach_i17_paper_shadow_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_attachment_does_not_mutate_inputs() -> None:
    payload = _i17_payload(
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID}
    )
    snapshot = copy.deepcopy(payload)
    record = attach_i17_paper_shadow_join_v1(payload)
    payload["session_id"] = "MUTATED"
    payload["historical_provenance"]["legacy_experiment_id"] = "MUTATED"  # type: ignore[index]
    assert record.session_id == snapshot["session_id"]
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert payload != snapshot


def test_historical_provenance_non_authoritative() -> None:
    payload = _i17_payload(
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID}
    )
    record = attach_i17_paper_shadow_join_v1(payload)
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
    assert (
        "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1"
        not in modules
    )
    assert (
        "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1"
        not in modules
    )
    assert (
        "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1"
        not in modules
    )
    assert "src.experiments.base" not in modules
    source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "validate_preregistration_contract_v1" not in source
    assert "build_authorization_artifact_v1" not in source
