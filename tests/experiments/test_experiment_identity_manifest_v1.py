"""Tests for Package N experiment identity manifest producer v1."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    IDENTITY_DOMAIN,
    IDENTITY_SCHEMA_VERSION,
    ExperimentIdentityManifestError,
    _FORBIDDEN_MANIFEST_KEYS,
    _is_phase41_constraint_bridge_active,
    _is_regime_config_behaviorally_active,
    _is_switching_config_behaviorally_active,
    active_input_matrix_classifications,
    build_identity_config,
    build_manifest,
    compute_experiment_identity_id,
    compute_legacy_experiment_id_md5_12,
    experiment_config_from_mapping,
    produce_experiment_identity_manifest_v1,
    unclassified_active_input_count,
    validate_active_input_completeness,
    validate_experiment_identity_manifest_v1,
)


def _sample_config(**overrides: Any) -> ExperimentConfig:
    base = ExperimentConfig(
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
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_identity_happy_path_deterministic(tmp_path: Path) -> None:
    config = _sample_config()
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    produce_experiment_identity_manifest_v1(config, out_a)
    produce_experiment_identity_manifest_v1(config, out_b)
    assert (out_a / ARTIFACT_FILENAME).read_text() == (out_b / ARTIFACT_FILENAME).read_text()


def test_experiment_identity_id_sha256_64hex() -> None:
    manifest = build_manifest(_sample_config())
    identity_id = manifest["experiment_identity_id"]
    assert len(identity_id) == 64
    assert identity_id.islower()
    assert all(ch in "0123456789abcdef" for ch in identity_id)


def test_domain_separator_and_schema_version() -> None:
    identity = build_identity_config(_sample_config())
    assert identity["identity_schema_version"] == IDENTITY_SCHEMA_VERSION
    assert identity["identity_domain"] == IDENTITY_DOMAIN


def test_required_fields_present() -> None:
    manifest = build_manifest(_sample_config())
    for key in (
        "schema_version",
        "contract_version",
        "identity_domain",
        "experiment_identity_id",
        "identity_config",
        "legacy_aliases",
        "provenance",
        "integrity",
        "safety",
    ):
        assert key in manifest


def test_base_params_recursive_canonicalization() -> None:
    identity = build_identity_config(
        _sample_config(base_params={"z": 1, "nested": {"b": 2, "a": 1}})
    )
    assert list(identity["base_params"].keys()) == ["nested", "z"]
    assert list(identity["base_params"]["nested"].keys()) == ["a", "b"]


def test_param_sweeps_sorted_by_name() -> None:
    identity = build_identity_config(_sample_config())
    assert [item["name"] for item in identity["param_sweeps"]] == ["fast", "slow"]


def test_symbols_lex_sort_default() -> None:
    identity = build_identity_config(_sample_config())
    assert identity["symbols"] == ["BTC/EUR", "ETH/EUR"]


def test_float_numpy_normalization() -> None:
    config = _sample_config(
        param_sweeps=[ParamSweep("threshold", [np.float64(0.1), np.float32(0.2)])]
    )
    identity = build_identity_config(config)
    assert identity["param_sweeps"][0]["values"] == [0.1, 0.2]


def test_none_vs_missing_dates() -> None:
    with_dates = build_identity_config(_sample_config())
    without_dates = build_identity_config(_sample_config(start_date=None, end_date=None))
    assert with_dates["start_date"] == "2024-01-01"
    assert without_dates["start_date"] is None
    assert without_dates["end_date"] is None
    assert compute_experiment_identity_id(with_dates) != compute_experiment_identity_id(
        without_dates
    )


class _Mode(Enum):
    FAST = "fast"
    SLOW = "slow"


def test_enum_serialization_in_base_params() -> None:
    identity = build_identity_config(_sample_config(base_params={"mode": _Mode.FAST}))
    assert identity["base_params"]["mode"] == "fast"


def test_path_normalization_in_base_params() -> None:
    identity = build_identity_config(
        _sample_config(base_params={"path": "/tmp/Foo/Bar-Config.JSON"})
    )
    assert identity["base_params"]["path"] == "tmp.foo.bar_config.json"


def test_legacy_md5_alias_parity() -> None:
    config = _sample_config()
    manifest = build_manifest(config)
    assert manifest["legacy_aliases"]["legacy_experiment_id_md5_12"] == config.get_experiment_id()


def test_forbidden_run_fields_rejected() -> None:
    manifest = build_manifest(_sample_config())
    for key in ("run_id", "run_index"):
        polluted = copy.deepcopy(manifest)
        polluted[key] = "forbidden"
        with pytest.raises(ExperimentIdentityManifestError, match="forbidden key"):
            validate_experiment_identity_manifest_v1(polluted)


def test_forbidden_result_fields_rejected() -> None:
    manifest = build_manifest(_sample_config())
    polluted = copy.deepcopy(manifest)
    polluted["metrics"] = {"sharpe": 1.0}
    with pytest.raises(ExperimentIdentityManifestError, match="forbidden key"):
        validate_experiment_identity_manifest_v1(polluted)


def test_forbidden_runtime_authority_fields() -> None:
    manifest = build_manifest(_sample_config())
    polluted = copy.deepcopy(manifest)
    polluted["promotion_authority"] = True
    with pytest.raises(ExperimentIdentityManifestError, match="forbidden key"):
        validate_experiment_identity_manifest_v1(polluted)


def test_regime_config_inactive_regression() -> None:
    config = _sample_config(regime_config={"detector": "volatility"})
    validate_active_input_completeness(config)
    manifest = build_manifest(config)
    assert "regime_config" not in manifest["identity_config"]


def test_switching_config_inactive_regression() -> None:
    config = _sample_config(switching_config={"mode": "auto"})
    validate_active_input_completeness(config)
    manifest = build_manifest(config)
    assert "switching_config" not in manifest["identity_config"]


def test_regime_active_simulation_fail_closed_hook() -> None:
    config = _sample_config(regime_config={"detector": "volatility"})
    with patch(
        "src.experiments.experiment_identity_manifest_v1._is_regime_config_behaviorally_active",
        return_value=True,
    ):
        with pytest.raises(ExperimentIdentityManifestError, match="regime_config"):
            validate_active_input_completeness(config)


def test_switching_active_simulation_fail_closed_hook() -> None:
    config = _sample_config(switching_config={"mode": "auto"})
    with patch(
        "src.experiments.experiment_identity_manifest_v1._is_switching_config_behaviorally_active",
        return_value=True,
    ):
        with pytest.raises(ExperimentIdentityManifestError, match="switching_config"):
            validate_active_input_completeness(config)


def test_phase41_unmaterialized_fail_closed() -> None:
    config = _sample_config()
    with patch(
        "src.experiments.experiment_identity_manifest_v1._is_phase41_constraint_bridge_active",
        return_value=True,
    ):
        with pytest.raises(ExperimentIdentityManifestError, match="Phase-41"):
            validate_active_input_completeness(config)


def test_phase41_materialized_passes() -> None:
    config = _sample_config(
        param_sweeps=[ParamSweep("window", [10, 20]), ParamSweep("threshold", [0.1, 0.2])]
    )
    validate_active_input_completeness(config)
    manifest = build_manifest(config)
    assert manifest["identity_config"]["param_sweeps"]


def test_active_input_completeness_validator() -> None:
    validate_active_input_completeness(_sample_config())
    assert unclassified_active_input_count() == 0


def test_all_active_input_matrix_entries_classified() -> None:
    classifications = active_input_matrix_classifications()
    assert len(classifications) >= 27
    assert all(
        classification
        in {
            "IDENTITY_REQUIRED",
            "DERIVED_FROM_IDENTITY_FIELD",
            "PROVABLY_INACTIVE",
            "RUNTIME_ONLY",
            "RESULT_ONLY",
            "EXTERNAL_ALIAS",
        }
        for classification in classifications.values()
    )


def test_unknown_active_field_fail_closed() -> None:
    with pytest.raises(ExperimentIdentityManifestError, match="unknown active input field"):
        experiment_config_from_mapping(
            {
                "name": "x",
                "strategy_name": "ma_crossover",
                "unexpected_field": True,
            }
        )


def test_input_mutation_fail_closed(tmp_path: Path) -> None:
    config = _sample_config()
    with patch(
        "src.experiments.experiment_identity_manifest_v1._assert_config_unchanged",
        side_effect=ExperimentIdentityManifestError("mutated"),
    ):
        with pytest.raises(ExperimentIdentityManifestError, match="mutated"):
            produce_experiment_identity_manifest_v1(config, tmp_path / "out")


def test_atomic_write_and_cleanup(tmp_path: Path) -> None:
    config = _sample_config()
    out = tmp_path / "bundle"
    artifact = produce_experiment_identity_manifest_v1(config, out)
    assert artifact.exists()
    assert not any(p.name.startswith(".experiment_identity_staging_") for p in tmp_path.iterdir())


def test_existing_target_unchanged_on_error(tmp_path: Path) -> None:
    config = _sample_config()
    out = tmp_path / "bundle"
    produce_experiment_identity_manifest_v1(config, out)
    original = (out / ARTIFACT_FILENAME).read_text()
    with patch(
        "src.experiments.experiment_identity_manifest_v1.validate_experiment_identity_manifest_v1",
        side_effect=[None, ExperimentIdentityManifestError("verify failed")],
    ):
        with pytest.raises(ExperimentIdentityManifestError):
            produce_experiment_identity_manifest_v1(config, tmp_path / "bundle2")
    assert (out / ARTIFACT_FILENAME).read_text() == original


def test_completion_gate_self_verification() -> None:
    manifest = build_manifest(_sample_config())
    validate_experiment_identity_manifest_v1(manifest)


def test_integrity_block_recompute() -> None:
    manifest = build_manifest(_sample_config())
    integrity = manifest["integrity"]["content_sha256"]
    tampered = copy.deepcopy(manifest)
    tampered["integrity"] = {"content_sha256": "0" * 64}
    with pytest.raises(ExperimentIdentityManifestError, match="mismatch"):
        validate_experiment_identity_manifest_v1(tampered)
    assert len(integrity) == 64


def test_safety_block_canonical_refs() -> None:
    manifest = build_manifest(_sample_config())
    safety = manifest["safety"]
    assert safety["evidence_does_not_authorize_runtime"] is True
    assert safety["runtime_authority_impact"] == "NONE"
    assert safety["futures_scope_ref"]["scope"] == "FUTURES_ONLY"
    assert safety["trading_logic_immutability_ref"]["trading_logic_immutability"] is True


def test_no_config_mutation() -> None:
    config = _sample_config()
    before = config.to_dict()
    build_manifest(config)
    assert config.to_dict() == before


def test_no_experiment_execution(tmp_path: Path) -> None:
    with patch("src.experiments.base.ExperimentRunner.run") as run_mock:
        build_manifest(_sample_config())
        produce_experiment_identity_manifest_v1(_sample_config(), tmp_path / "out")
    run_mock.assert_not_called()


def test_fee_slippage_provably_inactive_classification() -> None:
    classifications = active_input_matrix_classifications()
    assert classifications["fee_bps_implicit"] == "PROVABLY_INACTIVE"
    assert classifications["slippage_bps_implicit"] == "PROVABLY_INACTIVE"


def test_duplicate_param_sweep_names_fail_closed() -> None:
    config = _sample_config(param_sweeps=[ParamSweep("fast", [1]), ParamSweep("fast", [2])])
    with pytest.raises(ExperimentIdentityManifestError, match="duplicate param_sweep"):
        build_identity_config(config)


def test_source_experiment_id_external_alias_only() -> None:
    manifest = build_manifest(_sample_config(), source_experiment_id="legacy-src-123")
    assert manifest["provenance"]["source_experiment_id"] == "legacy-src-123"
    assert manifest["experiment_identity_id"] != "legacy-src-123"


def test_provenance_null_by_default() -> None:
    manifest = build_manifest(_sample_config())
    assert manifest["provenance"]["source_experiment_id"] is None


def test_manifest_forbidden_keys_at_build_time() -> None:
    assert "run_id" in _FORBIDDEN_MANIFEST_KEYS
    assert "metrics" in _FORBIDDEN_MANIFEST_KEYS


def test_compute_legacy_experiment_id_md5_12_matches_get_experiment_id() -> None:
    config = _sample_config()
    assert compute_legacy_experiment_id_md5_12(config) == config.get_experiment_id()
