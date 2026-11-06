"""U-I82-R14 tests for dormant I56 live-contract join registration."""

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
from src.ingress.capsules.i56_ingress_live_contract_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I56_LIVE_CONTRACT_REGISTERED,
    I56IngressLiveContractJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i56_live_contract_registered,
    register_i56_live_contract_join_v1,
)
from src.levelup.i52_levelup_live_contract_join_v1 import (
    I52_LIVE_CONTRACT_REGISTERED,
    is_i52_live_contract_registered,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_live_contract_join_v1 import (
    I17_LIVE_CONTRACT_REGISTERED,
    is_i17_live_contract_registered,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_PATH = (
    REPO_ROOT / "src" / "ingress" / "capsules" / "i56_ingress_live_contract_join_v1.py"
)
ATTACHMENT_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "i56_ingress_join_attachment_v1.py"
CAPSULE_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "evidence_capsule.py"
BUILDER_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "evidence_capsule_builder.py"
INIT_PATH = REPO_ROOT / "src" / "ingress" / "capsules" / "__init__.py"
I17_REGISTRATION_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "i17_paper_shadow_live_contract_join_v1.py"
)
I52_REGISTRATION_PATH = REPO_ROOT / "src" / "levelup" / "i52_levelup_live_contract_join_v1.py"
_LIVE_CONTRACT_FILES = (CAPSULE_PATH, BUILDER_PATH, INIT_PATH, ATTACHMENT_PATH)

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r14-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r14-other").hexdigest()
_ARTIFACT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r14-artifact").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_DEFAULT_RUN_ID = "default"
_CAPSULE_ID = "default.capsule"


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


def _envelope(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "capsule": _capsule(),
    }
    payload.update(overrides)
    return payload


def test_live_contract_registration_flag_is_reachable() -> None:
    assert CONTRACT_ID == "i56_ingress_live_contract_join_v1"
    assert I56_LIVE_CONTRACT_REGISTERED is True
    assert is_i56_live_contract_registered() is True
    assert LIVE_CONTRACT_SURFACES == ("capsule", "artifact")
    assert I17_LIVE_CONTRACT_REGISTERED is True
    assert is_i17_live_contract_registered() is True
    assert I52_LIVE_CONTRACT_REGISTERED is True
    assert is_i52_live_contract_registered() is True


def test_canonical_package_n_sha256_present_join_from_capsule() -> None:
    record = register_i56_live_contract_join_v1(_envelope())
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True
    assert record.run_id == _DEFAULT_RUN_ID
    assert record.evidence_ref == _CAPSULE_ID
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _DEFAULT_RUN_ID
    assert record.experiment_identity_id != _CAPSULE_ID


def test_declared_absence_for_alias_campaign_session_content_hash() -> None:
    record = register_i56_live_contract_join_v1(_envelope())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.campaign_id is None
    assert record.session_id is None
    assert record.content_sha256 is None


def test_artifact_present_join_uses_sha256_as_content_hash() -> None:
    record = register_i56_live_contract_join_v1(
        {
            "experiment_identity_id": _PACKAGE_N_SHA256,
            "artifact": _artifact(),
        }
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.content_sha256 == _ARTIFACT_SHA256
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.content_sha256 != record.experiment_identity_id


def test_capsule_artifact_sha256_is_content_hash_not_identity() -> None:
    record = register_i56_live_contract_join_v1(
        _envelope(capsule=_capsule(artifacts=[_artifact()]))
    )
    assert record.content_sha256 == _ARTIFACT_SHA256
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.content_sha256 != record.experiment_identity_id


def test_explicit_declared_alias_remains_non_authoritative() -> None:
    record = register_i56_live_contract_join_v1(
        _envelope(legacy_alias_md5_12=_MD5_12, session_id="sess-non-auth")
    )
    assert record.legacy_alias_md5_12 == _MD5_12
    assert record.session_id == "sess-non-auth"
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _MD5_12
    assert record.run_id == _DEFAULT_RUN_ID
    assert record.experiment_identity_id != _DEFAULT_RUN_ID


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I56IngressLiveContractJoinError, match="implicit absence rejected"):
        register_i56_live_contract_join_v1({"capsule": _capsule()})


def test_implicit_absence_of_live_surface_rejected() -> None:
    with pytest.raises(I56IngressLiveContractJoinError, match="implicit absence rejected"):
        register_i56_live_contract_join_v1({"experiment_identity_id": _PACKAGE_N_SHA256})


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(I56IngressLiveContractJoinError, match="noncanonical ID substitution"):
        register_i56_live_contract_join_v1(_envelope(experiment_identity_id=_RUN_ID))
    with pytest.raises(I56IngressLiveContractJoinError, match="noncanonical ID substitution"):
        register_i56_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_12))
    with pytest.raises(I56IngressLiveContractJoinError, match="noncanonical ID substitution"):
        register_i56_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_32))
    with pytest.raises(I56IngressLiveContractJoinError, match="noncanonical ID substitution"):
        register_i56_live_contract_join_v1(_envelope(experiment_identity_id=_DEFAULT_RUN_ID))
    with pytest.raises(I56IngressLiveContractJoinError, match="noncanonical ID substitution"):
        register_i56_live_contract_join_v1(_envelope(experiment_identity_id=_CAPSULE_ID))


def test_legacy_experiment_id_and_run_id_on_envelope_rejected() -> None:
    with pytest.raises(I56IngressLiveContractJoinError, match="noncanonical ID substitution"):
        register_i56_live_contract_join_v1(_envelope(experiment_id=_RUN_ID))
    with pytest.raises(I56IngressLiveContractJoinError, match="noncanonical ID substitution"):
        register_i56_live_contract_join_v1(_envelope(run_id=_DEFAULT_RUN_ID))


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I56IngressLiveContractJoinError, match="conflicting"):
        register_i56_live_contract_join_v1(
            _envelope(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )
    with pytest.raises(I56IngressLiveContractJoinError, match="conflicting"):
        register_i56_live_contract_join_v1(_envelope(evidence_ref="other.capsule"))
    with pytest.raises(I56IngressLiveContractJoinError, match="conflicting"):
        register_i56_live_contract_join_v1(
            _envelope(
                capsule=_capsule(
                    artifacts=[
                        _artifact(),
                        {"path": "/ops/events/other.jsonl", "sha256": _OTHER_SHA256},
                    ]
                )
            )
        )


def test_ambiguous_join_rejected() -> None:
    with pytest.raises(I56IngressLiveContractJoinError, match="ambiguous join rejected"):
        register_i56_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "capsule": _capsule(),
                "artifact": _artifact(),
            }
        )
    with pytest.raises(I56IngressLiveContractJoinError, match="ambiguous join rejected"):
        register_i56_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "capsule": [_capsule(), _capsule(capsule_id="other.capsule")],
            }
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I56IngressLiveContractJoinError, match="malformed plane data"):
        register_i56_live_contract_join_v1("not-an-object")  # type: ignore[arg-type]
    with pytest.raises(I56IngressLiveContractJoinError, match="malformed plane data"):
        register_i56_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "capsule": "bad"}
        )
    mutated = _capsule()
    mutated.pop("capsule_id")
    with pytest.raises(I56IngressLiveContractJoinError, match="malformed plane data"):
        register_i56_live_contract_join_v1(_envelope(capsule=mutated))
    with pytest.raises(I56IngressLiveContractJoinError, match="malformed plane data"):
        register_i56_live_contract_join_v1(_envelope(capsule=_capsule(payload={"secret": "x"})))


def test_cross_plane_substitution_rejected() -> None:
    with pytest.raises(I56IngressLiveContractJoinError, match="cross-plane substitution"):
        register_i56_live_contract_join_v1(_envelope(plane_presence={"IDENTITY": "PRESENT"}))
    with pytest.raises(I56IngressLiveContractJoinError, match="cross-plane substitution"):
        register_i56_live_contract_join_v1(
            _envelope(capsule=_capsule(capsule_id=_PACKAGE_N_SHA256))
        )
    with pytest.raises(I56IngressLiveContractJoinError, match="cross-plane substitution"):
        register_i56_live_contract_join_v1(_envelope(capsule=_capsule(run_id=_PACKAGE_N_SHA256)))


def test_cross_lane_substitution_rejected() -> None:
    with pytest.raises(I56IngressLiveContractJoinError, match="cross-lane substitution"):
        register_i56_live_contract_join_v1(_envelope(I61={"session_dir": "/tmp/eval"}))
    with pytest.raises(I56IngressLiveContractJoinError, match="malformed plane data"):
        register_i56_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "capsule": {
                    "slice_id": "S1-R3",
                    "relative_dir": "out/ops/slice_demo_001/",
                },
            }
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = _capsule()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I56IngressLiveContractJoinError, match="noncanonical ID substitution"):
        register_i56_live_contract_join_v1(_envelope(capsule=live))


def test_join_is_deterministic() -> None:
    payload = _envelope(capsule=_capsule(artifacts=[_artifact()]))
    first = register_i56_live_contract_join_v1(payload).to_canonical_mapping()
    second = register_i56_live_contract_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_registration_does_not_mutate_inputs() -> None:
    payload = _envelope(historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID})
    snapshot = copy.deepcopy(payload)
    record = register_i56_live_contract_join_v1(payload)
    payload["experiment_identity_id"] = "MUTATED"
    payload["capsule"]["run_id"] = "MUTATED"  # type: ignore[index]
    payload["historical_provenance"]["legacy_experiment_id"] = "MUTATED"  # type: ignore[index]
    assert record.experiment_identity_id == snapshot["experiment_identity_id"]
    assert record.run_id == snapshot["capsule"]["run_id"]  # type: ignore[index]
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert payload != snapshot


def test_legacy_experiment_id_and_run_id_remain_non_authoritative() -> None:
    payload = _envelope(historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID})
    record = register_i56_live_contract_join_v1(payload)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _RUN_ID
    assert record.run_id == _DEFAULT_RUN_ID
    assert record.experiment_identity_id != _DEFAULT_RUN_ID
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


def test_no_cap72_execution_hook_or_persistence() -> None:
    modules = _imported_modules(REGISTRATION_PATH)
    assert not any(mod == "src.execution" or mod.startswith("src.execution.") for mod in modules)
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
    )
    assert "src.experiments.base" not in modules
    assert "src.ingress.capsules.evidence_capsule_builder" not in modules
    assert "src.ingress.orchestrator.ingress_orchestrator" not in modules
    assert "src.ingress.cli.ingress_cli" not in modules
    assert "src.ingress.io.evidence_capsule_writer" not in modules
    assert "src.live_eval.live_session_eval" not in modules
    assert "src.analytics.explorer" not in modules
    assert "src.ingress.capsules.evidence_capsule" in modules
    assert "src.ingress.capsules.i56_ingress_join_attachment_v1" in modules
    source = REGISTRATION_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "write_text" not in source
    assert "Path(" not in source
    assert "build_evidence_capsule" not in source


def test_live_contracts_and_prior_registrations_remain_unhooked() -> None:
    for path in _LIVE_CONTRACT_FILES:
        source = path.read_text(encoding="utf-8")
        assert "register_i56_live_contract_join_v1" not in source
        assert "i56_ingress_live_contract_join_v1" not in source
    capsule = CAPSULE_PATH.read_text(encoding="utf-8")
    assert "experiment_identity_id" not in capsule
    for prior in (I17_REGISTRATION_PATH, I52_REGISTRATION_PATH):
        source = prior.read_text(encoding="utf-8")
        assert "i56_ingress_live_contract_join_v1" not in source
        assert "I56_LIVE_CONTRACT_REGISTERED = True" not in source
