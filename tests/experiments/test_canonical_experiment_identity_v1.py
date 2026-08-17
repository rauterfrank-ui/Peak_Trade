"""Phase 1 Canonical Experiment Identity v1 contract tests."""

from __future__ import annotations

import ast
import hashlib
import inspect
import logging
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from src.experiments.canonical_experiment_identity_v1 import (
    COMPLETENESS_COMPLETE,
    EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY,
    IDENTITY_DOMAIN,
    PARENT_KIND_PARENT_BOUND,
    PARENT_KIND_ROOT,
    SCHEMA_VERSION,
    WORKING_TREE_CLEAN,
    WORKING_TREE_DIRTY,
    CanonicalCodeProvenanceV1,
    CanonicalExperimentIdentityError,
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
    canonicalize_mapping,
    inspect_code_provenance_v1,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.experiment_identity_manifest_v1 import (
    PACKAGE_N_IDENTITY_COMPLETENESS,
    build_manifest,
)
from src.experiments.base import ExperimentConfig, ParamSweep

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_experiment_identity_v1.py"
_GIT_SHA = "a7f4502e04e168b2dd12b56fecb745323bd6c783"


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _request(**overrides: Any) -> CanonicalExperimentIdentityRequestV1:
    payload: dict[str, Any] = {
        "git_sha": _GIT_SHA,
        "working_tree_status": WORKING_TREE_CLEAN,
        "strategy_identity": "ma_crossover.v1",
        "strategy_params": {"slow": 50, "fast": 10},
        "dataset_digest": _digest("dataset"),
        "feature_pipeline_digest": _digest("features"),
        "fee_model_digest": _digest("fee"),
        "slippage_model_digest": _digest("slippage"),
        "funding_model_digest": _digest("funding"),
        "risk_policy_digest": _digest("risk"),
        "portfolio_digest": _digest("portfolio"),
        "split_policy_digest": _digest("split"),
        "seed": 7,
        "environment": {
            "python_version": "3.11.15",
            "python_implementation": "CPython",
        },
        "parent_lineage_ref": None,
        "dirty_paths_digest": None,
    }
    payload.update(overrides)
    return CanonicalExperimentIdentityRequestV1(**payload)


def test_determinism_same_inputs_same_identity() -> None:
    first = dict(build_canonical_experiment_identity_v1(_request()))
    second = dict(build_canonical_experiment_identity_v1(_request()))
    assert first == second
    assert first["identity_digest"] == second["identity_digest"]
    assert first["completeness"] == COMPLETENESS_COMPLETE


def test_mutation_sensitivity_each_critical_field_changes_identity() -> None:
    baseline = build_canonical_experiment_identity_v1(_request())["identity_digest"]
    mutations: list[dict[str, Any]] = [
        {"git_sha": "b" * 40},
        {"strategy_identity": "macd.v1"},
        {"strategy_params": {"slow": 51, "fast": 10}},
        {"dataset_digest": _digest("dataset-b")},
        {"feature_pipeline_digest": _digest("features-b")},
        {"fee_model_digest": _digest("fee-b")},
        {"slippage_model_digest": _digest("slippage-b")},
        {"funding_model_digest": _digest("funding-b")},
        {"risk_policy_digest": _digest("risk-b")},
        {"portfolio_digest": _digest("portfolio-b")},
        {"split_policy_digest": _digest("split-b")},
        {"seed": 8},
        {"environment": {"python_version": "3.10.14", "python_implementation": "CPython"}},
        {"parent_lineage_ref": _digest("parent")},
    ]
    changed: set[str] = set()
    for mutation in mutations:
        digest = build_canonical_experiment_identity_v1(_request(**mutation))["identity_digest"]
        assert digest != baseline
        changed.add(digest)
    assert len(changed) == len(mutations)


def test_ordering_stability_equivalent_maps_and_sets() -> None:
    left = build_canonical_experiment_identity_v1(
        _request(strategy_params={"z": 1, "nested": {"b": 2, "a": {3, 1, 2}}, "list": [1, 2]})
    )
    right = build_canonical_experiment_identity_v1(
        _request(strategy_params={"list": [1, 2], "nested": {"a": {2, 3, 1}, "b": 2}, "z": 1})
    )
    assert left["strategy_params_digest"] == right["strategy_params_digest"]
    assert left["identity_digest"] == right["identity_digest"]


def test_missing_critical_inputs_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    missing_cases: list[dict[str, Any]] = [
        {"dataset_digest": None},
        {"dataset_digest": "UNKNOWN"},
        {"feature_pipeline_digest": "UNAVAILABLE"},
        {"fee_model_digest": ""},
        {"slippage_model_digest": "n/a"},
        {"funding_model_digest": "implicit"},
        {"risk_policy_digest": "default"},
        {"split_policy_digest": "none"},
        {"seed": None},
    ]
    for mutation in missing_cases:
        with pytest.raises(CanonicalExperimentIdentityError, match="fail-closed|explicit int"):
            build_canonical_experiment_identity_v1(_request(**mutation))


def test_cost_model_decomposition_single_component_changes_identity() -> None:
    baseline = build_canonical_experiment_identity_v1(_request())
    fee_changed = build_canonical_experiment_identity_v1(
        _request(fee_model_digest=_digest("fee-only"))
    )
    assert fee_changed["fee_model_digest"] != baseline["fee_model_digest"]
    assert fee_changed["slippage_model_digest"] == baseline["slippage_model_digest"]
    assert fee_changed["funding_model_digest"] == baseline["funding_model_digest"]
    assert fee_changed["cost_model_digest"] != baseline["cost_model_digest"]
    assert fee_changed["identity_digest"] != baseline["identity_digest"]


def test_lineage_root_versus_parent_bound_distinct() -> None:
    root = build_canonical_experiment_identity_v1(_request(parent_lineage_ref=None))
    child = build_canonical_experiment_identity_v1(
        _request(parent_lineage_ref=_digest("parent-experiment"))
    )
    assert root["parent_lineage"]["kind"] == PARENT_KIND_ROOT
    assert root["parent_lineage"]["parent_lineage_ref"] is None
    assert child["parent_lineage"]["kind"] == PARENT_KIND_PARENT_BOUND
    assert child["identity_digest"] != root["identity_digest"]


def test_secrets_are_neither_serialized_nor_logged(caplog: pytest.LogCaptureFixture) -> None:
    secret_value = "super-secret-credential-value-9f3a"
    caplog.set_level(logging.DEBUG)
    with pytest.raises(CanonicalExperimentIdentityError, match="secret or credential"):
        build_canonical_experiment_identity_v1(
            _request(strategy_params={"window": 3, "api_key": secret_value})
        )
    joined = "\n".join(record.getMessage() for record in caplog.records)
    assert secret_value not in joined
    with pytest.raises(CanonicalExperimentIdentityError) as exc_info:
        canonicalize_mapping({"confirm_token": secret_value})
    assert secret_value not in str(exc_info.value)


def test_dirty_tree_cannot_equal_clean_git_sha_identity() -> None:
    clean = build_canonical_experiment_identity_v1(_request())
    with pytest.raises(CanonicalExperimentIdentityError, match="DIRTY_TREE_PROVENANCE_FAIL_CLOSED"):
        build_canonical_experiment_identity_v1(
            _request(
                working_tree_status=WORKING_TREE_DIRTY,
                dirty_paths_digest=_digest("dirty-paths"),
            )
        )
    dirty_provenance = CanonicalCodeProvenanceV1(
        git_sha=_GIT_SHA,
        working_tree_status=WORKING_TREE_DIRTY,
        dirty_paths_digest=_digest("dirty-paths"),
    )
    assert dirty_provenance.git_sha == clean["git_sha"]
    assert dirty_provenance.working_tree_status != clean["working_tree_status"]


def test_inspect_code_provenance_clean_worktree() -> None:
    provenance = inspect_code_provenance_v1(REPO_ROOT)
    assert provenance.git_sha == _GIT_SHA or len(provenance.git_sha) == 40
    if provenance.working_tree_status == WORKING_TREE_CLEAN:
        assert provenance.dirty_paths_digest is None
        record = build_canonical_experiment_identity_v1(_request(git_sha=provenance.git_sha))
        assert record["working_tree_status"] == WORKING_TREE_CLEAN
    else:
        with pytest.raises(CanonicalExperimentIdentityError, match="DIRTY_TREE"):
            build_canonical_experiment_identity_v1(
                _request(
                    git_sha=provenance.git_sha,
                    working_tree_status=WORKING_TREE_DIRTY,
                    dirty_paths_digest=provenance.dirty_paths_digest,
                )
            )


def test_package_n_identity_not_reinterpreted() -> None:
    config = ExperimentConfig(
        name="MA Optimization",
        strategy_name="ma_crossover",
        param_sweeps=[ParamSweep("fast", [5, 10])],
        symbols=["BTC/EUR"],
        timeframe="1h",
    )
    package_n = build_manifest(config)
    canonical = build_canonical_experiment_identity_v1(_request())
    assert package_n["experiment_identity_id"] != canonical["identity_digest"]
    assert PACKAGE_N_IDENTITY_COMPLETENESS.startswith("INCOMPLETE_")
    assert canonical["schema_version"] != package_n["schema_version"]
    assert canonical["identity_domain"] == IDENTITY_DOMAIN
    assert canonical["schema_version"] == SCHEMA_VERSION


def test_frozen_record_is_immutable() -> None:
    record = build_canonical_experiment_identity_v1(_request())
    assert isinstance(record, MappingProxyType)
    with pytest.raises(TypeError):
        record["seed"] = 99  # type: ignore[index]
    validate_canonical_experiment_identity_v1(record)


def test_authority_boundary_regression_no_write_or_live_paths() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_imports = {
        "src.core.peak_config",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "scripts.run_learning_apply_cycle",
        "src.live",
    }
    assert forbidden_imports.isdisjoint(imported)
    forbidden_tokens = (
        "config/live_overrides",
        "load_config_with_live_overrides",
        "submit_order",
        "confirm_token",
        "LIVE_AUTHORIZED",
        "TESTNET_AUTHORIZED",
        "apply_proposals_to_live_overrides",
    )
    for token in forbidden_tokens:
        assert token not in source
    assert "enabled" not in source.split("EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY")[0]
    assert EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY is False
    record = build_canonical_experiment_identity_v1(_request())
    assert record["experiment_identity_has_runtime_authority"] is False
    assert record["runtime_authority_impact"] == "NONE"
    assert "write_live_config" not in inspect.getsource(build_canonical_experiment_identity_v1)


def test_host_identifying_environment_rejected() -> None:
    with pytest.raises(CanonicalExperimentIdentityError, match="non-reproducibility"):
        build_canonical_experiment_identity_v1(
            _request(
                environment={
                    "python_version": "3.11.15",
                    "python_implementation": "CPython",
                    "hostname": "mac-local",
                }
            )
        )


def test_bool_seed_rejected() -> None:
    with pytest.raises(CanonicalExperimentIdentityError, match="explicit int"):
        build_canonical_experiment_identity_v1(_request(seed=True))
