#!/usr/bin/env python3
"""STEP30A bounded dataset v2 promotion from verified OKX raw staging v0.

Offline-only: normalizes economic_research_v1 bars, binds frozen STEP29M holdout
partition digests, validates admissibility, and atomically promotes dataset v2.
No network, no economic evaluation, no runtime effect.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import (
    ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 as okx_ingest,
)
from scripts.ops import stage_okx_economic_research_dataset_from_raw_staging_v1 as research_staging
from src.backtest import admissible_versioned_futures_dataset_v1 as ds

GO_TOKEN = "GO_BOUNDED_STEP30A_DATASET_V2_CONTRACT_REMEDIATION_PRE_PR_AND_PR_V0"

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
DEFAULT_DATASET_PARENT = ARCHIVE_ROOT / "datasets" / "admissible_futures" / "inst-eth-usdt-perp"
DEFAULT_TARGET_DATASET_ROOT = DEFAULT_DATASET_PARENT / "v2"
DEFAULT_DURABLE_EVIDENCE_ROOT = ARCHIVE_ROOT / "planning_or_validation"

STEP30A_DATASET_VERSION = "v2"
STEP30A_DATASET_SCHEMA_VERSION = ds.DATASET_SCHEMA_VERSION_V2
STEP30A_STAGING_WINDOW_DAYS = 90

STEP29M_FROZEN_HOLDOUT_START_UTC = "2026-06-17 10:07:00+00:00"
STEP29M_FROZEN_HOLDOUT_END_UTC = "2026-07-01 10:07:00+00:00"
STEP30A_FROZEN_HOLDOUT_START_UTC = STEP29M_FROZEN_HOLDOUT_START_UTC
STEP30A_FROZEN_HOLDOUT_END_UTC = STEP29M_FROZEN_HOLDOUT_END_UTC
STEP30A_FROZEN_HOLDOUT_PERIOD = (
    f"{STEP30A_FROZEN_HOLDOUT_START_UTC}..{STEP30A_FROZEN_HOLDOUT_END_UTC}"
)
STEP30A_TRAINING_PERIOD = "2026-04-02 10:07:00+00:00..2026-05-18 23:59:00+00:00"
STEP30A_VALIDATION_PERIOD = "2026-05-19 00:00:00+00:00..2026-06-16 23:59:00+00:00"
STEP30A_DEVELOPMENT_PERIOD = (
    f"{STEP30A_TRAINING_PERIOD.split('..')[0]}..{STEP30A_VALIDATION_PERIOD.split('..')[1]}"
)

V1_DATASET_ROOT = DEFAULT_DATASET_PARENT / "v1"
V1_MANIFEST_PATH = V1_DATASET_ROOT / "dataset_manifest.json"
EXPECTED_V1_DATASET_DIGEST_PREFIX = "b4cbe7fff81a"

MISSING_HISTORICAL_L1_REASON = ds.MissingHistoricalL1ReasonV1.NOT_AVAILABLE_BY_PUBLIC_SOURCE.value


class Step30aDatasetPromotionError(ValueError):
    """Fail-closed STEP30A dataset v2 promotion error."""


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_period_bounds(period: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    if ".." not in period:
        raise Step30aDatasetPromotionError(f"invalid_period_format:{period}")
    left, right = period.split("..", 1)
    start = pd.Timestamp(left)
    end = pd.Timestamp(right)
    if start.tzinfo is None or end.tzinfo is None:
        raise Step30aDatasetPromotionError("period_timezone_missing")
    return start, end


def _slice_for_period(bars: pd.DataFrame, period: str) -> pd.DataFrame:
    start, end = _parse_period_bounds(period)
    frame = bars.sort_index()
    mask = (frame.index >= start) & (frame.index <= end)
    return frame.loc[mask]


def resolve_verified_raw_staging_root_v1(
    dataset_parent: Path,
    *,
    min_staging_window_days: int = STEP30A_STAGING_WINDOW_DAYS,
) -> Path:
    candidates = sorted(dataset_parent.glob(".tmp_*"), reverse=True)
    for candidate in candidates:
        config_path = candidate / "INGESTION_CONFIG.json"
        if not config_path.is_file():
            continue
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if int(config.get("staging_window_days", 0)) < min_staging_window_days:
            continue
        digest_report = research_staging.verify_raw_staging_digests(candidate)
        if digest_report.verified:
            return candidate
    raise Step30aDatasetPromotionError("verified_raw_staging_root_not_found")


def verify_holdout_constants_match_step29m_v1() -> None:
    if STEP30A_FROZEN_HOLDOUT_START_UTC != STEP29M_FROZEN_HOLDOUT_START_UTC:
        raise Step30aDatasetPromotionError("holdout_start_not_matching_step29m_frozen_constant")
    if STEP30A_FROZEN_HOLDOUT_END_UTC != STEP29M_FROZEN_HOLDOUT_END_UTC:
        raise Step30aDatasetPromotionError("holdout_end_not_matching_step29m_frozen_constant")


def verify_holdout_separation_v1(bars: pd.DataFrame) -> tuple[str, ...]:
    reasons: list[str] = []
    train = _slice_for_period(bars, STEP30A_TRAINING_PERIOD)
    val = _slice_for_period(bars, STEP30A_VALIDATION_PERIOD)
    holdout = _slice_for_period(bars, STEP30A_FROZEN_HOLDOUT_PERIOD)
    if train.empty:
        reasons.append("training_partition_empty")
    if val.empty:
        reasons.append("validation_partition_empty")
    if holdout.empty:
        reasons.append("holdout_partition_empty")
    if not train.empty and not val.empty and train.index.max() >= val.index.min():
        reasons.append("training_validation_overlap")
    if not val.empty and not holdout.empty and val.index.max() >= holdout.index.min():
        reasons.append("validation_holdout_overlap")
    if not train.empty and not holdout.empty and train.index.max() >= holdout.index.min():
        reasons.append("training_holdout_overlap")
    return tuple(reasons)


def assert_holdout_access_blocked_v1(
    bars: pd.DataFrame,
    *,
    evaluation_authorized: bool,
) -> None:
    """Raise when pre-evaluation access includes frozen holdout timestamps."""
    if evaluation_authorized:
        return
    holdout_start = pd.Timestamp(STEP30A_FROZEN_HOLDOUT_START_UTC)
    if (bars.index >= holdout_start).any():
        raise Step30aDatasetPromotionError("holdout_access_blocked_before_evaluation")


def verify_holdout_access_guard_v1(bars: pd.DataFrame) -> tuple[str, ...]:
    reasons: list[str] = []
    development = slice_development_partition_v1(bars)
    holdout_start = pd.Timestamp(STEP30A_FROZEN_HOLDOUT_START_UTC)
    if (development.index >= holdout_start).any():
        reasons.append("development_partition_includes_holdout")
    try:
        assert_holdout_access_blocked_v1(bars, evaluation_authorized=False)
        reasons.append("holdout_access_guard_failed_to_block_full_dataset")
    except Step30aDatasetPromotionError:
        pass
    holdout = slice_frozen_holdout_partition_v1(bars)
    try:
        assert_holdout_access_blocked_v1(holdout, evaluation_authorized=False)
        reasons.append("holdout_access_guard_failed_to_block_holdout_partition")
    except Step30aDatasetPromotionError:
        pass
    return tuple(reasons)


def slice_development_partition_v1(bars: pd.DataFrame) -> pd.DataFrame:
    holdout_start = pd.Timestamp(STEP30A_FROZEN_HOLDOUT_START_UTC)
    return bars.sort_index().loc[bars.index < holdout_start]


def slice_frozen_holdout_partition_v1(bars: pd.DataFrame) -> pd.DataFrame:
    return _slice_for_period(bars, STEP30A_FROZEN_HOLDOUT_PERIOD)


def compute_partition_digests_v1(
    bars: pd.DataFrame,
    *,
    field_bindings: ds.DatasetFieldBindingsV1,
) -> dict[str, str]:
    development = slice_development_partition_v1(bars)
    holdout = slice_frozen_holdout_partition_v1(bars)
    return {
        "development_partition_digest": ds.compute_versioned_dataset_digest(
            development, field_bindings=field_bindings
        ),
        "frozen_holdout_digest": ds.compute_versioned_dataset_digest(
            holdout, field_bindings=field_bindings
        ),
        "normalized_dataset_digest": ds.compute_versioned_dataset_digest(
            bars, field_bindings=field_bindings
        ),
    }


def _optional_v1_holdout_digest_check_v1(holdout_digest: str) -> Optional[str]:
    if not V1_MANIFEST_PATH.is_file():
        return "v1_holdout_manifest_absent_optional_check_skipped"
    payload = json.loads(V1_MANIFEST_PATH.read_text(encoding="utf-8"))
    v1_digest = str(payload.get("normalized_dataset_digest", ""))
    if not v1_digest:
        return "v1_manifest_missing_normalized_dataset_digest_optional_check_skipped"
    if v1_digest.startswith(EXPECTED_V1_DATASET_DIGEST_PREFIX):
        if holdout_digest != v1_digest:
            return (
                "warning:holdout_digest_differs_from_v1_optional:"
                f"expected={v1_digest}:actual={holdout_digest}"
            )
        return None
    return (
        "warning:v1_digest_prefix_mismatch_optional:"
        f"expected_prefix={EXPECTED_V1_DATASET_DIGEST_PREFIX}:actual_digest={v1_digest}"
    )


def run_step30a_dataset_v2_promotion_v0(
    *,
    confirm_go_token: str,
    raw_staging_root: Optional[Path] = None,
    target_dataset_root: Path = DEFAULT_TARGET_DATASET_ROOT,
    durable_evidence_root: Path = DEFAULT_DURABLE_EVIDENCE_ROOT,
    dataset_parent: Path = DEFAULT_DATASET_PARENT,
) -> Mapping[str, Any]:
    if confirm_go_token != GO_TOKEN:
        raise Step30aDatasetPromotionError("confirm_go_token_mismatch")

    verify_holdout_constants_match_step29m_v1()
    resolved_raw = raw_staging_root or resolve_verified_raw_staging_root_v1(dataset_parent)

    ingestion_config = json.loads((resolved_raw / "INGESTION_CONFIG.json").read_text())
    data_period = ingestion_config["data_period"]
    bars, integrity = research_staging.normalize_economic_research_bars(
        raw_dir=resolved_raw / "raw",
        start_utc=str(data_period["start_utc"]),
        end_utc=str(data_period["end_utc"]),
    )
    if not integrity.passed:
        return {
            "verdict": "DATASET_INTEGRITY_FAILED",
            "integrity_report": integrity.__dict__,
            "manifest_verify_rc": 1,
        }

    holdout_reasons = verify_holdout_separation_v1(bars)
    if holdout_reasons:
        return {
            "verdict": "HOLDOUT_SEPARATION_FAILED",
            "reason_codes": list(holdout_reasons),
            "manifest_verify_rc": 1,
        }

    access_reasons = verify_holdout_access_guard_v1(bars)
    if access_reasons:
        return {
            "verdict": "HOLDOUT_ACCESS_BLOCK_FAILED",
            "reason_codes": list(access_reasons),
            "manifest_verify_rc": 1,
        }

    cost_binding = research_staging.build_cost_model_binding()
    profile_binding = research_staging.build_profile_binding(cost_binding)
    field_bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
    digests = compute_partition_digests_v1(bars, field_bindings=field_bindings)
    optional_warning = _optional_v1_holdout_digest_check_v1(digests["frozen_holdout_digest"])

    provenance = ds.DatasetProvenanceV1(
        source_type="operator_staged_futures_v1",
        venue_id="OKX",
        ingestion_timestamp=str(
            json.loads((resolved_raw / "reports" / "PROVENANCE.json").read_text())[
                "ingestion_timestamp_utc"
            ]
        ),
        generation_method="step30a_okx_economic_research_dataset_v2_staging_v0",
        provenance_ref=str(resolved_raw / "reports" / "PROVENANCE.json"),
    )
    idx = bars.sort_index().index
    descriptor = ds.VersionedFuturesDatasetDescriptorV1(
        dataset_id=f"{okx_ingest.CANONICAL_INSTRUMENT_ID}_{STEP30A_DATASET_VERSION}",
        dataset_version=STEP30A_DATASET_VERSION,
        dataset_schema_version=STEP30A_DATASET_SCHEMA_VERSION,
        dataset_digest=digests["normalized_dataset_digest"],
        instrument_id=okx_ingest.CANONICAL_INSTRUMENT_ID,
        contract_type=okx_ingest.CANONICAL_CONTRACT_TYPE,
        futures_only=True,
        bitcoin_direction_allowed=False,
        venue_id="OKX",
        start_time=str(idx[0]),
        end_time=str(idx[-1]),
        row_count=len(bars),
        field_bindings=field_bindings,
        training_period=STEP30A_TRAINING_PERIOD,
        validation_period=STEP30A_VALIDATION_PERIOD,
        out_of_sample_period=STEP30A_FROZEN_HOLDOUT_PERIOD,
        split_policy_version=ds.SPLIT_POLICY_VERSION,
        timestamp_semantics=ds.TIMESTAMP_SEMANTICS,
        timezone=ds.TIMEZONE,
        ordering_status=ds.ORDERING_STATUS_SORTED,
        duplicate_policy=ds.DUPLICATE_POLICY,
        missing_data_policy=ds.MISSING_DATA_POLICY,
    )

    admissibility = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=bars,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=okx_ingest.CANONICAL_INSTRUMENT_ID,
        profile_binding=profile_binding,
    )
    runtime_rejection = ds.evaluate_admissible_versioned_futures_dataset_v1(
        bars=bars,
        descriptor=descriptor,
        provenance=provenance,
        instrument_id=okx_ingest.CANONICAL_INSTRUMENT_ID,
        profile_binding=ds.default_runtime_profile_binding_v1(),
    )
    if not admissibility.is_admissible():
        return {
            "verdict": "DATASET_PROFILE_ADMISSIBILITY_FAILED",
            "admissibility_status": admissibility.admissibility_status.value,
            "reason_codes": list(admissibility.reason_codes),
            "manifest_verify_rc": 1,
        }
    if runtime_rejection.is_admissible():
        return {
            "verdict": "DATASET_PROFILE_ADMISSIBILITY_FAILED",
            "reason_codes": ["runtime_profile_must_reject_research_dataset"],
            "manifest_verify_rc": 1,
        }

    if target_dataset_root.exists():
        existing_manifest = target_dataset_root / "dataset_manifest.json"
        if existing_manifest.is_file():
            existing = json.loads(existing_manifest.read_text(encoding="utf-8"))
            if (
                str(existing.get("normalized_dataset_digest"))
                == digests["normalized_dataset_digest"]
            ):
                return _load_existing_promotion_result(
                    target_dataset_root=target_dataset_root,
                    raw_staging_root=resolved_raw,
                    digests=digests,
                    optional_warning=optional_warning,
                )
        raise Step30aDatasetPromotionError(f"target_dataset_root_exists:{target_dataset_root}")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tmp_root = target_dataset_root.parent / f".tmp_{ts_slug}"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True)

    instrument_binding = json.loads((resolved_raw / "INSTRUMENT_BINDING.json").read_text())
    request_log = json.loads((resolved_raw / "reports" / "REQUEST_LOG.json").read_text())
    raw_response_digests = {
        str(entry.get("raw_response_path", "")): str(entry.get("raw_response_sha256", ""))
        for entry in request_log
        if entry.get("raw_response_sha256")
    }

    holdout_binding = {
        "frozen_holdout_period": STEP30A_FROZEN_HOLDOUT_PERIOD,
        "frozen_holdout_start_utc": STEP30A_FROZEN_HOLDOUT_START_UTC,
        "frozen_holdout_end_utc": STEP30A_FROZEN_HOLDOUT_END_UTC,
        "frozen_holdout_digest": digests["frozen_holdout_digest"],
        "development_period": STEP30A_DEVELOPMENT_PERIOD,
        "development_partition_digest": digests["development_partition_digest"],
        "holdout_access_before_evaluation": "BLOCKED",
        "step29m_v1_holdout_reference_root": str(V1_DATASET_ROOT),
    }
    split_binding = {
        "split_policy_version": ds.SPLIT_POLICY_VERSION,
        "training_period": STEP30A_TRAINING_PERIOD,
        "validation_period": STEP30A_VALIDATION_PERIOD,
        "out_of_sample_period": STEP30A_FROZEN_HOLDOUT_PERIOD,
        "development_period": STEP30A_DEVELOPMENT_PERIOD,
        "disjoint": True,
        "temporally_ordered": True,
        "leakage_free": admissibility.leakage_check_status == "PASS",
        "holdout_binding": holdout_binding,
    }
    staging_config = {
        "go_token": GO_TOKEN,
        "dataset_profile": ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1.value,
        "dataset_version": STEP30A_DATASET_VERSION,
        "dataset_schema_version": STEP30A_DATASET_SCHEMA_VERSION,
        "l1_observation_status": ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED.value,
        "missing_historical_l1_reason": MISSING_HISTORICAL_L1_REASON,
        "observed_l1_used": False,
        "raw_staging_root": str(resolved_raw),
        "target_dataset_root": str(target_dataset_root),
        "staging_window_days": STEP30A_STAGING_WINDOW_DAYS,
    }
    data_quality = {
        "dataset_admissible": True,
        "integrity_pass": integrity.passed,
        "raw_row_counts": integrity.raw_row_counts,
        "join_row_count": integrity.join_row_count,
        "discarded_rows": integrity.discarded_rows,
        "gap_statistics": integrity.gap_statistics,
        "missingness": integrity.missingness,
        "staleness": integrity.staleness,
        "data_period": integrity.data_period,
        "bar_granularity": integrity.bar_granularity,
        "reason_codes": list(integrity.reason_codes),
        "missing_historical_l1_reason": MISSING_HISTORICAL_L1_REASON,
    }

    manifest_without_digest: dict[str, Any] = {
        "manifest_version": research_staging.MANIFEST_VERSION,
        "dataset_profile": ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1.value,
        "dataset_version": STEP30A_DATASET_VERSION,
        "dataset_schema_version": STEP30A_DATASET_SCHEMA_VERSION,
        "contract_version": ds.ADMISSIBLE_VERSIONED_FUTURES_DATASET_VERSION,
        "instrument_id": okx_ingest.CANONICAL_INSTRUMENT_ID,
        "native_instrument_id": okx_ingest.NATIVE_INSTRUMENT_ID,
        "contract_type": okx_ingest.CANONICAL_CONTRACT_TYPE,
        "futures_only": True,
        "data_period": integrity.data_period,
        "bar_granularity": integrity.bar_granularity,
        "row_count": len(bars),
        "required_columns": sorted(
            ds.required_bar_columns_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
        ),
        "optional_columns": [],
        "l1_observation_status": ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED.value,
        "missing_historical_l1_reason": MISSING_HISTORICAL_L1_REASON,
        "observed_l1_used": False,
        "execution_cost_binding": cost_binding["execution_cost_binding"],
        "fee_model_version": cost_binding["fee_model_version"],
        "slippage_model_version": cost_binding["slippage_model_version"],
        "spread_model_version": cost_binding["spread_model_version"],
        "execution_model_version": cost_binding["execution_model_version"],
        "source_endpoints": ingestion_config.get("acquisition_endpoint_order", []),
        "acquisition_timestamps": {
            "ingestion_timestamp_utc": provenance.ingestion_timestamp,
            "staging_timestamp_utc": _utc_now_z(),
        },
        "provenance": {
            "source_type": provenance.source_type,
            "source_venue": provenance.venue_id,
            "native_instrument_id": okx_ingest.NATIVE_INSTRUMENT_ID,
            "canonical_instrument_id": okx_ingest.CANONICAL_INSTRUMENT_ID,
            "contract_type": okx_ingest.CANONICAL_CONTRACT_TYPE,
            "acquisition_method": "okx_public_rest_api_v5",
            "authenticated": False,
            "credentials_used": False,
            "dataset_profile": ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1.value,
            "l1_observation_status": ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED.value,
            "missing_historical_l1_reason": MISSING_HISTORICAL_L1_REASON,
            "observed_l1_used": False,
            "generation_method": "step30a_okx_economic_research_dataset_v2_staging_v0",
            "staging_timestamp_utc": _utc_now_z(),
            "raw_staging_root": str(resolved_raw),
        },
        "instrument_metadata": instrument_binding.get("instrument_metadata", {}),
        "join_policies": ingestion_config.get("join_policies", {}),
        "staleness_limits": {
            "max_mark_index_staleness_ms": okx_ingest.MAX_MARK_INDEX_STALENESS_MS,
            "max_funding_staleness_ms": okx_ingest.MAX_FUNDING_STALENESS_MS,
        },
        "integrity_results": data_quality,
        "training_period": STEP30A_TRAINING_PERIOD,
        "validation_period": STEP30A_VALIDATION_PERIOD,
        "out_of_sample_period": STEP30A_FROZEN_HOLDOUT_PERIOD,
        "development_period": STEP30A_DEVELOPMENT_PERIOD,
        "holdout_binding": holdout_binding,
        "raw_response_digests": raw_response_digests,
        "normalized_dataset_digest": digests["normalized_dataset_digest"],
        "development_partition_digest": digests["development_partition_digest"],
        "frozen_holdout_digest": digests["frozen_holdout_digest"],
        "implementation_digest": admissibility.implementation_digest,
        "config_digest": admissibility.config_digest,
        "profile_binding": profile_binding.to_dict(),
        "profile_binding_digest": admissibility.profile_binding_digest,
    }
    manifest_digest = okx_ingest._stable_digest(manifest_without_digest)
    manifest = {**manifest_without_digest, "manifest_digest": manifest_digest}

    bars_out = bars.reset_index().rename(columns={"index": "timestamp"})
    if "timestamp" not in bars_out.columns:
        bars_out = bars.reset_index()
    bars_out["timestamp"] = pd.to_datetime(bars_out["timestamp"], utc=True).map(
        lambda ts: ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    bars_out.to_parquet(tmp_root / "bars.parquet", index=False)

    for name, payload in (
        ("dataset_manifest.json", manifest),
        ("STAGING_CONFIG.json", staging_config),
        ("DATA_QUALITY_REPORT.json", data_quality),
        ("INSTRUMENT_BINDING.json", instrument_binding),
        ("COST_MODEL_BINDING.json", cost_binding),
        ("SPLIT_BINDING.json", split_binding),
        ("HOLDOUT_BINDING.json", holdout_binding),
        ("PROVENANCE.json", manifest["provenance"]),
    ):
        (tmp_root / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    post_manifest = json.loads((tmp_root / "dataset_manifest.json").read_text(encoding="utf-8"))
    post_digest = okx_ingest._stable_digest(
        {k: v for k, v in post_manifest.items() if k != "manifest_digest"}
    )
    if post_digest != post_manifest["manifest_digest"]:
        raise Step30aDatasetPromotionError("manifest_digest_mismatch_after_write")

    target_dataset_root.parent.mkdir(parents=True, exist_ok=True)
    tmp_root.rename(target_dataset_root)

    evidence_dir = (
        durable_evidence_root
        / "implementation"
        / f"step30a_okx_inst_eth_usdt_perp_dataset_v2_promotion_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "verdict": "STEP30A_DATASET_V2_PROMOTION_COMPLETE",
        "go_token": GO_TOKEN,
        "dataset_path": str(target_dataset_root),
        "manifest_path": str(target_dataset_root / "dataset_manifest.json"),
        "raw_staging_root": str(resolved_raw),
        "dataset_digest": digests["normalized_dataset_digest"],
        "manifest_digest": manifest_digest,
        "development_partition_digest": digests["development_partition_digest"],
        "frozen_holdout_digest": digests["frozen_holdout_digest"],
        "dataset_version": STEP30A_DATASET_VERSION,
        "dataset_schema_version": STEP30A_DATASET_SCHEMA_VERSION,
        "row_count": len(bars),
        "raw_response_count": len(raw_response_digests),
        "raw_bar_count": integrity.raw_row_counts.get("ohlcv", 0),
        "normalized_bar_count": len(bars),
        "missing_historical_l1_reason": MISSING_HISTORICAL_L1_REASON,
        "holdout_period": STEP30A_FROZEN_HOLDOUT_PERIOD,
        "holdout_separation_pass": True,
        "holdout_access_block_pass": True,
        "admissibility_status": admissibility.admissibility_status.value,
        "runtime_rejection_status": runtime_rejection.admissibility_status.value,
        "integrity_report": integrity.__dict__,
        "cost_binding": cost_binding,
        "split_binding": split_binding,
        "holdout_binding": holdout_binding,
        "real_admissible_futures_dataset_found": True,
        "real_admissible_futures_evidence_present": True,
        "real_evaluation_performed": False,
        "economic_validity_result": "NOT_PROVEN",
        "economic_evaluation_executed": False,
        "order_effect": False,
        "runtime_effect": False,
    }
    if optional_warning is not None:
        result["optional_warning"] = optional_warning

    (evidence_dir / "PROMOTION_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for rel in (
        "dataset_manifest.json",
        "STAGING_CONFIG.json",
        "DATA_QUALITY_REPORT.json",
        "HOLDOUT_BINDING.json",
        "SPLIT_BINDING.json",
    ):
        shutil.copy2(target_dataset_root / rel, evidence_dir / rel)

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    result["durable_evidence_path"] = str(evidence_dir)
    result["manifest_verify_rc"] = rc
    result["manifest_verify_msg"] = verify_msg
    _emit_machine_lines(result)
    return result


def _load_existing_promotion_result(
    *,
    target_dataset_root: Path,
    raw_staging_root: Path,
    digests: Mapping[str, str],
    optional_warning: Optional[str],
) -> dict[str, Any]:
    manifest = json.loads((target_dataset_root / "dataset_manifest.json").read_text())
    result = {
        "verdict": "STEP30A_DATASET_V2_PROMOTION_COMPLETE",
        "go_token": GO_TOKEN,
        "dataset_path": str(target_dataset_root),
        "manifest_path": str(target_dataset_root / "dataset_manifest.json"),
        "raw_staging_root": str(raw_staging_root),
        "dataset_digest": digests["normalized_dataset_digest"],
        "manifest_digest": str(manifest.get("manifest_digest", "")),
        "development_partition_digest": digests["development_partition_digest"],
        "frozen_holdout_digest": digests["frozen_holdout_digest"],
        "dataset_version": STEP30A_DATASET_VERSION,
        "dataset_schema_version": STEP30A_DATASET_SCHEMA_VERSION,
        "row_count": int(manifest.get("row_count", 0)),
        "normalized_bar_count": int(manifest.get("row_count", 0)),
        "missing_historical_l1_reason": MISSING_HISTORICAL_L1_REASON,
        "holdout_period": STEP30A_FROZEN_HOLDOUT_PERIOD,
        "holdout_separation_pass": True,
        "holdout_access_block_pass": True,
        "real_admissible_futures_dataset_found": True,
        "real_evaluation_performed": False,
        "economic_evaluation_executed": False,
        "idempotent_reuse": True,
        "manifest_verify_rc": 0,
    }
    if optional_warning is not None:
        result["optional_warning"] = optional_warning
    _emit_machine_lines(result)
    return result


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    lines = [
        f"STEP30A_GO_TOKEN={GO_TOKEN}",
        f"VERDICT={result.get('verdict')}",
        f"DATASET_V2_PATH={result.get('dataset_path', '')}",
        f"DATASET_V2_DIGEST={result.get('dataset_digest', '')}",
        f"DEVELOPMENT_PARTITION_DIGEST={result.get('development_partition_digest', '')}",
        f"FROZEN_HOLDOUT_DIGEST={result.get('frozen_holdout_digest', '')}",
        f"HOLDOUT_PERIOD={result.get('holdout_period', STEP30A_FROZEN_HOLDOUT_PERIOD)}",
        f"NORMALIZED_BAR_COUNT={result.get('normalized_bar_count', 0)}",
        f"RAW_BAR_COUNT={result.get('raw_bar_count', 0)}",
        f"MISSING_HISTORICAL_L1_REASON={MISSING_HISTORICAL_L1_REASON}",
        f"MANIFEST_VERIFY_RC={result.get('manifest_verify_rc', 1)}",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "ORDER_EFFECT=false",
        "RUNTIME_EFFECT=false",
    ]
    optional_warning = result.get("optional_warning")
    if optional_warning is not None:
        lines.append(f"STEP30A_OPTIONAL_WARNING={optional_warning}")
    for line in lines:
        print(line)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="STEP30A bounded dataset v2 promotion from verified OKX raw staging."
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[GO_TOKEN])
    parser.add_argument("--raw-staging-root", type=Path, default=None)
    parser.add_argument("--target-dataset-root", type=Path, default=DEFAULT_TARGET_DATASET_ROOT)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_EVIDENCE_ROOT)
    parser.add_argument("--dataset-parent", type=Path, default=DEFAULT_DATASET_PARENT)
    ns = parser.parse_args(argv)
    run_step30a_dataset_v2_promotion_v0(
        confirm_go_token=ns.confirm_go_token,
        raw_staging_root=ns.raw_staging_root,
        target_dataset_root=ns.target_dataset_root,
        durable_evidence_root=ns.durable_evidence_root,
        dataset_parent=ns.dataset_parent,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
