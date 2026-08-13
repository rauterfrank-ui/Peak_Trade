"""U-I82-R18 tests for I16 named-lane remaining-plane join on lineage producer."""

from __future__ import annotations

import ast
import copy
import json
import shutil
import uuid
from pathlib import Path
from typing import Callable

import pytest

from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.cross_lane_identity_join_v1 import (
    PlanePresence,
    is_package_n_sha256_canonical_id,
)
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    produce_experiment_identity_manifest_v1,
)
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    build_experiment_lineage_ref_from_manifest,
    produce_experiment_lineage_ref_v1,
    produce_experiment_lineage_ref_v1_to_path,
    serialize_experiment_lineage_ref_v1,
)
from src.governance.promotion_loop.i16_lineage_remaining_planes_live_join_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I16LineageRemainingPlanesLiveJoinError,
    I16_LINEAGE_REMAINING_PLANES_JOIN_REGISTERED,
    LIVE_CONTRACT_SURFACES,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    is_i16_lineage_remaining_planes_join_registered,
    join_i16_lineage_remaining_planes_v1,
)
from src.governance.promotion_loop.i16_remaining_planes_join_attachment_v1 import (
    CONTRACT_ID as R4_CONTRACT_ID,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRATION_PATH = (
    REPO_ROOT
    / "src"
    / "governance"
    / "promotion_loop"
    / "i16_lineage_remaining_planes_live_join_v1.py"
)
PRODUCER_PATH = (
    REPO_ROOT / "src" / "governance" / "promotion_loop" / "experiment_lineage_ref_producer_v1.py"
)
ATTACHMENT_PATH = (
    REPO_ROOT
    / "src"
    / "governance"
    / "promotion_loop"
    / "i16_remaining_planes_join_attachment_v1.py"
)
BINDING_PATH = (
    REPO_ROOT
    / "src"
    / "meta"
    / "learning_loop"
    / "comparison_promotion_candidate_identity_binding_v1.py"
)
DURABLE_PATH = (
    REPO_ROOT / "src" / "meta" / "learning_loop" / "experiment_durable_evidence_binding_v1.py"
)
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".package_m_pytest_outputs"

_RUN_ID = str(uuid.uuid4())
_SESSION_ID = "runtime-session-i16-r18"
_CAMPAIGN_ID = "campaign-i16-r18"
_PACKAGE_N_OTHER = "a" * 64


def _sample_config() -> ExperimentConfig:
    return ExperimentConfig(
        name="MA Optimization",
        strategy_name="ma_crossover",
        param_sweeps=[
            ParamSweep("slow", [50, 100], description="ignored in identity"),
            ParamSweep("fast", [5, 10]),
        ],
        symbols=["ETH/EUR", "BTC/EUR"],
        timeframe="1h",
        start_date="2024-01-01",
        end_date="2024-06-01",
        initial_capital=10000.0,
        base_params={"window": 3},
    )


@pytest.fixture
def durable_output_dir() -> Callable[[], Path]:
    """Output paths outside /tmp for Package-N manifest production."""
    _DURABLE_OUTPUT_ROOT.mkdir(exist_ok=True)
    created: list[Path] = []

    def _make() -> Path:
        path = _DURABLE_OUTPUT_ROOT / uuid.uuid4().hex
        created.append(path)
        return path

    yield _make

    for path in created:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def _write_manifest_dir(durable_output_dir: Callable[[], Path]) -> tuple[Path, dict[str, object]]:
    manifest_dir = durable_output_dir()
    produce_experiment_identity_manifest_v1(_sample_config(), manifest_dir)
    manifest = json.loads((manifest_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    return manifest_dir, manifest


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_lineage_remaining_planes_join_is_registered_and_reachable() -> None:
    assert CONTRACT_ID == "i16_lineage_remaining_planes_live_join_v1"
    assert R4_CONTRACT_ID == "i16_remaining_planes_join_attachment_v1"
    assert I16_LINEAGE_REMAINING_PLANES_JOIN_REGISTERED is True
    assert is_i16_lineage_remaining_planes_join_registered() is True
    assert LIVE_CONTRACT_SURFACES == ("lineage_ref",)


def test_named_lane_producer_attaches_remaining_planes(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert result.ref.ref_id == manifest["experiment_identity_id"]
    assert is_package_n_sha256_canonical_id(result.ref.ref_id) is True
    assert result.join.experiment_identity_id == result.ref.ref_id
    assert result.join.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.run_id is None
    assert result.ref.ref_id != manifest["legacy_aliases"]["legacy_experiment_id_md5_12"]


def test_declared_absence_for_run_campaign_session_on_named_lane(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert result.join.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert result.join.campaign_id is None
    assert result.join.session_id is None


def test_present_run_sidecar_is_joined_and_not_identity(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir, run_id=_RUN_ID)
    assert result.join.plane_presence["RUN"] == PlanePresence.PRESENT.value
    assert result.join.run_id == _RUN_ID
    assert result.join.experiment_identity_id == manifest["experiment_identity_id"]
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.ref.ref_id == manifest["experiment_identity_id"]


def test_present_campaign_and_session_sidecars_are_not_identity(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(
        manifest_dir=manifest_dir,
        campaign_id=_CAMPAIGN_ID,
        session_id=_SESSION_ID,
    )
    assert result.join.plane_presence["CAMPAIGN"] == PlanePresence.PRESENT.value
    assert result.join.plane_presence["SESSION"] == PlanePresence.PRESENT.value
    assert result.join.campaign_id == _CAMPAIGN_ID
    assert result.join.session_id == _SESSION_ID
    assert result.join.experiment_identity_id == manifest["experiment_identity_id"]
    assert result.join.experiment_identity_id != _CAMPAIGN_ID
    assert result.join.experiment_identity_id != _SESSION_ID


def test_run_id_must_not_substitute_identity(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    identity = str(manifest["experiment_identity_id"])
    with pytest.raises(Exception, match="cross-plane substitution rejected"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir, run_id=identity)


def test_session_id_must_not_substitute_identity(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    identity = str(manifest["experiment_identity_id"])
    with pytest.raises(Exception, match="cross-plane substitution rejected"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir, session_id=identity)


def test_conflicting_ref_id_rejected(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    mutated = copy.deepcopy(result.ref)
    object.__setattr__(mutated, "ref_id", _PACKAGE_N_OTHER)
    with pytest.raises(I16LineageRemainingPlanesLiveJoinError, match="conflicting identity"):
        join_i16_lineage_remaining_planes_v1(
            manifest,
            ref=mutated,
            artifact_path=ARTIFACT_FILENAME,
        )


def test_cross_lane_substitution_rejected(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    polluted = copy.deepcopy(manifest)
    polluted["I17"] = {"session_id": _SESSION_ID}
    with pytest.raises(I16LineageRemainingPlanesLiveJoinError, match="cross-lane substitution"):
        join_i16_lineage_remaining_planes_v1(
            polluted,
            ref=result.ref,
            artifact_path=ARTIFACT_FILENAME,
        )


def test_cross_plane_substitution_rejected(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    polluted = copy.deepcopy(manifest)
    polluted["plane_presence"] = {"IDENTITY": "PRESENT"}
    with pytest.raises(I16LineageRemainingPlanesLiveJoinError, match="cross-plane substitution"):
        join_i16_lineage_remaining_planes_v1(
            polluted,
            ref=result.ref,
            artifact_path=ARTIFACT_FILENAME,
        )


def test_malformed_sidecar_rejected(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    with pytest.raises(Exception, match="malformed plane data"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir, run_id="   ")


def test_legacy_experiment_id_and_run_id_remain_non_authoritative(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir, run_id=_RUN_ID)
    legacy = manifest["legacy_aliases"]["legacy_experiment_id_md5_12"]
    assert result.join.experiment_identity_id != legacy
    assert result.join.experiment_identity_id != _RUN_ID
    assert result.ref.ref_id != legacy
    assert result.ref.ref_id != _RUN_ID


def test_join_is_deterministic(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    first = produce_experiment_lineage_ref_v1(
        manifest_dir=manifest_dir, run_id=_RUN_ID
    ).join.to_canonical_mapping()
    second = produce_experiment_lineage_ref_v1(
        manifest_dir=manifest_dir, run_id=_RUN_ID
    ).join.to_canonical_mapping()
    assert first == second


def test_producer_does_not_mutate_manifest(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    artifact = manifest_dir / ARTIFACT_FILENAME
    snapshot = artifact.read_text(encoding="utf-8")
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir, run_id=_RUN_ID)
    assert artifact.read_text(encoding="utf-8") == snapshot
    assert result.join.run_id == _RUN_ID


def test_written_lineage_json_has_no_join_record(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    output_path = durable_output_dir() / "ref.json"
    result = produce_experiment_lineage_ref_v1_to_path(
        manifest_dir=manifest_dir,
        output_path=output_path,
        run_id=_RUN_ID,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert "plane_presence" not in payload
    assert "run_id" not in payload
    assert "campaign_id" not in payload
    assert "session_id" not in payload
    assert "join" not in payload
    assert payload["ref_id"] == manifest["experiment_identity_id"]
    assert payload["ref_id"] == result.ref.ref_id
    assert result.join.run_id == _RUN_ID
    serialized = serialize_experiment_lineage_ref_v1(result.ref)
    assert "plane_presence" not in serialized


def test_build_from_manifest_fail_closed_joins_remaining_planes(
    durable_output_dir: Callable[[], Path],
) -> None:
    _manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    ref = build_experiment_lineage_ref_from_manifest(manifest, run_id=_RUN_ID)
    assert ref.ref_id == manifest["experiment_identity_id"]
    join = join_i16_lineage_remaining_planes_v1(
        manifest, ref=ref, artifact_path=ARTIFACT_FILENAME, run_id=_RUN_ID
    )
    assert join.plane_presence["RUN"] == PlanePresence.PRESENT.value


def test_md5_still_not_ref_id(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert result.ref.ref_id != manifest["legacy_aliases"]["legacy_experiment_id_md5_12"]
    assert (
        result.join.legacy_alias_md5_12 == manifest["legacy_aliases"]["legacy_experiment_id_md5_12"]
    )
    assert result.join.experiment_identity_id == result.ref.ref_id


def test_runtime_invariants_remain_unauthorized() -> None:
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert SECOND_EXECUTION_AUTHORITY_AUTHORIZED is False
    assert CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS == 1


def test_named_lane_producer_is_hooked_and_forbidden_surfaces_are_not() -> None:
    producer_modules = _imported_modules(PRODUCER_PATH)
    join_modules = _imported_modules(REGISTRATION_PATH)
    assert (
        "src.governance.promotion_loop.i16_lineage_remaining_planes_live_join_v1"
        in producer_modules
    )
    assert "src.governance.promotion_loop.i16_remaining_planes_join_attachment_v1" in join_modules
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in producer_modules
    )
    assert not any(
        mod == "src.execution" or mod.startswith("src.execution.") for mod in join_modules
    )
    for modules in (producer_modules, join_modules):
        assert not any(
            "single_future_stateful_no_order_runtime_activation_v1" in mod for mod in modules
        )
        assert "src.analytics.explorer" not in modules
        assert "src.ingress.capsules.evidence_capsule" not in modules
        assert "src.levelup.v0_models" not in modules
        assert "src.live_eval.live_session_eval" not in modules
        assert "src.experiments.base" not in modules
    attachment_source = ATTACHMENT_PATH.read_text(encoding="utf-8")
    assert "i16_lineage_remaining_planes_live_join_v1" not in attachment_source
    binding_source = BINDING_PATH.read_text(encoding="utf-8")
    durable_source = DURABLE_PATH.read_text(encoding="utf-8")
    assert "i16_lineage_remaining_planes_live_join_v1" not in binding_source
    assert "i16_lineage_remaining_planes_live_join_v1" not in durable_source
    join_source = REGISTRATION_PATH.read_text(encoding="utf-8")
    assert "write_text" not in join_source
    assert "open(" not in join_source
    producer_source = PRODUCER_PATH.read_text(encoding="utf-8")
    assert "serialize_experiment_lineage_ref_v1(ref)" in producer_source
    assert "serialize_experiment_lineage_ref_v1(result.join" not in producer_source
    assert "write_experiment_lineage_ref_v1_atomic(\n        result.ref" in producer_source
