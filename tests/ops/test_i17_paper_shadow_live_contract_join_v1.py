"""U-I82-R12 tests for dormant I17 live-contract join registration."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
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
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.authorization_artifact_v1 import (
    build_authorization_artifact_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_live_contract_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I17_LIVE_CONTRACT_REGISTERED,
    I17PaperShadowLiveContractJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i17_live_contract_registered,
    register_i17_live_contract_join_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "i17_paper_shadow_live_contract_join_v1.py"
)
ATTACHMENT_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "i17_paper_shadow_join_attachment_v1.py"
)
PREREG_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "preregistration_contract_v1.py"
)
GO_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "operator_go_contract_v1.py"
)
ARTIFACT_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "authorization_artifact_v1.py"
)
INIT_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "__init__.py"
)
FIX = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
)

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r12-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r12-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r12-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_GIT_SHA = "cd1bd6fa40d664c22b3f6abeef3cc00cdda72688"
_LIVE_CONTRACT_FILES = (PREREG_PATH, GO_PATH, ARTIFACT_PATH, INIT_PATH, ATTACHMENT_PATH)


def _prereg() -> dict[str, object]:
    return load_preregistration_contract_dict_v1(
        FIX / "preregistration_valid_non_authoritative.json"
    )


def _go() -> dict[str, object]:
    raw = load_operator_go_contract_dict_v1(FIX / "operator_go_valid_non_authoritative.json")
    if "session_execution_authorized" not in raw:
        raw["session_execution_authorized"] = False
    return raw


def _artifact() -> dict[str, object]:
    prereg = parse_preregistration_contract_v1(_prereg())
    go = parse_operator_go_contract_v1(_go())
    material = "GO_PSO_SESSION_PREREG_V1_" + "FIXTURE_NON_AUTHORITATIVE_" + "MATERIAL_9F3A"
    built = build_authorization_artifact_v1(
        prereg=prereg,
        go=go,
        confirm_token=material,
        authorization_id="auth_fixture_v1",
        now_unix=1_700_000_000.0,
    )
    assert built.ok and built.artifact is not None
    return built.artifact.to_dict()


def _envelope(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "preregistration": _prereg(),
    }
    payload.update(overrides)
    return payload


def test_live_contract_registration_flag_is_reachable() -> None:
    assert CONTRACT_ID == "i17_paper_shadow_live_contract_join_v1"
    assert I17_LIVE_CONTRACT_REGISTERED is True
    assert is_i17_live_contract_registered() is True
    assert LIVE_CONTRACT_SURFACES == (
        "preregistration",
        "operator_go",
        "authorization_artifact",
    )


def test_canonical_package_n_sha256_present_join_from_prereg() -> None:
    record = register_i17_live_contract_join_v1(_envelope())
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True
    assert record.session_id == "pso_fixture_session_non_auth_v1"
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != record.session_id


def test_declared_absence_for_alias_run_campaign_content_hash() -> None:
    record = register_i17_live_contract_join_v1(_envelope())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.run_id is None
    assert record.campaign_id is None
    assert record.content_sha256 is None


def test_operator_go_present_join_uses_explicit_scope_digest_as_content_hash() -> None:
    record = register_i17_live_contract_join_v1(
        {
            "experiment_identity_id": _PACKAGE_N_SHA256,
            "operator_go": _go(),
        }
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.session_id == "pso_fixture_session_non_auth_v1"
    assert record.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert record.content_sha256 == _go()["scope_digest"]
    assert record.content_sha256 != record.experiment_identity_id


def test_authorization_artifact_present_join() -> None:
    artifact = _artifact()
    record = register_i17_live_contract_join_v1(
        {
            "experiment_identity_id": _PACKAGE_N_SHA256,
            "authorization_artifact": artifact,
        }
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.session_id == artifact["session_id"]
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["SESSION"] == PlanePresence.PRESENT.value


def test_explicit_declared_run_and_alias_remain_non_authoritative() -> None:
    record = register_i17_live_contract_join_v1(
        _envelope(run_id=_RUN_ID, legacy_alias_md5_12=_MD5_12)
    )
    assert record.run_id == _RUN_ID
    assert record.legacy_alias_md5_12 == _MD5_12
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _RUN_ID
    assert record.experiment_identity_id != _MD5_12


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="implicit absence rejected"):
        register_i17_live_contract_join_v1({"preregistration": _prereg()})


def test_implicit_absence_of_live_surface_rejected() -> None:
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="implicit absence rejected"):
        register_i17_live_contract_join_v1({"experiment_identity_id": _PACKAGE_N_SHA256})


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="noncanonical ID substitution"):
        register_i17_live_contract_join_v1(_envelope(experiment_identity_id=_RUN_ID))
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="noncanonical ID substitution"):
        register_i17_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_12))
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="noncanonical ID substitution"):
        register_i17_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_32))
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="noncanonical ID substitution"):
        register_i17_live_contract_join_v1(_envelope(experiment_identity_id=_GIT_SHA))


def test_legacy_experiment_id_and_session_id_on_envelope_rejected() -> None:
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="noncanonical ID substitution"):
        register_i17_live_contract_join_v1(_envelope(experiment_id=_RUN_ID))
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="noncanonical ID substitution"):
        register_i17_live_contract_join_v1(_envelope(session_id="pso_fixture_session_non_auth_v1"))


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="conflicting"):
        register_i17_live_contract_join_v1(
            _envelope(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="conflicting"):
        register_i17_live_contract_join_v1(_envelope(evidence_ref="evidence/other"))


def test_ambiguous_join_rejected() -> None:
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="ambiguous join rejected"):
        register_i17_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "preregistration": _prereg(),
                "operator_go": _go(),
            }
        )
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="ambiguous join rejected"):
        register_i17_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "preregistration": [_prereg(), copy.deepcopy(_prereg())],
            }
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="malformed plane data"):
        register_i17_live_contract_join_v1("not-an-object")  # type: ignore[arg-type]
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="malformed plane data"):
        register_i17_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "preregistration": "bad"}
        )
    mutated = _prereg()
    mutated.pop("session_id")
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="malformed plane data"):
        register_i17_live_contract_join_v1(_envelope(preregistration=mutated))


def test_cross_plane_substitution_rejected() -> None:
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="cross-plane substitution"):
        register_i17_live_contract_join_v1(_envelope(plane_presence={"IDENTITY": "PRESENT"}))
    live = _prereg()
    live["session_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="cross-plane substitution"):
        register_i17_live_contract_join_v1(_envelope(preregistration=live))


def test_cross_lane_substitution_rejected() -> None:
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="cross-lane substitution"):
        register_i17_live_contract_join_v1(_envelope(I52={"slice_id": "slice-a"}))
    i52_as_prereg = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "slice_id": "slice-a",
        "relative_dir": "out/ops/levelup/slice-a",
    }
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="noncanonical ID substitution"):
        register_i17_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "preregistration": i52_as_prereg,
            }
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = _prereg()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I17PaperShadowLiveContractJoinError, match="noncanonical ID substitution"):
        register_i17_live_contract_join_v1(_envelope(preregistration=live))


def test_join_is_deterministic() -> None:
    payload = _envelope(content_sha256=_CONTENT_SHA256)
    first = register_i17_live_contract_join_v1(payload).to_canonical_mapping()
    second = register_i17_live_contract_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_registration_does_not_mutate_inputs() -> None:
    payload = _envelope(historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID})
    snapshot = copy.deepcopy(payload)
    record = register_i17_live_contract_join_v1(payload)
    payload["experiment_identity_id"] = "MUTATED"
    payload["preregistration"]["session_id"] = "MUTATED"  # type: ignore[index]
    payload["historical_provenance"]["legacy_experiment_id"] = "MUTATED"  # type: ignore[index]
    assert record.experiment_identity_id == snapshot["experiment_identity_id"]
    assert record.session_id == snapshot["preregistration"]["session_id"]  # type: ignore[index]
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert payload != snapshot


def test_legacy_experiment_id_and_run_id_remain_non_authoritative() -> None:
    payload = _envelope(
        run_id=_RUN_ID,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    record = register_i17_live_contract_join_v1(payload)
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _RUN_ID
    assert record.run_id == _RUN_ID
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
    assert "src.ingress.capsules.evidence_capsule" not in modules
    assert "src.levelup.v0_models" not in modules
    assert "src.live_eval.live_session_eval" not in modules
    assert "src.analytics.explorer" not in modules
    assert (
        "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1"
        ".preregistration_contract_v1"
        in modules
        or "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1"
        in modules
    )
    source = REGISTRATION_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "write_text" not in source
    assert "Path(" not in source
    assert "build_authorization_artifact_v1" not in source
    assert "load_preregistration_contract_dict_v1" not in source


def test_live_contracts_remain_unhooked() -> None:
    for path in _LIVE_CONTRACT_FILES:
        source = path.read_text(encoding="utf-8")
        assert "register_i17_live_contract_join_v1" not in source
        assert "i17_paper_shadow_live_contract_join_v1" not in source
    prereg = json.dumps(_prereg())
    assert "experiment_identity_id" not in prereg
    assert _PACKAGE_N_SHA256 not in PREREG_PATH.read_text(encoding="utf-8")
