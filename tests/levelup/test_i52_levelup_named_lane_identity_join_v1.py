"""U-I82-R20 tests for I52 named-lane IDENTITY join on v0 models."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.experiments.cross_lane_identity_join_v1 import (
    PlanePresence,
    is_package_n_sha256_canonical_id,
)
from src.levelup.i52_levelup_join_attachment_v1 import CONTRACT_ID as R6_CONTRACT_ID
from src.levelup.i52_levelup_named_lane_identity_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I52_NAMED_LANE_IDENTITY_JOIN_REGISTERED,
    I52LevelUpNamedLaneIdentityJoinError,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i52_named_lane_identity_join_registered,
    join_i52_named_lane_identity_v1,
)
from src.levelup.v0_models import (
    EvidenceBundleRefV0,
    LevelUpManifestV0,
    SliceContractV0,
    parse_evidence_bundle_with_identity_join_v1,
    parse_levelup_manifest_with_identity_join_v1,
    parse_slice_contract_with_identity_join_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
JOIN_PATH = REPO_ROOT / "src" / "levelup" / "i52_levelup_named_lane_identity_join_v1.py"
ATTACHMENT_PATH = REPO_ROOT / "src" / "levelup" / "i52_levelup_join_attachment_v1.py"
MODELS_PATH = REPO_ROOT / "src" / "levelup" / "v0_models.py"
IO_PATH = REPO_ROOT / "src" / "levelup" / "v0_io.py"
CLI_PATH = REPO_ROOT / "src" / "levelup" / "cli.py"
INIT_PATH = REPO_ROOT / "src" / "levelup" / "__init__.py"
R13_PATH = REPO_ROOT / "src" / "levelup" / "i52_levelup_live_contract_join_v1.py"
_JOIN_MODULE = "src.levelup.i52_levelup_named_lane_identity_join_v1"

_PACKAGE_N_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r20-package-n").hexdigest()
_OTHER_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r20-other").hexdigest()
_CONTENT_SHA256 = hashlib.sha256(b"peak-trade-u-i82-r20-content").hexdigest()
_MD5_12 = "abcdef012345"
_MD5_32 = "d41d8cd98f00b204e9800998ecf8427e"
_RUN_ID = str(uuid.uuid4())
_CAMPAIGN_ID = "campaign-i52-r20"
_SESSION_ID = "session-i52-r20"
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
    assert CONTRACT_ID == "i52_levelup_named_lane_identity_join_v1"
    assert R6_CONTRACT_ID == "i52_levelup_join_attachment_v1"
    assert I52_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True
    assert is_i52_named_lane_identity_join_registered() is True
    assert LIVE_CONTRACT_SURFACES == ("manifest", "slice", "evidence_bundle")


def test_named_manifest_producer_attaches_identity() -> None:
    result = parse_levelup_manifest_with_identity_join_v1(
        _manifest_payload(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert is_package_n_sha256_canonical_id(result.join.experiment_identity_id) is True
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert result.join.evidence_ref == _RELATIVE_DIR
    assert result.join.experiment_identity_id != _SLICE_ID
    assert result.join.experiment_identity_id != _RELATIVE_DIR
    dumped = result.contract.model_dump(mode="python")
    assert "experiment_identity_id" not in dumped
    assert dumped["slices"][0]["slice_id"] == _SLICE_ID


def test_declared_absence_for_alias_run_campaign_session_content_hash() -> None:
    result = parse_levelup_manifest_with_identity_join_v1(
        _manifest_payload(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.plane_presence["ALIAS"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.legacy_alias_md5_12 is None
    assert result.join.run_id is None
    assert result.join.campaign_id is None
    assert result.join.session_id is None
    assert result.join.content_sha256 is None


def test_empty_manifest_is_declared_absence_not_implicit() -> None:
    result = parse_levelup_manifest_with_identity_join_v1(
        _manifest_payload(slices=()),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.evidence_ref is None


def test_present_sidecars_are_joined_and_not_identity() -> None:
    result = parse_levelup_manifest_with_identity_join_v1(
        _manifest_payload(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
        campaign_id=_CAMPAIGN_ID,
        session_id=_SESSION_ID,
        legacy_alias_md5_12=_MD5_12,
        content_sha256=_CONTENT_SHA256,
    )
    assert result.join.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["ALIAS"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["CONTENT_HASH"] == PlanePresence.PRESENT.value
    assert result.join.run_id == _RUN_ID
    assert result.join.campaign_id == _CAMPAIGN_ID
    assert result.join.session_id == _SESSION_ID
    assert result.join.legacy_alias_md5_12 == _MD5_12
    assert result.join.content_sha256 == _CONTENT_SHA256
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.join.experiment_identity_id != _CAMPAIGN_ID
    assert result.join.experiment_identity_id != _SESSION_ID
    assert result.join.experiment_identity_id != _MD5_12
    assert result.join.experiment_identity_id != _CONTENT_SHA256


def test_slice_named_lane_attaches_identity() -> None:
    result = parse_slice_contract_with_identity_join_v1(
        _slice_payload(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.contract.slice_id == _SLICE_ID
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert "experiment_identity_id" not in result.contract.model_dump(mode="python")


def test_evidence_bundle_named_lane_attaches_identity() -> None:
    result = parse_evidence_bundle_with_identity_join_v1(
        _evidence_payload(),
        experiment_identity_id=_PACKAGE_N_SHA256,
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.evidence_ref == result.contract.relative_dir
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["EVIDENCE"] == PlanePresence.PRESENT.value
    assert "experiment_identity_id" not in result.contract.model_dump(mode="python")


def test_existing_model_validate_still_accepts_identity_free_schema() -> None:
    manifest = LevelUpManifestV0.model_validate(_manifest_payload())
    dumped = manifest.model_dump(mode="python")
    assert "experiment_identity_id" not in dumped
    assert dumped["slices"][0]["slice_id"] == _SLICE_ID


def test_implicit_absence_of_identity_rejected() -> None:
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="implicit absence rejected"):
        parse_levelup_manifest_with_identity_join_v1(_manifest_payload())


def test_noncanonical_id_substitution_rejected() -> None:
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_levelup_manifest_with_identity_join_v1(
            _manifest_payload(),
            experiment_identity_id=_RUN_ID,
        )
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_levelup_manifest_with_identity_join_v1(
            _manifest_payload(),
            experiment_identity_id=_MD5_12,
        )
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_levelup_manifest_with_identity_join_v1(
            _manifest_payload(),
            experiment_identity_id=_MD5_32,
        )
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        parse_levelup_manifest_with_identity_join_v1(
            _manifest_payload(),
            experiment_identity_id=_SLICE_ID,
        )


def test_slice_id_must_not_substitute_identity() -> None:
    live = _slice_payload()
    live["slice_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i52_named_lane_identity_v1(
            live,
            surface="slice",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_identity_inside_live_payload_rejected() -> None:
    live = _slice_payload()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="noncanonical ID substitution"):
        join_i52_named_lane_identity_v1(
            live,
            surface="slice",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_conflicting_identity_rejected() -> None:
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="conflicting"):
        parse_levelup_manifest_with_identity_join_v1(
            _manifest_payload(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            historical_provenance={"experiment_identity_id": _OTHER_SHA256},
        )
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="conflicting"):
        parse_levelup_manifest_with_identity_join_v1(
            _manifest_payload(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            evidence_ref="out/ops/other_slice/",
        )


def test_ambiguous_join_rejected() -> None:
    second = _slice_payload()
    second["slice_id"] = "S2-R3"
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="ambiguous join rejected"):
        parse_levelup_manifest_with_identity_join_v1(
            _manifest_payload(slices=(_slice_payload(), second)),
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_malformed_plane_data_rejected() -> None:
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="malformed plane data"):
        join_i52_named_lane_identity_v1(
            "not-an-object",  # type: ignore[arg-type]
            surface="manifest",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="malformed plane data"):
        parse_levelup_manifest_with_identity_join_v1(
            _manifest_payload(),
            experiment_identity_id=_PACKAGE_N_SHA256,
            run_id="   ",
        )


def test_cross_lane_substitution_rejected() -> None:
    live = _manifest_payload()
    live["I17"] = {"session_id": "pso_fixture"}
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="cross-lane substitution"):
        join_i52_named_lane_identity_v1(
            live,
            surface="manifest",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_cross_plane_substitution_rejected() -> None:
    live = _manifest_payload()
    live["plane_presence"] = {"IDENTITY": "PRESENT"}
    with pytest.raises(I52LevelUpNamedLaneIdentityJoinError, match="cross-plane substitution"):
        join_i52_named_lane_identity_v1(
            live,
            surface="manifest",
            experiment_identity_id=_PACKAGE_N_SHA256,
        )


def test_join_is_deterministic() -> None:
    first = parse_levelup_manifest_with_identity_join_v1(
        _manifest_payload(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
    ).join.to_canonical_mapping()
    second = parse_levelup_manifest_with_identity_join_v1(
        _manifest_payload(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
    ).join.to_canonical_mapping()
    assert first == second


def test_named_lane_does_not_mutate_inputs() -> None:
    raw = _manifest_payload()
    snapshot = copy.deepcopy(raw)
    result = parse_levelup_manifest_with_identity_join_v1(
        raw,
        experiment_identity_id=_PACKAGE_N_SHA256,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    raw["title"] = "MUTATED"
    assert result.contract.title == snapshot["title"]
    assert dict(raw) != snapshot


def test_legacy_experiment_id_and_run_id_remain_non_authoritative() -> None:
    result = parse_levelup_manifest_with_identity_join_v1(
        _manifest_payload(),
        experiment_identity_id=_PACKAGE_N_SHA256,
        run_id=_RUN_ID,
        historical_provenance={"legacy_experiment_id": _RUN_ID, "run_id": _RUN_ID},
    )
    assert result.join.experiment_identity_id == _PACKAGE_N_SHA256
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.join.run_id == _RUN_ID
    assert dict(result.join.historical_provenance)["legacy_experiment_id"] == _RUN_ID


def test_persisted_schema_still_forbids_identity_field() -> None:
    live = _manifest_payload()
    live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(ValidationError):
        LevelUpManifestV0.model_validate(live)
    slice_live = _slice_payload()
    slice_live["experiment_identity_id"] = _PACKAGE_N_SHA256
    with pytest.raises(ValidationError):
        SliceContractV0.model_validate(slice_live)


def test_runtime_invariants_remain_unauthorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1


def test_named_lane_producer_is_hooked_and_forbidden_surfaces_are_not() -> None:
    join_modules = _imported_modules(JOIN_PATH)
    assert "src.levelup.i52_levelup_join_attachment_v1" in join_modules
    assert "src.levelup.v0_models" not in join_modules
    models_modules = _imported_modules(MODELS_PATH)
    assert _JOIN_MODULE in models_modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in models_modules
    )
    assert not any(
        "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in models_modules
    )
    assert "src.analytics.explorer" not in models_modules
    assert "src.ingress.capsules.evidence_capsule" not in models_modules
    assert "src.live_eval.live_session_eval" not in models_modules
    assert "src.experiments.base" not in models_modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in join_modules
    )
    join_source = JOIN_PATH.read_text(encoding="utf-8")
    assert "write_text" not in join_source
    assert "open(" not in join_source
    assert "Path(" not in join_source
    assert "write_manifest" not in join_source
    assert "read_manifest" not in join_source
    models_source = MODELS_PATH.read_text(encoding="utf-8")
    assert "experiment_identity_id" not in models_source
    assert "i52_levelup_live_contract_join_v1" not in models_source
    init_source = INIT_PATH.read_text(encoding="utf-8")
    assert "i52_levelup_named_lane_identity_join_v1" not in init_source
    io_source = IO_PATH.read_text(encoding="utf-8")
    cli_source = CLI_PATH.read_text(encoding="utf-8")
    attachment_source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    r13_source = R13_PATH.read_text(encoding="utf-8")
    assert "i52_levelup_named_lane_identity_join_v1" not in io_source
    assert "i52_levelup_named_lane_identity_join_v1" not in cli_source
    assert "i52_levelup_named_lane_identity_join_v1" not in attachment_source
    assert "i52_levelup_named_lane_identity_join_v1" not in r13_source
    assert _PACKAGE_N_SHA256 not in models_source
