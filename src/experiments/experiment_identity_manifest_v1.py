"""Offline Package N — Experiment Identity Manifest Producer v1."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import uuid
from dataclasses import fields
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp
from src.experiments.base import ExperimentConfig, ParamSweep
from src.meta.learning_loop.contract_safety_v1 import (
    SCHEMA_VERSION_V1,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
    normalize_path_token,
    validate_futures_scope_ref,
    validate_integrity_block,
    validate_schema_version,
    validate_trading_logic_immutability_ref,
)

CONTRACT_VERSION = SCHEMA_VERSION_V1
IDENTITY_SCHEMA_VERSION = SCHEMA_VERSION_V1
IDENTITY_DOMAIN = "peak_trade.experiment_identity.v1"
ARTIFACT_FILENAME = "experiment_identity_manifest_v1.json"
STAGING_DIRNAME_PREFIX = ".experiment_identity_staging_"
RUNTIME_AUTHORITY_IMPACT = "NONE"

_REQUIRED_IDENTITY_FIELDS = (
    "name",
    "strategy_name",
    "param_sweeps",
    "symbols",
    "timeframe",
    "start_date",
    "end_date",
    "initial_capital",
    "base_params",
    "identity_schema_version",
    "identity_domain",
)

_FORBIDDEN_MANIFEST_KEYS = frozenset(
    {
        "run_id",
        "run_index",
        "metrics",
        "equity",
        "trades",
        "returns",
        "registry_run_id",
        "mlflow_run_id",
        "promotion",
        "promotion_authority",
        "apply_authority",
        "live_arming",
        "runtime_status",
        "orders",
        "positions",
        "credentials",
        "summary_stats",
        "result_payload",
    }
)

_ACTIVE_INPUT_FIELD_CLASSIFICATION: dict[str, str] = {
    "name": "IDENTITY_REQUIRED",
    "strategy_name": "IDENTITY_REQUIRED",
    "param_sweeps": "IDENTITY_REQUIRED",
    "symbols": "IDENTITY_REQUIRED",
    "timeframe": "IDENTITY_REQUIRED",
    "start_date": "IDENTITY_REQUIRED",
    "end_date": "IDENTITY_REQUIRED",
    "initial_capital": "IDENTITY_REQUIRED",
    "base_params": "IDENTITY_REQUIRED",
    "regime_config": "PROVABLY_INACTIVE",
    "switching_config": "PROVABLY_INACTIVE",
    "metrics_to_collect": "RUNTIME_ONLY",
    "parallel": "PROVABLY_INACTIVE",
    "max_workers": "RUNTIME_ONLY",
    "save_results": "RUNTIME_ONLY",
    "output_dir": "RUNTIME_ONLY",
    "tags": "RUNTIME_ONLY",
}

_IMPLICIT_ACTIVE_INPUT_CLASSIFICATION: dict[str, str] = {
    "fee_bps_implicit": "PROVABLY_INACTIVE",
    "slippage_bps_implicit": "PROVABLY_INACTIVE",
    "random_seed_implicit": "PROVABLY_INACTIVE",
    "data_limit_720": "PROVABLY_INACTIVE",
    "StrategySweepConfig.constraints": "PROVABLY_INACTIVE",
    "StrategySweepConfig.portfolio_config": "PROVABLY_INACTIVE",
    "get_experiment_id": "EXTERNAL_ALIAS",
    "source_experiment_id": "EXTERNAL_ALIAS",
    "identity_schema_version": "IDENTITY_REQUIRED",
    "identity_domain": "IDENTITY_REQUIRED",
}


class ExperimentIdentityManifestError(ValueError):
    """Fail-closed Package N experiment identity manifest error."""


def _is_regime_config_behaviorally_active(config: ExperimentConfig) -> bool:
    return False


def _is_switching_config_behaviorally_active(config: ExperimentConfig) -> bool:
    return False


def _is_phase41_constraint_bridge_active(config: ExperimentConfig) -> bool:
    return False


def _coerce_numpy_scalar(value: Any) -> tuple[Any, bool]:
    module_name = type(value).__module__
    if module_name == "numpy" and hasattr(value, "item"):
        return value.item(), True
    return value, False


def _canonicalize_scalar(value: Any, *, from_numpy: bool = False) -> Any:
    value, coerced_from_numpy = _coerce_numpy_scalar(value)
    from_numpy = from_numpy or coerced_from_numpy
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, float):
        if from_numpy:
            return float(f"{value:.8g}")
        return json.loads(json.dumps(value))
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        return value
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    raise ExperimentIdentityManifestError(
        f"unsupported scalar type for identity canonicalization: {type(value)!r}"
    )


def _canonicalize_value(
    value: Any, *, path_key: str | None = None, from_numpy: bool = False
) -> Any:
    coerced, was_numpy = _coerce_numpy_scalar(value)
    from_numpy = from_numpy or was_numpy
    value = coerced
    if isinstance(value, Mapping):
        return _canonicalize_mapping(value)
    if isinstance(value, list):
        return [_canonicalize_value(item, from_numpy=from_numpy) for item in value]
    if isinstance(value, tuple):
        return [_canonicalize_value(item, from_numpy=from_numpy) for item in value]
    if isinstance(value, set):
        return sorted(_canonicalize_value(item, from_numpy=from_numpy) for item in value)
    if path_key in {"path", "file", "filepath", "config_path"} and isinstance(value, str):
        return normalize_path_token(value)
    return _canonicalize_scalar(value, from_numpy=from_numpy)


def _canonicalize_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(key): _canonicalize_value(item, path_key=str(key))
        for key, item in sorted(payload.items(), key=lambda pair: str(pair[0]))
    }


def _canonicalize_param_sweeps(param_sweeps: list[ParamSweep]) -> list[dict[str, Any]]:
    if not param_sweeps:
        return []
    names = [sweep.name for sweep in param_sweeps]
    if len(names) != len(set(names)):
        raise ExperimentIdentityManifestError("duplicate param_sweep names are forbidden")
    sorted_sweeps = sorted(param_sweeps, key=lambda sweep: sweep.name)
    canonical: list[dict[str, Any]] = []
    for sweep in sorted_sweeps:
        canonical.append(
            {
                "name": sweep.name,
                "values": [_canonicalize_value(value) for value in sweep.values],
            }
        )
    return canonical


def _canonicalize_symbols(symbols: list[str]) -> list[str]:
    return sorted(symbols)


def build_identity_config(config: ExperimentConfig) -> dict[str, Any]:
    """Build ratified canonical identity projection from ExperimentConfig."""
    return {
        "name": config.name,
        "strategy_name": config.strategy_name,
        "param_sweeps": _canonicalize_param_sweeps(config.param_sweeps),
        "symbols": _canonicalize_symbols(config.symbols),
        "timeframe": config.timeframe,
        "start_date": config.start_date,
        "end_date": config.end_date,
        "initial_capital": _canonicalize_scalar(config.initial_capital),
        "base_params": _canonicalize_mapping(config.base_params),
        "identity_schema_version": IDENTITY_SCHEMA_VERSION,
        "identity_domain": IDENTITY_DOMAIN,
    }


def compute_experiment_identity_id(identity_config: Mapping[str, Any]) -> str:
    return compute_content_sha256(dict(identity_config))


def compute_legacy_experiment_id_md5_12(config: ExperimentConfig) -> str:
    config_str = json.dumps(
        {
            "name": config.name,
            "strategy": config.strategy_name,
            "sweeps": [sweep.to_dict() for sweep in config.param_sweeps],
            "symbols": config.symbols,
            "timeframe": config.timeframe,
        },
        sort_keys=True,
    )
    return hashlib.md5(config_str.encode()).hexdigest()[:12]


def _config_field_snapshot(config: ExperimentConfig) -> dict[str, Any]:
    return {
        field.name: copy.deepcopy(getattr(config, field.name)) for field in fields(ExperimentConfig)
    }


def _assert_config_unchanged(
    config: ExperimentConfig,
    snapshot: Mapping[str, Any],
) -> None:
    current = _config_field_snapshot(config)
    if current != dict(snapshot):
        raise ExperimentIdentityManifestError(
            "ExperimentConfig mutated during manifest production (fail-closed)"
        )


def validate_active_input_completeness(
    config: ExperimentConfig,
    *,
    extra_keys: tuple[str, ...] = (),
    regime_active_hook: Callable[[ExperimentConfig], bool] | None = None,
    switching_active_hook: Callable[[ExperimentConfig], bool] | None = None,
    phase41_active_hook: Callable[[ExperimentConfig], bool] | None = None,
) -> None:
    """Fail-closed active-input completeness and classification guard."""
    for key in extra_keys:
        if key not in _ACTIVE_INPUT_FIELD_CLASSIFICATION:
            raise ExperimentIdentityManifestError(
                f"unknown active input field in config payload: {key}"
            )

    for field in fields(ExperimentConfig):
        classification = _ACTIVE_INPUT_FIELD_CLASSIFICATION.get(field.name)
        if classification is None:
            raise ExperimentIdentityManifestError(
                f"unclassified active ExperimentConfig field: {field.name}"
            )

    if (regime_active_hook or _is_regime_config_behaviorally_active)(config):
        raise ExperimentIdentityManifestError(
            "regime_config is behaviorally active; identity production blocked (fail-closed)"
        )
    if (switching_active_hook or _is_switching_config_behaviorally_active)(config):
        raise ExperimentIdentityManifestError(
            "switching_config is behaviorally active; identity production blocked (fail-closed)"
        )
    if (phase41_active_hook or _is_phase41_constraint_bridge_active)(config):
        raise ExperimentIdentityManifestError(
            "Phase-41 constraints are not materialized in param_sweeps (fail-closed)"
        )


def active_input_matrix_classifications() -> dict[str, str]:
    merged = dict(_IMPLICIT_ACTIVE_INPUT_CLASSIFICATION)
    merged.update(_ACTIVE_INPUT_FIELD_CLASSIFICATION)
    return merged


def unclassified_active_input_count() -> int:
    known = set(active_input_matrix_classifications())
    config_fields = {field.name for field in fields(ExperimentConfig)}
    unclassified = config_fields - set(_ACTIVE_INPUT_FIELD_CLASSIFICATION)
    return len(unclassified)


def _reject_forbidden_manifest_keys(payload: Mapping[str, Any], *, prefix: str = "") -> None:
    for key, value in payload.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if key in _FORBIDDEN_MANIFEST_KEYS:
            raise ExperimentIdentityManifestError(
                f"manifest must not contain forbidden key: {full_key}"
            )
        if isinstance(value, Mapping):
            _reject_forbidden_manifest_keys(value, prefix=full_key)


def _manifest_without_integrity(manifest: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(manifest)
    payload.pop("integrity", None)
    return payload


def build_manifest(
    config: ExperimentConfig,
    *,
    source_experiment_id: str | None = None,
) -> dict[str, Any]:
    validate_active_input_completeness(config)
    identity_config = build_identity_config(config)
    experiment_identity_id = compute_experiment_identity_id(identity_config)
    manifest: dict[str, Any] = {
        "schema_version": CONTRACT_VERSION,
        "contract_version": CONTRACT_VERSION,
        "identity_domain": IDENTITY_DOMAIN,
        "experiment_identity_id": experiment_identity_id,
        "identity_config": identity_config,
        "legacy_aliases": {
            "legacy_experiment_id_md5_12": compute_legacy_experiment_id_md5_12(config),
        },
        "provenance": {
            "source_experiment_id": source_experiment_id,
        },
        "safety": {
            "evidence_does_not_authorize_runtime": True,
            "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
            "futures_scope_ref": canonical_futures_scope_ref(),
            "trading_logic_immutability_ref": canonical_trading_logic_immutability_ref(),
        },
    }
    _reject_forbidden_manifest_keys(manifest)
    digest = compute_content_sha256(_manifest_without_integrity(manifest))
    manifest["integrity"] = {"content_sha256": digest}
    return manifest


def validate_experiment_identity_manifest_v1(manifest: Mapping[str, Any]) -> None:
    if not isinstance(manifest, Mapping):
        raise ExperimentIdentityManifestError("manifest root must be an object")

    schema_result = validate_schema_version(manifest.get("schema_version"))
    if not schema_result.valid:
        raise ExperimentIdentityManifestError(schema_result.errors[0])
    if manifest.get("contract_version") != CONTRACT_VERSION:
        raise ExperimentIdentityManifestError("contract_version must equal 1.0")

    identity_config = manifest.get("identity_config")
    if not isinstance(identity_config, Mapping):
        raise ExperimentIdentityManifestError("identity_config must be an object")
    for key in _REQUIRED_IDENTITY_FIELDS:
        if key not in identity_config:
            raise ExperimentIdentityManifestError(f"identity_config missing required field: {key}")

    experiment_identity_id = manifest.get("experiment_identity_id")
    if not isinstance(experiment_identity_id, str) or not is_valid_sha256_hex(
        experiment_identity_id
    ):
        raise ExperimentIdentityManifestError(
            "experiment_identity_id must be 64-char lowercase sha256 hex"
        )
    expected_identity_id = compute_experiment_identity_id(identity_config)
    if experiment_identity_id != expected_identity_id:
        raise ExperimentIdentityManifestError("experiment_identity_id mismatch")

    legacy_aliases = manifest.get("legacy_aliases")
    if not isinstance(legacy_aliases, Mapping):
        raise ExperimentIdentityManifestError("legacy_aliases must be an object")
    legacy_id = legacy_aliases.get("legacy_experiment_id_md5_12")
    if not isinstance(legacy_id, str) or len(legacy_id) != 12:
        raise ExperimentIdentityManifestError(
            "legacy_aliases.legacy_experiment_id_md5_12 must be 12 hex chars"
        )

    provenance = manifest.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ExperimentIdentityManifestError("provenance must be an object")
    source_id = provenance.get("source_experiment_id")
    if source_id is not None and not isinstance(source_id, str):
        raise ExperimentIdentityManifestError(
            "provenance.source_experiment_id must be string or null"
        )

    safety = manifest.get("safety")
    if not isinstance(safety, Mapping):
        raise ExperimentIdentityManifestError("safety must be an object")
    if safety.get("evidence_does_not_authorize_runtime") is not True:
        raise ExperimentIdentityManifestError(
            "safety.evidence_does_not_authorize_runtime must be true"
        )
    if safety.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise ExperimentIdentityManifestError("safety.runtime_authority_impact must be NONE")

    futures_result = validate_futures_scope_ref(safety.get("futures_scope_ref"))
    if not futures_result.valid:
        raise ExperimentIdentityManifestError(futures_result.errors[0])
    immutability_result = validate_trading_logic_immutability_ref(
        safety.get("trading_logic_immutability_ref")
    )
    if not immutability_result.valid:
        raise ExperimentIdentityManifestError(immutability_result.errors[0])

    _reject_forbidden_manifest_keys(manifest)

    expected_digest = compute_content_sha256(_manifest_without_integrity(manifest))
    integrity_result = validate_integrity_block(
        manifest.get("integrity"), expected_digest=expected_digest
    )
    if not integrity_result.valid:
        raise ExperimentIdentityManifestError(integrity_result.errors[0])


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ExperimentIdentityManifestError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ExperimentIdentityManifestError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ExperimentIdentityManifestError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise ExperimentIdentityManifestError("output parent directory must be outside /tmp")


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def produce_experiment_identity_manifest_v1(
    config: ExperimentConfig,
    output_dir: Path | str,
    *,
    source_experiment_id: str | None = None,
) -> Path:
    """Atomically produce experiment_identity_manifest_v1.json under output_dir."""
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)

    snapshot = _config_field_snapshot(config)
    manifest = build_manifest(config, source_experiment_id=source_experiment_id)
    validate_experiment_identity_manifest_v1(manifest)
    _assert_config_unchanged(config, snapshot)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ExperimentIdentityManifestError(f"staging directory collision: {staging}")

    artifact_path = staging / ARTIFACT_FILENAME
    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path.write_text(
            deterministic_json_dumps(manifest) + "\n",
            encoding="utf-8",
        )

        written = json.loads(artifact_path.read_text(encoding="utf-8"))
        validate_experiment_identity_manifest_v1(written)
        _assert_config_unchanged(config, snapshot)

        staging.replace(final_dir)

        final_artifact = final_dir / ARTIFACT_FILENAME
        final_payload = json.loads(final_artifact.read_text(encoding="utf-8"))
        validate_experiment_identity_manifest_v1(final_payload)
        _assert_config_unchanged(config, snapshot)
        return final_artifact
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise


def experiment_config_from_mapping(data: Mapping[str, Any]) -> ExperimentConfig:
    if not isinstance(data, Mapping):
        raise ExperimentIdentityManifestError("config payload must be a JSON object")

    extra_keys = tuple(
        key for key in data if key not in {field.name for field in fields(ExperimentConfig)}
    )
    if extra_keys:
        raise ExperimentIdentityManifestError(
            f"unknown active input field in config payload: {extra_keys[0]}"
        )

    required = ("name", "strategy_name")
    for key in required:
        if key not in data:
            raise ExperimentIdentityManifestError(f"config missing required field: {key}")

    raw_sweeps = data.get("param_sweeps", [])
    if not isinstance(raw_sweeps, list):
        raise ExperimentIdentityManifestError("param_sweeps must be a list")
    param_sweeps: list[ParamSweep] = []
    for item in raw_sweeps:
        if not isinstance(item, Mapping):
            raise ExperimentIdentityManifestError("param_sweeps entries must be objects")
        param_sweeps.append(
            ParamSweep(
                name=str(item["name"]),
                values=list(item["values"]),
                description=item.get("description"),
            )
        )

    return ExperimentConfig(
        name=str(data["name"]),
        strategy_name=str(data["strategy_name"]),
        param_sweeps=param_sweeps,
        symbols=list(data.get("symbols", ["BTC/EUR"])),
        timeframe=str(data.get("timeframe", "1h")),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        initial_capital=float(data.get("initial_capital", 10000.0)),
        regime_config=data.get("regime_config"),
        switching_config=data.get("switching_config"),
        base_params=dict(data.get("base_params", {})),
        metrics_to_collect=list(
            data.get(
                "metrics_to_collect",
                [
                    "total_return",
                    "sharpe_ratio",
                    "max_drawdown",
                    "win_rate",
                    "num_trades",
                    "profit_factor",
                    "ulcer_index",
                    "recovery_factor",
                ],
            )
        ),
        parallel=bool(data.get("parallel", False)),
        max_workers=int(data.get("max_workers", 4)),
        save_results=bool(data.get("save_results", True)),
        output_dir=str(data.get("output_dir", "reports/experiments")),
        tags=list(data.get("tags", [])),
    )


__all__ = [
    "ARTIFACT_FILENAME",
    "CONTRACT_VERSION",
    "ExperimentIdentityManifestError",
    "IDENTITY_DOMAIN",
    "IDENTITY_SCHEMA_VERSION",
    "RUNTIME_AUTHORITY_IMPACT",
    "active_input_matrix_classifications",
    "build_identity_config",
    "build_manifest",
    "compute_experiment_identity_id",
    "compute_legacy_experiment_id_md5_12",
    "experiment_config_from_mapping",
    "produce_experiment_identity_manifest_v1",
    "unclassified_active_input_count",
    "validate_active_input_completeness",
    "validate_experiment_identity_manifest_v1",
]
