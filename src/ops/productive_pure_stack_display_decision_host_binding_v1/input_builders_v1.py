"""Productive Pure-Stack input builders — fail-closed without invented authority.

Each builder returns either a typed input or raises
``CanonicalInputAuthorityAbsentError``. No fixtures, scenario defaults,
WebUI data, ResultV1 conversion, or semantic remapping.
"""

from __future__ import annotations

from typing import Any, Optional

from trading.master_v2.double_play_capital_slot import CapitalSlotConfig, CapitalSlotState
from trading.master_v2.double_play_futures_input import FuturesInputSnapshot
from trading.master_v2.double_play_state import TransitionDecision
from trading.master_v2.double_play_suitability import SuitabilityProjectionInput
from trading.master_v2.double_play_survival import DoublePlaySurvivalEnvelope

from src.ops.productive_pure_stack_display_decision_host_binding_v1.authority_inventory_v1 import (
    probe_pure_stack_display_input_authorities_v1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.constants_v1 import (
    FIXTURE_FALLBACK_AUTHORIZED,
    RESULTV1_MAPPING_AUTHORIZED,
    SCENARIO_DEFAULT_AUTHORIZED,
    STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT,
    WEBUI_DATA_AUTHORIZED,
)


class CanonicalInputAuthorityAbsentError(RuntimeError):
    """Raised when a required Pure-Stack input lacks ratified source authority."""

    def __init__(self, input_name: str, detail: str = "") -> None:
        self.input_name = input_name
        self.code = STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT
        msg = f"{self.code}:{input_name}"
        if detail:
            msg = f"{msg}:{detail}"
        super().__init__(msg)


def _probe(input_name: str) -> None:
    for probe in probe_pure_stack_display_input_authorities_v1():
        if probe.input_name == input_name:
            if not probe.authority_present:
                raise CanonicalInputAuthorityAbsentError(input_name, probe.detail)
            return
    raise CanonicalInputAuthorityAbsentError(input_name, "unknown_input")


def assert_no_unauthorized_fallback_flags_v1() -> None:
    if RESULTV1_MAPPING_AUTHORIZED:
        raise RuntimeError("RESULTV1_MAPPING_MUST_REMAIN_FALSE")
    if FIXTURE_FALLBACK_AUTHORIZED:
        raise RuntimeError("FIXTURE_FALLBACK_MUST_REMAIN_FALSE")
    if SCENARIO_DEFAULT_AUTHORIZED:
        raise RuntimeError("SCENARIO_DEFAULT_MUST_REMAIN_FALSE")
    if WEBUI_DATA_AUTHORIZED:
        raise RuntimeError("WEBUI_DATA_MUST_REMAIN_FALSE")


def build_productive_futures_input_snapshot_v1(
    *,
    authorized_snapshot: Optional[FuturesInputSnapshot] = None,
) -> FuturesInputSnapshot:
    """Build FuturesInputSnapshot only from an already-authorized productive source."""
    assert_no_unauthorized_fallback_flags_v1()
    _probe("FuturesInputSnapshot")
    if authorized_snapshot is None:
        raise CanonicalInputAuthorityAbsentError(
            "FuturesInputSnapshot",
            "authorized_snapshot_argument_required_when_authority_present",
        )
    return authorized_snapshot


def build_productive_survival_envelope_v1(
    *,
    authorized_envelope: Optional[DoublePlaySurvivalEnvelope] = None,
) -> DoublePlaySurvivalEnvelope:
    assert_no_unauthorized_fallback_flags_v1()
    _probe("DoublePlaySurvivalEnvelope")
    if authorized_envelope is None:
        raise CanonicalInputAuthorityAbsentError(
            "DoublePlaySurvivalEnvelope",
            "authorized_envelope_argument_required_when_authority_present",
        )
    return authorized_envelope


def build_productive_suitability_projection_input_v1(
    *,
    authorized_input: Optional[SuitabilityProjectionInput] = None,
) -> SuitabilityProjectionInput:
    assert_no_unauthorized_fallback_flags_v1()
    _probe("SuitabilityProjectionInput")
    if authorized_input is None:
        raise CanonicalInputAuthorityAbsentError(
            "SuitabilityProjectionInput",
            "authorized_input_argument_required_when_authority_present",
        )
    return authorized_input


def build_productive_capital_slot_config_v1(
    *,
    authorized_config: Optional[CapitalSlotConfig] = None,
) -> CapitalSlotConfig:
    assert_no_unauthorized_fallback_flags_v1()
    _probe("CapitalSlotConfig")
    if authorized_config is None:
        raise CanonicalInputAuthorityAbsentError(
            "CapitalSlotConfig",
            "authorized_config_argument_required_when_authority_present",
        )
    return authorized_config


def build_productive_capital_slot_state_v1(
    *,
    authorized_state: Optional[CapitalSlotState] = None,
) -> CapitalSlotState:
    assert_no_unauthorized_fallback_flags_v1()
    _probe("CapitalSlotState")
    if authorized_state is None:
        raise CanonicalInputAuthorityAbsentError(
            "CapitalSlotState",
            "authorized_state_argument_required_when_authority_present",
        )
    return authorized_state


def extract_transition_decision_passthrough_v1(
    *,
    transition_decision: Optional[TransitionDecision],
) -> TransitionDecision:
    """Pass through the identical TransitionDecision from transition_state."""
    assert_no_unauthorized_fallback_flags_v1()
    _probe("TransitionDecision")
    if transition_decision is None:
        raise CanonicalInputAuthorityAbsentError(
            "TransitionDecision",
            "transition_decision_missing_from_replay_intermediate",
        )
    if not isinstance(transition_decision, TransitionDecision):
        raise CanonicalInputAuthorityAbsentError(
            "TransitionDecision",
            f"unexpected_type:{type(transition_decision).__name__}",
        )
    return transition_decision


def reject_resultv1_mapping_attempt_v1(source: Any) -> None:
    """Fail-closed guard: ResultV1 objects must never become Pure-Stack Decisions."""
    name = type(source).__name__
    forbidden_suffixes = ("ResultV1", "EvidenceV1", "PolicyDecisionV0")
    if any(name.endswith(suffix) for suffix in forbidden_suffixes):
        raise CanonicalInputAuthorityAbsentError(
            name,
            "RESULTV1_MAPPING_FORBIDDEN",
        )
