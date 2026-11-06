# src/trading/master_v2/staged_execution_enablement_v1.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

STAGED_EXECUTION_ENABLEMENT_LAYER_VERSION = "v1"


class ExecutionStageV1(str, Enum):
    BACKTEST = "backtest"
    RESEARCH = "research"
    TESTNET = "testnet"
    LIVE_GATED = "live_gated"
    LIVE_AUTHORIZED = "live_authorized"


@dataclass(frozen=True)
class StagedExecutionEnablementInputV1:
    current_stage: ExecutionStageV1
    requested_stage: ExecutionStageV1
    safety_decision_allowed: bool
    live_authority_acknowledged: bool = False


@dataclass(frozen=True)
class StagedExecutionEnablementDecisionV1:
    """Evaluationsergebnis; keine I/O, nur strukturierte Werte."""

    layer_version: str
    can_progress: bool
    reason_code: str


def validate_staged_execution_enablement_input_v1(
    inp: StagedExecutionEnablementInputV1,
) -> None:
    if not isinstance(inp.current_stage, ExecutionStageV1) or not isinstance(
        inp.requested_stage, ExecutionStageV1
    ):
        raise TypeError("stages must be ExecutionStageV1")
    if inp.safety_decision_allowed not in (True, False):
        raise TypeError("safety_decision_allowed must be bool")
    if inp.live_authority_acknowledged not in (True, False):
        raise TypeError("live_authority_acknowledged must be bool")


def evaluate_staged_execution_enablement_v1(
    inp: StagedExecutionEnablementInputV1,
) -> StagedExecutionEnablementDecisionV1:
    """Minimaler, deterministischer Schritt-Check fuer Fixture-/Szenarien-Gebrauch."""
    validate_staged_execution_enablement_input_v1(inp)
    can = inp.current_stage != inp.requested_stage
    if (
        inp.current_stage is ExecutionStageV1.LIVE_GATED
        and inp.requested_stage is ExecutionStageV1.LIVE_AUTHORIZED
        and not inp.live_authority_acknowledged
    ):
        can = False
    return StagedExecutionEnablementDecisionV1(
        layer_version=STAGED_EXECUTION_ENABLEMENT_LAYER_VERSION,
        can_progress=bool(can and inp.safety_decision_allowed),
        reason_code="OK" if can else "BLOCKED",
    )
