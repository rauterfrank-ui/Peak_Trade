"""Productive-faithful bindings for historical CURRENT offline replay (AUTHORITY=NONE)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from src.backtest.strategy_signal_binding_v1 import StrategySignalBindingError
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from src.backtest.strategy_signal_binding_v1 import execute_configured_strategy_signal_series_v1
from src.core.config_simple import load_config
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    _resolve_f1_m9_governed_seam_for_integrated_offline_replay_v1,
    _wire_simulated_economics_crs_boundary_onto_replay_input_v1,
)
from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1, WarmupStatus
from trading.master_v2.canonical_scope_initialization_v1 import ScopeInitializationPrerequisitesV1
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    collect_typed_volatility_binding_block_reasons_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    MINIMUM_PRICE_OBSERVATIONS,
    MINIMUM_RETURN_OBSERVATIONS,
    build_canonical_volatility_estimate_v1,
)
from src.trading.master_v2 import (
    canonical_volatility_estimate_feature_contract_v1 as vol_feature_contract,
)
from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayResultV1,
)
from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED,
)
from trading.master_v2.suitability_binding_v1 import SuitabilityRegimeStatus

HISTORICAL_AGREEMENT_STRATEGY_ID = "trend_following"
CAPITAL_RISK_CONTEXT_UNRESOLVED = REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED


def precompute_economic_research_g17_typed_estimates_v1(
    bars: pd.DataFrame,
) -> dict[int, Any]:
    """One-pass typed G17 carriers from contract-materialized economic-research bars."""
    if "mark_price" not in bars.columns or "volatility_estimate" not in bars.columns:
        return {}
    mark = bars["mark_price"].astype(float)
    out: dict[int, Any] = {}
    for i in range(len(bars)):
        row = bars.iloc[i]
        raw_vol = row.get("volatility_estimate")
        if raw_vol is None or pd.isna(raw_vol):
            continue
        contract_ver = row.get("volatility_estimate_contract_version")
        if contract_ver is not None and str(contract_ver) != vol_feature_contract.CONTRACT_VERSION:
            continue
        if i + 1 < MINIMUM_PRICE_OBSERVATIONS:
            continue
        window = mark.iloc[i + 1 - MINIMUM_PRICE_OBSERVATIONS : i + 1]
        ts = pd.Timestamp(bars.index[i])
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        oldest = pd.Timestamp(window.index[0])
        if oldest.tzinfo is None:
            oldest = oldest.tz_localize("UTC")
        else:
            oldest = oldest.tz_convert("UTC")
        try:
            out[i] = build_canonical_volatility_estimate_v1(
                value=float(raw_vol),
                observation_count=int(MINIMUM_RETURN_OBSERVATIONS),
                as_of_event_time=ts.to_pydatetime(),
                oldest_observation_event_time=oldest.to_pydatetime(),
                mark_prices=window.astype(float).tolist(),
            )
        except Exception:  # noqa: BLE001 — skip invalid typed carrier rows only
            continue
    return out


def apply_g17_typed_volatility_to_context_v1(
    context: CanonicalMarketContextV1,
    *,
    typed_estimate: Any | None,
) -> CanonicalMarketContextV1:
    if typed_estimate is None:
        return context
    return bind_typed_canonical_volatility_estimate_into_market_context_v1(
        context,
        typed_estimate,
    )


@dataclass
class ProductiveContextBindingReportV1:
    g17_binding_complete: bool = False
    cap61_binding_complete: bool = False
    confirmation_binding_complete: bool = False
    host_confirmation_binding_complete: bool = False
    scope_gge_binding_complete: bool = False
    suitability_binding_complete: bool = False
    double_play_binding_complete: bool = False
    capital_context_binding_complete: bool = False
    risk_context_binding_complete: bool = False
    sizing_binding_complete: bool = False
    safety_binding_complete: bool = True
    g17_blocker: str = ""
    f1_m9_blocker: str = ""
    crs_boundary_bound: bool = False

    @property
    def productive_context_complete(self) -> bool:
        return all(
            (
                self.g17_binding_complete,
                self.cap61_binding_complete,
                self.confirmation_binding_complete,
                self.host_confirmation_binding_complete,
                self.scope_gge_binding_complete,
                self.suitability_binding_complete,
                self.double_play_binding_complete,
                self.capital_context_binding_complete,
                self.risk_context_binding_complete,
                self.sizing_binding_complete,
                self.safety_binding_complete,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "g17_binding_complete": self.g17_binding_complete,
            "cap61_binding_complete": self.cap61_binding_complete,
            "confirmation_binding_complete": self.confirmation_binding_complete,
            "host_confirmation_binding_complete": self.host_confirmation_binding_complete,
            "scope_gge_binding_complete": self.scope_gge_binding_complete,
            "suitability_binding_complete": self.suitability_binding_complete,
            "double_play_binding_complete": self.double_play_binding_complete,
            "capital_context_binding_complete": self.capital_context_binding_complete,
            "risk_context_binding_complete": self.risk_context_binding_complete,
            "sizing_binding_complete": self.sizing_binding_complete,
            "safety_binding_complete": self.safety_binding_complete,
            "productive_context_complete": self.productive_context_complete,
            "g17_blocker": self.g17_blocker,
            "f1_m9_blocker": self.f1_m9_blocker,
            "crs_boundary_bound": self.crs_boundary_bound,
        }


def resolve_regime_from_context_v1(
    context: CanonicalMarketContextV1,
) -> tuple[str, SuitabilityRegimeStatus]:
    if context.warmup_status != WarmupStatus.WARMUP_COMPLETE:
        return "unclassified", SuitabilityRegimeStatus.UNKNOWN
    vol = float(context.volatility_estimate or 0.0)
    if vol <= 0:
        return "unclassified", SuitabilityRegimeStatus.UNKNOWN
    return "trending", SuitabilityRegimeStatus.KNOWN


def apply_productive_scope_prerequisites_v1(
    replay_input: IntegratedOfflineReplayInputV1,
    *,
    context: CanonicalMarketContextV1,
) -> IntegratedOfflineReplayInputV1:
    warmup_complete = context.warmup_status == WarmupStatus.WARMUP_COMPLETE
    return replace(
        replay_input,
        scope_prerequisites=ScopeInitializationPrerequisitesV1(
            required_window_complete=warmup_complete,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
    )


def apply_productive_historical_replay_bindings_v1(
    replay_input: IntegratedOfflineReplayInputV1,
    *,
    repo_root: Path,
    instrument_id: str,
    context: CanonicalMarketContextV1,
) -> tuple[IntegratedOfflineReplayInputV1, ProductiveContextBindingReportV1]:
    """Delegate CRS + G17/F1-M9 seam wiring to productive cycle authorities."""
    report = ProductiveContextBindingReportV1()
    typed_eligibility = evaluate_typed_volatility_binding_eligibility_v1(context)
    typed_blocks = collect_typed_volatility_binding_block_reasons_v1(context)
    if typed_blocks:
        report.g17_blocker = str(typed_blocks[0])
    else:
        report.g17_binding_complete = True

    governed_seam, seam_blocker = _resolve_f1_m9_governed_seam_for_integrated_offline_replay_v1(
        repo_root=repo_root,
        apply_ledger_paths=None,
        threshold_ledger_paths=None,
    )
    if seam_blocker:
        report.f1_m9_blocker = seam_blocker
    elif governed_seam is not None:
        report.g17_binding_complete = report.g17_binding_complete and True

    wired = _wire_simulated_economics_crs_boundary_onto_replay_input_v1(
        replay_input,
        instrument_id=instrument_id,
    )
    report.crs_boundary_bound = (
        wired.current_instrument_capital_risk_sizing_boundary_state_file is not None
    )
    report.capital_context_binding_complete = report.crs_boundary_bound

    regime_id, regime_status = resolve_regime_from_context_v1(context)
    wired = replace(
        wired,
        regime_id=regime_id,
        regime_status=regime_status,
        require_productive_typed_volatility_presence_gate=True,
        productive_typed_volatility_binding_eligibility=typed_eligibility,
        governed_authorized_productive_parameter_seam_record=governed_seam,
    )
    wired = apply_productive_scope_prerequisites_v1(wired, context=context)
    return wired, report


def build_strategy_agreement_signal_binding_v1(bars_for_strategy: Any) -> Any | None:
    """MV2 agreement-material assembly (REFERENCE: trend_following signal series)."""
    cfg = load_config()
    try:
        return execute_configured_strategy_signal_series_v1(
            bars_for_strategy,
            strategy_id=HISTORICAL_AGREEMENT_STRATEGY_ID,
            cfg=cfg,
        )
    except StrategySignalBindingError:
        return None


def agreement_material_for_epoch_v1(
    binding: Any,
    *,
    instrument_id: str,
    trading_epoch: int,
) -> Any | None:
    try:
        return normalize_strategy_signal_to_suitability_agreement_material_v1(
            binding,
            instrument_id=instrument_id,
            trading_epoch=trading_epoch,
            expected_configured_strategy_id=HISTORICAL_AGREEMENT_STRATEGY_ID,
        )
    except Exception:  # noqa: BLE001 — per-epoch agreement skip only
        return None


def attach_agreement_material_v1(
    replay_input: IntegratedOfflineReplayInputV1,
    *,
    agreement_material: Any | None,
) -> IntegratedOfflineReplayInputV1:
    if agreement_material is None:
        return replay_input
    return replace(
        replay_input,
        strategy_suitability_agreement_material=agreement_material,
    )


def derive_first_blocking_node_v1(
    *,
    result: IntegratedOfflineReplayResultV1,
) -> str:
    codes = tuple(str(c) for c in (result.evidence.reason_codes or ()))
    if CAPITAL_RISK_CONTEXT_UNRESOLVED in codes:
        return "CAPITAL_RISK_SIZING"
    for code in codes:
        if "TYPED_VOLATILITY" in code or code == "PRESENCE_GATE_UNAVAILABLE":
            return "G17_TYPED_VOLATILITY_PRESENCE_GATE"
        if code.startswith("scope_initialization"):
            return "SCOPE_INITIALIZATION"
        if "confirmation" in code.lower():
            return "CONFIRMATION"
        if "suitability" in code.lower():
            return "SUITABILITY"
        if "composition" in code.lower() or "survival" in code.lower():
            return "DOUBLE_PLAY_COMPOSITION"
        if "SAFETY" in code:
            return "SAFETY"
    inter = result.intermediate
    if inter is not None and inter.composition_result is not None:
        status = inter.composition_result.composition_status
        if status is CompositionStatus.BLOCKED:
            return "DOUBLE_PLAY_COMPOSITION"
    if inter is not None and inter.composition_result is not None:
        status = inter.composition_result.composition_status
        if (
            status
            in {
                CompositionStatus.LONG_SELECTED,
                CompositionStatus.SHORT_SELECTED,
            }
            and inter.capital_risk_sizing_decision is None
        ):
            return "CAPITAL_RISK_SIZING"
    if not result.replay_pass:
        return "REPLAY_FAIL_CLOSED"
    return "NONE"


@dataclass
class DecisionEpochStatsV1:
    observations_total: int = 0
    observations_accepted: int = 0
    decision_epochs: int = 0
    no_action_count: int = 0
    observe_count: int = 0
    enter_long_count: int = 0
    enter_short_count: int = 0
    reduce_count: int = 0
    exit_count: int = 0
    blocked_count: int = 0
    hold_count: int = 0
    execution_eligible_count: int = 0
    order_intent_count: int = 0
    safety_reject_count: int = 0
    canonical_order_intent_present_count: int = 0
    blocking_reason_counts: Counter[str] = field(default_factory=Counter)
    blocking_node_counts: Counter[str] = field(default_factory=Counter)

    def record_replay(
        self,
        *,
        result: IntegratedOfflineReplayResultV1,
        order_intent_increment: int = 0,
    ) -> None:
        outcome = str(result.evidence.decision_outcome or "")
        try:
            parsed = DecisionOutcome(outcome)
        except ValueError:
            parsed = None
        if parsed is DecisionOutcome.NO_ACTION:
            self.no_action_count += 1
        elif parsed is DecisionOutcome.OBSERVE:
            self.observe_count += 1
        elif parsed is DecisionOutcome.ENTER_LONG:
            self.enter_long_count += 1
        elif parsed is DecisionOutcome.ENTER_SHORT:
            self.enter_short_count += 1
        elif parsed is DecisionOutcome.REDUCE:
            self.reduce_count += 1
        elif parsed is DecisionOutcome.BLOCKED:
            self.blocked_count += 1
        elif parsed is DecisionOutcome.HOLD:
            self.hold_count += 1
        elif parsed is not None and parsed.value.startswith("exit"):
            self.exit_count += 1
        elif outcome.startswith("exit"):
            self.exit_count += 1

        if result.evidence.execution_eligible:
            self.execution_eligible_count += 1
        if order_intent_increment:
            self.order_intent_count += order_intent_increment
        if any("SAFETY" in str(c) for c in (result.evidence.reason_codes or ())):
            self.safety_reject_count += 1
        if result.intermediate is not None and result.intermediate.canonical_order_intent:
            self.canonical_order_intent_present_count += 1

        primary_reason = (
            str(result.evidence.reason_codes[0])
            if result.evidence.reason_codes
            else "NO_REASON_CODE"
        )
        self.blocking_reason_counts[primary_reason] += 1
        node = derive_first_blocking_node_v1(result=result)
        self.blocking_node_counts[node] += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "observations_total": self.observations_total,
            "observations_accepted": self.observations_accepted,
            "decision_epochs": self.decision_epochs,
            "no_action_count": self.no_action_count,
            "observe_count": self.observe_count,
            "enter_long_count": self.enter_long_count,
            "enter_short_count": self.enter_short_count,
            "reduce_count": self.reduce_count,
            "exit_count": self.exit_count,
            "blocked_count": self.blocked_count,
            "hold_count": self.hold_count,
            "execution_eligible_count": self.execution_eligible_count,
            "order_intent_count": self.order_intent_count,
            "safety_reject_count": self.safety_reject_count,
            "canonical_order_intent_present_count": self.canonical_order_intent_present_count,
        }


def update_binding_report_from_replay_v1(
    report: ProductiveContextBindingReportV1,
    *,
    result: IntegratedOfflineReplayResultV1,
) -> None:
    inter = result.intermediate
    if inter is None:
        return
    report.cap61_binding_complete = True
    report.confirmation_binding_complete = True
    report.host_confirmation_binding_complete = True
    if inter.composition_result is not None:
        report.scope_gge_binding_complete = True
        report.double_play_binding_complete = True
    if inter.bull_suitability is not None or inter.bear_suitability is not None:
        report.suitability_binding_complete = True
    if inter.capital_risk_sizing_decision is not None:
        report.risk_context_binding_complete = True
        report.sizing_binding_complete = True
    if inter.canonical_order_intent is not None:
        report.capital_context_binding_complete = True


def prove_capital_context_enables_sizing_v1(
    *,
    replay_fn: Any,
    build_replay_input: Any,
    scan_limit: int = 50_000,
) -> tuple[bool, str, int | None]:
    """Scan early epochs for CRS-bound sizing on composition-selected decisions."""
    for epoch in range(scan_limit):
        built = build_replay_input(epoch)
        if built is None:
            continue
        result = replay_fn(built)
        inter = result.intermediate
        if inter is None or inter.composition_result is None:
            continue
        status = inter.composition_result.composition_status
        if status not in {
            CompositionStatus.LONG_SELECTED,
            CompositionStatus.SHORT_SELECTED,
        }:
            continue
        if CAPITAL_RISK_CONTEXT_UNRESOLVED in (result.evidence.reason_codes or ()):
            return False, "CAPITAL_RISK_CONTEXT_UNRESOLVED_ON_SELECTED_COMPOSITION", epoch
        if inter.capital_risk_sizing_decision is None:
            return False, "SIZING_DECISION_ABSENT_ON_SELECTED_COMPOSITION", epoch
        return True, "CRS_SIZING_BOUND_ON_SELECTED_COMPOSITION", epoch
    return False, "NO_COMPOSITION_SELECTED_EPOCH_IN_SCAN_WINDOW", None
