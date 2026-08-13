"""U-I82-R13 tests for dormant I52 live-contract join registration."""

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
from src.levelup.i52_levelup_live_contract_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I52_LIVE_CONTRACT_REGISTERED,
    I52LevelUpLiveContractJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i52_live_contract_registered,
    register_i52_live_contract_join_v1,
)
from src.levelup.v0_models import EvidenceBundleRefV0, LevelUpManifestV0, SliceContractV0
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.i17_paper_shadow_live_contract_join_v1 import (
    I17_LIVE_CONTRACT_REGISTERED,
    is_i17_live_contract_registered,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_PATH = REPO_ROOT / "src" / "levelup" / "i52_levelup_live_contract_join_v1.py"
ATTACHMENT_PATH = REPO_ROOT / "src" / "levelup" / "i52_levelup_join_attachment_v1.py"
MODELS_PATH = REPO_ROOT / "src" / "levelup" / "v0_models.py"
IO_PATH = REPO_ROOT / "src" / "levelup" / "v0_io.py"
CLI_PATH = REPO_ROOT / "src" / "levelup" / "cli.py"
INIT_PATH = REPO_ROOT / "src" / "levelup" / "__init__.py"
I17_REGISTRATION_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "paper_shadow_observation_operator_go_session_preregistration_v1"
    / "i17_paper_shadow_live_contract_join_v1.py"
)
_LIVE_CONTRACT_FILES = (MODELS_PATH, IO_PATH, CLI_PATH, INIT_PATH, ATTACHMENT_PATH)

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r13-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r13-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r13-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_SLICE_ID = "S1-R3"
_RELATIVE_DIR = "out/ops/slice_demo_001/"


def _slice_payload(*, with_evidence: bool = True) -> dict[str, object]:
    evidence = EvidenceBundleRefV0(relative_dir=_RELATIVE_DIR) if with_evidence else None
    return SliceContractV0(
        slice_id=_SLICE_ID,
        title="Live execution gated",
        contract_summary="Without enabled+armed+token → no order.",
        evidence=evidence,
    ).model_dump(mode="python")


def _manifest_payload(*, slices: tuple[dict[str, object], ...] | None = None) -> dict[str, object]:
    if slices is None:
        slices = (_slice_payload(),)
    models = tuple(SliceContractV0.model_validate(item) for item in slices)
    return LevelUpManifestV0(title="Test", slices=models).model_dump(mode="python")


def _evidence_payload() -> dict[str, object]:
    return EvidenceBundleRefV0(relative_dir=_RELATIVE_DIR).model_dump(mode="python")


def _envelope(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "experiment_identity_id": _PACKAGE_N_SHA256,
        "manifest": _manifest_payload(),
    }
    payload.update(overrides)
    return payload


def test_live_contract_registration_flag_is_reachable() -> None:
    assert CONTRACT_ID == "i52_levelup_live_contract_join_v1"
    assert I52_LIVE_CONTRACT_REGISTERED is True
    assert is_i52_live_contract_registered() is True
    assert LIVE_CONTRACT_SURFACES == ("manifest", "slice", "evidence_bundle")
    assert I17_LIVE_CONTRACT_REGISTERED is True
    assert is_i17_live_contract_registered() is True


def test_canonical_package_n_sha256_present_join_from_manifest() -> None:
    record = register_i52_live_contract_join_v1(_envelope())
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True
    assert record.evidence_ref == _RELATIVE_DIR
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert record.experiment_identity_id != _SLICE_ID
    assert record.experiment_identity_id != _RELATIVE_DIR


def test_declared_absence_for_alias_run_campaign_session_content_hash() -> None:
    record = register_i52_live_contract_join_v1(_envelope())
    assert record.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert record.legacy_alias_md5_12 is None
    assert record.run_id is None
    assert record.campaign_id is None
    assert record.session_id is None
    assert record.content_sha256 is None


def test_empty_manifest_is_declared_absence_not_implicit() -> None:
    record = register_i52_live_contract_join_v1(
        {
            "experiment_identity_id": _PACKAGE_N_SHA256,
            "manifest": _manifest_payload(slices=()),
        }
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.evidence_ref is None


def test_slice_present_join() -> None:
    record = register_i52_live_contract_join_v1(
        {
            "experiment_identity_id": _PACKAGE_N_SHA256,
            "slice": _slice_payload(),
        }
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.evidence_ref == _RELATIVE_DIR
    assert record.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value


def test_evidence_bundle_present_join() -> None:
    record = register_i52_live_contract_join_v1(
        {
            "experiment_identity_id": _PACKAGE_N_SHA256,
            "evidence_bundle": _evidence_payload(),
        }
    )
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.evidence_ref == _RELATIVE_DIR
    assert record.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value


def test_explicit_declared_run_and_alias_remain_non_authoritative() -> None:
    record = register_i52_live_contract_join_v1(
        _envelope(run_id=_RUN_ID, legacy_alias_md5_12=_MD5_12, content_sha256=_CONTENT_SHA256)
    )
    assert record.run_id == _RUN_ID
    assert record.legacy_alias_md5_12 == _MD5_12
    assert record.content_sha256 == _CONTENT_SHA256
    assert record.experiment_identity_id == _PACKAGE_N_SHA256
    assert record.experiment_identity_id != _RUN_ID
    assert record.experiment_identity_id != _MD5_12
    assert record.experiment_identity_id != _CONTENT_SHA256


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I52LevelUpLiveContractJoinError, match="implicit absence rejected"):
        register_i52_live_contract_join_v1({"manifest": _manifest_payload()})


def test_implicit_absence_of_live_surface_rejected() -> None:
    with pytest.raises(I52LevelUpLiveContractJoinError, match="implicit absence rejected"):
        register_i52_live_contract_join_v1({"experiment_identity_id": _PACKAGE_N_SHA256})


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(I52LevelUpLiveContractJoinError, match="noncanonical ID substitution"):
        register_i52_live_contract_join_v1(_envelope(experiment_identity_id=_RUN_ID))
    with pytest.raises(I52LevelUpLiveContractJoinError, match="noncanonical ID substitution"):
        register_i52_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_12))
    with pytest.raises(I52LevelUpLiveContractJoinError, match="noncanonical ID substitution"):
        register_i52_live_contract_join_v1(_envelope(experiment_identity_id=_MD5_32))
    with pytest.raises(I52LevelUpLiveContractJoinError, match="noncanonical ID substitution"):
        register_i52_live_contract_join_v1(_envelope(experiment_identity_id=_SLICE_ID))


def test_legacy_experiment_id_and_slice_id_on_envelope_rejected() -> None:
    with pytest.raises(I52LevelUpLiveContractJoinError, match="noncanonical ID substitution"):
        register_i52_live_contract_join_v1(_envelope(experiment_id=_RUN_ID))
    with pytest.raises(I52LevelUpLiveContractJoinError, match="noncanonical ID substitution"):
        register_i52_live_contract_join_v1(_envelope(slice_id=_SLICE_ID))


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I52LevelUpLiveContractJoinError, match="conflicting"):
        register_i52_live_contract_join_v1(
            _envelope(historical_provenance={"experiment_identity_id": _OTHER_SHA256})
        )
    with pytest.raises(I52LevelUpLiveContractJoinError, match="conflicting"):
        register_i52_live_contract_join_v1(_envelope(evidence_ref="out/ops/other_slice/"))


def test_ambiguous_join_rejected() -> None:
    with pytest.raises(I52LevelUpLiveContractJoinError, match="ambiguous join rejected"):
        register_i52_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "manifest": _manifest_payload(),
                "slice": _slice_payload(),
            }
        )
    second = _slice_payload()
    second["slice_id"] = "S2-R3"
    with pytest.raises(I52LevelUpLiveContractJoinError, match="ambiguous join rejected"):
        register_i52_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "manifest": _manifest_payload(slices=(_slice_payload(), second)),
            }
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I52LevelUpLiveContractJoinError, match="malformed plane data"):
        register_i52_live_contract_join_v1("not-an-object")  # type: ignore[arg-type]
    with pytest.raises(I52LevelUpLiveContractJoinError, match="malformed plane data"):
        register_i52_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "manifest": "bad"}
        )
    mutated = _slice_payload()
    mutated.pop("slice_id")
    with pytest.raises(I52LevelUpLiveContractJoinError, match="malformed plane data"):
        register_i52_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "slice": mutated}
        )


def test_cross_plane_substitution_rejected() -> None:
    with pytest.raises(I52LevelUpLiveContractJoinError, match="cross-plane substitution"):
        register_i52_live_contract_join_v1(_envelope(plane_presence={"IDENTITY": "PRESENT"}))
    live = _slice_payload()
    live["slice_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I52LevelUpLiveContractJoinError, match="cross-plane substitution"):
        register_i52_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "slice": live}
        )


def test_cross_lane_substitution_rejected() -> None:
    with pytest.raises(I52LevelUpLiveContractJoinError, match="cross-lane substitution"):
        register_i52_live_contract_join_v1(_envelope(I17={"session_id": "pso_fixture"}))
    i17_as_manifest = {
        "session_id": "pso_fixture_session_non_auth_v1",
        "evidence_root": "evidence/fixtures/paper_shadow_observation_non_authoritative_v1",
    }
    with pytest.raises(I52LevelUpLiveContractJoinError, match="malformed plane data"):
        register_i52_live_contract_join_v1(
            {
                "experiment_identity_id": _PACKAGE_N_SHA256,
                "manifest": i17_as_manifest,
            }
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = _slice_payload()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I52LevelUpLiveContractJoinError, match="noncanonical ID substitution"):
        register_i52_live_contract_join_v1(
            {"experiment_identity_id": _PACKAGE_N_SHA256, "slice": live}
        )


def test_join_is_deterministic() -> None:
    payload = _envelope(content_sha256=_CONTENT_SHA256)
    first = register_i52_live_contract_join_v1(payload).to_canonical_mapping()
    second = register_i52_live_contract_join_v1(copy.deepcopy(payload)).to_canonical_mapping()
    assert first == second


def test_registration_does_not_mutate_inputs() -> None:
    payload = _envelope(historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID})
    snapshot = copy.deepcopy(payload)
    record = register_i52_live_contract_join_v1(payload)
    payload["experiment_identity_id"] = "MUTATED"
    payload["manifest"]["title"] = "MUTATED"  # type: ignore[index]
    payload["historical_provenance"]["legacy_experiment_id"] = "MUTATED"  # type: ignore[index]
    assert record.experiment_identity_id == snapshot["experiment_identity_id"]
    assert dict(record.historical_provenance)["legacy_experiment_id"] == _RUN_ID
    assert payload != snapshot


def test_legacy_experiment_id_and_run_id_remain_non_authoritative() -> None:
    payload = _envelope(
        run_id=_RUN_ID,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    record = register_i52_live_contract_join_v1(payload)
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
    assert "src.levelup.v0_io" not in modules
    assert "src.levelup.cli" not in modules
    assert "src.ingress.capsules.evidence_capsule" not in modules
    assert "src.live_eval.live_session_eval" not in modules
    assert "src.analytics.explorer" not in modules
    assert "src.levelup.v0_models" in modules
    assert "src.levelup.i52_levelup_join_attachment_v1" in modules
    source = REGISTRATION_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "write_text" not in source
    assert "Path(" not in source
    assert "write_manifest" not in source
    assert "read_manifest" not in source


def test_live_contracts_and_i17_remain_unhooked() -> None:
    for path in _LIVE_CONTRACT_FILES:
        source = path.read_text(encoding="utf-8")
        assert "register_i52_live_contract_join_v1" not in source
        assert "i52_levelup_live_contract_join_v1" not in source
    models = MODELS_PATH.read_text(encoding="utf-8")
    assert "experiment_identity_id" not in models
    i17 = I17_REGISTRATION_PATH.read_text(encoding="utf-8")
    assert "i52_levelup_live_contract_join_v1" not in i17
    assert "I52_LIVE_CONTRACT_REGISTERED = True" not in i17
