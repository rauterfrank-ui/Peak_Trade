# src/trading/master_v2/scenario_matrix_v1.py
"""
Master V2 — Canonical scenario matrix (contract v1)

Benannte Standardfaelle nur aus bestehender validate/critic/replay-Semantik; keine
neue Policy, kein I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional, Tuple

from .decision_packet_fixtures_v1 import (
    sample_doubleplay_decision_v1,
    sample_risk_caps_result_v1,
    sample_safety_decision_v1,
    sample_scope_envelope_v1,
    sample_universe_selection_v1,
)
from .decision_packet_snapshot_v1 import decision_packet_to_snapshot_v1
from .decision_packet_v1 import (
    MASTER_V2_DECISION_PACKET_LAYER_VERSION,
    MasterV2DecisionPacketV1,
    RiskExposureCapHandoffV1,
    SafetyKillSwitchHandoffV1,
    build_master_v2_decision_packet_v1,
    validate_master_v2_decision_packet_v1,
)
from .staged_execution_enablement_v1 import ExecutionStageV1, StagedExecutionEnablementInputV1

SCENARIO_MATRIX_LAYER_VERSION = "v1"

# Stabile Szenario-Namen (keine Leerzeichen; regressionssicher)
SCENARIO_HAPPY_LIVE_GATED = "happy_live_gated"
SCENARIO_SAFETY_BLOCKED = "safety_blocked"
SCENARIO_RISK_BLOCKED = "risk_blocked"
SCENARIO_LIVE_AUTH_MISSING_ACK = "live_auth_missing_ack"
SCENARIO_OPTIONAL_LAYERS_MISSING = "optional_layers_missing"

_ALL_NAMES: Tuple[str, ...] = (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_SAFETY_BLOCKED,
    SCENARIO_RISK_BLOCKED,
    SCENARIO_LIVE_AUTH_MISSING_ACK,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
)


@dataclass(frozen=True)
class ScenarioExpectedOutcomeV1:
    """Erwartete Readouts; nur Teil-Mengen an Codes, wo noetig."""

    validate_ok: bool
    critic_has_error_findings: bool
    expect_validate_reason_substrings: Tuple[str, ...] = ()
    """Muss in validate.reason_codes vorkommen (wenn validate_ok false)."""

    expect_critic_codes: Tuple[str, ...] = ()
    """Muss in critic-Findings vorkommen (codes)."""

    expect_critic_warning_layer_missing: bool = False
    """Kurzform: LAYER_MISSING_OPTIONAL als Warning."""


@dataclass(frozen=True)
class MasterV2ScenarioCaseV1:
    name: str
    description: str
    packet: MasterV2DecisionPacketV1
    snapshot: Optional[Dict[str, object]]
    expected: ScenarioExpectedOutcomeV1

    def to_dict(self) -> dict:
        return {
            "layer_version": SCENARIO_MATRIX_LAYER_VERSION,
            "name": self.name,
            "description": self.description,
            "has_snapshot": self.snapshot is not None,
        }


def _snap_if_ok(p: MasterV2DecisionPacketV1) -> Optional[Dict[str, object]]:
    v = validate_master_v2_decision_packet_v1(p)
    if not v.ok:
        return None
    return decision_packet_to_snapshot_v1(p, require_consistent_packet=True)


def _case_happy_live_gated() -> MasterV2ScenarioCaseV1:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.LIVE_GATED,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    p = build_master_v2_decision_packet_v1(
        f"scn-{SCENARIO_HAPPY_LIVE_GATED}",
        sei,
        universe=sample_universe_selection_v1(),
        doubleplay=sample_doubleplay_decision_v1(),
        scope_envelope=sample_scope_envelope_v1(),
        risk_cap=sample_risk_caps_result_v1(),
        safety=sample_safety_decision_v1(
            safety_decision_allowed=sei.safety_decision_allowed,
        ),
    )
    return MasterV2ScenarioCaseV1(
        name=SCENARIO_HAPPY_LIVE_GATED,
        description="Vollstaendige optionale layer; ein Schritt testnet->live_gated; safety erlaubt",
        packet=p,
        snapshot=_snap_if_ok(p),
        expected=ScenarioExpectedOutcomeV1(
            validate_ok=True,
            critic_has_error_findings=False,
        ),
    )


def _case_safety_blocked() -> MasterV2ScenarioCaseV1:
    """safety-Handoff widerspricht safety_decision_allowed im staged input (validate fail)."""
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.BACKTEST,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    p = build_master_v2_decision_packet_v1(
        f"scn-{SCENARIO_SAFETY_BLOCKED}",
        sei,
        safety=SafetyKillSwitchHandoffV1(
            layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
            safety_decision_allowed=False,
        ),
    )
    return MasterV2ScenarioCaseV1(
        name=SCENARIO_SAFETY_BLOCKED,
        description="SAFETY_HANDOFF_STAGED_INPUT_MISMATCH (keine Stille-Heilung)",
        packet=p,
        snapshot=None,
        expected=ScenarioExpectedOutcomeV1(
            validate_ok=False,
            critic_has_error_findings=True,
            expect_validate_reason_substrings=("SAFETY_HANDOFF_STAGED_INPUT_MISMATCH",),
            expect_critic_codes=("SAFETY_ENABLEMENT_MISMATCH",),
        ),
    )


def _case_risk_blocked() -> MasterV2ScenarioCaseV1:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    p = build_master_v2_decision_packet_v1(
        f"scn-{SCENARIO_RISK_BLOCKED}",
        sei,
        risk_cap=RiskExposureCapHandoffV1(
            layer_version="v1",
            cap_satisfied=False,
        ),
        safety=sample_safety_decision_v1(
            safety_decision_allowed=sei.safety_decision_allowed,
        ),
    )
    return MasterV2ScenarioCaseV1(
        name=SCENARIO_RISK_BLOCKED,
        description="Risk cap unbefriedigt bei erlaubtem enablement (validate fail)",
        packet=p,
        snapshot=None,
        expected=ScenarioExpectedOutcomeV1(
            validate_ok=False,
            critic_has_error_findings=True,
            expect_validate_reason_substrings=("RISK_CAP_BLOCKED_BUT_ENABLEMENT_ALLOWED",),
            expect_critic_codes=("BLOCKED_BUT_ENABLEMENT_ALLOWED",),
        ),
    )


def _case_live_auth_missing_ack() -> MasterV2ScenarioCaseV1:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.LIVE_GATED,
        requested_stage=ExecutionStageV1.LIVE_AUTHORIZED,
        safety_decision_allowed=True,
        live_authority_acknowledged=False,
    )
    p = build_master_v2_decision_packet_v1(
        f"scn-{SCENARIO_LIVE_AUTH_MISSING_ACK}",
        sei,
        safety=sample_safety_decision_v1(
            safety_decision_allowed=sei.safety_decision_allowed,
        ),
    )
    return MasterV2ScenarioCaseV1(
        name=SCENARIO_LIVE_AUTH_MISSING_ACK,
        description="LIVE_AUTH_ACK_REQUIRED ohne separates ack",
        packet=p,
        snapshot=None,
        expected=ScenarioExpectedOutcomeV1(
            validate_ok=False,
            critic_has_error_findings=True,
            expect_validate_reason_substrings=("LIVE_AUTH_ACK_REQUIRED",),
            expect_critic_codes=("LIVE_AUTH_ACK_MISSING",),
        ),
    )


def _case_optional_layers_missing() -> MasterV2ScenarioCaseV1:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.LIVE_GATED,
        safety_decision_allowed=True,
    )
    p = build_master_v2_decision_packet_v1(
        f"scn-{SCENARIO_OPTIONAL_LAYERS_MISSING}",
        sei,
    )
    return MasterV2ScenarioCaseV1(
        name=SCENARIO_OPTIONAL_LAYERS_MISSING,
        description="Fortgeschrittene Stufe ohne optionale vorgelagerte layer-Handoffs (critic warn)",
        packet=p,
        snapshot=_snap_if_ok(p),
        expected=ScenarioExpectedOutcomeV1(
            validate_ok=True,
            critic_has_error_findings=False,
            expect_critic_codes=("LAYER_MISSING_OPTIONAL",),
            expect_critic_warning_layer_missing=True,
        ),
    )


def build_master_v2_scenario_matrix_v1() -> Dict[str, MasterV2ScenarioCaseV1]:
    """Deterministische Map name -> Szenariofall."""
    m = (
        _case_happy_live_gated(),
        _case_safety_blocked(),
        _case_risk_blocked(),
        _case_live_auth_missing_ack(),
        _case_optional_layers_missing(),
    )
    return {c.name: c for c in m}


def get_master_v2_scenario_case_v1(name: str) -> MasterV2ScenarioCaseV1:
    m = build_master_v2_scenario_matrix_v1()
    if name not in m:
        raise KeyError(f"unbekanntes szenario: {name!r}; erlaubt: {_ALL_NAMES!r}")
    return m[name]


def scenario_matrix_all_names_v1() -> FrozenSet[str]:
    return frozenset(_ALL_NAMES)
