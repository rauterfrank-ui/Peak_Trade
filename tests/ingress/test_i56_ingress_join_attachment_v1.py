"""U-I82-R7 tests for dormant I56 Ingress join attachment."""

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
from src.ingress.capsules.evidence_capsule import EvidenceCapsule
from src.ingress.capsules.i56_ingress_join_attachment_v1 import (
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I56IngressJoinAttachmentError,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    attach_i56_ingress_join_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTACHMENT_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "i56_ingress_join_attachment_v1.py"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r7-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r7-other").hexdigest()
_ARTIFACT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r7-artifact").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_DEFAULT_RUN_ID = "default"
_CAPSULE_ID = "default.capsule"


def _i56_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "capsule_id": _CAPSULE_ID,
        "run_id": _DEFAULT_RUN_ID,
    }
    payload.update(overrides)
    return payload


def test_canonical_package_n_sha256_happy_path() -> None:
    record = attach_i56_ingress_join_v1(_i56_payload())
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.evidence_ref == _CAPSULE_ID
    assert record.run_id == _DEFAULT_RUN_ID
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _DEFAULT_RUN_ID
    assert record.experiment_identity_id != _CAPSULE_ID
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True


def test_alias_campaign_session_absent_declared_by_default() -> None:
    record = attach_i56_ingress_join_v1(_i56_payload())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.campaign_id is None
    assert record.session_id is None


def test_declared_absent_without_run_or_capsule() -> None:
    payload = {"experiment_identity_id": _PACKAGE_N_SHA256}
    record = attach_i56_ingress_join_v1(payload)
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert record.run_id is None
    assert record.evidence_ref is None
    assert record.content_sha256 is None


def test_explicit_artifact_sha256_is_content_hash_not_identity() -> None:
    record = attach_i56_ingress_join_v1(_i56_payload(artifact_sha256=_ARTIFACT_SHA256))
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.content_sha256 == _ARTIFACT_SHA256
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.content_sha256 != record.experiment_identity_id


def test_default_run_id_stays_run_plane() -> None:
    record = attach_i56_ingress_join_v1(_i56_payload(run_id=_DEFAULT_RUN_ID))
    assert record.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert record.run_id == _DEFAULT_RUN_ID
    assert record.experiment_identity_id != _DEFAULT_RUN_ID


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="IDENTITY missing"):
        attach_i56_ingress_join_v1({"capsule_id": _CAPSULE_ID, "run_id": _DEFAULT_RUN_ID})


def test_run_id_default_as_identity_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="run_id default cannot fill IDENTITY"):
        attach_i56_ingress_join_v1(
            _i56_payload(experiment_identity_id=_DEFAULT_RUN_ID, run_id=_DEFAULT_RUN_ID)
        )


def test_capsule_id_as_identity_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="capsule_id cannot fill IDENTITY"):
        attach_i56_ingress_join_v1(
            _i56_payload(experiment_identity_id=_CAPSULE_ID, capsule_id=_CAPSULE_ID)
        )


def test_uuid_run_id_as_identity_rejected() -> None:
    assert is_package_n_sha256_canonical_id(_RUN_ID) is False
    with pytest.raises(I56IngressJoinAttachmentError, match="Package-N SHA256"):
        attach_i56_ingress_join_v1(_i56_payload(experiment_identity_id=_RUN_ID, run_id=_RUN_ID))


def test_legacy_experiment_id_as_identity_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="forbidden I56 join field"):
        attach_i56_ingress_join_v1(_i56_payload(experiment_id=_RUN_ID))


def test_md5_as_identity_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="Package-N SHA256"):
        attach_i56_ingress_join_v1(_i56_payload(experiment_identity_id=_MD5_12))
    with pytest.raises(I56IngressJoinAttachmentError, match="Package-N SHA256"):
        attach_i56_ingress_join_v1(_i56_payload(experiment_identity_id=_MD5_32))


def test_run_id_must_not_substitute_identity() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="must not substitute"):
        attach_i56_ingress_join_v1(_i56_payload(run_id=_PACKAGE_N_SHA256))


def test_capsule_id_must_not_substitute_identity() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="must not substitute"):
        attach_i56_ingress_join_v1(_i56_payload(capsule_id=_PACKAGE_N_SHA256))


def test_raw_payload_and_secrets_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="forbidden I56 join field"):
        attach_i56_ingress_join_v1(_i56_payload(payload={"raw": True}))
    with pytest.raises(I56IngressJoinAttachmentError, match="forbidden I56 join field"):
        attach_i56_ingress_join_v1(_i56_payload(secrets="token"))
    with pytest.raises(I56IngressJoinAttachmentError, match="forbidden I56 join field"):
        attach_i56_ingress_join_v1(_i56_payload(transcript="leak"))


def test_conflicting_evidence_values_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="conflicting EVIDENCE"):
        attach_i56_ingress_join_v1(
            _i56_payload(evidence_ref="other.capsule", capsule_id=_CAPSULE_ID)
        )


def test_conflicting_content_hash_values_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="conflicting CONTENT_HASH"):
        attach_i56_ingress_join_v1(
            _i56_payload(artifact_sha256=_ARTIFACT_SHA256, content_sha256=_OTHER_SHA256)
        )


def test_conflicting_identity_values_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="forbidden I56 join field"):
        attach_i56_ingress_join_v1(_i56_payload(ref_id=_OTHER_SHA256))
    with pytest.raises(I56IngressJoinAttachmentError, match="conflicting identities"):
        attach_i56_ingress_join_v1(
            _i56_payload(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )


def test_malformed_and_ambiguous_join_rejected() -> None:
    with pytest.raises(I56IngressJoinAttachmentError, match="must be an object"):
        attach_i56_ingress_join_v1("not-an-object")  # type: ignore[arg-type]
    with pytest.raises(I56IngressJoinAttachmentError, match="unknown I56 join field"):
        attach_i56_ingress_join_v1(_i56_payload(ts_ms=1))
    with pytest.raises(I56IngressJoinAttachmentError, match="empty or whitespace-padded"):
        attach_i56_ingress_join_v1(_i56_payload(experiment_identity_id="   "))


def test_join_is_deterministic() -> None:
    payload = _i56_payload(artifact_sha256=_ARTIFACT_SHA256, run_id=_DEFAULT_RUN_ID)
    first = attach_i56_ingress_join_v1(payload).to_canonical_mapping()
    second = attach_i56_ingress_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_attachment_does_not_mutate_inputs() -> None:
    payload = _i56_payload(
        historical_provenance={"legacy_capsule_id": _CAPSULE_ID, "run_id": _DEFAULT_RUN_ID}
    )
    snapshot = copy.deepcopy(payload)
    record = attach_i56_ingress_join_v1(payload)
    payload["run_id"] = "MUTATED"
    payload["historical_provenance"]["run_id"] = "MUTATED"  # type: ignore[index]
    assert dict(record.historical_provenance)["run_id"] == _DEFAULT_RUN_ID
    assert dict(record.historical_provenance)["legacy_capsule_id"] == _CAPSULE_ID
    assert payload != snapshot


def test_historical_provenance_non_authoritative() -> None:
    payload = _i56_payload(
        historical_provenance={"legacy_capsule_id": _CAPSULE_ID, "run_id": _DEFAULT_RUN_ID}
    )
    record = attach_i56_ingress_join_v1(payload)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _CAPSULE_ID
    assert record.experiment_identity_id != _DEFAULT_RUN_ID
    assert dict(record.historical_provenance)["legacy_capsule_id"] == _CAPSULE_ID


def test_live_evidence_capsule_contract_unregistered() -> None:
    capsule = EvidenceCapsule(capsule_id=_CAPSULE_ID, run_id=_DEFAULT_RUN_ID, ts_ms=0)
    serialized = capsule.to_dict()
    assert "experiment_identity_id" not in serialized
    assert serialized["run_id"] == _DEFAULT_RUN_ID
    assert serialized["capsule_id"] == _CAPSULE_ID


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
    assert "src.ingress.capsules.evidence_capsule" not in modules
    assert "src.ingress.capsules.evidence_capsule_builder" not in modules
    assert "src.ingress.orchestrator.ingress_orchestrator" not in modules
    assert "src.ingress.cli.ingress_cli" not in modules
    assert "src.experiments.base" not in modules
    source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "write_evidence_capsule" not in source
    assert "run_ingress" not in source
    assert "build_evidence_capsule" not in source
