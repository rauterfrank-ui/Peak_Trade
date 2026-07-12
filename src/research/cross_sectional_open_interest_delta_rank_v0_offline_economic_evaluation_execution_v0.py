"""Cross-sectional open-interest delta-rank v0 offline economic evaluation execution v0.

Deterministic, fail-closed precheck owner for adapter wiring validation. Full economic
evaluation requires a separate Operator GO and execution scope. No runtime, order, or
authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    SIGNAL_LAG_BARS,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH,
    RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
    RATIFIED_PANEL_DATASET_DIGEST,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    BindingValidationVerdict,
    load_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
    validate_versioned_research_binding_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0 import (
    DATASET_EXTENSION,
    DATASET_ID,
    PANEL_DATASET_SCHEMA,
    derive_target_instrument_ids_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_and_materialization_admissibility_contract_v0 import (
    REQUIRED_CONTIGUOUS_BARS,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
)
from src.research.pit_okx_pt1h_panel_open_interest_dataset_v1 import (
    OPEN_INTEREST_UNIT,
    InstrumentOpenInterestPanelSeriesV1,
    PanelBarWithOpenInterestV1,
    validate_open_interest_panel_series_v1,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"
)

SCHEMA_VERSION = (
    "cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_execution.v0"
)
EXECUTION_ID = (
    "cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_execution_v0"
)
EXECUTION_VERSION = "v0"

GO_TOKEN = (
    "GO_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_"
    "EXECUTION_NO_RUNTIME_AUTHORITY_V0"
)
ADAPTER_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_SOURCE_EVIDENCE_INTEGRITY_"
    "RECONCILIATION_AND_OFFLINE_EVALUATION_ADAPTER_IMPLEMENTATION_V0"
)

CANONICAL_EVALUATION_CALLABLE = "run_offline_evaluation_adapter_precheck_v0"

REASON_BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_OFFLINE_GATE_VIOLATION = "OFFLINE_GATE_VIOLATION"
REASON_DATASET_DIGEST_MISMATCH = "DATASET_DIGEST_MISMATCH"
REASON_UNIVERSE_DIGEST_MISMATCH = "UNIVERSE_DIGEST_MISMATCH"
REASON_INSTRUMENT_SET_MISMATCH = "INSTRUMENT_SET_MISMATCH"
REASON_SUBSTITUTED_INSTRUMENT = "SUBSTITUTED_INSTRUMENT_REJECTED"
REASON_EXPANDED_UNIVERSE = "EXPANDED_UNIVERSE_REJECTED"
REASON_INSUFFICIENT_PANEL_HISTORY = "INSUFFICIENT_PANEL_HISTORY_REJECTED"
REASON_NON_ALIGNED_PANEL = "NON_ALIGNED_PANEL_REJECTED"
REASON_PANEL_MANIFEST_MISSING = "PANEL_MANIFEST_MISSING"
REASON_PANEL_BARS_MISSING = "PANEL_BARS_MISSING"
REASON_ECONOMIC_EXECUTION_FORBIDDEN = "ECONOMIC_EXECUTION_FORBIDDEN_IN_ADAPTER_SCOPE"


class PrecheckTerminalStatus(str, Enum):
    ADAPTER_PRECHECK_COMPLETE = "ADAPTER_PRECHECK_COMPLETE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class LoadedBoundOpenInterestPanelV0:
    manifest: dict[str, Any]
    panel_series: tuple[InstrumentOpenInterestPanelSeriesV1, ...]
    panel_calendar_timestamps_utc: tuple[str, ...]
    panel_dataset_digest: str
    instrument_universe_digest: str


@dataclass(frozen=True)
class OfflineEvaluationAdapterPrecheckResultV0:
    status: PrecheckTerminalStatus
    precheck_passed: bool
    binding_valid: bool
    panel_contract_valid: bool
    canonical_callable_invoked: bool
    panel_dataset_digest: str
    instrument_universe_digest: str
    instrument_count: int
    panel_bar_count: int
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_bound_open_interest_panel_from_materialization_root_v0(
    materialization_root: Path,
) -> LoadedBoundOpenInterestPanelV0:
    panel_dir = materialization_root / "panel"
    manifest_path = panel_dir / "panel_open_interest_dataset_manifest.json"
    bars_path = panel_dir / "normalized_panel_bars_with_open_interest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"{REASON_PANEL_MANIFEST_MISSING}:{manifest_path}")
    if not bars_path.is_file():
        raise FileNotFoundError(f"{REASON_PANEL_BARS_MISSING}:{bars_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload = json.loads(bars_path.read_text(encoding="utf-8"))
    rows = payload.get("bars", [])
    if not isinstance(rows, list):
        raise ValueError("PANEL_BARS_INVALID_SHAPE")

    by_instrument: dict[str, list[PanelBarWithOpenInterestV1]] = {}
    native_by_instrument: dict[str, str] = {}
    for row in rows:
        instrument_id = str(row["instrument_id"])
        native_by_instrument[instrument_id] = str(row.get("native_instrument_id", ""))
        by_instrument.setdefault(instrument_id, []).append(
            PanelBarWithOpenInterestV1(
                instrument_id=instrument_id,
                native_instrument_id=str(row.get("native_instrument_id", "")),
                timestamp_utc=str(row["timestamp_utc"]),
                open_interest=row.get("open_interest"),
                open_interest_unit=str(row.get("open_interest_unit", OPEN_INTEREST_UNIT)),
                availability_time_utc=str(row.get("availability_time_utc", "")),
                is_final=bool(row.get("is_final", True)),
                data_quality_status=str(row.get("data_quality_status", "OK")),
                stale_flag=bool(row.get("stale_flag", False)),
                missing_flag=bool(row.get("missing_flag", False)),
                universe_membership_status=str(row.get("universe_membership_status", "ELIGIBLE")),
                source_schema_version=str(
                    row.get("source_schema_version", "okx_rubik_open_interest_history.v0")
                ),
            )
        )

    panel_series: list[InstrumentOpenInterestPanelSeriesV1] = []
    for instrument_id in sorted(by_instrument):
        bars = tuple(sorted(by_instrument[instrument_id], key=lambda b: b.timestamp_utc))
        panel_series.append(
            InstrumentOpenInterestPanelSeriesV1(
                instrument_id=instrument_id,
                native_instrument_id=native_by_instrument.get(instrument_id, ""),
                bars=bars,
                series_digest=_stable_digest(
                    [{"instrument_id": b.instrument_id, "ts": b.timestamp_utc} for b in bars]
                ),
            )
        )

    calendar = tuple(manifest.get("panel_calendar_timestamps_utc", []))
    panel_digest = str(
        manifest.get("open_interest_panel_digest", manifest.get("panel_dataset_digest", ""))
    )
    universe_digest = str(manifest.get("instrument_universe_digest", ""))
    return LoadedBoundOpenInterestPanelV0(
        manifest=manifest,
        panel_series=tuple(panel_series),
        panel_calendar_timestamps_utc=calendar,
        panel_dataset_digest=panel_digest,
        instrument_universe_digest=universe_digest,
    )


def validate_bound_panel_contract_v0(
    *,
    loaded_panel: LoadedBoundOpenInterestPanelV0,
    expected_instrument_ids: Sequence[str] | None = None,
    expected_panel_dataset_digest: str = RATIFIED_PANEL_DATASET_DIGEST,
    expected_universe_digest: str = RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
    minimum_panel_bars: int = REQUIRED_CONTIGUOUS_BARS,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    expected_ids = tuple(expected_instrument_ids or derive_target_instrument_ids_v0())
    actual_ids = tuple(sorted(series.instrument_id for series in loaded_panel.panel_series))

    if len(actual_ids) != len(expected_ids):
        reasons.append(REASON_INSTRUMENT_SET_MISMATCH)
    if set(actual_ids) != set(expected_ids):
        if len(actual_ids) == len(expected_ids):
            reasons.append(REASON_SUBSTITUTED_INSTRUMENT)
        elif len(actual_ids) > len(expected_ids):
            reasons.append(REASON_EXPANDED_UNIVERSE)
        else:
            reasons.append(REASON_INSTRUMENT_SET_MISMATCH)

    if loaded_panel.panel_dataset_digest != expected_panel_dataset_digest:
        reasons.append(REASON_DATASET_DIGEST_MISMATCH)
    if loaded_panel.instrument_universe_digest != expected_universe_digest:
        reasons.append(REASON_UNIVERSE_DIGEST_MISMATCH)

    manifest = loaded_panel.manifest
    if manifest.get("dataset_id") != DATASET_ID:
        reasons.append("FOREIGN_DATASET_REJECTED")
    if manifest.get("dataset_extension") != DATASET_EXTENSION:
        reasons.append("FOREIGN_DATASET_EXTENSION_REJECTED")
    if manifest.get("panel_dataset_schema") != PANEL_DATASET_SCHEMA:
        reasons.append("PANEL_SCHEMA_MISMATCH")

    calendar = loaded_panel.panel_calendar_timestamps_utc
    if len(calendar) < minimum_panel_bars:
        reasons.append(REASON_INSUFFICIENT_PANEL_HISTORY)

    if calendar:
        for series in loaded_panel.panel_series:
            series_timestamps = {bar.timestamp_utc for bar in series.bars}
            if not set(calendar).issubset(series_timestamps):
                reasons.append(REASON_NON_ALIGNED_PANEL)
                break
        for series in loaded_panel.panel_series:
            validation = validate_open_interest_panel_series_v1(
                series,
                expected_timestamps=calendar,
            )
            if not validation.valid:
                reasons.extend(validation.error_codes)

    unique_reasons = tuple(dict.fromkeys(reasons))
    return not unique_reasons, unique_reasons


def verify_offline_and_go_gates_v0(
    *,
    go_token: str,
    offline_only: bool = True,
    allow_economic_execution: bool = False,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if go_token != ADAPTER_GO_TOKEN:
        reasons.append(REASON_GO_TOKEN_INVALID)
    if not offline_only:
        reasons.append(REASON_OFFLINE_GATE_VIOLATION)
    if allow_economic_execution:
        reasons.append(REASON_ECONOMIC_EXECUTION_FORBIDDEN)
    unique_reasons = tuple(dict.fromkeys(reasons))
    return not unique_reasons, unique_reasons


def run_offline_evaluation_adapter_precheck_v0(
    *,
    repo_root: Path,
    materialization_root: Path,
    go_token: str,
    versioned_binding: Mapping[str, Any] | None = None,
    offline_only: bool = True,
) -> OfflineEvaluationAdapterPrecheckResultV0:
    """Canonical evaluation precheck callable; stops before economic execution."""
    gate_ok, gate_reasons = verify_offline_and_go_gates_v0(
        go_token=go_token,
        offline_only=offline_only,
        allow_economic_execution=False,
    )
    if not gate_ok:
        return OfflineEvaluationAdapterPrecheckResultV0(
            status=PrecheckTerminalStatus.FAIL_CLOSED,
            precheck_passed=False,
            binding_valid=False,
            panel_contract_valid=False,
            canonical_callable_invoked=True,
            panel_dataset_digest="0" * 64,
            instrument_universe_digest="0" * 64,
            instrument_count=0,
            panel_bar_count=0,
            reason_codes=gate_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    validation_verdict, binding_reasons = validate_versioned_research_binding_v0(envelope)
    binding_valid = validation_verdict is BindingValidationVerdict.ACCEPTED_COMPLETE

    try:
        loaded_panel = load_bound_open_interest_panel_from_materialization_root_v0(
            materialization_root
        )
    except (FileNotFoundError, ValueError) as exc:
        return OfflineEvaluationAdapterPrecheckResultV0(
            status=PrecheckTerminalStatus.FAIL_CLOSED,
            precheck_passed=False,
            binding_valid=binding_valid,
            panel_contract_valid=False,
            canonical_callable_invoked=True,
            panel_dataset_digest="0" * 64,
            instrument_universe_digest="0" * 64,
            instrument_count=0,
            panel_bar_count=0,
            reason_codes=(str(exc), *binding_reasons),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    panel_ok, panel_reasons = validate_bound_panel_contract_v0(loaded_panel=loaded_panel)
    reasons = tuple(dict.fromkeys((*binding_reasons, *panel_reasons)))
    precheck_passed = binding_valid and panel_ok and not reasons

    return OfflineEvaluationAdapterPrecheckResultV0(
        status=(
            PrecheckTerminalStatus.ADAPTER_PRECHECK_COMPLETE
            if precheck_passed
            else PrecheckTerminalStatus.FAIL_CLOSED
        ),
        precheck_passed=precheck_passed,
        binding_valid=binding_valid,
        panel_contract_valid=panel_ok,
        canonical_callable_invoked=True,
        panel_dataset_digest=loaded_panel.panel_dataset_digest,
        instrument_universe_digest=loaded_panel.instrument_universe_digest,
        instrument_count=len(loaded_panel.panel_series),
        panel_bar_count=len(loaded_panel.panel_calendar_timestamps_utc),
        reason_codes=reasons,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        economic_evaluation_executed=False,
    )


def precheck_result_to_dict(result: OfflineEvaluationAdapterPrecheckResultV0) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "execution_version": EXECUTION_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "canonical_evaluation_callable": CANONICAL_EVALUATION_CALLABLE,
        "status": result.status.value,
        "precheck_passed": result.precheck_passed,
        "binding_valid": result.binding_valid,
        "panel_contract_valid": result.panel_contract_valid,
        "canonical_callable_invoked": result.canonical_callable_invoked,
        "panel_dataset_digest": result.panel_dataset_digest,
        "instrument_universe_digest": result.instrument_universe_digest,
        "instrument_count": result.instrument_count,
        "panel_bar_count": result.panel_bar_count,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "economic_evaluation_executed": result.economic_evaluation_executed,
    }


def materialize_execution_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "canonical_evaluation_callable": CANONICAL_EVALUATION_CALLABLE,
        "adapter_go_token": ADAPTER_GO_TOKEN,
        "execution_go_token": GO_TOKEN,
        "versioned_binding_config": CONFIG_REL_PATH,
        "materializer_owner": (
            "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0"
        ),
        "minimum_panel_bars": REQUIRED_CONTIGUOUS_BARS,
        "signal_lag_bars": SIGNAL_LAG_BARS,
        "target_instrument_count": len(CANONICAL_UNIVERSE_BINDING),
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
