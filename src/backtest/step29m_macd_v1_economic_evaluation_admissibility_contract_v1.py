"""
STEP 29M macd v1 economic evaluation admissibility contract v1.

Read-only contract diagnostics: strategy identity, parameter binding, dataset
compatibility, signal admissibility, split/warmup semantics, and staged
evaluation config readiness. No economic evaluation execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

import pandas as pd

from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.backtest.strategy_signal_binding_v1 import (
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    MV2_REPLAY_SIGNAL_SOURCE,
    SignalAlignmentStatus,
    SignalContractStatus,
    StrategyExecutionStatus,
    StrategySignalBindingError,
    assert_engine_signal_provenance_consistency_v1,
    collect_configured_strategy_params_v1,
    compute_required_warmup_rows_v1,
    compute_strategy_signal_digest_v1,
    execute_configured_strategy_signal_series_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

CONTRACT_LAYER_VERSION = "v1"
CONTRACT_OWNER = "backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1"

MACD_V1_STRATEGY_ID = "macd"
MACD_V1_STRATEGY_VERSION = "v1"
MACD_V1_STRATEGY_OWNER = "src.strategies.macd.MACDStrategy"
MACD_V1_CANONICAL_PARAMS = {
    "fast_ema": 12,
    "slow_ema": 26,
    "signal_ema": 9,
}

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
DATASET_ROOT = ARCHIVE_ROOT / "datasets/admissible_futures/inst-eth-usdt-perp/v1"
DATASET_BARS_PATH = DATASET_ROOT / "bars.parquet"
DATASET_MANIFEST_PATH = DATASET_ROOT / "dataset_manifest.json"
EXPECTED_DATASET_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
EXPECTED_MANIFEST_DIGEST = "317105798c749943074911b1e9ea91ac9b94fab3b115fb7a64b692339426651a"

TRAINING_PERIOD = "2026-06-17 16:00:00+00:00..2026-06-24 13:03:00+00:00"
VALIDATION_PERIOD = "2026-06-24 13:04:00+00:00..2026-06-27 23:35:00+00:00"
OUT_OF_SAMPLE_PERIOD = "2026-06-27 23:36:00+00:00..2026-07-01 10:07:00+00:00"

SPLIT_WARMUP_SEMANTICS = "CAUSAL_FULL_SERIES_THEN_SLICE_POLICY_A"

DEFAULT_EVALUATION_CONFIG_PATH = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v1.json"
)


class AdmissibilityResult(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class MacdV1SignalDiagnosticV1:
    dataset_rows: int
    required_warmup_rows: int
    valid_rows_after_warmup: int
    signal_min_value: int
    signal_max_value: int
    flat_signal_count: int
    long_signal_count: int
    short_signal_count: int
    signal_transition_count: int
    first_valid_signal_timestamp: str
    last_valid_signal_timestamp: str
    signal_digest: str
    index_alignment_status: str
    signal_contract_status: str
    determinism_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_rows": self.dataset_rows,
            "required_warmup_rows": self.required_warmup_rows,
            "valid_rows_after_warmup": self.valid_rows_after_warmup,
            "signal_min_value": self.signal_min_value,
            "signal_max_value": self.signal_max_value,
            "flat_signal_count": self.flat_signal_count,
            "long_signal_count": self.long_signal_count,
            "short_signal_count": self.short_signal_count,
            "signal_transition_count": self.signal_transition_count,
            "first_valid_signal_timestamp": self.first_valid_signal_timestamp,
            "last_valid_signal_timestamp": self.last_valid_signal_timestamp,
            "signal_digest": self.signal_digest,
            "index_alignment_status": self.index_alignment_status,
            "signal_contract_status": self.signal_contract_status,
            "determinism_status": self.determinism_status,
        }


@dataclass(frozen=True)
class MacdV1ProvenanceContractV1:
    configured_strategy_execution_contract: str
    signal_provenance_contract: str
    engine_signal_binding_contract: str
    mv2_diagnostic_separation_contract: str

    def to_dict(self) -> dict[str, str]:
        return {
            "configured_strategy_execution_contract": (self.configured_strategy_execution_contract),
            "signal_provenance_contract": self.signal_provenance_contract,
            "engine_signal_binding_contract": self.engine_signal_binding_contract,
            "mv2_diagnostic_separation_contract": self.mv2_diagnostic_separation_contract,
        }


@dataclass(frozen=True)
class MacdV1AdmissibilityContractResultV1:
    admissibility_result: AdmissibilityResult
    blocking_reasons: tuple[str, ...]
    strategy_id: str
    strategy_version: str
    strategy_owner: str
    configured_strategy_params: dict[str, Any]
    effective_strategy_params: dict[str, Any]
    strategy_params_digest: str
    signal_diagnostic: Optional[MacdV1SignalDiagnosticV1]
    provenance_contract: Optional[MacdV1ProvenanceContractV1]
    split_warmup_semantics: str
    leakage_status: str
    evaluation_config_path: str
    config_digest: str
    cost_binding_status: str

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "admissibility_result": self.admissibility_result.value,
            "blocking_reasons": list(self.blocking_reasons),
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "strategy_owner": self.strategy_owner,
            "configured_strategy_params": self.configured_strategy_params,
            "effective_strategy_params": self.effective_strategy_params,
            "strategy_params_digest": self.strategy_params_digest,
            "split_warmup_semantics": self.split_warmup_semantics,
            "leakage_status": self.leakage_status,
            "evaluation_config_path": self.evaluation_config_path,
            "config_digest": self.config_digest,
            "cost_binding_status": self.cost_binding_status,
        }
        if self.signal_diagnostic is not None:
            payload["signal_diagnostic"] = self.signal_diagnostic.to_dict()
        if self.provenance_contract is not None:
            payload["provenance_contract"] = self.provenance_contract.to_dict()
        return payload


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_evaluation_config_digest_v1(cfg: Mapping[str, Any]) -> str:
    return _stable_digest(cfg)


def load_macd_v1_evaluation_config_v1(
    repo_root: Path,
    config_path: Optional[str] = None,
) -> dict[str, Any]:
    rel = config_path or DEFAULT_EVALUATION_CONFIG_PATH
    path = repo_root / rel
    if not path.is_file():
        raise FileNotFoundError(f"evaluation_config_not_found:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evaluation_config_not_object")
    return payload


def load_admissible_okx_eth_bars_v1() -> pd.DataFrame:
    if not DATASET_BARS_PATH.is_file():
        raise FileNotFoundError(f"dataset_bars_missing:{DATASET_BARS_PATH}")
    bars = pd.read_parquet(DATASET_BARS_PATH)
    if "timestamp" in bars.columns:
        bars = bars.set_index("timestamp")
    bars.index = pd.to_datetime(bars.index, utc=True)
    return bars.sort_index()


def verify_macd_v1_strategy_identity_v1() -> tuple[str, ...]:
    reasons: list[str] = []
    resolution = resolve_strategy_id(MACD_V1_STRATEGY_ID)
    if resolution.canonical_strategy_id != MACD_V1_STRATEGY_ID:
        reasons.append("strategy_id_not_canonical")
    entry = get_strategy_registry_entry(MACD_V1_STRATEGY_ID)
    if entry.strategy_version != MACD_V1_STRATEGY_VERSION:
        reasons.append("strategy_version_mismatch")
    if entry.implementation_ref != MACD_V1_STRATEGY_OWNER:
        reasons.append("strategy_owner_mismatch")
    if not entry.futures_compatible:
        reasons.append("strategy_not_futures_compatible")
    if entry.spot_compatible:
        reasons.append("strategy_spot_compatible_true")
    if "btc" in entry.strategy_id.lower() or "xbt" in entry.strategy_id.lower():
        reasons.append("strategy_btc_specialization")
    return tuple(reasons)


def verify_dataset_compatibility_v1(bars: pd.DataFrame) -> tuple[str, ...]:
    reasons: list[str] = []
    if not DATASET_MANIFEST_PATH.is_file():
        reasons.append("dataset_manifest_missing")
        return tuple(reasons)

    manifest = json.loads(DATASET_MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("normalized_dataset_digest") != EXPECTED_DATASET_DIGEST:
        reasons.append("dataset_digest_mismatch")
    if manifest.get("manifest_digest") != EXPECTED_MANIFEST_DIGEST:
        reasons.append("manifest_digest_mismatch")
    if manifest.get("dataset_profile") != "economic_research_v1":
        reasons.append("dataset_profile_mismatch")
    instrument_id = str(manifest.get("instrument_id", ""))
    if instrument_id != "inst-eth-usdt-perp":
        reasons.append("instrument_id_mismatch")
    metadata = manifest.get("instrument_metadata", {})
    if isinstance(metadata, Mapping):
        if metadata.get("canonical_instrument_id") != "inst-eth-usdt-perp":
            reasons.append("canonical_instrument_id_mismatch")
    if manifest.get("native_instrument_id") != "ETH-USDT-SWAP":
        reasons.append("native_instrument_id_mismatch")
    provenance = manifest.get("provenance", {})
    if isinstance(provenance, Mapping):
        if provenance.get("source_venue") != "OKX":
            reasons.append("source_venue_mismatch")

    if "close" not in bars.columns:
        reasons.append("close_column_missing")
    else:
        close = bars["close"]
        if close.isna().any():
            reasons.append("close_has_nan")
        if (close <= 0).any():
            reasons.append("close_non_positive")

    if not bars.index.is_monotonic_increasing:
        reasons.append("index_not_sorted")
    if bars.index.has_duplicates:
        reasons.append("duplicate_timestamps")
    if str(bars.index.tz) != "UTC":
        reasons.append("index_not_utc")

    bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
    digest = ds.compute_versioned_dataset_digest(bars, field_bindings=bindings)
    if digest != EXPECTED_DATASET_DIGEST:
        reasons.append("recomputed_dataset_digest_mismatch")

    return tuple(reasons)


def _count_signals(signals: pd.Series) -> dict[str, int]:
    int_signals = signals.astype(int)
    return {
        "flat_signal_count": int((int_signals == 0).sum()),
        "long_signal_count": int((int_signals == 1).sum()),
        "short_signal_count": int((int_signals == -1).sum()),
        "signal_transition_count": int((int_signals.diff().fillna(0) != 0).sum()),
    }


def run_macd_v1_signal_admissibility_diagnostic_v1(
    bars: pd.DataFrame,
    cfg: Mapping[str, Any],
) -> MacdV1SignalDiagnosticV1:
    effective, params_digest = resolve_effective_strategy_params_v1(
        MACD_V1_STRATEGY_ID,
        collect_configured_strategy_params_v1(cfg, MACD_V1_STRATEGY_ID),
    )
    warmup_rows = compute_required_warmup_rows_v1(MACD_V1_STRATEGY_ID, effective)

    binding = execute_configured_strategy_signal_series_v1(
        bars,
        strategy_id=MACD_V1_STRATEGY_ID,
        cfg=cfg,
    )
    signals = binding.signals
    post_warmup = signals.iloc[warmup_rows:]
    if post_warmup.isna().any():
        raise StrategySignalBindingError("signals_contain_nan_after_warmup")

    counts = _count_signals(post_warmup)
    repeat_binding = execute_configured_strategy_signal_series_v1(
        bars,
        strategy_id=MACD_V1_STRATEGY_ID,
        cfg=cfg,
    )
    determinism_status = (
        "PASS"
        if repeat_binding.provenance.strategy_signal_digest
        == binding.provenance.strategy_signal_digest
        else "FAIL"
    )

    return MacdV1SignalDiagnosticV1(
        dataset_rows=len(bars),
        required_warmup_rows=warmup_rows,
        valid_rows_after_warmup=len(post_warmup),
        signal_min_value=int(post_warmup.min()),
        signal_max_value=int(post_warmup.max()),
        flat_signal_count=counts["flat_signal_count"],
        long_signal_count=counts["long_signal_count"],
        short_signal_count=counts["short_signal_count"],
        signal_transition_count=counts["signal_transition_count"],
        first_valid_signal_timestamp=str(post_warmup.index[0]),
        last_valid_signal_timestamp=str(post_warmup.index[-1]),
        signal_digest=binding.provenance.strategy_signal_digest,
        index_alignment_status=binding.provenance.signal_alignment_status.value,
        signal_contract_status=binding.provenance.signal_contract_status.value,
        determinism_status=determinism_status,
    )


def verify_macd_v1_provenance_contract_v1(
    bars: pd.DataFrame,
    cfg: Mapping[str, Any],
) -> tuple[MacdV1ProvenanceContractV1, tuple[str, ...]]:
    from src.backtest import mv2_research_wiring_v1 as wiring

    reasons: list[str] = []
    binding = execute_configured_strategy_signal_series_v1(
        bars,
        strategy_id=MACD_V1_STRATEGY_ID,
        cfg=cfg,
    )
    provenance = binding.provenance
    try:
        assert_engine_signal_provenance_consistency_v1(provenance)
        execution_status = "PASS"
    except StrategySignalBindingError as exc:
        execution_status = "FAIL"
        reasons.append(str(exc))

    if provenance.configured_strategy_id != MACD_V1_STRATEGY_ID:
        reasons.append("configured_strategy_id_mismatch")
    if provenance.executed_strategy_id != MACD_V1_STRATEGY_ID:
        reasons.append("executed_strategy_id_mismatch")
    if provenance.strategy_version != MACD_V1_STRATEGY_VERSION:
        reasons.append("configured_strategy_version_mismatch")
    if provenance.strategy_owner != MACD_V1_STRATEGY_OWNER:
        reasons.append("strategy_owner_mismatch")
    if provenance.strategy_execution_status is not StrategyExecutionStatus.EXECUTED:
        reasons.append("strategy_not_executed")
    if provenance.engine_signal_source != ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY:
        reasons.append("engine_signal_source_not_configured_strategy")
    if provenance.strategy_signal_digest != provenance.engine_signal_digest:
        reasons.append("strategy_engine_digest_mismatch")

    wiring_result = wiring.run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=MACD_V1_STRATEGY_ID,
        cfg=cfg,
    )
    mv2_status = "PASS"
    if wiring_result.mv2_replay_signal_digest == provenance.strategy_signal_digest:
        mv2_status = "FAIL"
        reasons.append("mv2_replay_not_separate_from_strategy_signal")
    if wiring_result.strategy_signal_provenance.strategy_signal_source == MV2_REPLAY_SIGNAL_SOURCE:
        mv2_status = "FAIL"
        reasons.append("strategy_signal_source_is_mv2_replay")

    provenance_contract = MacdV1ProvenanceContractV1(
        configured_strategy_execution_contract=execution_status,
        signal_provenance_contract=(
            "PASS" if provenance.signal_contract_status is SignalContractStatus.PASS else "FAIL"
        ),
        engine_signal_binding_contract=(
            "PASS"
            if provenance.signal_alignment_status is SignalAlignmentStatus.ALIGNED
            else "FAIL"
        ),
        mv2_diagnostic_separation_contract=mv2_status,
    )
    return provenance_contract, tuple(reasons)


def verify_split_warmup_semantics_macd_v1(
    bars: pd.DataFrame,
    cfg: Mapping[str, Any],
) -> tuple[str, str, tuple[str, ...]]:
    reasons: list[str] = []
    binding = cfg.get("real_admissible_futures_evaluation_binding_v1", {})
    if not isinstance(binding, Mapping):
        reasons.append("real_binding_missing")
        return SPLIT_WARMUP_SEMANTICS, "BLOCKED", tuple(reasons)

    for field, expected in (
        ("training_period", TRAINING_PERIOD),
        ("validation_period", VALIDATION_PERIOD),
        ("out_of_sample_period", OUT_OF_SAMPLE_PERIOD),
    ):
        if binding.get(field) != expected:
            reasons.append(f"{field}_mismatch")

    train = ds._slice_for_period(bars, TRAINING_PERIOD)
    val = ds._slice_for_period(bars, VALIDATION_PERIOD)
    oos = ds._slice_for_period(bars, OUT_OF_SAMPLE_PERIOD)
    if train.empty or val.empty or oos.empty:
        reasons.append("split_slice_empty")

    full_binding = execute_configured_strategy_signal_series_v1(
        bars,
        strategy_id=MACD_V1_STRATEGY_ID,
        cfg=cfg,
    )
    slice_binding = execute_configured_strategy_signal_series_v1(
        val,
        strategy_id=MACD_V1_STRATEGY_ID,
        cfg=cfg,
    )
    first_val_ts = val.index[0]
    full_at_val = int(full_binding.signals.loc[first_val_ts])
    slice_at_val = int(slice_binding.signals.loc[first_val_ts])
    if full_at_val == slice_at_val and full_at_val != 0:
        reasons.append("split_only_signal_matches_full_unexpected")
    if full_at_val != slice_at_val:
        # Split-only execution loses MACD state — canonical runner must use Policy A.
        pass

    effective, _ = resolve_effective_strategy_params_v1(
        MACD_V1_STRATEGY_ID,
        collect_configured_strategy_params_v1(cfg, MACD_V1_STRATEGY_ID),
    )
    warmup = compute_required_warmup_rows_v1(MACD_V1_STRATEGY_ID, effective)
    for label, frame in (("training", train), ("validation", val), ("oos", oos)):
        if len(frame) <= warmup:
            reasons.append(f"insufficient_rows_after_warmup:{label}")

    descriptor = ds.VersionedFuturesDatasetDescriptorV1(
        dataset_id="inst-eth-usdt-perp",
        dataset_version="v1",
        dataset_schema_version="v1",
        dataset_digest=EXPECTED_DATASET_DIGEST,
        instrument_id="inst-eth-usdt-perp",
        contract_type="perpetual",
        futures_only=True,
        bitcoin_direction_allowed=False,
        venue_id="OKX",
        start_time=str(bars.index[0]),
        end_time=str(bars.index[-1]),
        row_count=len(bars),
        field_bindings=ds.research_field_bindings_v1(),
        training_period=TRAINING_PERIOD,
        validation_period=VALIDATION_PERIOD,
        out_of_sample_period=OUT_OF_SAMPLE_PERIOD,
        split_policy_version=ds.SPLIT_POLICY_VERSION,
        timestamp_semantics=ds.TIMESTAMP_SEMANTICS,
        timezone=ds.TIMEZONE,
        ordering_status=ds.ORDERING_STATUS_SORTED,
        duplicate_policy=ds.DUPLICATE_POLICY,
        missing_data_policy=ds.MISSING_DATA_POLICY,
    )
    split_ok, leakage_status, _ = ds._validate_splits(bars, descriptor, [])
    if not split_ok:
        reasons.append("split_validation_failed")

    return SPLIT_WARMUP_SEMANTICS, leakage_status, tuple(reasons)


def verify_cost_binding_v1(cfg: Mapping[str, Any]) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    backtest = cfg.get("backtest", {})
    binding = cfg.get("real_admissible_futures_evaluation_binding_v1", {})
    if not isinstance(backtest, Mapping) or not isinstance(binding, Mapping):
        reasons.append("cost_binding_sections_missing")
        return "FAIL", tuple(reasons)

    fee = float(backtest.get("fee_bps", 0.0))
    slippage = float(backtest.get("slippage_bps", 0.0))
    half_spread = float(
        backtest.get("economic_research_execution_cost", {}).get(
            "conservative_half_spread_bps", 0.0
        )
    )
    if fee != 10.0 or slippage != 5.0 or half_spread != 5.0:
        reasons.append("cost_bps_mismatch")
    if float(binding.get("effective_entry_cost_bps", 0.0)) != 20.0:
        reasons.append("effective_entry_cost_mismatch")
    if float(binding.get("effective_exit_cost_bps", 0.0)) != 20.0:
        reasons.append("effective_exit_cost_mismatch")
    if float(binding.get("roundtrip_cost_bps", 0.0)) != 40.0:
        reasons.append("roundtrip_cost_mismatch")
    if fee <= 0.0 or slippage <= 0.0:
        reasons.append("zero_cost_forbidden")
    funding = backtest.get("funding", {})
    if not isinstance(funding, Mapping) or not funding.get("bind"):
        reasons.append("funding_model_not_bound")

    return ("PASS" if not reasons else "FAIL"), tuple(reasons)


def evaluate_macd_v1_admissibility_contract_v1(
    *,
    repo_root: Path,
    config_path: Optional[str] = None,
) -> MacdV1AdmissibilityContractResultV1:
    blocking: list[str] = []
    rel_path = config_path or DEFAULT_EVALUATION_CONFIG_PATH
    cfg = load_macd_v1_evaluation_config_v1(repo_root, rel_path)
    config_digest = compute_evaluation_config_digest_v1(cfg)

    blocking.extend(verify_macd_v1_strategy_identity_v1())

    configured = collect_configured_strategy_params_v1(cfg, MACD_V1_STRATEGY_ID)
    try:
        effective, params_digest = resolve_effective_strategy_params_v1(
            MACD_V1_STRATEGY_ID,
            configured,
        )
    except StrategySignalBindingError as exc:
        blocking.append(str(exc))
        effective = dict(MACD_V1_CANONICAL_PARAMS)
        params_digest = _stable_digest(
            {
                "strategy_id": MACD_V1_STRATEGY_ID,
                "effective_strategy_params": effective,
                "owner": CONTRACT_OWNER,
            }
        )

    if effective != MACD_V1_CANONICAL_PARAMS:
        blocking.append("effective_strategy_params_not_canonical")

    cost_status, cost_reasons = verify_cost_binding_v1(cfg)
    blocking.extend(cost_reasons)

    eval_section = cfg.get("economic_evaluation_v1", {})
    if not isinstance(eval_section, Mapping):
        blocking.append("economic_evaluation_v1_missing")
    else:
        if eval_section.get("strategy_id") != MACD_V1_STRATEGY_ID:
            blocking.append("config_strategy_id_mismatch")
        if eval_section.get("strategy_version") != MACD_V1_STRATEGY_VERSION:
            blocking.append("config_strategy_version_mismatch")
        if eval_section.get("engine_signal_source") != ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY:
            blocking.append("engine_signal_source_not_bound")

    signal_diagnostic: Optional[MacdV1SignalDiagnosticV1] = None
    provenance_contract: Optional[MacdV1ProvenanceContractV1] = None
    leakage_status = "NOT_RUN"
    split_semantics = SPLIT_WARMUP_SEMANTICS

    try:
        bars = load_admissible_okx_eth_bars_v1()
    except FileNotFoundError as exc:
        blocking.append(str(exc))
        bars = pd.DataFrame()

    if not bars.empty:
        blocking.extend(verify_dataset_compatibility_v1(bars))
        try:
            signal_diagnostic = run_macd_v1_signal_admissibility_diagnostic_v1(bars, cfg)
            if signal_diagnostic.signal_min_value < -1 or signal_diagnostic.signal_max_value > 1:
                blocking.append("signal_range_violation")
            if (
                signal_diagnostic.long_signal_count <= 0
                or signal_diagnostic.short_signal_count <= 0
            ):
                blocking.append("missing_long_or_short_semantics")
            if signal_diagnostic.determinism_status != "PASS":
                blocking.append("signal_digest_not_deterministic")
            if signal_diagnostic.index_alignment_status != "ALIGNED":
                blocking.append("signal_index_not_aligned")
            if signal_diagnostic.signal_contract_status != "PASS":
                blocking.append("signal_contract_not_pass")
        except StrategySignalBindingError as exc:
            blocking.append(str(exc))

        try:
            provenance_contract, prov_reasons = verify_macd_v1_provenance_contract_v1(bars, cfg)
            blocking.extend(prov_reasons)
            for field, value in provenance_contract.to_dict().items():
                if value != "PASS":
                    blocking.append(f"{field}_fail")
        except (StrategySignalBindingError, ValueError) as exc:
            blocking.append(str(exc))

        split_semantics, leakage_status, split_reasons = verify_split_warmup_semantics_macd_v1(
            bars,
            cfg,
        )
        blocking.extend(split_reasons)

    binding_section = cfg.get("real_admissible_futures_evaluation_binding_v1", {})
    if isinstance(binding_section, Mapping):
        if binding_section.get("expected_dataset_digest") != EXPECTED_DATASET_DIGEST:
            blocking.append("config_expected_dataset_digest_mismatch")
        if binding_section.get("expected_manifest_digest") != EXPECTED_MANIFEST_DIGEST:
            blocking.append("config_expected_manifest_digest_mismatch")

    admissibility = AdmissibilityResult.PASS if not blocking else AdmissibilityResult.BLOCKED
    return MacdV1AdmissibilityContractResultV1(
        admissibility_result=admissibility,
        blocking_reasons=tuple(sorted(set(blocking))),
        strategy_id=MACD_V1_STRATEGY_ID,
        strategy_version=MACD_V1_STRATEGY_VERSION,
        strategy_owner=MACD_V1_STRATEGY_OWNER,
        configured_strategy_params=dict(configured),
        effective_strategy_params=dict(effective),
        strategy_params_digest=params_digest,
        signal_diagnostic=signal_diagnostic,
        provenance_contract=provenance_contract,
        split_warmup_semantics=split_semantics,
        leakage_status=leakage_status,
        evaluation_config_path=rel_path,
        config_digest=config_digest,
        cost_binding_status=cost_status,
    )
