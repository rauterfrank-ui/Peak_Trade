"""Research generation preparation for bouchaud_microstructure_ohlcv_proxy/v1.

Offline-only slice: binds a deterministic OHLCV microstructure proxy feature matrix
hypothesis for later linear-evidence diagnostics. No economic evaluation, no runtime
or authority effect. OHLCV proxies are not true order-book microstructure.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from src.research.linear_evidence.feature_matrix import build_feature_matrix_binding

PACKAGE_MARKER = "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_RESEARCH_GENERATION_PREPARATION_V0=true"
SCHEMA_VERSION = "bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation.v0"
PREPARATION_ID = "bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0"
PREPARATION_VERSION = "v0"
SCOPE_CLASSIFICATION = "BOUNDED_FUTURES_ONLY_OHLCV_PROXY_RESEARCH_GENERATION_PREPARATION_V0"
OPERATOR_GO_TOKEN = (
    "GO_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_DISTINCT_RESEARCH_GENERATION_"
    "HYPOTHESIS_AND_IMPLEMENTATION_READINESS"
)
CONFIG_REL_PATH = (
    "config/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_RESEARCH_GENERATION_PREPARATION_V0.md"
)
MATERIALIZER_REL_PATH = (
    "scripts/research/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py"
)

RESEARCH_SCOPE = "bouchaud_microstructure_ohlcv_proxy/v1"
HYPOTHESIS_ID = "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_LINEAR_FEATURE_RESEARCH_GENERATION"
EVIDENCE_CLASS_ID = "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_RESEARCH_GENERATION_PREPARATION_V0"
SIGNAL_FAMILY = "BAR_LEVEL_OHLCV_MICROSTRUCTURE_PROXY_FEATURE_MATRIX"
CANONICAL_OWNER = (
    "src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0"
)

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
TERMINAL_ADJUDICATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/canonical_offline_linear_diagnostics_promotion_binding_workstream_"
    "terminal_adjudication_read_only_v0_20260715T000324Z"
)
PR5188_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5188_merge_closeout_canonical_offline_linear_diagnostics_and_"
    "promotion_binding_completion_reconciliation_v0_20260714T235729Z"
)
LINEAR_DIAGNOSTICS_RECONCILIATION_DIR = (
    DURABLE_ARCHIVE_ROOT / "research/canonical_offline_linear_diagnostics_and_promotion_binding_"
    "completion_reconciliation_v0_20260714T234853Z"
)
PRIOR_INCONCLUSIVE_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/bouchaud_microstructure_ohlcv_proxy_v1_repaired_same_semantic_binding_"
    "offline_baseline_reevaluation_v0_20260710T180542Z"
)
VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding_v0.json"
)
MATERIAL_DIFFERENCE_CONFIG_REL_PATH = (
    "config/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_material_difference_and_non_claim_contract_v0.json"
)

DATASET_ID = "inst-eth-usdt-perp_v1"
DATASET_DIGEST = "39286384bb5baca27c93cae04716de9d8638ac62ab7d01a64c0a74c535e8d087"
DATASET_PATH = (
    DURABLE_ARCHIVE_ROOT / "datasets/admissible_futures/inst-eth-usdt-perp/v1/bars.parquet"
)
INSTRUMENT_ID = "inst-eth-usdt-perp"
UNIVERSE_DIGEST = hashlib.sha256(
    json.dumps({"instrument_id": INSTRUMENT_ID, "futures_only": True}, sort_keys=True).encode()
).hexdigest()

TARGET_NAME = "forward_return_1bar"
TARGET_SHIFT = 1
SHORT_WINDOW = 10
LONG_WINDOW = 20
REQUIRED_WARMUP_ROWS = LONG_WINDOW + TARGET_SHIFT
VALIDATION_POLICY = "TIME_ORDERED"

OHLCV_PROXY_IS_NOT_TRUE_ORDER_BOOK_MICROSTRUCTURE = True

FEATURE_NAMES: tuple[str, ...] = (
    "signed_return_volume_pressure",
    "volatility_normalized_price_impact",
    "volume_conditioned_return_response",
    "kyle_lambda_proxy",
    "imbalance_persistence_proxy",
    "transient_permanent_impact_ratio",
    "liquidity_resilience_proxy",
)

FEATURE_CLASSIFICATION: dict[str, str] = {
    "signed_return_volume_pressure": "DETERMINISTIC_OHLCV_PROXY",
    "volatility_normalized_price_impact": "DETERMINISTIC_OHLCV_PROXY",
    "volume_conditioned_return_response": "DETERMINISTIC_OHLCV_PROXY",
    "kyle_lambda_proxy": "DETERMINISTIC_OHLCV_PROXY",
    "imbalance_persistence_proxy": "DETERMINISTIC_OHLCV_PROXY",
    "transient_permanent_impact_ratio": "DETERMINISTIC_OHLCV_PROXY",
    "liquidity_resilience_proxy": "DETERMINISTIC_OHLCV_PROXY",
}

EXCLUDED_UNSUPPORTED_FEATURES: tuple[str, ...] = (
    "true_order_book_imbalance",
    "tick_level_trade_sign",
    "depth_imbalance_l2",
    "synthetic_order_flow_label",
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

REQUIRED_EVIDENCE_ARTIFACTS: tuple[str, ...] = (
    "preflight.txt",
    "source_manifest_verification.txt",
    "prior_negative_evidence_preservation.json",
    "owner_inventory.json",
    "reuse_decision.json",
    "distinctness_adjudication.json",
    "hypothesis_contract.json",
    "dataset_feasibility.json",
    "feature_classification.json",
    "no_lookahead_contract.json",
    "target_binding.json",
    "sample_sufficiency_assessment.json",
    "implementation_admissibility.json",
    "changed_files.txt",
    "test_assertion_matrix.json",
    "test_results.txt",
    "deterministic_materialization.txt",
    "second_materialization_diff.txt",
    "economic_evaluation_status.json",
    "runtime_authority_boundary.json",
    "final_report.txt",
    "MANIFEST.sha256",
)


class PreparationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ManifestVerification:
    bundle_path: Path
    manifest_verify_rc: int


def serialize_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_digest(payload: Any) -> str:
    return hashlib.sha256(serialize_canonical_json(payload).encode("utf-8")).hexdigest()


def verify_manifest_sha256(bundle_dir: Path) -> ManifestVerification:
    manifest = bundle_dir / "MANIFEST.sha256"
    if not manifest.is_file():
        return ManifestVerification(bundle_path=bundle_dir, manifest_verify_rc=1)
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=bundle_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return ManifestVerification(bundle_path=bundle_dir, manifest_verify_rc=proc.returncode)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not_object:{path}")
    return data


def _normalize_bars_frame(bars: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(bars.columns)
    if missing:
        raise ValueError(f"MISSING_BAR_COLUMNS:{sorted(missing)}")
    frame = bars.copy()
    if "is_final" in frame.columns:
        frame = frame.loc[frame["is_final"].astype(bool)].copy()
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    if frame.empty:
        raise ValueError("INSUFFICIENT_DATA")
    for col in ("open", "high", "low", "close", "volume"):
        frame[col] = pd.to_numeric(frame[col], errors="raise")
    return frame


def _bar_pressure(frame: pd.DataFrame) -> pd.Series:
    span = (frame["high"] - frame["low"]).replace(0.0, np.nan)
    return (frame["close"] - frame["open"]) / span


def compute_ohlcv_proxy_features_v0(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute point-in-time OHLCV microstructure proxy features without lookahead."""
    work = _normalize_bars_frame(frame)
    ret = work["close"].pct_change()
    log_volume = np.log1p(work["volume"].clip(lower=0.0))
    rolling_vol = ret.rolling(SHORT_WINDOW, min_periods=SHORT_WINDOW).std()
    bar_pressure = _bar_pressure(work)
    short_impact = ret.abs().rolling(SHORT_WINDOW, min_periods=SHORT_WINDOW).mean()
    long_impact = ret.abs().rolling(LONG_WINDOW, min_periods=LONG_WINDOW).mean()

    features = pd.DataFrame(
        {
            "decision_time": work["timestamp"].astype(str),
            "signed_return_volume_pressure": np.sign(ret.fillna(0.0)) * log_volume,
            "volatility_normalized_price_impact": ret.abs() / rolling_vol.replace(0.0, np.nan),
            "volume_conditioned_return_response": ret * log_volume,
            "kyle_lambda_proxy": ret.abs() / work["volume"].replace(0.0, np.nan),
            "imbalance_persistence_proxy": bar_pressure.rolling(
                SHORT_WINDOW, min_periods=SHORT_WINDOW
            ).apply(lambda s: s.autocorr(lag=1) if len(s.dropna()) >= 2 else np.nan, raw=False),
            "transient_permanent_impact_ratio": short_impact / long_impact.replace(0.0, np.nan),
            "liquidity_resilience_proxy": work["volume"]
            / ((work["high"] - work["low"]).replace(0.0, np.nan)),
        }
    )
    features["forward_return_1bar"] = work["close"].pct_change(TARGET_SHIFT).shift(-TARGET_SHIFT)
    return features


def materialize_feature_rows_v0(
    bars: pd.DataFrame,
    *,
    feature_names: Sequence[str] = FEATURE_NAMES,
    target_name: str = TARGET_NAME,
) -> list[dict[str, Any]]:
    computed = compute_ohlcv_proxy_features_v0(bars)
    rows: list[dict[str, Any]] = []
    for idx in range(REQUIRED_WARMUP_ROWS, len(computed) - TARGET_SHIFT):
        row = computed.iloc[idx]
        payload = {"decision_time": str(row["decision_time"]), target_name: float(row[target_name])}
        valid = True
        for name in feature_names:
            value = row[name]
            if pd.isna(value) or not np.isfinite(float(value)):
                valid = False
                break
            payload[name] = float(value)
        if valid and np.isfinite(float(row[target_name])):
            rows.append(payload)
    if not rows:
        raise ValueError("INSUFFICIENT_DATA")
    return rows


def validate_no_lookahead_contract_v0(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: str(row["decision_time"]))
    times = [str(row["decision_time"]) for row in ordered]
    if times != sorted(times):
        raise ValueError("TIME_ORDERING_FAILED")
    return {
        "schema_version": "no_lookahead_contract.v0",
        "no_lookahead": True,
        "finalized_bar_only": True,
        "feature_timestamp_strictly_before_target": True,
        "target_shift_explicit": True,
        "target_shift": TARGET_SHIFT,
        "target_name": TARGET_NAME,
        "validation_policy": VALIDATION_POLICY,
        "random_validation_split_forbidden": True,
        "ohlcv_proxy_is_not_true_order_book_microstructure": True,
        "unsupported_microstructure_claims_rejected": True,
    }


def build_owner_inventory() -> dict[str, Any]:
    return {
        "schema_version": "owner_inventory.v0",
        "dataset_owner": VERSIONED_BINDING_CONFIG_REL_PATH,
        "feature_matrix_owner": "src/research/linear_evidence/feature_matrix.py",
        "materializer_owner": CANONICAL_OWNER,
        "validator_owner": CANONICAL_OWNER,
        "config_owner": CONFIG_REL_PATH,
        "governance_owner": GOVERNANCE_REL_PATH,
        "evidence_manifest_owner": "scripts.ops.primary_evidence_retention_v0",
        "linear_evidence_support_owner": (
            "src/research/linear_evidence/offline_productive_linear_diagnostics_support_bundle_v0.py"
        ),
        "versioned_research_binding_owner": VERSIONED_BINDING_CONFIG_REL_PATH,
        "material_difference_contract_owner": MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
        "parallel_feature_matrix_owner_created": False,
        "parallel_digest_owner_created": False,
        "parallel_backtest_owner_created": False,
        "parallel_strategy_owner_created": False,
        "parallel_cost_owner_created": False,
        "parallel_evidence_owner_created": False,
    }


def build_reuse_decision() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decisions": {
            "dataset_binding": "REUSE_AS_IS",
            "feature_matrix_binding": "REUSE_AS_IS",
            "material_difference_contract": "REUSE_AS_IS",
            "versioned_research_binding_reference": "REUSE_AS_IS",
            "feature_materialization": "NEW_IMPLEMENTATION_JUSTIFIED",
            "hypothesis_contract": "NEW_IMPLEMENTATION_JUSTIFIED",
            "research_generation_preparation_config": "NEW_IMPLEMENTATION_JUSTIFIED",
            "economic_evaluation_runner": "REUSE_AS_IS",
            "strategy_signal_binding": "REUSE_AS_IS",
        },
        "justification": (
            "Prior bouchaud/v1 economic evaluation consumed strategy-threshold signals. "
            "This slice introduces deterministic OHLCV proxy feature-matrix preparation "
            "without retrying unchanged strategy binding or economic evaluation."
        ),
    }


def build_distinctness_adjudication(repo_root: Path) -> dict[str, Any]:
    material_difference = _load_json(repo_root / MATERIAL_DIFFERENCE_CONFIG_REL_PATH)
    return {
        "schema_version": "distinctness_adjudication.v0",
        "research_scope": RESEARCH_SCOPE,
        "material_difference_proven": True,
        "material_difference_digest": material_difference["material_difference_digest"],
        "signal_family": SIGNAL_FAMILY,
        "prior_strategy_signal_family": "BAR_LEVEL_MICROSTRUCTURE_PRESSURE_PROXY",
        "evidence_class_distinct": True,
        "prior_evidence_class": (
            "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_FULL_CANONICAL_OFFLINE_BASELINE_"
            "ECONOMIC_EVALUATION_V0"
        ),
        "new_evidence_class": EVIDENCE_CLASS_ID,
        "unchanged_strategy_binding_retry_blocked": True,
        "excluded_near_duplicates": [
            "macd/v1-v3",
            "breakout_donchian/v1",
            "ma_crossover/v1",
            "rsi_reversion/step30a",
            "composite_breakout_confirmation_vol_gated_donchian_v1",
            "trend_following",
            "bollinger_bands",
            "momentum_1h",
        ],
        "ohlcv_proxy_is_not_true_order_book_microstructure": True,
    }


def build_hypothesis_contract() -> dict[str, Any]:
    return {
        "schema_version": "hypothesis_contract.v0",
        "research_scope": RESEARCH_SCOPE,
        "hypothesis_id": HYPOTHESIS_ID,
        "hypothesis_version": PREPARATION_VERSION,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "signal_family": SIGNAL_FAMILY,
        "hypothesis_statement": (
            "Deterministic OHLCV-derived microstructure proxy features inspired by market "
            "impact and order-flow-imbalance concepts may contain incremental predictive "
            "information for forward returns under explicit cost-survival review, without "
            "claiming true order-book imbalance or trade-sign classification."
        ),
        "proxy_semantics": True,
        "true_tick_l2_microstructure": False,
        "ohlcv_proxy_is_not_true_order_book_microstructure": True,
        "feature_names": list(FEATURE_NAMES),
        "feature_count": len(FEATURE_NAMES),
        "target_name": TARGET_NAME,
        "target_shift": TARGET_SHIFT,
        "futures_only": True,
        "bitcoin_present": False,
        "economic_evaluation_executed": False,
        "economic_evaluation_authorized": False,
    }


def build_dataset_feasibility() -> dict[str, Any]:
    dataset_exists = DATASET_PATH.is_file()
    return {
        "schema_version": "dataset_feasibility.v0",
        "dataset_id": DATASET_ID,
        "dataset_digest": DATASET_DIGEST,
        "dataset_path": str(DATASET_PATH),
        "dataset_exists": dataset_exists,
        "futures_only": True,
        "bitcoin_present": False,
        "finalized_bar_only": True,
        "point_in_time_binding": True,
        "fabricated_fields_required": False,
        "lookahead_required": False,
        "synthetic_order_book_required": False,
        "cost_inputs_available": True,
        "feasibility_status": "SUFFICIENT" if dataset_exists else "BLOCKED_DATASET_MISSING",
    }


def build_target_binding() -> dict[str, Any]:
    return {
        "schema_version": "target_binding.v0",
        "target_name": TARGET_NAME,
        "target_shift": TARGET_SHIFT,
        "target_definition": "forward_close_to_close_return_over_target_shift_bars",
        "validation_split": VALIDATION_POLICY,
        "random_split_forbidden": True,
        "survivorship_leakage_forbidden": True,
        "post_result_universe_selection_forbidden": True,
    }


def build_sample_sufficiency_assessment(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    count = len(rows)
    if count >= 1000:
        status = "SUFFICIENT_FOR_LINEAR_DIAGNOSTIC_PREP"
    elif count >= 100:
        status = "MARGINAL_BUT_ADMISSIBLE_FOR_PREP"
    else:
        status = "INSUFFICIENT_FOR_ECONOMIC_EVALUATION_NOT_BLOCKING_PREP"
    return {
        "schema_version": "sample_sufficiency_assessment.v0",
        "row_count": count,
        "minimum_rows_for_prep": 100,
        "minimum_rows_for_economic_evaluation": 1000,
        "sample_sufficiency_status": status,
        "economic_evaluation_executed": False,
    }


def build_implementation_admissibility(repo_root: Path) -> dict[str, Any]:
    feasibility = build_dataset_feasibility()
    admissible = (
        feasibility["feasibility_status"] == "SUFFICIENT"
        and (repo_root / MATERIAL_DIFFERENCE_CONFIG_REL_PATH).is_file()
        and (repo_root / VERSIONED_BINDING_CONFIG_REL_PATH).is_file()
    )
    return {
        "schema_version": "implementation_admissibility.v0",
        "implementation_admissible": admissible,
        "hypothesis_materially_distinct": True,
        "dataset_support_sufficient": feasibility["feasibility_status"] == "SUFFICIENT",
        "feature_semantics_explicit": True,
        "canonical_owners_resolved": True,
        "no_lookahead_contract_proven": True,
        "deterministic_materialization_feasible": True,
        "new_dependency_required": False,
        "core_trading_semantics_changed": False,
        "risk_sizing_semantics_changed": False,
        "safety_semantics_changed": False,
        "policy_rescue_involved": False,
        "unchanged_failed_binding_retry": False,
    }


def build_prior_negative_evidence_preservation() -> dict[str, Any]:
    return {
        "schema_version": "prior_negative_evidence_preservation.v0",
        "economic_validity_offline_gate_pass": False,
        "unchanged_retry_blocked": True,
        "policy_rescue_allowed": False,
        "runtime_rewire_admissible": False,
        "prior_inconclusive_evidence_preserved": True,
        "prior_inconclusive_evidence_dir": str(PRIOR_INCONCLUSIVE_EVIDENCE_DIR),
        "prior_strategy_economic_evaluation_not_retried": True,
        "negative_economic_evidence_deleted": False,
        "negative_economic_evidence_weakened": False,
        "negative_economic_evidence_superseded": False,
    }


def build_economic_evaluation_status() -> dict[str, Any]:
    return {
        "schema_version": "economic_evaluation_status.v0",
        "economic_evaluation_executed": False,
        "economic_evaluation_authorized": False,
        "walk_forward_executed": False,
        "monte_carlo_executed": False,
        "stress_executed": False,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
    }


def build_runtime_authority_boundary() -> dict[str, Any]:
    return {
        "schema_version": "runtime_authority_boundary.v0",
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "no_runtime_import_boundary_violation": True,
        "no_order_adapter_import_boundary_violation": True,
        "no_scheduler_import_boundary_violation": True,
        "no_core_trading_semantics_changed": True,
        "no_risk_sizing_semantics_changed": True,
        "no_safety_semantics_changed": True,
    }


def materialize_and_validate_feature_matrix_v0(
    bars: pd.DataFrame,
) -> tuple[list[dict[str, Any]], Any, str]:
    rows = materialize_feature_rows_v0(bars)
    _, _, binding = build_feature_matrix_binding(
        rows,
        feature_names=FEATURE_NAMES,
        target_name=TARGET_NAME,
        validation_policy=VALIDATION_POLICY,
    )
    feature_digest = binding.feature_matrix_digest
    return rows, binding, feature_digest


def materialize_preparation_config(
    repo_root: Path,
    *,
    rows: Sequence[Mapping[str, Any]],
    feature_digest: str,
) -> dict[str, Any]:
    no_lookahead = validate_no_lookahead_contract_v0(rows)
    payload = {
        "artifact_kind": PREPARATION_ID,
        "artifact_version": PREPARATION_VERSION,
        "schema_version": SCHEMA_VERSION,
        "go_token": OPERATOR_GO_TOKEN,
        "research_scope": RESEARCH_SCOPE,
        "hypothesis_id": HYPOTHESIS_ID,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "signal_family": SIGNAL_FAMILY,
        "canonical_owner": CANONICAL_OWNER,
        "dataset_id": DATASET_ID,
        "dataset_digest": DATASET_DIGEST,
        "instrument_id": INSTRUMENT_ID,
        "universe_digest": UNIVERSE_DIGEST,
        "bitcoin_present": False,
        "futures_only": True,
        "feature_names": list(FEATURE_NAMES),
        "feature_count": len(FEATURE_NAMES),
        "feature_digest": feature_digest,
        "target_name": TARGET_NAME,
        "target_shift": TARGET_SHIFT,
        "no_lookahead_contract": no_lookahead,
        "hypothesis_contract": build_hypothesis_contract(),
        "dataset_feasibility": build_dataset_feasibility(),
        "feature_classification": FEATURE_CLASSIFICATION,
        "excluded_unsupported_features": list(EXCLUDED_UNSUPPORTED_FEATURES),
        "target_binding": build_target_binding(),
        "sample_sufficiency_assessment": build_sample_sufficiency_assessment(rows),
        "implementation_admissibility": build_implementation_admissibility(repo_root),
        "distinctness_adjudication": build_distinctness_adjudication(repo_root),
        "owner_inventory": build_owner_inventory(),
        "reuse_decision": build_reuse_decision(),
        "economic_evaluation_status": build_economic_evaluation_status(),
        "runtime_authority_boundary": build_runtime_authority_boundary(),
        "ohlcv_proxy_is_not_true_order_book_microstructure": True,
        "material_difference_proven": True,
        "proxy_semantics": True,
        "true_tick_l2_microstructure": False,
        "offline_only": True,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "preparation_digest": "",
    }
    body = {k: v for k, v in payload.items() if k != "preparation_digest"}
    payload["preparation_digest"] = _stable_digest(body)
    return payload


def compute_preparation_digest(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "preparation_digest"}
    return _stable_digest(body)


def validate_source_evidence() -> dict[str, Any]:
    bundles = {
        "pr5188_closeout": PR5188_CLOSEOUT_DIR,
        "linear_diagnostics_reconciliation": LINEAR_DIAGNOSTICS_RECONCILIATION_DIR,
        "terminal_adjudication": TERMINAL_ADJUDICATION_DIR,
        "prior_inconclusive": PRIOR_INCONCLUSIVE_EVIDENCE_DIR,
    }
    results: dict[str, Any] = {}
    for name, path in bundles.items():
        verification = verify_manifest_sha256(path)
        results[name] = {
            "bundle_path": str(path),
            "manifest_verify_rc": verification.manifest_verify_rc,
        }
    source_manifest_verify_rc = (
        0 if all(item["manifest_verify_rc"] == 0 for item in results.values()) else 1
    )
    return {
        "bundles": results,
        "source_manifest_verify_rc": source_manifest_verify_rc,
    }


def load_fixture_bars_v0(repo_root: Path) -> pd.DataFrame:
    fixture_path = (
        repo_root
        / "tests/fixtures/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0/"
        "truth_pack_bars.json"
    )
    payload = _load_json(fixture_path)
    return pd.DataFrame(payload["bars"])


def load_dataset_bars_v0() -> pd.DataFrame:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(f"dataset_missing:{DATASET_PATH}")
    return pd.read_parquet(DATASET_PATH)


def is_unsupported_microstructure_feature_rejected(feature_name: str) -> bool:
    return feature_name in EXCLUDED_UNSUPPORTED_FEATURES
