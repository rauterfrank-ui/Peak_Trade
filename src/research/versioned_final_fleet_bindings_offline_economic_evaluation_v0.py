"""Versioned final fleet bindings and offline economic evaluation v0.

Deterministic, fail-closed materialization of immutable fleet bindings for
trend_following/v1, bollinger_bands/v1, and momentum_1h/v1 bound to the
materialized extended_chronological_v1 panel with funding from PR #4815/#4817,
followed by bounded offline economic evaluation using canonical STEP29M/STEP31F
owners.

Research-only. No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.backtest.economic_validity_policy_v1 import (
    ECONOMIC_VALIDITY_POLICY_VERSION,
    EconomicValidityEvaluationStatus,
)
from src.backtest.strategy_signal_binding_v1 import resolve_effective_strategy_params_v1
from src.research.bounded_offline_funding_fetch_for_materialized_panel_v0 import (
    FundingCoverageReportV0,
    PanelMemberBindingV0,
    compute_funding_coverage_report_v0,
    load_panel_member_binding_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (
    load_funding_panel_from_staging,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    FleetTerminalStatus,
    resolve_fleet_terminal_status_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    CANONICAL_INSTRUMENT_ID,
    FLEET_CANDIDATES,
    FLEET_ID,
    FLEET_VERSION,
    NATIVE_INSTRUMENT_ID,
    SOURCE_VENUE,
    compute_config_digest_v1,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    CANONICAL_TRADING_LOGIC_BINDING_VERSION,
    FAILED_HISTORICAL_CANDIDATES,
    FORBIDDEN_INSTRUMENT_TOKENS,
    canonical_candidate_identifier,
    compute_binding_semantic_digest_v0,
    compute_completion_digest_v0,
)
from src.strategies.registry import get_strategy_registry_entry

PACKAGE_MARKER = "VERSIONED_FINAL_FLEET_BINDINGS_OFFLINE_ECONOMIC_EVALUATION_V0=true"

SCHEMA_VERSION = "versioned_final_fleet_bindings_offline_economic_evaluation.v0"
COMPLETION_ID = "versioned_final_fleet_bindings_offline_economic_evaluation_v0"
CONFIG_REL_PATH = "config/ops/versioned_final_fleet_bindings_offline_economic_evaluation_v0.json"
CANONICAL_SERIALIZATION_VERSION = "research_binding_completion_canonical_json_v1"

GO_TOKEN = "GO_BOUNDED_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_V0"
SCOPE_CLASSIFICATION = "BOUNDED_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_V0"
EXPECTED_ORIGIN_MAIN_SHA = "d7e03de515a7349b01cc4058379fcbb65c4548d8"
DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_STAGING_REL = (
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)
PERIOD_POLICY_REL = (
    "config/research/pit_cross_sectional_research_data_digest_period_split_policy_v1.json"
)

DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
DATASET_EXTENSION_OHLCV = "extended_chronological_v1"
DATASET_EXTENSION_FUNDING = "extended_chronological_with_funding_v1"
PANEL_CALENDAR_START_UTC = "2024-05-01T00:00:00Z"
PANEL_CALENDAR_END_UTC = "2024-09-01T00:00:00Z"
EVALUATION_INSTRUMENT_ID = "okx:linear_perpetual:ETH:USDT:USDT:perp"
EVALUATION_NATIVE_INSTRUMENT_ID = NATIVE_INSTRUMENT_ID

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
CONSERVATIVE_HALF_SPREAD_BPS = 5.0
ROUNDTRIP_COST_BPS = 40.0

STEP31F_TEMPLATE_CONFIG_PATHS: dict[str, str] = {
    "trend_following": (
        "config/ops/step31f_okx_inst_eth_usdt_perp_trend_following_v1_economic_evaluation_v1.json"
    ),
    "bollinger_bands": (
        "config/ops/step31f_okx_inst_eth_usdt_perp_bollinger_bands_v1_economic_evaluation_v1.json"
    ),
    "momentum_1h": (
        "config/ops/step31f_okx_inst_eth_usdt_perp_momentum_1h_v1_economic_evaluation_v1.json"
    ),
}

PRIOR_EVIDENCE_BUNDLES: tuple[tuple[str, str], ...] = (
    (
        "PR4815",
        "research/offline_panel_materialization_from_partial_tmp_no_fetch_v0_20260703T221342Z",
    ),
    (
        "PR4816",
        "research/bounded_offline_funding_fetch_for_materialized_panel_v0_20260704T165402Z",
    ),
    (
        "PR4817",
        "research/okx_historical_funding_archive_ingest_v0_20260704T171836Z",
    ),
)

REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_ORIGIN_MAIN_MISMATCH = "ORIGIN_MAIN_SHA_MISMATCH"
REASON_STAGING_MISSING = "STAGING_MISSING"
REASON_FUNDING_COVERAGE_INCOMPLETE = "FAIL_CLOSED_DATASET_OR_FUNDING_COVERAGE_INCOMPLETE"
REASON_IMPLICIT_ZERO_COST = "FAIL_CLOSED_IMPLICIT_ZERO_COST_PATH"
REASON_BINDING_INCOMPLETE = "FAIL_CLOSED_DIGEST_BINDING_INCOMPLETE"
REASON_SHARED_BINDING_MISMATCH = "FAIL_CLOSED_CANDIDATE_POLICY_DRIFT"
REASON_STRATEGY_BINDING_MISSING = "FAIL_CLOSED_STRATEGY_BINDING_MISSING"
REASON_PARAMETER_BINDING_MISSING = "FAIL_CLOSED_PARAMETER_BINDING_MISSING"

_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class CandidateDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class BindingValidationResultV0:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]


@dataclass(frozen=True)
class NarrowDatasetMaterializationV0:
    dataset_root: Path
    bars_path: Path
    manifest_path: Path
    dataset_digest: str
    manifest_digest: str
    row_count: int
    bar_granularity: str
    training_period: str
    validation_period: str
    out_of_sample_period: str


@dataclass(frozen=True)
class ScopeExecutionResultV0:
    binding_completion: dict[str, Any]
    candidate_results: tuple[CandidateExecutionResultV0, ...]
    fleet_status: FleetTerminalStatus
    economic_validity_offline_gate_pass: bool
    manifest_verify_rc: int
    evidence_root: Path
    candidate_decisions: dict[str, CandidateDecision]
    narrow_dataset: NarrowDatasetMaterializationV0


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_origin_main_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def load_scope_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        raise FileNotFoundError(f"missing_scope_config:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_staging_root(
    *,
    durable_archive_root: Path,
    scope_config: Mapping[str, Any],
) -> Path:
    staging = scope_config.get("staging_root")
    if isinstance(staging, str) and staging.strip():
        return Path(staging).resolve()
    return (durable_archive_root / DEFAULT_STAGING_REL).resolve()


def _load_period_policy(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / PERIOD_POLICY_REL).read_text(encoding="utf-8"))


def _period_label_from_policy(period_policy: Mapping[str, Any]) -> tuple[str, str, str]:
    training = f"{period_policy['training_start']}..{period_policy['training_end']}"
    validation = f"{period_policy['validation_start']}..{period_policy['validation_end']}"
    oos = f"{period_policy['out_of_sample_start']}..{period_policy['out_of_sample_end']}"
    return training, validation, oos


def verify_preconditions_v0(
    *,
    repo_root: Path,
    confirm: str,
    staging_root: Path,
    origin_main_sha: str | None = None,
) -> tuple[bool, tuple[str, ...], PanelMemberBindingV0, FundingCoverageReportV0]:
    reasons: list[str] = []
    if confirm != GO_TOKEN:
        reasons.append(REASON_GO_TOKEN_INVALID)
    resolved = origin_main_sha or _resolve_origin_main_sha(repo_root)
    if resolved != EXPECTED_ORIGIN_MAIN_SHA:
        reasons.append(f"{REASON_ORIGIN_MAIN_MISMATCH}:{resolved}")
    coverage = FundingCoverageReportV0(
        row_count_total=0,
        missing_funding_count=0,
        populated_funding_count=0,
        coverage_ratio=0.0,
        fetched_from_okx_public=None,
        instrument_count=0,
        manifest_verified=False,
    )
    panel_binding: PanelMemberBindingV0 | None = None
    if not staging_root.is_dir():
        reasons.append(REASON_STAGING_MISSING)
    else:
        try:
            panel_binding = load_panel_member_binding_v0(staging_root)
        except FileNotFoundError as exc:
            reasons.append(str(exc))
        coverage = compute_funding_coverage_report_v0(staging_root)
        if coverage.coverage_ratio < 1.0 or coverage.missing_funding_count > 0:
            reasons.append(REASON_FUNDING_COVERAGE_INCOMPLETE)
    if panel_binding is None and REASON_STAGING_MISSING not in reasons:
        reasons.append(REASON_STAGING_MISSING)
    if not reasons and panel_binding is None:
        reasons.append(REASON_STAGING_MISSING)
    return not reasons, tuple(reasons), panel_binding, coverage  # type: ignore[return-value]


def materialize_narrow_evaluation_dataset_v0(
    *,
    staging_root: Path,
    output_root: Path,
    period_policy: Mapping[str, Any],
) -> NarrowDatasetMaterializationV0:
    funding_series, _panel_ref, _manifest_path = load_funding_panel_from_staging(staging_root)
    eth_series = None
    for series in funding_series:
        if series.instrument_id == EVALUATION_INSTRUMENT_ID:
            eth_series = series
            break
    if eth_series is None:
        raise ValueError(f"missing_evaluation_instrument:{EVALUATION_INSTRUMENT_ID}")

    rows: list[dict[str, Any]] = []
    for bar in eth_series.bars:
        close = float(bar.close)
        rows.append(
            {
                "timestamp": pd.Timestamp(bar.timestamp_utc, tz="UTC"),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": close,
                "volume": float(bar.volume),
                "mark_price": close,
                "index_price": close,
                "funding_rate": float(bar.funding_rate),
                "is_final": True,
            }
        )
    frame = pd.DataFrame(rows).set_index("timestamp").sort_index()
    if frame.empty:
        raise ValueError("empty_narrow_evaluation_dataset")

    field_bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
    dataset_digest = ds.compute_versioned_dataset_digest(frame, field_bindings=field_bindings)
    training, validation, oos = ds.compute_split_periods_from_bars(frame)

    output_root.mkdir(parents=True, exist_ok=True)
    bars_path = output_root / "bars.parquet"
    frame.to_parquet(bars_path)

    provenance = ds.DatasetProvenanceV1(
        source_type="panel_narrow_adapter_v0",
        venue_id=SOURCE_VENUE,
        ingestion_timestamp=_utc_now_z(),
        generation_method="versioned_final_fleet_panel_narrow_adapter_v0",
        provenance_ref=str(staging_root / "panel" / "panel_funding_dataset_manifest.json"),
    )
    descriptor = ds.VersionedFuturesDatasetDescriptorV1(
        dataset_id=f"{CANONICAL_INSTRUMENT_ID}_{ds.DEFAULT_DATASET_VERSION}",
        dataset_version=ds.DEFAULT_DATASET_VERSION,
        dataset_schema_version=ds.DATASET_SCHEMA_VERSION,
        dataset_digest=dataset_digest,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        contract_type="perpetual",
        futures_only=True,
        bitcoin_direction_allowed=False,
        venue_id=SOURCE_VENUE,
        start_time=str(frame.index[0]),
        end_time=str(frame.index[-1]),
        row_count=len(frame),
        field_bindings=field_bindings,
        training_period=training,
        validation_period=validation,
        out_of_sample_period=oos,
        split_policy_version=ds.SPLIT_POLICY_VERSION,
        timestamp_semantics=ds.TIMESTAMP_SEMANTICS,
        timezone=ds.TIMEZONE,
        ordering_status=ds.ORDERING_STATUS_SORTED,
        duplicate_policy=ds.DUPLICATE_POLICY,
        missing_data_policy=ds.MISSING_DATA_POLICY,
    )
    profile_binding = ds.DatasetProfileBindingV1(
        dataset_profile=ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ds.ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=CONSERVATIVE_HALF_SPREAD_BPS,
        ),
        l1_observation_status=ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )
    admissibility = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=frame,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=CANONICAL_INSTRUMENT_ID,
        profile_binding=profile_binding,
    )
    manifest_body: dict[str, Any] = {
        "acquisition_timestamps": {
            "ingestion_timestamp_utc": _utc_now_z(),
            "staging_timestamp_utc": _utc_now_z(),
        },
        "dataset_profile": ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1.value,
        "dataset_schema_version": ds.DATASET_SCHEMA_VERSION,
        "dataset_version": ds.DEFAULT_DATASET_VERSION,
        "instrument_id": CANONICAL_INSTRUMENT_ID,
        "native_instrument_id": EVALUATION_NATIVE_INSTRUMENT_ID,
        "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
        "source_venue": SOURCE_VENUE,
        "contract_type": "perpetual",
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "bar_granularity": "1h",
        "row_count": len(frame),
        "normalized_dataset_digest": dataset_digest,
        "data_period": {
            "start_utc": str(frame.index[0]),
            "end_utc": str(frame.index[-1]),
        },
        "training_period": training,
        "validation_period": validation,
        "out_of_sample_period": oos,
        "execution_cost_binding": {
            "conservative_half_spread_bps": CONSERVATIVE_HALF_SPREAD_BPS,
            "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
            "spread_model_version": "research_conservative_bps_v1",
        },
        "profile_binding": {
            "dataset_profile": ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1.value,
            "l1_observation_status": "EXECUTION_MODEL_BOUND_NOT_OBSERVED",
            "execution_cost_binding": {
                "conservative_half_spread_bps": CONSERVATIVE_HALF_SPREAD_BPS,
                "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
                "spread_model_version": "research_conservative_bps_v1",
            },
        },
        "fee_model_version": "backtest_fee_taker_symmetric_v0",
        "slippage_model_version": "backtest_slippage_symmetric_v0",
        "funding_model_version": "backtest_funding_perpetual_interval_v1",
        "execution_model_version": "backtest_execution_v0",
        "observed_l1_used": False,
        "l1_observation_status": "EXECUTION_MODEL_BOUND_NOT_OBSERVED",
        "integrity_results": {
            "integrity_pass": admissibility.is_admissible(),
            "dataset_admissible": admissibility.is_admissible(),
            "leakage_check_status": admissibility.leakage_check_status,
            "bar_granularity": "1h",
            "data_period": {
                "start_utc": str(frame.index[0]),
                "end_utc": str(frame.index[-1]),
            },
        },
        "provenance": {
            "source_type": "panel_narrow_adapter_v0",
            "source_venue": SOURCE_VENUE,
            "venue_id": SOURCE_VENUE,
            "ingestion_timestamp_utc": _utc_now_z(),
            "staging_timestamp_utc": _utc_now_z(),
            "generation_method": "versioned_final_fleet_panel_narrow_adapter_v0",
            "provenance_ref": str(staging_root / "panel" / "panel_funding_dataset_manifest.json"),
            "native_instrument_id": EVALUATION_NATIVE_INSTRUMENT_ID,
            "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
            "dataset_profile": ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1.value,
            "l1_observation_status": "EXECUTION_MODEL_BOUND_NOT_OBSERVED",
            "observed_l1_used": False,
        },
        "panel_source_binding": {
            "dataset_id": DATASET_ID,
            "dataset_extension_ohlcv": DATASET_EXTENSION_OHLCV,
            "dataset_extension_funding": DATASET_EXTENSION_FUNDING,
            "staging_root": str(staging_root),
            "evaluation_instrument_id": EVALUATION_INSTRUMENT_ID,
            "adapter_kind": "NARROW_ADAPTER_INST_ETH_USDT_PERP_FROM_EXTENDED_CHRONOLOGICAL_V1_PANEL_v0",
        },
    }
    manifest_body["manifest_digest"] = _stable_digest(
        {k: v for k, v in manifest_body.items() if k != "manifest_digest"}
    )
    manifest_path = output_root / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest_body, indent=2, sort_keys=True) + "\n")

    return NarrowDatasetMaterializationV0(
        dataset_root=output_root,
        bars_path=bars_path,
        manifest_path=manifest_path,
        dataset_digest=dataset_digest,
        manifest_digest=str(manifest_body["manifest_digest"]),
        row_count=len(frame),
        bar_granularity="1h",
        training_period=training,
        validation_period=validation,
        out_of_sample_period=oos,
    )


def _build_cost_bindings(step31f_cfg: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    backtest = step31f_cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        backtest = {}
    fee_bps = float(backtest.get("fee_bps", FEE_BPS))
    slippage_bps = float(backtest.get("slippage_bps", SLIPPAGE_BPS))
    if fee_bps <= 0.0 or slippage_bps <= 0.0:
        raise ValueError(REASON_IMPLICIT_ZERO_COST)
    funding = backtest.get("funding") or {}
    if not isinstance(funding, Mapping) or funding.get("bind") is not True:
        raise ValueError(REASON_IMPLICIT_ZERO_COST)
    return {
        "fee_model_binding": {
            "fee_bps": fee_bps,
            "fee_model_version": str(
                backtest.get("fee_model_version", "backtest_fee_taker_symmetric_v0")
            ),
        },
        "slippage_model_binding": {
            "slippage_bps": slippage_bps,
            "slippage_model_version": str(
                backtest.get("slippage_model_version", "backtest_slippage_symmetric_v0")
            ),
        },
        "funding_model_binding": {
            "bind": True,
            "model_version": str(
                funding.get("model_version", "backtest_funding_perpetual_interval_v1")
            ),
        },
        "execution_model_binding": {
            "execution_model_version": "backtest_execution_v0",
            "roundtrip_cost_bps": ROUNDTRIP_COST_BPS,
            "conservative_half_spread_bps": CONSERVATIVE_HALF_SPREAD_BPS,
        },
        "economic_policy_binding": {
            "policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        },
    }


def _build_shared_bindings(
    *,
    panel_binding: PanelMemberBindingV0,
    coverage: FundingCoverageReportV0,
    period_policy: Mapping[str, Any],
    narrow_dataset: NarrowDatasetMaterializationV0,
    funding_manifest_path: Path,
) -> dict[str, Any]:
    period_digest = _stable_digest(
        {
            "dataset_id": DATASET_ID,
            "dataset_extension_funding": DATASET_EXTENSION_FUNDING,
            "period_policy_rel": PERIOD_POLICY_REL,
        }
    )
    dataset_binding = {
        "dataset_binding_active": True,
        "dataset_id": DATASET_ID,
        "dataset_extension_ohlcv": DATASET_EXTENSION_OHLCV,
        "dataset_extension_funding": DATASET_EXTENSION_FUNDING,
        "panel_calendar_start_utc": panel_binding.panel_calendar_start_utc,
        "panel_calendar_end_utc": panel_binding.panel_calendar_end_utc,
        "panel_member_count": panel_binding.panel_member_count,
        "panel_staging_root": panel_binding.staging_root,
        "panel_dataset_manifest_ref": panel_binding.panel_dataset_manifest_path,
        "panel_funding_dataset_manifest_ref": str(funding_manifest_path),
        "funding_coverage_ratio": coverage.coverage_ratio,
        "evaluation_price_data_adapter": {
            "adapter_kind": "NARROW_ADAPTER_INST_ETH_USDT_PERP_FROM_EXTENDED_CHRONOLOGICAL_V1_PANEL_v0",
            "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
            "native_instrument_id": EVALUATION_NATIVE_INSTRUMENT_ID,
            "source_instrument_id": EVALUATION_INSTRUMENT_ID,
            "narrow_dataset_digest": narrow_dataset.dataset_digest,
            "narrow_dataset_root": str(narrow_dataset.dataset_root),
        },
        "network_access_forbidden": True,
    }
    period_binding = {
        "coverage_period_end_utc": period_policy["out_of_sample_end"],
        "coverage_period_start_utc": period_policy.get(
            "coverage_period_start_utc", PANEL_CALENDAR_START_UTC
        ),
        "embargo_duration": period_policy["embargo_duration"],
        "period_binding_id": period_policy["period_binding_id"],
        "period_binding_ref": (
            f"{period_policy['period_binding_id']}:{period_policy['period_binding_version']}"
        ),
        "period_binding_version": period_policy["period_binding_version"],
        "period_digest": period_digest,
        "purge_duration": period_policy["purge_duration"],
        "split_policy_id": period_policy["split_policy_id"],
        "split_policy_version": period_policy["split_policy_version"],
    }
    instrument_binding = {
        "binding_mode": "extended_chronological_v1_panel_member_binding",
        "bitcoin_direction_allowed": False,
        "eligible_instrument_count": panel_binding.panel_member_count,
        "eligible_instrument_ids": list(panel_binding.instrument_ids),
        "eligible_native_instrument_ids": list(panel_binding.native_instrument_ids),
        "evaluation_instrument_id": EVALUATION_INSTRUMENT_ID,
        "evaluation_native_instrument_id": EVALUATION_NATIVE_INSTRUMENT_ID,
        "futures_only": True,
        "instrument_binding_version": "v0",
        "instrument_selection_owner": "bounded_offline_funding_fetch_for_materialized_panel_v0",
        "no_parallel_universe_ssot": True,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "venue_id": "okx",
    }
    return {
        "dataset_binding": dataset_binding,
        "instrument_binding": instrument_binding,
        "period_binding": period_binding,
        "period_split": {
            "boundary_semantics": period_policy["boundary_semantics"],
            "dataset_id": DATASET_ID,
            "embargo_duration": period_policy["embargo_duration"],
            "out_of_sample_end": period_policy["out_of_sample_end"],
            "out_of_sample_start": period_policy["out_of_sample_start"],
            "period_binding_id": period_policy["period_binding_id"],
            "period_binding_version": period_policy["period_binding_version"],
            "period_digest": period_digest,
            "purge_duration": period_policy["purge_duration"],
            "split_policy_id": period_policy["split_policy_id"],
            "split_policy_version": period_policy["split_policy_version"],
            "split_timezone": period_policy["split_timezone"],
            "status": "MATERIALIZED",
            "training_end": period_policy["training_end"],
            "training_start": period_policy["training_start"],
            "validation_end": period_policy["validation_end"],
            "validation_start": period_policy["validation_start"],
        },
    }


def _build_candidate(
    *,
    repo_root: Path,
    strategy_id: str,
    strategy_version: str,
    shared_bindings: Mapping[str, Any],
    period_policy: Mapping[str, Any],
    narrow_dataset: NarrowDatasetMaterializationV0,
    runtime_config_path: Path,
) -> dict[str, Any]:
    template_path = STEP31F_TEMPLATE_CONFIG_PATHS[strategy_id]
    if not (repo_root / template_path).is_file():
        raise FileNotFoundError(f"{REASON_STRATEGY_BINDING_MISSING}:{template_path}")
    cfg = json.loads((repo_root / template_path).read_text(encoding="utf-8"))
    eval_block = cfg.get("economic_evaluation_v1")
    if not isinstance(eval_block, Mapping) or "strategy_params" not in eval_block:
        raise ValueError(f"{REASON_PARAMETER_BINDING_MISSING}:{strategy_id}")
    entry = get_strategy_registry_entry(strategy_id)
    parameter_binding = dict(eval_block["strategy_params"])
    _, strategy_params_digest = resolve_effective_strategy_params_v1(
        strategy_id,
        parameter_binding,
    )
    cost_bindings = _build_cost_bindings(cfg)
    candidate = {
        "binding_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "canonical_candidate_identifier": canonical_candidate_identifier(
            strategy_id, strategy_version
        ),
        "canonical_trading_logic_binding_version": CANONICAL_TRADING_LOGIC_BINDING_VERSION,
        "canonical_trading_logic_version": entry.semantic_digest,
        "config_digest": compute_config_digest_v1(cfg),
        "data_digest": narrow_dataset.dataset_digest,
        "dataset_binding": dict(shared_bindings["dataset_binding"]),
        "dataset_provenance": {
            "cross_branch_evidence_forbidden": True,
            "dataset_id": DATASET_ID,
            "dataset_extension_funding": DATASET_EXTENSION_FUNDING,
            "panel_staging_root": shared_bindings["dataset_binding"]["panel_staging_root"],
            "pit_safe": True,
        },
        "dataset_version": "v1",
        "economic_evaluation_authorized": True,
        "implementation_digest": entry.implementation_digest,
        "instrument_binding": dict(shared_bindings["instrument_binding"]),
        "operator_ratification_ref": SCOPE_CLASSIFICATION,
        "out_of_sample_period": {
            "end": period_policy["out_of_sample_end"],
            "start": period_policy["out_of_sample_start"],
            "status": "MATERIALIZED",
        },
        "parameter_binding": parameter_binding,
        "parameter_schema_version": str(cfg.get("config_schema_version", "")),
        "period_binding": dict(shared_bindings["period_binding"]),
        "period_digest": shared_bindings["period_binding"]["period_digest"],
        "ratified": True,
        "reason_codes": [],
        "reproducibility_metadata": {
            "materialization_module": "versioned_final_fleet_bindings_offline_economic_evaluation_v0",
            "narrow_dataset_digest": narrow_dataset.dataset_digest,
            "period_policy_ref": PERIOD_POLICY_REL,
            "runtime_config_path": str(runtime_config_path),
            "template_config_ref": template_path,
        },
        "source_config_ref": str(runtime_config_path),
        "strategy_id": strategy_id,
        "strategy_params_digest": strategy_params_digest,
        "strategy_version": strategy_version,
        "training_period": {
            "end": period_policy["training_end"],
            "start": period_policy["training_start"],
            "status": "MATERIALIZED",
        },
        "validation_period": {
            "end": period_policy["validation_end"],
            "start": period_policy["validation_start"],
            "status": "MATERIALIZED",
        },
        **cost_bindings,
    }
    candidate["binding_semantic_digest"] = compute_binding_semantic_digest_v0(candidate)
    return candidate


def materialize_binding_completion_v0(
    *,
    repo_root: Path,
    staging_root: Path,
    panel_binding: PanelMemberBindingV0,
    coverage: FundingCoverageReportV0,
    narrow_dataset: NarrowDatasetMaterializationV0,
    runtime_config_paths: Mapping[str, Path],
) -> dict[str, Any]:
    period_policy = _load_period_policy(repo_root)
    funding_manifest_path = staging_root / "panel" / "panel_funding_dataset_manifest.json"
    shared_bindings = _build_shared_bindings(
        panel_binding=panel_binding,
        coverage=coverage,
        period_policy=period_policy,
        narrow_dataset=narrow_dataset,
        funding_manifest_path=funding_manifest_path,
    )
    candidates = [
        _build_candidate(
            repo_root=repo_root,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            shared_bindings=shared_bindings,
            period_policy=period_policy,
            narrow_dataset=narrow_dataset,
            runtime_config_path=runtime_config_paths[strategy_id],
        )
        for strategy_id, strategy_version in FLEET_CANDIDATES
    ]
    completion_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "completion_id": COMPLETION_ID,
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "candidates": candidates,
        "shared_bindings": {
            "dataset_binding": shared_bindings["dataset_binding"],
            "instrument_binding": shared_bindings["instrument_binding"],
            "period_binding": shared_bindings["period_binding"],
            "period_split": shared_bindings["period_split"],
        },
        "excluded_failed_historical_candidates": [
            {"strategy_id": sid, "strategy_version": ver, "retry_forbidden": True}
            for sid, ver in FAILED_HISTORICAL_CANDIDATES
        ],
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "economic_evaluation_authorized": True,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": SPOT_ALLOWED,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        "dataset_binding_active": True,
        "dataset_id": DATASET_ID,
        "dataset_extension_funding": DATASET_EXTENSION_FUNDING,
        "binding_materialization_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "implementation_digest": _stable_digest(
            {"module": "versioned_final_fleet_bindings_offline_economic_evaluation_v0"}
        ),
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": GO_TOKEN,
        "expected_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
    }
    completion_body["completion_digest"] = compute_completion_digest_v0(completion_body)
    return completion_body


def validate_binding_completion_v0(
    completion: Any,
    *,
    repo_root: Path,
) -> BindingValidationResultV0:
    reasons: list[str] = []
    if not isinstance(completion, Mapping):
        return BindingValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=("COMPLETION_NOT_OBJECT",),
        )
    if completion.get("schema_version") != SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    candidates = completion.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(FLEET_CANDIDATES):
        reasons.append(REASON_STRATEGY_BINDING_MISSING)
        candidates = candidates or []
    expected_ids = {canonical_candidate_identifier(s, v) for s, v in FLEET_CANDIDATES}
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            reasons.append("CANDIDATE_NOT_OBJECT")
            continue
        ref = str(candidate.get("canonical_candidate_identifier", ""))
        seen.add(ref)
        if not candidate.get("parameter_binding"):
            reasons.append(f"{REASON_PARAMETER_BINDING_MISSING}:{ref}")
        for digest_field in ("implementation_digest", "config_digest", "data_digest"):
            if not candidate.get(digest_field):
                reasons.append(f"{REASON_BINDING_INCOMPLETE}:{digest_field}:{ref}")
        fee = candidate.get("fee_model_binding")
        slip = candidate.get("slippage_model_binding")
        if isinstance(fee, Mapping) and float(fee.get("fee_bps", 0.0)) <= 0.0:
            reasons.append(f"{REASON_IMPLICIT_ZERO_COST}:fee:{ref}")
        if isinstance(slip, Mapping) and float(slip.get("slippage_bps", 0.0)) <= 0.0:
            reasons.append(f"{REASON_IMPLICIT_ZERO_COST}:slippage:{ref}")
        expected_digest = compute_binding_semantic_digest_v0(candidate)
        if str(candidate.get("binding_semantic_digest", "")) != expected_digest:
            reasons.append(f"{REASON_BINDING_INCOMPLETE}:binding_semantic_digest:{ref}")
    if seen != expected_ids:
        reasons.extend(sorted(expected_ids - seen))
    if len(candidates) >= 2:
        reference = candidates[0]
        for field in (
            "dataset_binding",
            "period_binding",
            "instrument_binding",
            "fee_model_binding",
            "slippage_model_binding",
            "funding_model_binding",
            "execution_model_binding",
            "economic_policy_binding",
        ):
            ref_val = reference.get(field)
            for candidate in candidates[1:]:
                if candidate.get(field) != ref_val:
                    reasons.append(
                        f"{REASON_SHARED_BINDING_MISMATCH}:{field}:{candidate.get('strategy_id')}"
                    )
    expected_completion_digest = compute_completion_digest_v0(completion)
    if str(completion.get("completion_digest", "")) != expected_completion_digest:
        reasons.append(REASON_BINDING_INCOMPLETE)
    verdict = ValidationVerdict.ACCEPTED if not reasons else ValidationVerdict.REJECTED
    return BindingValidationResultV0(
        verdict=verdict,
        valid=verdict is ValidationVerdict.ACCEPTED,
        fail_reasons=tuple(reasons),
    )


def build_runtime_step31f_config_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    narrow_dataset: NarrowDatasetMaterializationV0,
    output_path: Path,
) -> Path:
    template_path = repo_root / STEP31F_TEMPLATE_CONFIG_PATHS[strategy_id]
    cfg = json.loads(template_path.read_text(encoding="utf-8"))
    binding = dict(cfg["real_admissible_futures_evaluation_binding_v1"])
    binding["dataset_path"] = str(narrow_dataset.bars_path)
    binding["dataset_manifest_path"] = str(narrow_dataset.manifest_path)
    binding["expected_dataset_digest"] = narrow_dataset.dataset_digest
    binding["expected_manifest_digest"] = narrow_dataset.manifest_digest
    binding["training_period"] = narrow_dataset.training_period
    binding["validation_period"] = narrow_dataset.validation_period
    binding["out_of_sample_period"] = narrow_dataset.out_of_sample_period
    binding["native_instrument_id"] = EVALUATION_NATIVE_INSTRUMENT_ID
    binding["canonical_instrument_id"] = CANONICAL_INSTRUMENT_ID
    cfg["real_admissible_futures_evaluation_binding_v1"] = binding
    eval_block = cfg.setdefault("economic_evaluation_v1", {})
    if isinstance(eval_block, dict):
        wf = eval_block.setdefault("walk_forward", {})
        if isinstance(wf, dict):
            wf["train_bars"] = 1200
            wf["test_bars"] = 300
            wf["step_bars"] = 300
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path


def _copy_stage_results(
    candidate_dir: Path,
    evidence_root: Path,
    strategy_id: str,
    stage_map: Mapping[str, str],
) -> None:
    for src_name, dest_subdir in stage_map.items():
        src = candidate_dir / src_name
        if src.is_file():
            dest_dir = evidence_root / dest_subdir / strategy_id
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest_dir / src_name)


def _resolve_candidate_decision(result: CandidateExecutionResultV0) -> CandidateDecision:
    if result.terminal_status.value == "PASS":
        return CandidateDecision.PASS
    if result.terminal_status.value == "INCONCLUSIVE":
        return CandidateDecision.INCONCLUSIVE
    return CandidateDecision.FAIL


def _write_evidence_bundle(
    *,
    evidence_root: Path,
    binding_completion: Mapping[str, Any],
    narrow_dataset: NarrowDatasetMaterializationV0,
    panel_binding: PanelMemberBindingV0,
    coverage: FundingCoverageReportV0,
    candidate_results: Sequence[CandidateExecutionResultV0],
    candidate_decisions: Mapping[str, CandidateDecision],
    evaluation_commands: Sequence[str],
    durable_archive_root: Path,
) -> None:
    first = binding_completion["candidates"][0]
    evidence_root.mkdir(parents=True, exist_ok=True)

    scope_lines = [
        "# SCOPE",
        "",
        f"- scope_classification: {SCOPE_CLASSIFICATION}",
        f"- go_token: {GO_TOKEN}",
        f"- expected_origin_main_sha: {EXPECTED_ORIGIN_MAIN_SHA}",
        f"- fleet: {', '.join(f'{s}/{v}' for s, v in FLEET_CANDIDATES)}",
        f"- dataset_id: {DATASET_ID}",
        f"- panel_extension: {DATASET_EXTENSION_OHLCV}",
        f"- funding_extension: {DATASET_EXTENSION_FUNDING}",
        "- offline_only: true",
        "- runtime_run: false",
        "- network_fetch_run: false",
    ]
    (evidence_root / "SCOPE.md").write_text("\n".join(scope_lines) + "\n", encoding="utf-8")

    input_links = ["# INPUT_EVIDENCE_LINKS", ""]
    for label, rel in PRIOR_EVIDENCE_BUNDLES:
        full = durable_archive_root / rel
        input_links.append(f"- {label}: `{full}` (exists={full.is_dir()})")
    (evidence_root / "INPUT_EVIDENCE_LINKS.md").write_text(
        "\n".join(input_links) + "\n",
        encoding="utf-8",
    )

    (evidence_root / "FINAL_FLEET_BINDING.json").write_text(
        json.dumps(binding_completion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    candidate_bindings_dir = evidence_root / "CANDIDATE_BINDINGS"
    candidate_bindings_dir.mkdir(exist_ok=True)
    for candidate in binding_completion["candidates"]:
        sid = str(candidate["strategy_id"])
        (candidate_bindings_dir / f"{sid}_binding.json").write_text(
            json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    (evidence_root / "DATASET_BINDING.json").write_text(
        json.dumps(first["dataset_binding"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    funding_binding = {
        "bind": True,
        "coverage_ratio": coverage.coverage_ratio,
        "funding_model_version": first["funding_model_binding"]["model_version"],
        "funding_panel_manifest": str(
            Path(panel_binding.staging_root) / "panel" / "panel_funding_dataset_manifest.json"
        ),
        "instrument_count": coverage.instrument_count,
        "missing_funding_count": coverage.missing_funding_count,
        "populated_funding_count": coverage.populated_funding_count,
    }
    (evidence_root / "FUNDING_BINDING.json").write_text(
        json.dumps(funding_binding, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    cost_binding = {
        "fee_model_binding": first["fee_model_binding"],
        "slippage_model_binding": first["slippage_model_binding"],
        "funding_model_binding": first["funding_model_binding"],
        "implicit_zero_cost_forbidden": True,
    }
    (evidence_root / "COST_MODEL_BINDING.json").write_text(
        json.dumps(cost_binding, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "EXECUTION_MODEL_BINDING.json").write_text(
        json.dumps(first["execution_model_binding"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "ECONOMIC_POLICY_BINDING.json").write_text(
        json.dumps(first["economic_policy_binding"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "EVALUATION_COMMANDS.txt").write_text(
        "\n\n".join(evaluation_commands) + "\n",
        encoding="utf-8",
    )

    stage_map = {
        "METRICS.json": "BACKTEST_RESULTS",
        "WALK_FORWARD_RESULTS.json": "WALK_FORWARD_RESULTS",
        "MONTE_CARLO_RESULTS.json": "MONTE_CARLO_RESULTS",
        "STRESS_RESULTS.json": "STRESS_RESULTS",
        "PARAMETER_SENSITIVITY_RESULTS.json": "PARAMETER_SENSITIVITY_RESULTS",
        "economic_viability_evidence_v1.json": "ECONOMIC_VIABILITY_EVIDENCE",
    }
    comparison: dict[str, Any] = {}
    for result in candidate_results:
        candidate_dir = Path(result.output_dir)
        _copy_stage_results(candidate_dir, evidence_root, result.strategy_id, stage_map)
        comparison[result.strategy_id] = {
            "terminal_status": result.terminal_status.value,
            "decision": candidate_decisions[result.strategy_id].value,
            "economic_validity_result": result.economic_validity_result,
            "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
            "evidence_status": result.evidence_status,
            "manifest_verify_rc": result.manifest_verify_rc,
            "reason_codes": list(result.reason_codes),
        }
    (evidence_root / "CANDIDATE_COMPARISON_SUMMARY.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    pass_ids = [sid for sid, d in candidate_decisions.items() if d is CandidateDecision.PASS]
    decision_lines = [
        "# PASS_FAIL_INCONCLUSIVE_DECISION",
        "",
        f"- fleet_status: {resolve_fleet_terminal_status_v0(candidate_results).value}",
        f"- pass_candidates: {pass_ids or 'none'}",
        f"- promotion_to_runtime: false",
        f"- result_rescue: false",
        "",
        "## Per candidate",
    ]
    for sid, decision in candidate_decisions.items():
        decision_lines.append(f"- {sid}: {decision.value}")
    (evidence_root / "PASS_FAIL_INCONCLUSIVE_DECISION.md").write_text(
        "\n".join(decision_lines) + "\n",
        encoding="utf-8",
    )

    safety_lines = [
        "# SAFETY_FLAGS",
        "",
        "RUNTIME_RUN=false",
        "SHADOW_RUN=false",
        "PAPER_RUN=false",
        "TESTNET_RUN=false",
        "LIVE_RUN=false",
        "SCHEDULER_RUN=false",
        "CREDENTIALS_USED=false",
        "ORDERS_ALLOWED=false",
        "NETWORK_FETCH_RUN=false",
        "FULL_UNIVERSE_FETCH_RUN=false",
        "PROMOTION_TO_RUNTIME=false",
        "PARAMETER_OPTIMIZATION=false",
        "THRESHOLD_LOWERING=false",
    ]
    (evidence_root / "SAFETY_FLAGS.md").write_text("\n".join(safety_lines) + "\n", encoding="utf-8")


def _run_candidate_with_runtime_config_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    strategy_version: str,
    config_path: Path,
    output_dir: Path,
) -> CandidateExecutionResultV0:
    from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
        CandidateTerminalStatus,
        REASON_CANDIDATE_EVIDENCE_MISSING,
        REASON_CANDIDATE_RUN_FAILED,
        REASON_MANIFEST_VERIFY_FAILED,
        extract_dataset_paths_from_config,
        map_candidate_terminal_status_v0,
    )

    candidate_ref = canonical_candidate_identifier(strategy_id, strategy_version)
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    dataset_path, manifest_path = extract_dataset_paths_from_config(cfg)

    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"output_dir_nonempty:{output_dir}")

    from scripts.ops.run_economic_viability_evidence_evaluation_v1 import (  # noqa: PLC0415
        RunnerError,
        build_arg_parser,
        execute_evaluation,
    )

    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--dataset-path",
            dataset_path,
            "--dataset-manifest-path",
            manifest_path,
            "--config-path",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--allow-existing-output",
            "--json",
        ]
    )
    stage_return_codes: dict[str, int] = {"economic_viability_runner": 0}
    try:
        outcome = execute_evaluation(args)
    except (RunnerError, Exception):
        stage_return_codes["economic_viability_runner"] = 1
        return CandidateExecutionResultV0(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            canonical_candidate_identifier=candidate_ref,
            config_path=str(config_path),
            output_dir=str(output_dir),
            run_id="",
            terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
            economic_validity_result="BLOCKED",
            economic_validity_offline_gate_pass=False,
            evidence_status="",
            manifest_verify_rc=1,
            reason_codes=(REASON_CANDIDATE_RUN_FAILED,),
            stage_return_codes=stage_return_codes,
            runner_execution_success=False,
        )

    if not outcome.runner_execution_success:
        stage_return_codes["economic_viability_runner"] = 1
        return CandidateExecutionResultV0(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            canonical_candidate_identifier=candidate_ref,
            config_path=str(config_path),
            output_dir=str(output_dir),
            run_id=outcome.run_id,
            terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
            economic_validity_result=outcome.economic_validity_result,
            economic_validity_offline_gate_pass=False,
            evidence_status="",
            manifest_verify_rc=outcome.manifest_verify_rc,
            reason_codes=(REASON_CANDIDATE_RUN_FAILED,),
            stage_return_codes=stage_return_codes,
            runner_execution_success=False,
        )

    economic_validity_result = str(outcome.economic_validity_result or "BLOCKED")
    economic_validity_offline_gate_pass = bool(outcome.economic_validity_offline_gate_pass)
    manifest_verify_rc = int(outcome.manifest_verify_rc)
    run_id = outcome.run_id

    from src.backtest.economic_viability_evidence_v1 import (  # noqa: PLC0415
        EconomicViabilityEvidenceError,
        load_economic_viability_evidence_bundle_v1,
    )

    try:
        loaded = load_economic_viability_evidence_bundle_v1(output_dir)
        evidence_status = loaded.evidence.status.value
    except EconomicViabilityEvidenceError:
        return CandidateExecutionResultV0(
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            canonical_candidate_identifier=candidate_ref,
            config_path=str(config_path),
            output_dir=str(output_dir),
            run_id=run_id,
            terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
            economic_validity_result=economic_validity_result,
            economic_validity_offline_gate_pass=False,
            evidence_status="",
            manifest_verify_rc=manifest_verify_rc,
            reason_codes=(REASON_CANDIDATE_EVIDENCE_MISSING,),
            stage_return_codes=stage_return_codes,
            runner_execution_success=False,
        )

    terminal_status = map_candidate_terminal_status_v0(
        runner_execution_success=True,
        economic_validity_result=economic_validity_result,
        economic_validity_offline_gate_pass=economic_validity_offline_gate_pass,
        evidence_status=evidence_status,
    )
    reason_codes: tuple[str, ...] = ()
    if manifest_verify_rc != 0:
        reason_codes = (REASON_MANIFEST_VERIFY_FAILED,)

    return CandidateExecutionResultV0(
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        canonical_candidate_identifier=candidate_ref,
        config_path=str(config_path),
        output_dir=str(output_dir),
        run_id=run_id,
        terminal_status=terminal_status,
        economic_validity_result=economic_validity_result,
        economic_validity_offline_gate_pass=economic_validity_offline_gate_pass,
        evidence_status=evidence_status,
        manifest_verify_rc=manifest_verify_rc,
        reason_codes=reason_codes,
        stage_return_codes=stage_return_codes,
        runner_execution_success=True,
    )


def run_bounded_scope_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    skip_candidate_runs: bool = False,
) -> ScopeExecutionResultV0:
    scope_config = load_scope_config_v0(repo_root)
    staging_root = resolve_staging_root(
        durable_archive_root=durable_evidence_root,
        scope_config=scope_config,
    )
    ok, reasons, panel_binding, coverage = verify_preconditions_v0(
        repo_root=repo_root,
        confirm=confirm,
        staging_root=staging_root,
    )
    if not ok:
        raise ValueError(f"PRECONDITION_FAILED:{reasons}")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_root = (
        durable_evidence_root
        / "research"
        / f"versioned_final_fleet_bindings_offline_economic_evaluation_v0_{ts_slug}"
    )
    narrow_root = evidence_root / "narrow_evaluation_dataset" / "inst-eth-usdt-perp" / "v1"
    period_policy = _load_period_policy(repo_root)
    narrow_dataset = materialize_narrow_evaluation_dataset_v0(
        staging_root=staging_root,
        output_root=narrow_root,
        period_policy=period_policy,
    )

    runtime_config_paths: dict[str, Path] = {}
    config_dir = evidence_root / "RUNTIME_STEP31F_CONFIGS"
    for strategy_id, _strategy_version in FLEET_CANDIDATES:
        runtime_config_paths[strategy_id] = build_runtime_step31f_config_v0(
            repo_root=repo_root,
            strategy_id=strategy_id,
            narrow_dataset=narrow_dataset,
            output_path=config_dir / f"step31f_{strategy_id}_v1_economic_evaluation_v1.json",
        )

    binding_completion = materialize_binding_completion_v0(
        repo_root=repo_root,
        staging_root=staging_root,
        panel_binding=panel_binding,
        coverage=coverage,
        narrow_dataset=narrow_dataset,
        runtime_config_paths=runtime_config_paths,
    )
    validation = validate_binding_completion_v0(binding_completion, repo_root=repo_root)
    if validation.verdict is not ValidationVerdict.ACCEPTED:
        raise ValueError(f"BINDING_VALIDATION_FAILED:{validation.fail_reasons}")

    candidate_results: list[CandidateExecutionResultV0] = []
    evaluation_commands: list[str] = []
    if not skip_candidate_runs:
        for strategy_id, strategy_version in FLEET_CANDIDATES:
            config_path = runtime_config_paths[strategy_id]
            output_dir = evidence_root / "candidates" / f"{strategy_id}_{strategy_version}"
            evaluation_commands.append(
                "\n".join(
                    [
                        f"# {strategy_id}/{strategy_version}",
                        f"python3 scripts/ops/run_economic_viability_evidence_evaluation_v1.py \\",
                        f'  --dataset-path "{narrow_dataset.bars_path}" \\',
                        f'  --dataset-manifest-path "{narrow_dataset.manifest_path}" \\',
                        f'  --config-path "{config_path}" \\',
                        f'  --output-dir "{output_dir}" \\',
                        "  --json",
                    ]
                )
            )
            result = _run_candidate_with_runtime_config_v0(
                repo_root=repo_root,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                config_path=config_path,
                output_dir=output_dir,
            )
            candidate_results.append(result)

    fleet_status = resolve_fleet_terminal_status_v0(candidate_results)
    gate_pass = fleet_status is FleetTerminalStatus.PASS and all(
        r.economic_validity_offline_gate_pass for r in candidate_results
    )
    candidate_decisions = {r.strategy_id: _resolve_candidate_decision(r) for r in candidate_results}

    _write_evidence_bundle(
        evidence_root=evidence_root,
        binding_completion=binding_completion,
        narrow_dataset=narrow_dataset,
        panel_binding=panel_binding,
        coverage=coverage,
        candidate_results=candidate_results,
        candidate_decisions=candidate_decisions,
        evaluation_commands=evaluation_commands,
        durable_archive_root=durable_evidence_root,
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, _msg = retention.finalize_durable_bundle_manifest(evidence_root)
    return ScopeExecutionResultV0(
        binding_completion=binding_completion,
        candidate_results=tuple(candidate_results),
        fleet_status=fleet_status,
        economic_validity_offline_gate_pass=gate_pass,
        manifest_verify_rc=rc,
        evidence_root=evidence_root,
        candidate_decisions=candidate_decisions,
        narrow_dataset=narrow_dataset,
    )


__all__ = [
    "GO_TOKEN",
    "SCOPE_CLASSIFICATION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "DATASET_ID",
    "materialize_binding_completion_v0",
    "validate_binding_completion_v0",
    "run_bounded_scope_v0",
    "ScopeExecutionResultV0",
    "ValidationVerdict",
    "CandidateDecision",
]
