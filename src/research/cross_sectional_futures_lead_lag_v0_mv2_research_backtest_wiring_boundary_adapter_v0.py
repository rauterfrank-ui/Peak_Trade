"""Lead-lag v0 MV2 research backtest wiring boundary adapter v0.

Thin reuse-first adapter binding cross-sectional lead-lag diffusion research scores
to canonical ``run_mv2_research_backtest_wiring_v1``. Does not duplicate trading
semantics, execute economic evaluation, or resolve score sign to final sides.

Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.backtest.mv2_research_wiring_v1 import (
    MV2_REQUIRED_INSTRUMENT_ID,
    MV2ResearchWiringResultV1,
    run_mv2_research_backtest_wiring_v1,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0 import (
    SCORE_FORMULA_VERSION,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    OrchestratorRunResultV0,
    SlotSide,
    run_cross_sectional_single_slot_orchestrator_v0,
    default_lead_lag_operator_binding_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_V0_MV2_RESEARCH_BACKTEST_WIRING_BOUNDARY_ADAPTER_V0=true"
)

ADAPTER_VERSION = "v0"
ADAPTER_OWNER = (
    "research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0"
)
ADAPTER_MODULE = "src/research/cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0.py"

GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_V0_MV2_RESEARCH_BACKTEST_WIRING_BOUNDARY_ADAPTER_"
    "IMPLEMENTATION_V0"
)
SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_V0_SYSTEM_EVIDENCE_MV2_OFFLINE_ECONOMIC_"
    "EVALUATION_BINDING_V0"
)
ALLOWED_ADAPTER_GO_TOKENS: frozenset[str] = frozenset(
    {GO_TOKEN, SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN}
)

LEGACY_RESEARCH_PATH_MODE = "LEGACY_RESEARCH"
SYSTEM_EVIDENCE_MV2_PATH_MODE = "SYSTEM_EVIDENCE_MV2"

MV2_CANONICAL_OWNER = "backtest.mv2_research_wiring_v1"
MV2_CANONICAL_CALLABLE = "run_mv2_research_backtest_wiring_v1"

# Registry-compatible engine signal delegate; research binding strategy_id unchanged.
MV2_ENGINE_SIGNAL_STRATEGY_ID = "momentum_1h"

REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_BINDING_DIGEST_MISMATCH = "BINDING_DIGEST_MISMATCH"
REASON_DATASET_DIGEST_MISMATCH = "DATASET_DIGEST_MISMATCH"
REASON_UNIVERSE_DIGEST_MISMATCH = "UNIVERSE_DIGEST_MISMATCH"
REASON_SCORE_SIDE_SHORTCUT_FORBIDDEN = (
    "SCORE_TO_FINAL_SIDE_SHORTCUT_FORBIDDEN_IN_SYSTEM_EVIDENCE_MODE"
)
REASON_ORCHESTRATOR_EMPTY = "ORCHESTRATOR_EMPTY"
REASON_PANEL_MEMBER_MISSING = "PANEL_MEMBER_MISSING"
REASON_MV2_BARS_EMPTY = "MV2_BARS_EMPTY"


class AdapterTerminalStatus(str, Enum):
    MV2_WIRING_BOUNDARY_COMPLETE = "MV2_WIRING_BOUNDARY_COMPLETE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class LeadLagScoreFeatureRowV0:
    timestamp_utc: str
    instrument_id: str
    diffusion_score: float
    panel_median_return: float
    lagged_return: float


@dataclass(frozen=True)
class LeadLagMv2WiringAdapterResultV0:
    status: AdapterTerminalStatus
    evaluation_path_mode: str
    wiring_result: MV2ResearchWiringResultV1 | None
    orchestrator_result: OrchestratorRunResultV0 | None
    score_feature_rows: tuple[LeadLagScoreFeatureRowV0, ...]
    selected_panel_member_id: str
    mv2_bars_row_count: int
    binding_digest: str
    dataset_digest: str
    universe_digest: str
    research_binding_strategy_id: str
    mv2_engine_signal_strategy_id: str
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def materialize_adapter_contract_v0() -> dict[str, Any]:
    return {
        "adapter_version": ADAPTER_VERSION,
        "adapter_owner": ADAPTER_OWNER,
        "adapter_module": ADAPTER_MODULE,
        "go_token": GO_TOKEN,
        "system_evidence_mv2_binding_go_token": SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
        "allowed_adapter_go_tokens": sorted(ALLOWED_ADAPTER_GO_TOKENS),
        "canonical_mv2_owner": MV2_CANONICAL_OWNER,
        "canonical_mv2_callable": MV2_CANONICAL_CALLABLE,
        "legacy_research_path_mode": LEGACY_RESEARCH_PATH_MODE,
        "system_evidence_mv2_path_mode": SYSTEM_EVIDENCE_MV2_PATH_MODE,
        "mv2_engine_signal_strategy_id": MV2_ENGINE_SIGNAL_STRATEGY_ID,
        "mv2_required_instrument_id": MV2_REQUIRED_INSTRUMENT_ID,
        "score_family_policy": SCORE_FORMULA_VERSION,
        "score_to_final_side_shortcut_allowed": False,
        "economic_evaluation_executed": False,
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
    }


def verify_adapter_go_token_v0(go_token: str) -> tuple[bool, tuple[str, ...]]:
    if go_token not in ALLOWED_ADAPTER_GO_TOKENS:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def verify_binding_digests_unchanged_v0(
    versioned_binding: Mapping[str, Any],
    *,
    expected_binding_digest: str = "",
    expected_dataset_digest: str = "",
    expected_universe_digest: str = "",
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    binding_digest = str(versioned_binding.get("binding_digest", ""))
    dataset_digest = str(versioned_binding.get("dataset_digest", ""))
    universe_digest = str(
        versioned_binding.get("binding", {})
        .get("pit_universe_binding", {})
        .get("universe_digest", "")
    )
    if expected_binding_digest and binding_digest != expected_binding_digest:
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)
    if expected_dataset_digest and dataset_digest != expected_dataset_digest:
        reasons.append(REASON_DATASET_DIGEST_MISMATCH)
    if expected_universe_digest and universe_digest != expected_universe_digest:
        reasons.append(REASON_UNIVERSE_DIGEST_MISMATCH)
    return not reasons, tuple(reasons)


def reject_score_to_final_side_shortcut_v0(
    *,
    evaluation_path_mode: str,
    resolved_side: SlotSide | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Fail-closed guard: system-evidence mode must not use score-sign side resolution."""
    if evaluation_path_mode != SYSTEM_EVIDENCE_MV2_PATH_MODE:
        return True, ()
    if resolved_side is not None:
        return False, (REASON_SCORE_SIDE_SHORTCUT_FORBIDDEN,)
    return True, ()


def extract_lead_lag_score_feature_rows_v0(
    orchestrator_result: OrchestratorRunResultV0,
) -> tuple[LeadLagScoreFeatureRowV0, ...]:
    """Adapt orchestrator scores to feature rows without slot-side resolution."""
    rows: list[LeadLagScoreFeatureRowV0] = []
    for epoch in orchestrator_result.epochs:
        if not epoch.scores:
            continue
        top = epoch.scores[0]
        instrument_id = top.instrument_id
        rows.append(
            LeadLagScoreFeatureRowV0(
                timestamp_utc=epoch.timestamp_utc,
                instrument_id=instrument_id,
                diffusion_score=float(top.score),
                panel_median_return=float(top.panel_median_return),
                lagged_return=float(top.lagged_return),
            )
        )
    return tuple(rows)


def _select_primary_panel_member_v0(
    score_rows: Sequence[LeadLagScoreFeatureRowV0],
    *,
    fallback_instrument_id: str,
) -> str:
    if not score_rows:
        return fallback_instrument_id
    counts: dict[str, int] = {}
    for row in score_rows:
        counts[row.instrument_id] = counts.get(row.instrument_id, 0) + 1
    return max(counts, key=counts.get)


def materialize_mv2_bars_with_score_features_v0(
    *,
    panel_member_bars: Sequence[Any],
    score_rows: Sequence[LeadLagScoreFeatureRowV0],
    instrument_id: str = MV2_REQUIRED_INSTRUMENT_ID,
) -> pd.DataFrame:
    score_by_ts = {row.timestamp_utc: row for row in score_rows}
    records: list[dict[str, Any]] = []
    for bar in panel_member_bars:
        ts = bar.timestamp_utc
        close = float(bar.close)
        feature = score_by_ts.get(ts)
        diffusion = float(feature.diffusion_score) if feature is not None else 0.0
        records.append(
            {
                "timestamp": pd.Timestamp(ts, tz="UTC"),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": close,
                "mark_price": close,
                "index_price": close,
                "volume": float(bar.volume),
                "open_interest": 10000.0,
                "funding_rate": 0.0001,
                "volatility_estimate": 0.2,
                "is_final": bool(bar.is_final),
                "bar_interval": "1h",
                "momentum": diffusion,
                "trend_slope": diffusion,
                "lead_lag_diffusion_score": diffusion,
                "panel_median_return": float(feature.panel_median_return) if feature else 0.0,
                "lagged_return": float(feature.lagged_return) if feature else 0.0,
                "instrument_id": instrument_id,
            }
        )
    if not records:
        return pd.DataFrame()
    frame = pd.DataFrame(records).set_index("timestamp").sort_index()
    return frame


def build_mv2_cfg_from_lead_lag_ops_config_v0(
    ops_config: Mapping[str, Any],
    *,
    versioned_binding: Mapping[str, Any],
) -> dict[str, Any]:
    backtest = dict(ops_config.get("backtest", {}))
    sizing = dict(ops_config.get("offline_evaluation_sizing_contract_v1", {}))
    max_position_pct = float(sizing.get("max_position_pct", 1.0))
    return {
        "backtest": backtest,
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": max_position_pct,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_params": {
                "lookback_period": int(
                    versioned_binding.get("parameter_binding", {}).get("lag_window_L", 8)
                ),
                "entry_threshold": 0.02,
                "exit_threshold": -0.01,
            },
        },
        "real_admissible_futures_evaluation_binding_v1": {
            "canonical_instrument_id": MV2_REQUIRED_INSTRUMENT_ID,
            "expected_dataset_digest": str(versioned_binding.get("dataset_digest", "")),
            "source_venue": "OKX",
        },
    }


def run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[Any],
    versioned_binding: Mapping[str, Any],
    ops_config: Mapping[str, Any],
    go_token: str,
    evaluation_path_mode: str = SYSTEM_EVIDENCE_MV2_PATH_MODE,
) -> LeadLagMv2WiringAdapterResultV0:
    """Bind lead-lag research scores to canonical MV2 research backtest wiring."""
    _ = repo_root
    authority = "NONE"
    runtime = "NONE"
    research_strategy_id = str(
        versioned_binding.get(
            "strategy_id", "cross_sectional_futures_lead_lag_information_diffusion"
        )
    )
    binding_digest = str(versioned_binding.get("binding_digest", ""))
    dataset_digest = str(versioned_binding.get("dataset_digest", ""))
    universe_digest = str(
        versioned_binding.get("binding", {})
        .get("pit_universe_binding", {})
        .get("universe_digest", "")
    )

    go_ok, go_reasons = verify_adapter_go_token_v0(go_token)
    if not go_ok:
        return LeadLagMv2WiringAdapterResultV0(
            status=AdapterTerminalStatus.FAIL_CLOSED,
            evaluation_path_mode=evaluation_path_mode,
            wiring_result=None,
            orchestrator_result=None,
            score_feature_rows=(),
            selected_panel_member_id="",
            mv2_bars_row_count=0,
            binding_digest=binding_digest,
            dataset_digest=dataset_digest,
            universe_digest=universe_digest,
            research_binding_strategy_id=research_strategy_id,
            mv2_engine_signal_strategy_id=MV2_ENGINE_SIGNAL_STRATEGY_ID,
            reason_codes=go_reasons,
            authority_effect=authority,
            runtime_effect=runtime,
            economic_evaluation_executed=False,
        )

    digest_ok, digest_reasons = verify_binding_digests_unchanged_v0(
        versioned_binding,
        expected_binding_digest=str(ops_config.get("binding_digest", "")) or binding_digest,
        expected_dataset_digest=str(
            ops_config.get("cross_sectional_evaluation_binding_v1", {})
            .get("dataset_binding", {})
            .get("dataset_digest", dataset_digest)
        ),
        expected_universe_digest=str(
            ops_config.get("cross_sectional_evaluation_binding_v1", {})
            .get("instrument_universe_binding", {})
            .get("universe_digest", universe_digest)
        ),
    )
    if not digest_ok:
        return LeadLagMv2WiringAdapterResultV0(
            status=AdapterTerminalStatus.FAIL_CLOSED,
            evaluation_path_mode=evaluation_path_mode,
            wiring_result=None,
            orchestrator_result=None,
            score_feature_rows=(),
            selected_panel_member_id="",
            mv2_bars_row_count=0,
            binding_digest=binding_digest,
            dataset_digest=dataset_digest,
            universe_digest=universe_digest,
            research_binding_strategy_id=research_strategy_id,
            mv2_engine_signal_strategy_id=MV2_ENGINE_SIGNAL_STRATEGY_ID,
            reason_codes=digest_reasons,
            authority_effect=authority,
            runtime_effect=runtime,
            economic_evaluation_executed=False,
        )

    shortcut_ok, shortcut_reasons = reject_score_to_final_side_shortcut_v0(
        evaluation_path_mode=evaluation_path_mode,
        resolved_side=None,
    )
    if not shortcut_ok:
        return LeadLagMv2WiringAdapterResultV0(
            status=AdapterTerminalStatus.FAIL_CLOSED,
            evaluation_path_mode=evaluation_path_mode,
            wiring_result=None,
            orchestrator_result=None,
            score_feature_rows=(),
            selected_panel_member_id="",
            mv2_bars_row_count=0,
            binding_digest=binding_digest,
            dataset_digest=dataset_digest,
            universe_digest=universe_digest,
            research_binding_strategy_id=research_strategy_id,
            mv2_engine_signal_strategy_id=MV2_ENGINE_SIGNAL_STRATEGY_ID,
            reason_codes=shortcut_reasons,
            authority_effect=authority,
            runtime_effect=runtime,
            economic_evaluation_executed=False,
        )

    operator_binding = default_lead_lag_operator_binding_v0(versioned_binding)
    orchestrator = run_cross_sectional_single_slot_orchestrator_v0(
        binding=operator_binding,
        panel_series=panel_series,
        score_formula_version=SCORE_FORMULA_VERSION,
    )
    if not orchestrator.epochs:
        return LeadLagMv2WiringAdapterResultV0(
            status=AdapterTerminalStatus.FAIL_CLOSED,
            evaluation_path_mode=evaluation_path_mode,
            wiring_result=None,
            orchestrator_result=orchestrator,
            score_feature_rows=(),
            selected_panel_member_id="",
            mv2_bars_row_count=0,
            binding_digest=binding_digest,
            dataset_digest=dataset_digest,
            universe_digest=universe_digest,
            research_binding_strategy_id=research_strategy_id,
            mv2_engine_signal_strategy_id=MV2_ENGINE_SIGNAL_STRATEGY_ID,
            reason_codes=(REASON_ORCHESTRATOR_EMPTY,),
            authority_effect=authority,
            runtime_effect=runtime,
            economic_evaluation_executed=False,
        )

    score_rows = extract_lead_lag_score_feature_rows_v0(orchestrator)
    fallback_id = panel_series[0].instrument_id if panel_series else ""
    selected_member = _select_primary_panel_member_v0(
        score_rows,
        fallback_instrument_id=fallback_id,
    )
    member_series = next(
        (series for series in panel_series if series.instrument_id == selected_member),
        None,
    )
    if member_series is None:
        return LeadLagMv2WiringAdapterResultV0(
            status=AdapterTerminalStatus.FAIL_CLOSED,
            evaluation_path_mode=evaluation_path_mode,
            wiring_result=None,
            orchestrator_result=orchestrator,
            score_feature_rows=score_rows,
            selected_panel_member_id=selected_member,
            mv2_bars_row_count=0,
            binding_digest=binding_digest,
            dataset_digest=dataset_digest,
            universe_digest=universe_digest,
            research_binding_strategy_id=research_strategy_id,
            mv2_engine_signal_strategy_id=MV2_ENGINE_SIGNAL_STRATEGY_ID,
            reason_codes=(REASON_PANEL_MEMBER_MISSING,),
            authority_effect=authority,
            runtime_effect=runtime,
            economic_evaluation_executed=False,
        )

    bars = materialize_mv2_bars_with_score_features_v0(
        panel_member_bars=member_series.bars,
        score_rows=score_rows,
    )
    if bars.empty:
        return LeadLagMv2WiringAdapterResultV0(
            status=AdapterTerminalStatus.FAIL_CLOSED,
            evaluation_path_mode=evaluation_path_mode,
            wiring_result=None,
            orchestrator_result=orchestrator,
            score_feature_rows=score_rows,
            selected_panel_member_id=selected_member,
            mv2_bars_row_count=0,
            binding_digest=binding_digest,
            dataset_digest=dataset_digest,
            universe_digest=universe_digest,
            research_binding_strategy_id=research_strategy_id,
            mv2_engine_signal_strategy_id=MV2_ENGINE_SIGNAL_STRATEGY_ID,
            reason_codes=(REASON_MV2_BARS_EMPTY,),
            authority_effect=authority,
            runtime_effect=runtime,
            economic_evaluation_executed=False,
        )

    cfg = build_mv2_cfg_from_lead_lag_ops_config_v0(
        ops_config,
        versioned_binding=versioned_binding,
    )
    backtest_section = dict(ops_config.get("backtest", {}))
    profile_binding = ds.DatasetProfileBindingV1(
        dataset_profile=ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ds.ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=float(
                backtest_section.get("economic_research_execution_cost", {}).get(
                    "conservative_half_spread_bps", 5.0
                )
            ),
        ),
        l1_observation_status=ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )

    wiring = run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=MV2_ENGINE_SIGNAL_STRATEGY_ID,
        cfg=cfg,
        instrument_id=MV2_REQUIRED_INSTRUMENT_ID,
        profile_binding=profile_binding,
    )

    return LeadLagMv2WiringAdapterResultV0(
        status=AdapterTerminalStatus.MV2_WIRING_BOUNDARY_COMPLETE,
        evaluation_path_mode=evaluation_path_mode,
        wiring_result=wiring,
        orchestrator_result=orchestrator,
        score_feature_rows=score_rows,
        selected_panel_member_id=selected_member,
        mv2_bars_row_count=len(bars),
        binding_digest=binding_digest,
        dataset_digest=dataset_digest,
        universe_digest=universe_digest,
        research_binding_strategy_id=research_strategy_id,
        mv2_engine_signal_strategy_id=MV2_ENGINE_SIGNAL_STRATEGY_ID,
        reason_codes=(),
        authority_effect=authority,
        runtime_effect=runtime,
        economic_evaluation_executed=False,
    )


def adapter_result_to_dict(result: LeadLagMv2WiringAdapterResultV0) -> dict[str, Any]:
    wiring = result.wiring_result
    return {
        "status": result.status.value,
        "evaluation_path_mode": result.evaluation_path_mode,
        "selected_panel_member_id": result.selected_panel_member_id,
        "mv2_bars_row_count": result.mv2_bars_row_count,
        "binding_digest": result.binding_digest,
        "dataset_digest": result.dataset_digest,
        "universe_digest": result.universe_digest,
        "research_binding_strategy_id": result.research_binding_strategy_id,
        "mv2_engine_signal_strategy_id": result.mv2_engine_signal_strategy_id,
        "score_feature_row_count": len(result.score_feature_rows),
        "mv2_bar_outcome_count": len(wiring.bar_outcomes) if wiring is not None else 0,
        "mv2_replay_nonzero_signal_count": (
            wiring.mv2_replay_nonzero_signal_count if wiring is not None else 0
        ),
        "trade_count": (
            int(wiring.backtest_result.stats.get("total_trades", 0)) if wiring is not None else 0
        ),
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "canonical_mv2_owner": MV2_CANONICAL_OWNER,
        "adapter_owner": ADAPTER_OWNER,
    }
