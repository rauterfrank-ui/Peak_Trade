"""U-I82-R19 tests for I17 named-lane IDENTITY join on prereg/GO/artifact."""

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
    parse_authorization_artifact_with_identity_join_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_join_attachment_v1 import (
    CONTRACT_ID as R5_CONTRACT_ID,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_named_lane_identity_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I17_NAMED_LANE_IDENTITY_JOIN_REGISTERED,
    I17PaperShadowNamedLaneIdentityJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i17_named_lane_identity_join_registered,
    join_i17_named_lane_identity_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
    parse_operator_go_contract_with_identity_join_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
    parse_preregistration_contract_with_identity_join_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
JOIN_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "i17_paper_shadow_named_lane_identity_join_v1.py"
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
R12_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "i17_paper_shadow_live_contract_join_v1.py"
)
FIX = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
)
_NAMED_LANE_FILES = (PREREG_PATH, GO_PATH, ARTIFACT_PATH)

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r19-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r19-other").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_GIT_SHA = "cd1bd6fa40d664c22b3f6abeef3cc00cdda72688"
_JOIN_MODULE = (
    "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1"
    ".i17_paper_shadow_named_lane_identity_join_v1"
)


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
    assert CONTRACT_ID == "i17_paper_shadow_named_lane_identity_join_v1"
    assert R5_CONTRACT_ID == "i17_paper_shadow_join_attachment_v1"
    assert I17_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True
    assert is_i17_named_lane_identity_join_registered() is True
    assert LIVE_CONTRACT_SURFACES == (
        "preregistration",
        "operator_go",
        "authorization_artifact",
    )


def test_named_prereg_producer_attaches_identity() -> None:
    result = parse_preregistration_contract_with_identity_join_v1(
        _prereg(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(result.join.experiment_identity_id) is True
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert result.join.session_id == result.contract.session_id
    assert result.join.experiment_identity_id != result.contract.session_id
    assert "experiment_identity_id" not in result.contract.to_dict()


def test_declared_absence_for_alias_run_campaign_on_named_lane() -> None:
    result = parse_preregistration_contract_with_identity_join_v1(
        _prereg(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.legacy_alias_md5_12 is None
    assert result.join.run_id is None
    assert result.join.campaign_id is None


def test_prereg_evidence_and_content_hash_are_joined() -> None:
    result = parse_preregistration_contract_with_identity_join_v1(
        _prereg(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert result.join.evidence_ref == result.contract.evidence_root
    assert result.join.content_sha256 == result.contract.scope_digest()
    assert result.join.content_sha256 != result.join.experiment_identity_id


def test_present_run_and_alias_sidecars_are_not_identity() -> None:
    result = parse_preregistration_contract_with_identity_join_v1(
        _prereg(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
        legacy_alias_md5_12=_MD5_12,
    )
    assert result.join.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["ALIAS"] == PlanePresence.PRESENT.value
    assert result.join.run_id == _RUN_ID
    assert result.join.legacy_alias_md5_12 == _MD5_12
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.join.experiment_identity_id != _MD5_12


def test_operator_go_named_lane_attaches_identity() -> None:
    result = parse_operator_go_contract_with_identity_join_v1(
        _go(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.session_id == result.contract.session_id
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert result.join.content_sha256 == result.contract.scope_digest
    assert "experiment_identity_id" not in result.contract.to_dict()


def test_authorization_artifact_named_lane_attaches_identity() -> None:
    artifact = _artifact()
    result = parse_authorization_artifact_with_identity_join_v1(
        artifact,
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.session_id == result.artifact.session_id
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert "experiment_identity_id" not in result.artifact.to_dict()


def test_existing_parse_still_accepts_identity_free_schema() -> None:
    contract = parse_preregistration_contract_v1(_prereg())
    go = parse_operator_go_contract_v1(_go())
    assert "experiment_identity_id" not in contract.to_dict()
    assert "experiment_identity_id" not in go.to_dict()
    assert contract.session_id == "pso_fixture_session_non_auth_v1"


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I17PaperShadowNamedLaneIdentityJoinError, match="implicit absence rejected"):
        parse_preregistration_contract_with_identity_join_v1(
            _prereg(),
            experiment_identity_id=None,  # type: ignore[arg-type]
        )


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(
        I17PaperShadowNamedLaneIdentityJoinError, match="noncanonical ID substitution"
    ):
        parse_preregistration_contract_with_identity_join_v1(
            _prereg(),
            experiment_identity_id=_RUN_ID,
        )
    with pytest.raises(
        I17PaperShadowNamedLaneIdentityJoinError, match="noncanonical ID substitution"
    ):
        parse_preregistration_contract_with_identity_join_v1(
            _prereg(),
            experiment_identity_id=_MD5_12,
        )
    with pytest.raises(
        I17PaperShadowNamedLaneIdentityJoinError, match="noncanonical ID substitution"
    ):
        parse_preregistration_contract_with_identity_join_v1(
            _prereg(),
            experiment_identity_id=_MD5_32,
        )
    with pytest.raises(
        I17PaperShadowNamedLaneIdentityJoinError, match="noncanonical ID substitution"
    ):
        parse_preregistration_contract_with_identity_join_v1(
            _prereg(),
            experiment_identity_id=_GIT_SHA,
        )


def test_session_id_must_not_substitute_identity() -> None:
    live = parse_preregistration_contract_v1(_prereg()).to_dict()
    live["session_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I17PaperShadowNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i17_named_lane_identity_v1(
            live,
            experiment_identity_id=_PACKAGE_N_SHA256,
            surface="preregistration",
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = parse_preregistration_contract_v1(_prereg()).to_dict()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(
        I17PaperShadowNamedLaneIdentityJoinError, match="noncanonical ID substitution"
    ):
        join_i17_named_lane_identity_v1(
            live,
            experiment_identity_id=_PACKAGE_N_SHA256,
            surface="preregistration",
        )


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I17PaperShadowNamedLaneIdentityJoinError, match="conflicting"):
        parse_preregistration_contract_with_identity_join_v1(
            _prereg(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            historical_provenance={"experiment_identity_id": _OTHER_SHA256},
        )


def test_cross_lane_substitution_rejected() -> None:
    live = parse_preregistration_contract_v1(_prereg()).to_dict()
    live["I52"] = {"slice_id": "slice-a"}
    with pytest.raises(I17PaperShadowNamedLaneIdentityJoinError, match="cross-lane substitution"):
        join_i17_named_lane_identity_v1(
            live,
            experiment_identity_id=_PACKAGE_N_SHA256,
            surface="preregistration",
        )


def test_cross_plane_substitution_rejected() -> None:
    live = parse_preregistration_contract_v1(_prereg()).to_dict()
    live["plane_presence"] = {"IDENTITY": "PRESENT"}
    with pytest.raises(I17PaperShadowNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i17_named_lane_identity_v1(
            live,
            experiment_identity_id=_PACKAGE_N_SHA256,
            surface="preregistration",
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I17PaperShadowNamedLaneIdentityJoinError, match="malformed plane data"):
        join_i17_named_lane_identity_v1(
            "not-an-object",  # type: ignore[arg-type]
            experiment_identity_id=_PACKAGE_N_SHA256,
            surface="preregistration",
        )
    with pytest.raises(I17PaperShadowNamedLaneIdentityJoinError, match="malformed plane data"):
        parse_preregistration_contract_with_identity_join_v1(
            _prereg(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            run_id="   ",
        )


def test_join_is_deterministic() -> None:
    first = parse_preregistration_contract_with_identity_join_v1(
        _prereg(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
    ).join.to_canonical_mapping()
    second = parse_preregistration_contract_with_identity_join_v1(
        _prereg(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
    ).join.to_canonical_mapping()
    assert first == second


def test_named_lane_does_not_mutate_inputs() -> None:
    raw = _prereg()
    snapshot = copy.deepcopy(raw)
    result = parse_preregistration_contract_with_identity_join_v1(
        raw,
        experiment_identity_id=_PACKAGE_N_SHA256,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    raw["session_id"] = "MUTATED"
    assert result.contract.session_id == snapshot["session_id"]
    assert dict(raw) != snapshot


def test_legacy_experiment_id_and_run_id_remain_non_authoritative() -> None:
    result = parse_preregistration_contract_with_identity_join_v1(
        _prereg(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.join.run_id == _RUN_ID
    assert dict(result.join.historical_provenance)["legacy_experiment_id"] == _RUN_ID


def test_known_fields_still_forbid_identity_on_persisted_schema() -> None:
    live = _prereg()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(Exception, match="PREREG_UNKNOWN_FIELDS"):
        parse_preregistration_contract_v1(live)
    go = _go()
    go["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(Exception, match="GO_UNKNOWN_FIELDS"):
        parse_operator_go_contract_v1(go)


def test_runtime_invariants_remain_unauthorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1


def test_named_lane_producer_is_hooked_and_forbidden_surfaces_are_not() -> None:
    join_modules = _imported_modules(JOIN_PATH)
    assert (
        "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1"
        ".i17_paper_shadow_join_attachment_v1"
        in join_modules
        or "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_join_attachment_v1"
        in join_modules
    )
    for path in _NAMED_LANE_FILES:
        modules = _imported_modules(path)
        assert _JOIN_MODULE in modules or (
            "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1"
            ".i17_paper_shadow_named_lane_identity_join_v1" in modules
        )
        assert not any(
            mod == "src.execution" or mod.startswith("src.execution.") for mod in modules
        )
        assert not any(
            "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
        )
        assert "src.analytics.explorer" not in modules
        assert "src.ingress.capsules.evidence_capsule" not in modules
        assert "src.levelup.v0_models" not in modules
        assert "src.live_eval.live_session_eval" not in modules
        assert "src.experiments.base" not in modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in join_modules
    )
    join_source = JOIN_PATH.read_text(encoding="utf-8")
    assert "write_text" not in join_source
    assert "open(" not in join_source
    assert "Path(" not in join_source
    init_source = INIT_PATH.read_text(encoding="utf-8")
    assert "i17_paper_shadow_named_lane_identity_join_v1" not in init_source
    attachment_source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    assert "i17_paper_shadow_named_lane_identity_join_v1" not in attachment_source
    r12_source = R12_PATH.read_text(encoding="utf-8")
    assert "i17_paper_shadow_named_lane_identity_join_v1" not in r12_source
    fixture = json.dumps(_prereg())
    assert "experiment_identity_id" not in fixture
    assert _PACKAGE_N_SHA256 not in PREREG_PATH.read_text(encoding="utf-8")
