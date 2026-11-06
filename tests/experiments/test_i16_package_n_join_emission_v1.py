"""U-I82-R10 tests for dormant I16 Package-N producer join emission."""

from __future__ import annotations

import ast
import copy
import hashlib
import uuid
from pathlib import Path

import pytest

from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.cross_lane_identity_join_v1 import (
    PlanePresence,
    is_package_n_sha256_canonical_id,
)
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    build_manifest,
)
from src.experiments.i16_package_n_join_emission_v1 import (
    CONTRACT_ID,
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    I16PackageNJoinEmissionError,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    emit_i16_package_n_join_from_producer_v1,
    emit_i16_package_n_join_v1,
)
from src.ops.config_truth_alignment_contract_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED as CONFIG_MULTI_FUTURE_RUNTIME_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EMISSION_PATH = REPO_ROOT / "src" / "experiments" / "i16_package_n_join_emission_v1.py"
PRODUCER_PATH = REPO_ROOT / "src" / "experiments" / "experiment_identity_manifest_v1.py"
CLI_PATH = REPO_ROOT / "scripts" / "run_experiment_identity_manifest_v1.py"

_MD5_12 = "abcdef012345"
_RUN_ID = str(uuid.uuid4())


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


def test_canonical_package_n_sha256_reaches_i82_join() -> None:
    config = _sample_config()
    manifest = build_manifest(config)
    record = emit_i16_package_n_join_v1(manifest)
    assert CONTRACT_ID == "i16_package_n_join_emission_v1"
    assert record.experiment_identity_id == manifest["experiment_identity_id"]
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True
    assert record.plane_presence["IDENTITY"] == PlanePresence.PRESENT.value
    assert record.legacy_alias_md5_12 == manifest["legacy_aliases"]["legacy_experiment_id_md5_12"]
    assert record.content_sha256 == manifest["integrity"]["content_sha256"]
    assert record.experiment_identity_id != record.legacy_alias_md5_12
    assert record.experiment_identity_id != record.content_sha256


def test_producer_path_is_deterministic() -> None:
    config = _sample_config()
    first = emit_i16_package_n_join_from_producer_v1(config).to_canonical_mapping()
    second = emit_i16_package_n_join_from_producer_v1(copy.deepcopy(config)).to_canonical_mapping()
    assert first == second
    assert first["experiment_identity_id"] == build_manifest(config)["experiment_identity_id"]


def test_declared_absence_for_run_campaign_session_evidence() -> None:
    record = emit_i16_package_n_join_v1(build_manifest(_sample_config()))
    assert record.plane_presence["RUN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["CAMPAIGN"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["SESSION"] == PlanePresence.ABSENT_DECLARED.value
    assert record.plane_presence["EVIDENCE"] == PlanePresence.ABSENT_DECLARED.value
    assert record.run_id is None
    assert record.campaign_id is None
    assert record.session_id is None
    assert record.evidence_ref is None


def test_implicit_absence_rejected() -> None:
    with pytest.raises(I16PackageNJoinEmissionError, match="malformed Package-N producer manifest"):
        emit_i16_package_n_join_v1({})


def test_noncanonical_id_substitution_rejected() -> None:
    manifest = build_manifest(_sample_config())
    mutated = copy.deepcopy(manifest)
    mutated["experiment_identity_id"] = _RUN_ID
    with pytest.raises(I16PackageNJoinEmissionError, match="malformed Package-N producer manifest"):
        emit_i16_package_n_join_v1(mutated)
    mutated_md5 = copy.deepcopy(manifest)
    mutated_md5["experiment_identity_id"] = _MD5_12
    with pytest.raises(I16PackageNJoinEmissionError, match="malformed Package-N producer manifest"):
        emit_i16_package_n_join_v1(mutated_md5)


def test_run_id_on_producer_manifest_rejected() -> None:
    manifest = build_manifest(_sample_config())
    mutated = copy.deepcopy(manifest)
    mutated["run_id"] = _RUN_ID
    with pytest.raises(I16PackageNJoinEmissionError, match="noncanonical ID substitution"):
        emit_i16_package_n_join_v1(mutated)


def test_conflicting_identity_rejected() -> None:
    manifest = build_manifest(_sample_config())
    mutated = copy.deepcopy(manifest)
    mutated["experiment_identity_id"] = hashlib.sha256(b"peak-trade-u-i82-r10-other").hexdigest()
    with pytest.raises(I16PackageNJoinEmissionError, match="malformed Package-N producer manifest"):
        emit_i16_package_n_join_v1(mutated)


def test_ambiguous_and_malformed_join_rejected() -> None:
    with pytest.raises(I16PackageNJoinEmissionError, match="must be an object"):
        emit_i16_package_n_join_v1("not-an-object")  # type: ignore[arg-type]
    manifest = build_manifest(_sample_config())
    mutated = copy.deepcopy(manifest)
    mutated["integrity"] = "bad"
    with pytest.raises(I16PackageNJoinEmissionError, match="malformed"):
        emit_i16_package_n_join_v1(mutated)


def test_source_experiment_id_is_non_authoritative() -> None:
    source = "legacy-source-alias"
    record = emit_i16_package_n_join_from_producer_v1(_sample_config(), source_experiment_id=source)
    assert record.experiment_identity_id != source
    assert dict(record.historical_provenance)["source_experiment_id"] == source
    assert is_package_n_sha256_canonical_id(record.experiment_identity_id) is True


def test_attachment_does_not_mutate_inputs() -> None:
    manifest = build_manifest(_sample_config())
    snapshot = copy.deepcopy(manifest)
    record = emit_i16_package_n_join_v1(manifest)
    manifest["experiment_identity_id"] = "MUTATED"
    manifest["legacy_aliases"]["legacy_experiment_id_md5_12"] = "MUTATED"
    assert record.experiment_identity_id == snapshot["experiment_identity_id"]
    assert record.legacy_alias_md5_12 == snapshot["legacy_aliases"]["legacy_experiment_id_md5_12"]
    assert snapshot != manifest


def test_producer_artifact_schema_has_no_join_record() -> None:
    manifest = build_manifest(_sample_config())
    assert "plane_presence" not in manifest
    assert "join_key" not in manifest
    assert ARTIFACT_FILENAME == "experiment_identity_manifest_v1.json"


def test_producer_and_cli_remain_unhooked() -> None:
    producer = PRODUCER_PATH.read_text(encoding="utf-8")
    cli = CLI_PATH.read_text(encoding="utf-8")
    assert "emit_i16_package_n_join_v1" not in producer
    assert "attach_i16_remaining_planes_join_v1" not in producer
    assert "emit_i16_package_n_join_v1" not in cli
    assert "i16_package_n_join_emission_v1" not in cli


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


def test_no_cap72_execution_or_live_contract_registration() -> None:
    modules = _imported_modules(EMISSION_PATH)
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
        "src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1"
        not in modules
    )
    assert "src.governance.promotion_loop.i16_remaining_planes_join_attachment_v1" in modules
    source = EMISSION_PATH.read_text(encoding="utf-8")
    assert "open(" not in source
    assert "produce_experiment_identity_manifest_v1" not in source
    assert "write_text" not in source
    assert "Path(" not in source
