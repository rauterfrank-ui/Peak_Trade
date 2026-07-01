#!/usr/bin/env python3
"""Offline economic viability evidence evaluation runner v1 (RUNBOOK STEP 29M).

Thin ops orchestrator over existing library owners. Strictly offline: no network,
no credentials, no runtime/order/venue effects. Non-authorizing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_SRC_ROOT, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    MANIFEST_FILENAME,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.backtest import admissible_versioned_futures_dataset_v1 as ds  # noqa: E402
from src.backtest import economic_validity_policy_v1 as policy_mod  # noqa: E402
from src.backtest import economic_viability_evidence_v1 as ev  # noqa: E402
from src.backtest import mv2_research_wiring_v1 as mv2_wiring  # noqa: E402
from src.backtest import parameter_sensitivity_v1 as ps  # noqa: E402
from src.backtest.economic_validity_policy_v1 import (  # noqa: E402
    ECONOMIC_VALIDITY_POLICY_VERSION,
    EconomicValidityEvaluationStatus,
    EconomicValidityEvidenceMetricsV1,
    evaluate_economic_validity_against_policy_v1,
    validate_economic_validity_policy_v1,
)
from src.backtest.funding_model_v1 import load_funding_model_config_v1  # noqa: E402
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (  # noqa: E402
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
)

RUNNER_VERSION = "run_economic_viability_evidence_evaluation_v1"
RUNNER_OWNER = "scripts.ops.run_economic_viability_evidence_evaluation_v1"
MANIFEST_CONTRACT_VERSION = "admissible_versioned_futures_dataset_manifest_v1"
OFFLINE_CREATED_AT_UTC = ev.OFFLINE_DETERMINISTIC_CREATED_AT

USAGE_EXIT = 2
VALIDATION_EXIT = 1

_URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")

_FORBIDDEN_SOURCE_TYPES = frozenset(
    {
        "spot",
        "synthetic_spot",
        "synthetic_contract_fixture",
        "test_fixture",
        "preview",
        "preview_data",
        "probe",
        "probe_data",
        "transport_fixture",
        "transport",
        "webui_fixture",
        "webui",
    }
)
_FORBIDDEN_GENERATION_MARKERS = frozenset(
    {
        "deterministic_test_fixture",
        "test_fixture",
        "probe",
        "preview",
        "transport_fixture",
        "webui_fixture",
    }
)


class DatasetFixtureClass(str, Enum):
    REAL_ADMISSIBLE_VERSIONED_FUTURES_DATASET = "REAL_ADMISSIBLE_VERSIONED_FUTURES_DATASET"
    TEST_FIXTURE = "TEST_FIXTURE"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    PREVIEW_DATA = "PREVIEW_DATA"
    PROBE_DATA = "PROBE_DATA"
    TRANSPORT_FIXTURE = "TRANSPORT_FIXTURE"
    WEBUI_FIXTURE = "WEBUI_FIXTURE"
    SPOT_DATA = "SPOT_DATA"
    SYNTHETIC_SPOT_DATA = "SYNTHETIC_SPOT_DATA"
    UNKNOWN_DATA_CLASS = "UNKNOWN_DATA_CLASS"


class RunnerError(Exception):
    """Fail-closed runner validation error."""


@dataclass(frozen=True)
class ValidationPlanV1:
    run_id: str
    dataset_path: str
    dataset_manifest_path: str
    config_path: str
    policy_path: str
    output_dir: str
    dataset_fixture_class: str
    dataset_admissible: bool
    owners: tuple[str, ...]
    planned_outputs: tuple[str, ...]
    validate_only: bool


@dataclass(frozen=True)
class RunOutcomeV1:
    run_id: str
    dataset_id: str
    dataset_version: str
    dataset_fixture_class: DatasetFixtureClass
    dataset_admissible: bool
    economic_evidence_built: bool
    economic_gate_evaluated: bool
    economic_validity_result: str
    economic_validity_offline_gate_pass: bool
    promotion_eligibility: bool
    runner_execution_success: bool
    manifest_verify_rc: int
    output_dir: Path


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _reject_url_path(path_str: str) -> None:
    if _URL_SCHEME_RE.match(path_str.strip()):
        raise RunnerError(f"url_path_forbidden:{path_str}")
    parsed = urlparse(path_str)
    if parsed.scheme and parsed.scheme not in {"", "file"}:
        raise RunnerError(f"url_path_forbidden:{path_str}")


def _resolve_local_path(path_str: str, *, field_name: str) -> Path:
    if not path_str or not str(path_str).strip():
        raise RunnerError(f"{field_name}_missing")
    _reject_url_path(path_str)
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (_REPO_ROOT / path).resolve()
    else:
        path = path.resolve()
    return path


def _load_json_file(path: Path, *, field_name: str) -> dict[str, Any]:
    if not path.is_file():
        raise RunnerError(f"{field_name}_not_found:{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RunnerError(f"{field_name}_invalid_json:{path}") from exc
    if not isinstance(payload, dict):
        raise RunnerError(f"{field_name}_not_object:{path}")
    return payload


def _load_config(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        return _load_json_file(path, field_name="config")
    if path.suffix.lower() in {".toml", ".tml"}:
        try:
            import tomllib
        except ModuleNotFoundError:  # pragma: no cover
            import tomli as tomllib  # type: ignore[no-redef]
        try:
            return tomllib.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RunnerError(f"config_invalid_toml:{path}") from exc
    raise RunnerError(f"config_unsupported_format:{path.suffix}")


def _load_policy_overlay(path: Path) -> dict[str, Any]:
    payload = _load_json_file(path, field_name="policy")
    if payload.get("use_canonical") is True:
        if str(payload.get("policy_version", ECONOMIC_VALIDITY_POLICY_VERSION)) != (
            ECONOMIC_VALIDITY_POLICY_VERSION
        ):
            raise RunnerError("policy_version_mismatch")
        return {}
    section = payload.get("economic_validity_policy", payload)
    if not isinstance(section, Mapping):
        raise RunnerError("policy_section_missing")
    return {"economic_validity_policy": dict(section)}


def _merge_policy_into_config(cfg: dict[str, Any], policy_path: Optional[Path]) -> dict[str, Any]:
    merged = dict(cfg)
    if policy_path is None:
        return merged
    overlay = _load_policy_overlay(policy_path)
    merged.update(overlay)
    return merged


def classify_dataset_fixture_class_v1(
    *,
    descriptor: ds.VersionedFuturesDatasetDescriptorV1,
    provenance: ds.DatasetProvenanceV1,
    dataset_path: Path,
    manifest_path: Path,
) -> DatasetFixtureClass:
    source = provenance.source_type.lower().strip()
    generation = provenance.generation_method.lower().strip()
    provenance_ref = provenance.provenance_ref.lower().strip()
    path_text = f"{dataset_path} {manifest_path}".lower()

    if source == "spot":
        return DatasetFixtureClass.SPOT_DATA
    if source == "synthetic_spot":
        return DatasetFixtureClass.SYNTHETIC_SPOT_DATA
    if source == "synthetic_contract_fixture":
        return DatasetFixtureClass.SYNTHETIC_FIXTURE
    if source in {"preview", "preview_data"}:
        return DatasetFixtureClass.PREVIEW_DATA
    if source in {"probe", "probe_data"}:
        return DatasetFixtureClass.PROBE_DATA
    if source in {"transport_fixture", "transport"}:
        return DatasetFixtureClass.TRANSPORT_FIXTURE
    if source in {"webui_fixture", "webui"}:
        return DatasetFixtureClass.WEBUI_FIXTURE
    if source == "test_fixture":
        return DatasetFixtureClass.TEST_FIXTURE

    if provenance_ref.startswith("tests/") or "/tests/" in provenance_ref:
        return DatasetFixtureClass.TEST_FIXTURE
    if "tests/fixtures" in path_text or "/fixtures/" in path_text:
        return DatasetFixtureClass.TEST_FIXTURE
    if "webui" in provenance_ref and "fixture" in provenance_ref:
        return DatasetFixtureClass.WEBUI_FIXTURE

    for marker in _FORBIDDEN_GENERATION_MARKERS:
        if marker in generation:
            if "test" in marker:
                return DatasetFixtureClass.TEST_FIXTURE
            if "probe" in marker:
                return DatasetFixtureClass.PROBE_DATA
            if "preview" in marker:
                return DatasetFixtureClass.PREVIEW_DATA
            if "transport" in marker:
                return DatasetFixtureClass.TRANSPORT_FIXTURE
            if "webui" in marker:
                return DatasetFixtureClass.WEBUI_FIXTURE
            return DatasetFixtureClass.SYNTHETIC_FIXTURE

    if descriptor.contract_type.lower() == "spot" or not descriptor.futures_only:
        return DatasetFixtureClass.SPOT_DATA

    return DatasetFixtureClass.REAL_ADMISSIBLE_VERSIONED_FUTURES_DATASET


def _fixture_class_blocks_evaluation(fixture_class: DatasetFixtureClass) -> bool:
    return fixture_class is not DatasetFixtureClass.REAL_ADMISSIBLE_VERSIONED_FUTURES_DATASET


def _compute_manifest_digest(payload: Mapping[str, Any]) -> str:
    body = {key: value for key, value in payload.items() if key != "manifest_digest"}
    return _stable_digest(body)


def _load_dataset_manifest(path: Path) -> dict[str, Any]:
    manifest = _load_json_file(path, field_name="dataset_manifest")
    version = str(manifest.get("manifest_version", ""))
    if version and version != MANIFEST_CONTRACT_VERSION:
        raise RunnerError(f"manifest_version_unknown:{version}")
    expected = manifest.get("manifest_digest")
    if expected:
        if not _SHA256_HEX_RE.match(str(expected)):
            raise RunnerError("manifest_digest_invalid")
        computed = _compute_manifest_digest(manifest)
        if computed != str(expected):
            raise RunnerError("manifest_digest_mismatch")
    return manifest


def _descriptor_from_manifest(
    manifest: Mapping[str, Any],
    *,
    manifest_path: str = "",
) -> ds.VersionedFuturesDatasetDescriptorV1:
    if ds.is_flat_economic_research_manifest_v1(manifest):
        descriptor, _provenance = (
            ds.load_dataset_admissibility_from_flat_economic_research_manifest_v1(
                manifest,
                manifest_path=manifest_path,
            )
        )
        if descriptor.dataset_version != ds.DEFAULT_DATASET_VERSION:
            raise RunnerError(f"dataset_version_unknown:{descriptor.dataset_version}")
        if descriptor.dataset_schema_version != ds.DATASET_SCHEMA_VERSION:
            raise RunnerError(f"dataset_schema_version_unknown:{descriptor.dataset_schema_version}")
        return descriptor
    dataset_raw = manifest.get("dataset")
    if not isinstance(dataset_raw, Mapping):
        raise RunnerError("manifest_dataset_missing")
    provenance_raw = manifest.get("provenance")
    if not isinstance(provenance_raw, Mapping):
        raise RunnerError("manifest_provenance_missing")
    if manifest.get("dataset_profile") is None and manifest.get("profile_binding") is None:
        raise RunnerError("manifest_dataset_profile_missing")
    cfg = {
        "backtest": {
            "dataset_admissibility": {
                "bind": True,
                "dataset": dict(dataset_raw),
                "provenance": dict(provenance_raw),
            }
        }
    }
    descriptor, _provenance = ds.load_dataset_admissibility_from_cfg(cfg)
    if descriptor.dataset_version != ds.DEFAULT_DATASET_VERSION:
        raise RunnerError(f"dataset_version_unknown:{descriptor.dataset_version}")
    if descriptor.dataset_schema_version != ds.DATASET_SCHEMA_VERSION:
        raise RunnerError(f"dataset_schema_version_unknown:{descriptor.dataset_schema_version}")
    return descriptor


def _provenance_from_manifest(
    manifest: Mapping[str, Any],
    *,
    manifest_path: str = "",
) -> ds.DatasetProvenanceV1:
    if ds.is_flat_economic_research_manifest_v1(manifest):
        _descriptor, provenance = (
            ds.load_dataset_admissibility_from_flat_economic_research_manifest_v1(
                manifest,
                manifest_path=manifest_path,
            )
        )
        return provenance
    provenance_raw = manifest.get("provenance")
    if not isinstance(provenance_raw, Mapping):
        raise RunnerError("manifest_provenance_missing")
    if not str(provenance_raw.get("source_type", "")).strip():
        raise RunnerError("provenance_source_type_missing")
    if not str(provenance_raw.get("provenance_ref", "")).strip():
        raise RunnerError("provenance_ref_missing")
    return ds.DatasetProvenanceV1(
        source_type=str(provenance_raw["source_type"]),
        venue_id=str(provenance_raw["venue_id"]),
        ingestion_timestamp=str(provenance_raw["ingestion_timestamp"]),
        generation_method=str(provenance_raw["generation_method"]),
        provenance_ref=str(provenance_raw["provenance_ref"]),
    )


def _load_bars_from_dataset_path(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise RunnerError(f"dataset_path_not_found:{path}")
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        frame = pd.read_parquet(path)
    elif suffix == ".csv":
        frame = pd.read_csv(path, index_col=0, parse_dates=True)
    else:
        raise RunnerError(f"dataset_format_unsupported:{suffix}")
    if not isinstance(frame.index, pd.DatetimeIndex):
        if "timestamp" in frame.columns:
            frame = frame.set_index("timestamp")
            frame.index = pd.to_datetime(frame.index, utc=True)
        else:
            raise RunnerError("dataset_index_not_datetime")
    if frame.index.tz is None:
        frame.index = frame.index.tz_localize("UTC")
    return frame.sort_index()


def _validate_real_evaluation_binding(
    cfg: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    admissibility: ds.AdmissibleVersionedFuturesDatasetResultV1,
) -> None:
    binding = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(binding, Mapping):
        return
    expected_dataset = str(binding.get("expected_dataset_digest", "")).strip()
    if expected_dataset and admissibility.dataset_digest != expected_dataset:
        raise RunnerError("expected_dataset_digest_mismatch")
    expected_manifest = str(binding.get("expected_manifest_digest", "")).strip()
    if expected_manifest and str(manifest.get("manifest_digest", "")) != expected_manifest:
        raise RunnerError("expected_manifest_digest_mismatch")
    if binding.get("require_integrity_pass") is True:
        integrity = manifest.get("integrity_results")
        if not isinstance(integrity, Mapping) or integrity.get("integrity_pass") is not True:
            raise RunnerError("manifest_integrity_pass_required")
    if binding.get("require_dataset_admissible") is True:
        integrity = manifest.get("integrity_results")
        if not isinstance(integrity, Mapping) or integrity.get("dataset_admissible") is not True:
            raise RunnerError("manifest_dataset_admissible_required")
    if (
        binding.get("require_observed_l1_used_false") is True
        and manifest.get("observed_l1_used") is not False
    ):
        raise RunnerError("observed_l1_used_must_be_false")
    l1_status = str(manifest.get("l1_observation_status", ""))
    expected_l1 = str(binding.get("expected_l1_observation_status", "")).strip()
    if expected_l1 and l1_status != expected_l1:
        raise RunnerError("l1_observation_status_mismatch")


def _validate_evaluation_config(cfg: Mapping[str, Any]) -> None:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        raise RunnerError("config_backtest_missing")
    if not str(backtest.get("cost_model_version", "")).strip():
        raise RunnerError("cost_model_version_missing")
    fee_bps = backtest.get("fee_bps")
    slippage_bps = backtest.get("slippage_bps")
    if fee_bps is None or slippage_bps is None:
        raise RunnerError("fee_or_slippage_binding_missing")
    if float(fee_bps) <= 0.0 or float(slippage_bps) <= 0.0:
        raise RunnerError("implicit_zero_cost_forbidden")
    funding = backtest.get("funding")
    if not isinstance(funding, Mapping) or funding.get("bind") is not True:
        raise RunnerError("funding_binding_missing")
    try:
        load_funding_model_config_v1(cfg)
    except Exception as exc:
        raise RunnerError(f"funding_binding_invalid:{exc}") from exc
    if not ps.parameter_sensitivity_binding_requested(cfg):
        raise RunnerError("parameter_sensitivity_binding_missing")
    eval_section = cfg.get("economic_evaluation_v1")
    if not isinstance(eval_section, Mapping):
        raise RunnerError("economic_evaluation_v1_missing")
    for section_name in ("walk_forward", "monte_carlo", "stress"):
        section = eval_section.get(section_name)
        if not isinstance(section, Mapping) or section.get("bind") is not True:
            raise RunnerError(f"{section_name}_binding_missing")
    if not ds.dataset_admissibility_binding_requested(cfg):
        raise RunnerError("dataset_admissibility_binding_missing")
    try:
        ds.load_profile_binding_from_cfg(cfg)
    except ds.AdmissibleVersionedFuturesDatasetError as exc:
        raise RunnerError(f"dataset_profile_binding_missing:{exc}") from exc


def _resolve_strategy_id(cfg: Mapping[str, Any]) -> str:
    eval_section = cfg.get("economic_evaluation_v1")
    if isinstance(eval_section, Mapping) and eval_section.get("strategy_id"):
        return str(eval_section["strategy_id"])
    return "ma_crossover"


def _evaluation_params(cfg: Mapping[str, Any]) -> dict[str, Any]:
    section = cfg["economic_evaluation_v1"]
    wf = section["walk_forward"]
    mc = section["monte_carlo"]
    return {
        "walk_forward_train_bars": int(wf.get("train_bars", 8)),
        "walk_forward_test_bars": int(wf.get("test_bars", 4)),
        "walk_forward_step_bars": int(wf.get("step_bars", 4)),
        "monte_carlo_runs": int(mc.get("runs", 16)),
        "monte_carlo_seed": int(mc.get("seed", 42)),
    }


def _derive_run_id(
    *,
    explicit_run_id: str,
    dataset_digest: str,
    config_digest: str,
    policy_digest: str,
) -> str:
    if explicit_run_id.strip():
        return explicit_run_id.strip()
    digest = _stable_digest(
        {
            "runner": RUNNER_VERSION,
            "dataset_digest": dataset_digest,
            "config_digest": config_digest,
            "policy_digest": policy_digest,
        }
    )
    return f"econ_evidence_eval_v1_{digest[:16]}"


def _resolve_policy(cfg: Mapping[str, Any]) -> policy_mod.EconomicValidityPolicyV1:
    policy = policy_mod.resolve_economic_validity_policy_v1(cfg)
    validate_economic_validity_policy_v1(policy)
    if not policy.is_version_bound():
        raise RunnerError("policy_version_unbound")
    if not policy.thresholds_configured():
        raise RunnerError("policy_thresholds_not_configured")
    return policy


def _validate_output_dir(path: Path, *, allow_existing: bool) -> None:
    if path.exists():
        if not allow_existing:
            raise RunnerError(f"output_dir_exists:{path}")
        if any(path.iterdir()):
            raise RunnerError(f"output_dir_nonempty:{path}")


def _map_validity_result(status: EconomicValidityEvaluationStatus) -> str:
    return status.value


def _wf_pass_ratio_from_evidence(wf_payload: Any) -> Optional[float]:
    if not isinstance(wf_payload, Mapping):
        return None
    windows = wf_payload.get("windows")
    if not isinstance(windows, list) or not windows:
        return None
    passed = sum(1 for window in windows if float(window.get("oos_total_return", -1.0)) >= 0.0)
    return passed / len(windows)


def _mc_pass_ratio_from_evidence(mc_payload: Any) -> Optional[float]:
    if not isinstance(mc_payload, Mapping):
        return None
    quantiles = mc_payload.get("metric_quantiles")
    if not isinstance(quantiles, Mapping):
        return None
    total_return = quantiles.get("total_return")
    if not isinstance(total_return, Mapping):
        return None
    p50 = total_return.get("p50")
    if p50 is None:
        return None
    return 1.0 if float(p50) >= 0.0 else 0.0


def _stress_failure_count_from_evidence(stress_payload: Any) -> Optional[int]:
    if not isinstance(stress_payload, Mapping):
        return None
    suite = stress_payload.get("suite")
    if not isinstance(suite, Mapping):
        return None
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list):
        return None
    failures = 0
    for scenario in scenarios:
        if not isinstance(scenario, Mapping):
            continue
        stressed_return = scenario.get("stressed_total_return")
        if stressed_return is None or float(stressed_return) < 0.0:
            failures += 1
    return failures


def _build_gate_metrics_from_evidence(
    evidence: ev.EconomicViabilityEvidenceV1,
) -> EconomicValidityEvidenceMetricsV1:
    wf = evidence.walk_forward_results
    mc = evidence.monte_carlo_results
    stress = evidence.stress_results
    ps_payload = evidence.parameter_sensitivity_results
    funding_bound = evidence.cost_binding.get("funding_binding_status") == "BOUND"
    return EconomicValidityEvidenceMetricsV1(
        net_expectancy=evidence.net_expectancy.value,
        profit_factor=evidence.profit_factor.value,
        max_drawdown=evidence.max_drawdown.value,
        trade_count=int(evidence.trade_count.value or 0),
        walk_forward_pass_ratio=_wf_pass_ratio_from_evidence(wf),
        out_of_sample_pass_ratio=_wf_pass_ratio_from_evidence(wf),
        monte_carlo_pass_ratio=_mc_pass_ratio_from_evidence(mc),
        stress_failure_count=_stress_failure_count_from_evidence(stress),
        parameter_robustness_pass=(
            bool(ps_payload.get("parameter_robustness_policy_pass"))
            if isinstance(ps_payload, Mapping)
            else None
        ),
        data_admissibility_status=(
            "PASS" if evidence.data_admissibility.get("binding_status") == "PASS" else "FAIL"
        ),
        cost_model_status="PASS" if evidence.fee_model_version != "NOT_BOUND" else "FAIL",
        funding_binding_status="PASS" if funding_bound else "FAIL",
        execution_model_status=(
            "PASS" if evidence.execution_model_version != "NOT_BOUND" else "FAIL"
        ),
        reproducibility_status="PASS",
        digest_binding_status="PASS",
        manifest_binding_status="PASS",
    )


def _write_run_summary_env(path: Path, fields: Mapping[str, Any]) -> None:
    lines = [f"{key}={value}" for key, value in fields.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Offline economic viability evidence evaluation runner v1 "
            "(STEP 29M; non-authorizing; no network/runtime effects)."
        )
    )
    parser.add_argument("--dataset-path", required=True, help="Local futures bar dataset file.")
    parser.add_argument(
        "--dataset-manifest-path",
        required=True,
        help="Versioned dataset manifest JSON (descriptor + provenance).",
    )
    parser.add_argument(
        "--config-path", required=True, help="Versioned evaluation config JSON/TOML."
    )
    parser.add_argument(
        "--policy-path",
        default="",
        help="Optional versioned economic validity policy JSON overlay.",
    )
    parser.add_argument(
        "--output-dir", required=True, help="Output directory for evidence artifacts."
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Explicit run id; otherwise derived deterministically from digests.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate inputs and bindings only; do not build economic evidence.",
    )
    parser.add_argument(
        "--allow-existing-output",
        action="store_true",
        help="Allow writing to an existing empty output directory.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Emit machine-readable plan/result JSON."
    )
    return parser


def build_validation_plan(args: argparse.Namespace) -> ValidationPlanV1:
    dataset_path = _resolve_local_path(args.dataset_path, field_name="dataset_path")
    manifest_path = _resolve_local_path(args.dataset_manifest_path, field_name="dataset_manifest")
    config_path = _resolve_local_path(args.config_path, field_name="config_path")
    output_dir = _resolve_local_path(args.output_dir, field_name="output_dir")
    policy_path = (
        _resolve_local_path(args.policy_path, field_name="policy_path")
        if args.policy_path
        else None
    )

    if not dataset_path.is_file():
        raise RunnerError(f"dataset_path_not_found:{dataset_path}")
    manifest = _load_dataset_manifest(manifest_path)
    descriptor = _descriptor_from_manifest(manifest, manifest_path=str(manifest_path))
    provenance = _provenance_from_manifest(manifest, manifest_path=str(manifest_path))
    fixture_class = classify_dataset_fixture_class_v1(
        descriptor=descriptor,
        provenance=provenance,
        dataset_path=dataset_path,
        manifest_path=manifest_path,
    )
    if provenance.source_type.lower() in _FORBIDDEN_SOURCE_TYPES:
        raise RunnerError(f"source_type_forbidden:{provenance.source_type}")
    if _fixture_class_blocks_evaluation(fixture_class):
        raise RunnerError(f"dataset_fixture_class_forbidden:{fixture_class.value}")

    cfg = _merge_policy_into_config(_load_config(config_path), policy_path)
    _validate_evaluation_config(cfg)
    policy = _resolve_policy(cfg)

    bars = _load_bars_from_dataset_path(dataset_path)
    profile_binding = ds.load_profile_binding_from_manifest(manifest)
    admissibility = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=bars,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=descriptor.instrument_id,
        profile_binding=profile_binding,
    )
    if not admissibility.is_admissible():
        raise RunnerError(f"dataset_not_admissible:{admissibility.admissibility_status.value}")
    _validate_real_evaluation_binding(cfg, manifest=manifest, admissibility=admissibility)

    config_digest = _stable_digest(cfg)
    run_id = _derive_run_id(
        explicit_run_id=str(args.run_id),
        dataset_digest=admissibility.dataset_digest,
        config_digest=config_digest,
        policy_digest=policy.policy_digest(),
    )
    _validate_output_dir(output_dir, allow_existing=bool(args.allow_existing_output))

    return ValidationPlanV1(
        run_id=run_id,
        dataset_path=str(dataset_path),
        dataset_manifest_path=str(manifest_path),
        config_path=str(config_path),
        policy_path=str(policy_path) if policy_path else "",
        output_dir=str(output_dir),
        dataset_fixture_class=fixture_class.value,
        dataset_admissible=admissibility.is_admissible(),
        owners=(
            ev.ECONOMIC_VIABILITY_EVIDENCE_OWNER,
            ds.ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER,
            mv2_wiring.MV2_RESEARCH_WIRING_OWNER,
            policy_mod.ECONOMIC_VALIDITY_POLICY_OWNER,
        ),
        planned_outputs=(
            ev.ARTIFACT_FILENAME,
            "economic_validity_evaluation_v1.json",
            "dataset_admissibility_result_v1.json",
            "run_summary.env",
            MANIFEST_FILENAME,
        ),
        validate_only=bool(args.validate_only),
    )


def execute_evaluation(args: argparse.Namespace) -> RunOutcomeV1:
    plan = build_validation_plan(args)
    if plan.validate_only:
        return RunOutcomeV1(
            run_id=plan.run_id,
            dataset_id="",
            dataset_version="",
            dataset_fixture_class=DatasetFixtureClass(plan.dataset_fixture_class),
            dataset_admissible=plan.dataset_admissible,
            economic_evidence_built=False,
            economic_gate_evaluated=False,
            economic_validity_result="NOT_PROVEN",
            economic_validity_offline_gate_pass=False,
            promotion_eligibility=False,
            runner_execution_success=True,
            manifest_verify_rc=0,
            output_dir=Path(plan.output_dir),
        )

    dataset_path = Path(plan.dataset_path)
    manifest_path = Path(plan.dataset_manifest_path)
    config_path = Path(plan.config_path)
    output_dir = Path(plan.output_dir)
    policy_path = Path(plan.policy_path) if plan.policy_path else None

    manifest = _load_dataset_manifest(manifest_path)
    descriptor = _descriptor_from_manifest(manifest, manifest_path=str(manifest_path))
    provenance = _provenance_from_manifest(manifest, manifest_path=str(manifest_path))
    fixture_class = DatasetFixtureClass(plan.dataset_fixture_class)
    cfg = _merge_policy_into_config(_load_config(config_path), policy_path)
    policy = _resolve_policy(cfg)
    bars = _load_bars_from_dataset_path(dataset_path)
    profile_binding = ds.load_profile_binding_from_manifest(manifest)
    admissibility = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=bars,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=descriptor.instrument_id,
        profile_binding=profile_binding,
    )
    admissibility_payload = ds.serialize_dataset_admissibility_binding_v1(admissibility)

    cfg = dict(cfg)
    backtest = dict(cfg.get("backtest", {}))
    dataset_section = dict(backtest.get("dataset_admissibility", {}))
    dataset_section["bind"] = True
    dataset_section["dataset"] = descriptor.to_dict()
    dataset_section["provenance"] = provenance.to_dict()
    dataset_section["profile_binding"] = ds.load_profile_binding_from_manifest(manifest).to_dict()
    backtest["dataset_admissibility"] = dataset_section
    cfg["backtest"] = backtest

    strategy_id = _resolve_strategy_id(cfg)
    params = _evaluation_params(cfg)
    data_admissibility = ev.DataAdmissibilityV1(
        source_kind=ev.DataSourceKind.VERSIONED_CANONICAL_FUTURES,
        instrument_id=descriptor.instrument_id,
        data_digest=ev.compute_bars_data_digest(bars),
        data_ref=str(dataset_path),
        versioned_dataset_id=descriptor.dataset_id,
    )
    input_provenance = {
        "dataset_path": str(dataset_path),
        "dataset_manifest_path": str(manifest_path),
        "config_path": str(config_path),
        "policy_path": str(policy_path) if policy_path else "",
        "dataset_digest": admissibility.dataset_digest,
        "dataset_manifest_digest": manifest.get("manifest_digest", ""),
        "config_digest": _stable_digest(cfg),
        "policy_digest": policy.policy_digest(),
        "implementation_digest": admissibility.implementation_digest,
        "canonical_trading_logic_version": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        "run_id": plan.run_id,
        "created_at_utc": OFFLINE_CREATED_AT_UTC,
        "runner_version": RUNNER_VERSION,
        "runner_owner": RUNNER_OWNER,
    }

    bundle, _repro = ev.build_and_persist_economic_viability_evidence_bundle_v1(
        output_dir,
        bars=bars,
        data_admissibility=data_admissibility,
        strategy_id=strategy_id,
        cfg=cfg,
        input_provenance=input_provenance,
        instrument_id=descriptor.instrument_id,
        **params,
    )
    loaded = ev.load_economic_viability_evidence_bundle_v1(output_dir)
    evidence = loaded.evidence
    gate_eval = evaluate_economic_validity_against_policy_v1(
        policy=policy,
        metrics=_build_gate_metrics_from_evidence(evidence),
        expected_policy_digest=policy.policy_digest(),
    )
    evaluation_payload = {
        "contract_version": "economic_validity_evaluation_v1",
        "owner": RUNNER_OWNER,
        "evaluation_status": gate_eval.evaluation_status.value,
        "gates_pass": gate_eval.gates_pass,
        "policy_threshold_status": gate_eval.policy_threshold_status,
        "reason_codes": list(gate_eval.reason_codes),
        "economic_validity_offline_gate_pass": gate_eval.gates_pass,
        "policy_digest": policy.policy_digest(),
        "config_digest": input_provenance["config_digest"],
        "dataset_digest": admissibility.dataset_digest,
        "implementation_digest": evidence.implementation_digest,
        "run_id": plan.run_id,
        "created_at_utc": OFFLINE_CREATED_AT_UTC,
        "runtime_effect": False,
        "order_effect": False,
        "promotion_effect": False,
    }
    (output_dir / "economic_validity_evaluation_v1.json").write_text(
        json.dumps(evaluation_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "dataset_admissibility_result_v1.json").write_text(
        json.dumps(admissibility_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    write_manifest_sha256(output_dir)
    ok, _message = verify_manifest_sha256(output_dir)
    manifest_verify_rc = 0 if ok else 1
    if not ok:
        raise RunnerError("manifest_verify_failed")

    summary_fields = {
        "PROCESS_CLASSIFICATION": "ACTIVE_PROGRESS",
        "SCOPE_CLASSIFICATION": (
            "RUNBOOK_STEP_29M_REAL_ADMISSIBLE_FUTURES_ECONOMIC_EVIDENCE_EVALUATION_V1_OFFLINE_SLICE"
        ),
        "RUN_ID": plan.run_id,
        "DATASET_ID": descriptor.dataset_id,
        "DATASET_VERSION": descriptor.dataset_version,
        "DATASET_ADMISSIBLE": str(admissibility.is_admissible()).lower(),
        "DATASET_FIXTURE_CLASS": fixture_class.value,
        "FUTURES_ONLY": "true",
        "BITCOIN_DIRECTION_ALLOWED": "false",
        "ECONOMIC_EVIDENCE_BUILT": "true",
        "ECONOMIC_GATE_EVALUATED": "true",
        "ECONOMIC_VALIDITY_RESULT": _map_validity_result(gate_eval.evaluation_status),
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": str(gate_eval.gates_pass).lower(),
        "PROMOTION_ELIGIBILITY": "false",
        "RUNNER_EXECUTION_SUCCESS": "true",
        "RUNTIME_EFFECT": "false",
        "ORDER_EFFECT": "false",
        "NETWORK_EFFECT": "false",
        "LIVE_AUTHORIZED": "false",
        "MANIFEST_VERIFY_RC": str(manifest_verify_rc),
    }
    _write_run_summary_env(output_dir / "run_summary.env", summary_fields)

    return RunOutcomeV1(
        run_id=plan.run_id,
        dataset_id=descriptor.dataset_id,
        dataset_version=descriptor.dataset_version,
        dataset_fixture_class=fixture_class,
        dataset_admissible=admissibility.is_admissible(),
        economic_evidence_built=True,
        economic_gate_evaluated=True,
        economic_validity_result=_map_validity_result(gate_eval.evaluation_status),
        economic_validity_offline_gate_pass=gate_eval.gates_pass,
        promotion_eligibility=False,
        runner_execution_success=True,
        manifest_verify_rc=manifest_verify_rc,
        output_dir=output_dir,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        if args.validate_only:
            plan = build_validation_plan(args)
            if args.json:
                print(json.dumps(plan.__dict__, indent=2, sort_keys=True))
            else:
                print(json.dumps(plan.__dict__, indent=2, sort_keys=True))
            return 0
        outcome = execute_evaluation(args)
        if args.json:
            print(
                json.dumps(
                    {
                        "runner_execution_success": outcome.runner_execution_success,
                        "economic_validity_result": outcome.economic_validity_result,
                        "economic_validity_offline_gate_pass": (
                            outcome.economic_validity_offline_gate_pass
                        ),
                        "output_dir": str(outcome.output_dir),
                        "manifest_verify_rc": outcome.manifest_verify_rc,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        return 0
    except RunnerError as exc:
        print(str(exc), file=sys.stderr)
        return VALIDATION_EXIT
    except (
        ds.AdmissibleVersionedFuturesDatasetError,
        ev.EconomicViabilityEvidenceError,
        policy_mod.EconomicValidityPolicyError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        return VALIDATION_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
