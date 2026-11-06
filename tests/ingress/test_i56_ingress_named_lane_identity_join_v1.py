"""U-I82-R21 tests for I56 named-lane IDENTITY join on EvidenceCapsule."""

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
from src.ingress.capsules.evidence_capsule import (
    ArtifactRef,
    EvidenceCapsule,
    parse_artifact_ref_with_identity_join_v1,
    parse_evidence_capsule_with_identity_join_v1,
)
from src.ingress.capsules.i56_ingress_join_attachment_v1 import CONTRACT_ID as R7_CONTRACT_ID
from src.ingress.capsules.i56_ingress_named_lane_identity_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I56_NAMED_LANE_IDENTITY_JOIN_REGISTERED,
    I56IngressNamedLaneIdentityJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i56_named_lane_identity_join_registered,
    join_i56_named_lane_identity_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
JOIN_PATH = (
    REPO_ROOT / "src" / "ingress" / "capsules" / "i56_ingress_named_lane_identity_join_v1.py"
)
ATTACHMENT_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "i56_ingress_join_attachment_v1.py"
CAPSULE_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "evidence_capsule.py"
BUILDER_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "evidence_capsule_builder.py"
INIT_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "__init__.py"
WRITER_PATH = REPO_ROOT / "src" / "ingress" / "io" / "evidence_capsule_writer.py"
ORCH_PATH = REPO_ROOT / "src" / "ingress" / "orchestrator" / "ingress_orchestrator.py"
R14_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "i56_ingress_live_contract_join_v1.py"
_JOIN_MODULE = "src.ingress.capsules.i56_ingress_named_lane_identity_join_v1"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r21-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r21-other").hexdigest()
_ARTIFACT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r21-artifact").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_DEFAULT_RUN_ID = "default"
_CAPSULE_ID = "default.capsule"
_CAMPAIGN_ID = "campaign-i56-r21"
_SESSION_ID = "session-i56-r21"


def _capsule(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "capsule_id": _CAPSULE_ID,
        "run_id": _DEFAULT_RUN_ID,
        "ts_ms": 1000,
        "artifacts": [],
        "labels": {},
        "facts": {},
    }
    payload.update(overrides)
    return payload


def _artifact() -> dict[str, object]:
    return {"path": "/ops/events/ev.jsonl", "sha256": _ARTIFACT_SHA256}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_named_lane_identity_join_is_registered_and_reachable() -> None:
    assert CONTRACT_ID == "i56_ingress_named_lane_identity_join_v1"
    assert R7_CONTRACT_ID == "i56_ingress_join_attachment_v1"
    assert I56_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True
    assert is_i56_named_lane_identity_join_registered() is True
    assert LIVE_CONTRACT_SURFACES == ("capsule", "artifact")


def test_named_capsule_producer_attaches_identity() -> None:
    result = parse_evidence_capsule_with_identity_join_v1(
        _capsule(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(result.join.experiment_identity_id) is True
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert result.join.run_id == _DEFAULT_RUN_ID
    assert result.join.evidence_ref == _CAPSULE_ID
    assert result.join.experiment_identity_id != _DEFAULT_RUN_ID
    assert result.join.experiment_identity_id != _CAPSULE_ID
    dumped = result.contract.to_dict()
    assert "experiment_identity_id" not in dumped
    assert dumped["run_id"] == _DEFAULT_RUN_ID


def test_declared_absence_for_alias_campaign_session_content_hash() -> None:
    result = parse_evidence_capsule_with_identity_join_v1(
        _capsule(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.legacy_alias_md5_12 is None
    assert result.join.campaign_id is None
    assert result.join.session_id is None
    assert result.join.content_sha256 is None


def test_present_sidecars_are_joined_and_not_identity() -> None:
    result = parse_evidence_capsule_with_identity_join_v1(
        _capsule(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        campaign_id=_CAMPAIGN_ID,
        session_id=_SESSION_ID,
        legacy_alias_md5_12=_MD5_12,
        content_sha256=_ARTIFACT_SHA256,
    )
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["ALIAS"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert result.join.campaign_id == _CAMPAIGN_ID
    assert result.join.session_id == _SESSION_ID
    assert result.join.legacy_alias_md5_12 == _MD5_12
    assert result.join.content_sha256 == _ARTIFACT_SHA256
    assert result.join.experiment_identity_id != _CAMPAIGN_ID
    assert result.join.experiment_identity_id != _SESSION_ID
    assert result.join.experiment_identity_id != _MD5_12
    assert result.join.experiment_identity_id != _ARTIFACT_SHA256
    assert result.join.run_id == _DEFAULT_RUN_ID


def test_capsule_artifact_sha256_is_content_hash_not_identity() -> None:
    result = parse_evidence_capsule_with_identity_join_v1(
        _capsule(artifacts=[_artifact()]),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.content_sha256 == _ARTIFACT_SHA256
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.content_sha256 != result.join.experiment_identity_id


def test_artifact_named_lane_attaches_identity() -> None:
    result = parse_artifact_ref_with_identity_join_v1(
        _artifact(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.content_sha256 == result.contract.sha256
    assert result.join.content_sha256 != result.join.experiment_identity_id


def test_existing_capsule_still_accepts_identity_free_schema() -> None:
    capsule = EvidenceCapsule(
        capsule_id=_CAPSULE_ID,
        run_id=_DEFAULT_RUN_ID,
        ts_ms=1000,
        artifacts=[ArtifactRef(path="/ops/events/ev.jsonl", sha256=_ARTIFACT_SHA256)],
    )
    dumped = capsule.to_dict()
    assert "experiment_identity_id" not in dumped
    assert dumped["run_id"] == _DEFAULT_RUN_ID


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="implicit absence rejected"):
        parse_evidence_capsule_with_identity_join_v1(_capsule())


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(),
            experiment_identity_id=_RUN_ID,
        )
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(),
            experiment_identity_id=_MD5_12,
        )
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(),
            experiment_identity_id=_MD5_32,
        )
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(),
            experiment_identity_id=_DEFAULT_RUN_ID,
        )
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(),
            experiment_identity_id=_CAPSULE_ID,
        )


def test_run_id_and_capsule_id_must_not_substitute_identity() -> None:
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="cross-plane substitution"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(run_id=_PACKAGE_N_SHA256),
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="cross-plane substitution"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(capsule_id=_PACKAGE_N_SHA256),
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = _capsule()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        join_i56_named_lane_identity_v1(
            live,
            surface="capsule",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="conflicting"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            historical_provenance={"experiment_identity_id": _OTHER_SHA256},
        )
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="conflicting"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            evidence_ref="other.capsule",
        )
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="conflicting"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(
                artifacts=[
                    _artifact(),
                    {"path": "/ops/events/other.jsonl", "sha256": _OTHER_SHA256},
                ]
            ),
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_ambiguous_join_rejected() -> None:
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="ambiguous join rejected"):
        join_i56_named_lane_identity_v1(
            [_capsule(), _capsule(capsule_id="other.capsule")],
            surface="capsule",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="malformed plane data"):
        join_i56_named_lane_identity_v1(
            "not-an-object",  # type: ignore[arg-type]
            surface="capsule",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="malformed plane data"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            session_id="   ",
        )
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="malformed plane data"):
        parse_evidence_capsule_with_identity_join_v1(
            _capsule(payload={"secret": "x"}),
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_cross_lane_substitution_rejected() -> None:
    live = _capsule()
    live["I61"] = {"session_dir": "/tmp/eval"}
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="cross-lane substitution"):
        join_i56_named_lane_identity_v1(
            live,
            surface="capsule",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_cross_plane_substitution_rejected() -> None:
    live = _capsule()
    live["plane_presence"] = {"IDENTITY": "PRESENT"}
    with pytest.raises(I56IngressNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i56_named_lane_identity_v1(
            live,
            surface="capsule",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_join_is_deterministic() -> None:
    first = parse_evidence_capsule_with_identity_join_v1(
        _capsule(artifacts=[_artifact()]),
        experiment_identity_id=_PACKAGE_N_SHA256,
    ).join.to_canonical_mapping()
    second = parse_evidence_capsule_with_identity_join_v1(
        _capsule(artifacts=[_artifact()]),
        experiment_identity_id=_PACKAGE_N_SHA256,
    ).join.to_canonical_mapping()
    assert first == second


def test_named_lane_does_not_mutate_inputs() -> None:
    raw = _capsule()
    snapshot = copy.deepcopy(raw)
    result = parse_evidence_capsule_with_identity_join_v1(
        raw,
        experiment_identity_id=_PACKAGE_N_SHA256,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    raw["run_id"] = "MUTATED"
    assert result.contract.run_id == snapshot["run_id"]
    assert dict(raw) != snapshot


def test_legacy_experiment_id_and_run_id_remain_non_authoritative() -> None:
    result = parse_evidence_capsule_with_identity_join_v1(
        _capsule(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.join.run_id == _DEFAULT_RUN_ID
    assert result.join.experiment_identity_id != _DEFAULT_RUN_ID
    assert dict(result.join.historical_provenance)["legacy_experiment_id"] == _RUN_ID


def test_runtime_invariants_remain_unauthorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1


def test_named_lane_producer_is_hooked_and_forbidden_surfaces_are_not() -> None:
    join_modules = _imported_modules(JOIN_PATH)
    assert "src.ingress.capsules.i56_ingress_join_attachment_v1" in join_modules
    assert "src.ingress.capsules.evidence_capsule" not in join_modules
    capsule_modules = _imported_modules(CAPSULE_PATH)
    assert _JOIN_MODULE in capsule_modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in capsule_modules
    )
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in capsule_modules
    )
    assert "src.analytics.explorer" not in capsule_modules
    assert "src.live_eval.live_session_eval" not in capsule_modules
    assert "src.experiments.base" not in capsule_modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in join_modules
    )
    join_source = JOIN_PATH.read_text(encoding="utf-8")
    assert "write_text" not in join_source
    assert "open(" not in join_source
    assert "Path(" not in join_source
    assert "build_evidence_capsule" not in join_source
    capsule_source = CAPSULE_PATH.read_text(encoding="utf-8")
    assert "experiment_identity_id" not in capsule_source
    assert "i56_ingress_live_contract_join_v1" not in capsule_source
    init_source = INIT_PATH.read_text(encoding="utf-8")
    builder_source = BUILDER_PATH.read_text(encoding="utf-8")
    writer_source = WRITER_PATH.read_text(encoding="utf-8")
    orch_source = ORCH_PATH.read_text(encoding="utf-8")
    attachment_source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    r14_source = R14_PATH.read_text(encoding="utf-8")
    assert "i56_ingress_named_lane_identity_join_v1" not in init_source
    assert "i56_ingress_named_lane_identity_join_v1" not in builder_source
    assert "i56_ingress_named_lane_identity_join_v1" not in writer_source
    assert "i56_ingress_named_lane_identity_join_v1" not in orch_source
    assert "i56_ingress_named_lane_identity_join_v1" not in attachment_source
    assert "i56_ingress_named_lane_identity_join_v1" not in r14_source
    assert _PACKAGE_N_SHA256 not in capsule_source
