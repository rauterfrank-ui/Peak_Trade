"""Producer → provenance bindings v1. Maps CURRENT seams to orthogonal provenance dimensions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Final, Mapping

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_v1 import (
    DecisionSourceV1,
    DdoLedgerEnvironmentV1,
    ExecutionModeLabelV1,
    ExternalCapitalFlowClassV1,
    FillSourceTypeV1,
    MarketObservationSourceV1,
    OutcomeRealizationKindV1,
    OutcomeSemanticClassV1,
    build_outcome_evidence_provenance_v1,
)

BINDING_ID: Final[str] = "peak_trade.learning.ddo.outcome_evidence_provenance_bindings_v1"


class ProvenanceProducerBindingV1(str, Enum):
    PRODUCTIVE_PRE_EXTERNAL_N_BARS = "PRODUCTIVE_PRE_EXTERNAL_N_BARS"
    INTERNAL_SIM_BRIDGE = "INTERNAL_SIM_BRIDGE"
    I67_PAPER_SIM = "I67_PAPER_SIM"
    I17_SHADOW_COUNTERFACTUAL = "I17_SHADOW_COUNTERFACTUAL"
    TESTNET_BOUNDED_OBSERVATION = "TESTNET_BOUNDED_OBSERVATION"
    REPLAY_HISTORICAL = "REPLAY_HISTORICAL"
    CANARY_EVIDENCE = "CANARY_EVIDENCE"
    DDO_CHALLENGER_SHADOW = "DDO_CHALLENGER_SHADOW"


@dataclass(frozen=True)
class ProvenanceBindingContextV1:
    decision_event_ref: str
    producer_id: str
    producer_version: str | None = None
    instrument_id: str | None = None
    venue_native_id: str | None = None
    cycle_id: str | None = None
    trading_epoch: str | None = None
    outcome_scalar_kind: str | None = None
    evaluation_horizon: str | None = None
    market_timestamp_utc: str | None = None
    decision_timestamp_utc: str | None = None
    evaluation_timestamp_utc: str | None = None
    ddo_ledger_environment: ExecutionEnvironment | None = None
    order_environment_label: str | None = None
    lineage_digest: str = UNKNOWN


def _map_execution_environment(env: ExecutionEnvironment | None) -> str:
    if env is None:
        return DdoLedgerEnvironmentV1.UNKNOWN.value
    mapping = {
        ExecutionEnvironment.DEV: DdoLedgerEnvironmentV1.DEV.value,
        ExecutionEnvironment.SHADOW: DdoLedgerEnvironmentV1.SHADOW.value,
        ExecutionEnvironment.TESTNET: DdoLedgerEnvironmentV1.TESTNET.value,
        ExecutionEnvironment.PROD: DdoLedgerEnvironmentV1.PROD.value,
    }
    return mapping.get(env, DdoLedgerEnvironmentV1.UNKNOWN.value)


def resolve_provenance_for_binding_v1(
    binding: ProvenanceProducerBindingV1,
    ctx: ProvenanceBindingContextV1,
) -> dict[str, Any]:
    """Return a validated provenance object for a known producer binding."""
    base: dict[str, Any] = {
        "decision_event_ref": ctx.decision_event_ref,
        "producer_id": ctx.producer_id,
        "producer_version": ctx.producer_version,
        "instrument_id": ctx.instrument_id or UNKNOWN,
        "venue_native_id": ctx.venue_native_id or UNKNOWN,
        "cycle_id": ctx.cycle_id,
        "trading_epoch": ctx.trading_epoch or UNKNOWN,
        "outcome_scalar_kind": ctx.outcome_scalar_kind or UNKNOWN,
        "evaluation_horizon": ctx.evaluation_horizon or UNKNOWN,
        "market_timestamp_utc": ctx.market_timestamp_utc,
        "decision_timestamp_utc": ctx.decision_timestamp_utc,
        "evaluation_timestamp_utc": ctx.evaluation_timestamp_utc,
        "ddo_ledger_environment": _map_execution_environment(ctx.ddo_ledger_environment),
        "order_environment_label": ctx.order_environment_label or UNKNOWN,
        "lineage_digest": ctx.lineage_digest,
        "external_capital_flow_class": ExternalCapitalFlowClassV1.NONE.value,
        "provenance_status": "KNOWN",
    }
    if binding is ProvenanceProducerBindingV1.PRODUCTIVE_PRE_EXTERNAL_N_BARS:
        base.update(
            {
                "market_observation_source": MarketObservationSourceV1.INJECTED_C1.value,
                "decision_source": DecisionSourceV1.PRODUCTIVE_MV2_DP_PRE_EXTERNAL.value,
                "execution_mode_label": ExecutionModeLabelV1.NO_EXECUTION.value,
                "fill_source_type": FillSourceTypeV1.NO_FILL.value,
                "position_truth_source": "RECONCILIATION_ADMISSION",
                "reconciliation_source": "PRODUCTIVE_RECON",
                "accounting_source": "SIMULATED_ECONOMICS_PARALLEL",
                "outcome_source": "N_BARS_HORIZON_ENGINE",
                "outcome_semantic_class": (
                    OutcomeSemanticClassV1.OBSERVED_PRODUCTIVE_PRE_EXTERNAL.value
                ),
                "outcome_realization_kind": OutcomeRealizationKindV1.OBSERVATION_ONLY.value,
            }
        )
    elif binding is ProvenanceProducerBindingV1.INTERNAL_SIM_BRIDGE:
        base.update(
            {
                "market_observation_source": MarketObservationSourceV1.PUBLIC_MD.value,
                "decision_source": DecisionSourceV1.INTERNAL_SIM_BRIDGE.value,
                "execution_mode_label": ExecutionModeLabelV1.INTERNAL_SIMULATED_EXECUTION.value,
                "fill_source_type": FillSourceTypeV1.SIMULATED.value,
                "accounting_source": "SIMULATED_PORTFOLIO_ECONOMICS",
                "outcome_source": "CAP7_WALLCLOCK_BRIDGE",
                "outcome_semantic_class": OutcomeSemanticClassV1.INTERNAL_SIMULATED_OUTCOME.value,
                "outcome_realization_kind": OutcomeRealizationKindV1.SIMULATED.value,
            }
        )
    elif binding is ProvenanceProducerBindingV1.I67_PAPER_SIM:
        base.update(
            {
                "market_observation_source": MarketObservationSourceV1.CALLER_SUPPLIED.value,
                "decision_source": DecisionSourceV1.I67_PAPER_SIM.value,
                "execution_mode_label": ExecutionModeLabelV1.SIMULATED.value,
                "fill_source_type": FillSourceTypeV1.SIMULATED.value,
                "accounting_source": "I67_LOCAL",
                "outcome_source": "I67_PAPER_SIMULATOR",
                "outcome_semantic_class": OutcomeSemanticClassV1.I67_PAPER_SIM_OUTCOME.value,
                "outcome_realization_kind": OutcomeRealizationKindV1.SIMULATED.value,
            }
        )
    elif binding is ProvenanceProducerBindingV1.I17_SHADOW_COUNTERFACTUAL:
        base.update(
            {
                "market_observation_source": MarketObservationSourceV1.PUBLIC_MD.value,
                "decision_source": DecisionSourceV1.I17_SHADOW_OBS.value,
                "execution_mode_label": ExecutionModeLabelV1.NO_EXECUTION.value,
                "fill_source_type": FillSourceTypeV1.NO_FILL.value,
                "outcome_source": "I17_SHADOW_OBSERVATION",
                "outcome_semantic_class": OutcomeSemanticClassV1.SHADOW_COUNTERFACTUAL.value,
                "outcome_realization_kind": OutcomeRealizationKindV1.COUNTERFACTUAL.value,
            }
        )
    elif binding is ProvenanceProducerBindingV1.DDO_CHALLENGER_SHADOW:
        base.update(
            {
                "market_observation_source": MarketObservationSourceV1.NOT_APPLICABLE.value,
                "decision_source": DecisionSourceV1.DDO_OBSERVATION.value,
                "execution_mode_label": ExecutionModeLabelV1.NO_EXECUTION.value,
                "fill_source_type": FillSourceTypeV1.NO_FILL.value,
                "outcome_source": "DDO_CHALLENGER_V0",
                "outcome_semantic_class": OutcomeSemanticClassV1.SHADOW_COUNTERFACTUAL.value,
                "outcome_realization_kind": OutcomeRealizationKindV1.COUNTERFACTUAL.value,
            }
        )
    elif binding is ProvenanceProducerBindingV1.TESTNET_BOUNDED_OBSERVATION:
        base.update(
            {
                "market_observation_source": MarketObservationSourceV1.TESTNET_BOUNDED.value,
                "decision_source": DecisionSourceV1.TESTNET_COMPLETION.value,
                "execution_mode_label": ExecutionModeLabelV1.TESTNET.value,
                "fill_source_type": FillSourceTypeV1.NO_FILL.value,
                "outcome_source": "BOUNDED_TESTNET_OBSERVATION",
                "outcome_semantic_class": OutcomeSemanticClassV1.TESTNET_VENUE_EVIDENCE.value,
                "outcome_realization_kind": OutcomeRealizationKindV1.OBSERVATION_ONLY.value,
                "ddo_ledger_environment": DdoLedgerEnvironmentV1.TESTNET.value,
            }
        )
    elif binding is ProvenanceProducerBindingV1.REPLAY_HISTORICAL:
        base.update(
            {
                "market_observation_source": MarketObservationSourceV1.REPLAY_HISTORICAL.value,
                "decision_source": DecisionSourceV1.REPLAY_SEMANTIC.value,
                "execution_mode_label": ExecutionModeLabelV1.NOT_APPLICABLE.value,
                "fill_source_type": FillSourceTypeV1.NOT_APPLICABLE.value,
                "outcome_source": "DDO_SEMANTIC_REPLAY",
                "outcome_semantic_class": OutcomeSemanticClassV1.REPLAY_HISTORICAL.value,
                "outcome_realization_kind": OutcomeRealizationKindV1.REPLAYED.value,
            }
        )
    elif binding is ProvenanceProducerBindingV1.CANARY_EVIDENCE:
        base.update(
            {
                "market_observation_source": MarketObservationSourceV1.PUBLIC_MD.value,
                "decision_source": DecisionSourceV1.CANARY_EVIDENCE.value,
                "execution_mode_label": ExecutionModeLabelV1.LIVE.value,
                "fill_source_type": FillSourceTypeV1.UNKNOWN.value,
                "outcome_source": "CANARY_VENUE_PROOF",
                "outcome_semantic_class": OutcomeSemanticClassV1.CANARY_EVIDENCE.value,
                "outcome_realization_kind": OutcomeRealizationKindV1.OBSERVATION_ONLY.value,
            }
        )
    else:
        base["provenance_status"] = "UNKNOWN"
        base["outcome_semantic_class"] = OutcomeSemanticClassV1.UNKNOWN.value
        base["outcome_realization_kind"] = OutcomeRealizationKindV1.UNKNOWN.value
    return dict(build_outcome_evidence_provenance_v1(base))


def binding_reachable_for_learning_v1(binding: ProvenanceProducerBindingV1) -> bool:
    """Whether CURRENT wiring can reach DDO learning ingest for this binding."""
    return binding in {
        ProvenanceProducerBindingV1.PRODUCTIVE_PRE_EXTERNAL_N_BARS,
        ProvenanceProducerBindingV1.INTERNAL_SIM_BRIDGE,
        ProvenanceProducerBindingV1.DDO_CHALLENGER_SHADOW,
        ProvenanceProducerBindingV1.REPLAY_HISTORICAL,
    }
