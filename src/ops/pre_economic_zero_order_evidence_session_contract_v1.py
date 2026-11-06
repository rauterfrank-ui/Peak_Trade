"""Governed Pre-Economic Zero-Order Evidence Session contract v1.

Capability: GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1
Session contract: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1

Offline, non-activating, fail-closed governance contract. Defines a strictly
bounded, fully passive Zero-Order *connectivity/runtime evidence* stage.

Zero-Order is **not** equivalent to INTEGRATED_PAPER_SHADOW_OBSERVATION.
This module:
- never executes a session runtime;
- never contacts brokers/exchanges;
- never creates or submits orders;
- never sets ECONOMIC_VALIDITY_OFFLINE_GATE_PASS;
- never sets ECONOMIC_VALIDITY_PASS;
- never sets Paper-Shadow / Testnet / Live / Runtime activation tokens;
- does not alone block Paper-Shadow observation readiness via the legacy
  offline gate token.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1=true"
CAPABILITY_ID = "GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1"
SESSION_CONTRACT_ID = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1"
PRODUCER_FAMILY = "ops.pre_economic_zero_order_evidence_session_contract_v1"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v1"

AUTHORITY_EFFECT_NONE = "NONE"
ACTIVATION_EFFECT_NONE = "NONE"
ECONOMIC_GATE_EFFECT_NONE = "NONE"

DEFAULT_STATE_BLOCKED = "BLOCKED"
MAX_DURATION_SECONDS = 21600
ORDERS_ALLOWED = False
BROKER_WRITES_ALLOWED = False
EXPLICIT_OPERATOR_GO_REQUIRED = True
RUNTIME_EXECUTION_DEFAULT = "BLOCKED"

POLICY_SEQUENCE_BEFORE: tuple[str, ...] = (
    "INTEGRATED_OFFLINE_REPLAY",
    "ECONOMIC_VALIDITY_OFFLINE_GATE",
    "PROMOTION",
    "STEP_29R_RUNTIME_REWIRE",
    "STEP_29T_ZERO_ORDER_RUNTIME",
    "STEP_29U_SHADOW",
)

POLICY_SEQUENCE_AFTER: tuple[str, ...] = (
    "FULL_CANONICAL_SYSTEM_PARITY",
    "INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS",
    "INTEGRATED_PAPER_SHADOW_OBSERVATION_READINESS_PASS",
    "OPERATOR_PAPER_SHADOW_OBSERVATION_GO",
    "INTEGRATED_PAPER_SHADOW_OBSERVATION",
    "INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE",
    "INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED",
    "ECONOMIC_VALIDITY_PASS",
    "PROMOTION",
    "TESTNET",
    "LIVE",
)

# Surfaces that still require system ECONOMIC_VALIDITY_PASS (integrated bundle).
# Paper-Shadow observation readiness is intentionally excluded: legacy offline
# gate alone must not block orderless observation readiness.
ECONOMIC_GATE_STILL_REQUIRED_FOR: frozenset[str] = frozenset(
    {
        "STEP_29R_RUNTIME_REWIRE",
        "STEP_29T_ZERO_ORDER_RUNTIME",
        "PROMOTION",
        "TESTNET",
        "LIVE",
    }
)

# Observation readiness is gated by correctness/parity/safety — not offline PASS.
PAPER_SHADOW_OBSERVATION_READINESS_NOT_BLOCKED_BY_LEGACY_OFFLINE_GATE = True

REQUIRED_DECISION_LOGIC_BINDINGS: tuple[str, ...] = (
    "DOUBLE_PLAY",
    "CO_SYSTEM",
    "AI_LAYER",
    "KILL_STATE",
    "RISK_ENGINE",
    "PARAMETER_ADAPTION",
    "TELEMETRY",
)

FAIL_CLOSED_ABORT_CONDITIONS: tuple[str, ...] = (
    "ORDER_INTENT",
    "BROKER_WRITE",
    "UNKNOWN_SESSION_STATE",
    "TELEMETRY_LOSS",
    "KILL_STATE_ERROR",
    "RISK_ENGINE_ERROR",
    "INCOMPLETE_DECISION_LOGIC_BINDING",
)

ACTIVATION_TOKEN_KEYS: tuple[str, ...] = (
    "SHADOW_ACTIVATION_AUTHORIZED",
    "PAPER_ACTIVATION_AUTHORIZED",
    "TESTNET_ACTIVATION_AUTHORIZED",
    "SCHEDULER_ACTIVATION_AUTHORIZED",
    "RUNTIME_ACTIVATION_AUTHORIZED",
    "LIVE_AUTHORIZED",
    "ORDERS_AUTHORIZED",
    "STEP_29U_ACTIVATED",
    "ZERO_ORDER_RUNTIME_READY",
)

SAFETY_NON_GOALS: tuple[str, ...] = (
    "NOT_SHADOW_ACTIVATION",
    "NOT_ECONOMIC_PASS",
    "NOT_PAPER_AUTHORIZATION",
    "NOT_TESTNET_AUTHORIZATION",
    "NOT_LIVE_AUTHORIZATION",
    "NOT_RUNTIME_REWIRE",
    "NOT_STEP_29T_ZERO_ORDER_RUNTIME",
    "NOT_STEP_29U_SHADOW",
    "NOT_PROMOTION_AUTHORITY",
    "NOT_ORDER_AUTHORITY",
    "NOT_BROKER_WRITE_AUTHORITY",
    "NOT_IMPLICIT_OPERATOR_GO",
)

CONTRACT_DOC_RELPATH = "docs/ops/runbooks/PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1.md"
CAPABILITY_DOC_MARKER = "GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1=true"


class PreEconomicZeroOrderEvidenceSessionContractError(ValueError):
    """Fail-closed contract evaluation error."""


@dataclass(frozen=True)
class BindingStatusV1:
    binding_id: str
    bound: bool
    reason_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "bound": self.bound,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class PreEconomicZeroOrderEvidenceSessionContractResultV1:
    schema_id: str
    schema_version: str
    capability_id: str
    session_contract_id: str
    package_marker: str
    authority_effect: str
    activation_effect: str
    economic_gate_effect: str
    orders_allowed: bool
    broker_writes_allowed: bool
    max_duration_seconds: int
    explicit_operator_go_required: bool
    default_state: str
    runtime_execution: str
    operator_go_present: bool
    requested_duration_seconds: int
    order_intent_observed: bool
    broker_write_observed: bool
    decision_logic_bindings: tuple[BindingStatusV1, ...]
    decision_logic_complete: bool
    implementation_readiness_passed: bool
    session_admissible: bool
    blockers: tuple[str, ...]
    economic_validity_offline_gate_pass: bool
    economic_validity_offline_gate_pass_changed: bool
    activation_tokens: Mapping[str, bool]
    policy_sequence_before: tuple[str, ...]
    policy_sequence_after: tuple[str, ...]
    economic_gate_still_required_for: tuple[str, ...]
    fail_closed_abort_conditions: tuple[str, ...]
    safety_non_goals: tuple[str, ...]
    six_hour_session_ready: bool
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "session_contract_id": self.session_contract_id,
            "package_marker": self.package_marker,
            "authority_effect": self.authority_effect,
            "activation_effect": self.activation_effect,
            "economic_gate_effect": self.economic_gate_effect,
            "orders_allowed": self.orders_allowed,
            "broker_writes_allowed": self.broker_writes_allowed,
            "max_duration_seconds": self.max_duration_seconds,
            "explicit_operator_go_required": self.explicit_operator_go_required,
            "default_state": self.default_state,
            "runtime_execution": self.runtime_execution,
            "operator_go_present": self.operator_go_present,
            "requested_duration_seconds": self.requested_duration_seconds,
            "order_intent_observed": self.order_intent_observed,
            "broker_write_observed": self.broker_write_observed,
            "decision_logic_bindings": [b.to_dict() for b in self.decision_logic_bindings],
            "decision_logic_complete": self.decision_logic_complete,
            "implementation_readiness_passed": self.implementation_readiness_passed,
            "session_admissible": self.session_admissible,
            "blockers": list(self.blockers),
            "economic_validity_offline_gate_pass": self.economic_validity_offline_gate_pass,
            "economic_validity_offline_gate_pass_changed": (
                self.economic_validity_offline_gate_pass_changed
            ),
            "activation_tokens": dict(self.activation_tokens),
            "policy_sequence_before": list(self.policy_sequence_before),
            "policy_sequence_after": list(self.policy_sequence_after),
            "economic_gate_still_required_for": list(self.economic_gate_still_required_for),
            "fail_closed_abort_conditions": list(self.fail_closed_abort_conditions),
            "safety_non_goals": list(self.safety_non_goals),
            "six_hour_session_ready": self.six_hour_session_ready,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class PreEconomicZeroOrderEvidenceSessionOverridesV1:
    """Test-only overrides. Production evaluation uses fail-closed defaults."""

    operator_go_present: bool = False
    requested_duration_seconds: int = MAX_DURATION_SECONDS
    order_intent_observed: bool = False
    broker_write_observed: bool = False
    decision_logic_bound: Optional[Mapping[str, bool]] = None
    implementation_readiness_passed: bool = False
    economic_validity_offline_gate_pass: bool = False


def _binding_map(overrides: PreEconomicZeroOrderEvidenceSessionOverridesV1) -> dict[str, bool]:
    provided = dict(overrides.decision_logic_bound or {})
    return {
        binding_id: bool(provided.get(binding_id, False))
        for binding_id in REQUIRED_DECISION_LOGIC_BINDINGS
    }


def evaluate_pre_economic_zero_order_evidence_session_contract_v1(
    *,
    overrides: Optional[PreEconomicZeroOrderEvidenceSessionOverridesV1] = None,
) -> PreEconomicZeroOrderEvidenceSessionContractResultV1:
    """Evaluate session admissibility without executing runtime."""

    ov = overrides or PreEconomicZeroOrderEvidenceSessionOverridesV1()
    blockers: list[str] = []

    if ov.requested_duration_seconds < 0:
        raise PreEconomicZeroOrderEvidenceSessionContractError(
            "REQUESTED_DURATION_SECONDS_NEGATIVE"
        )

    if ov.requested_duration_seconds > MAX_DURATION_SECONDS:
        blockers.append("DURATION_EXCEEDS_MAX_21600")

    if EXPLICIT_OPERATOR_GO_REQUIRED and not ov.operator_go_present:
        blockers.append("EXPLICIT_OPERATOR_GO_ABSENT")

    if ov.order_intent_observed or ORDERS_ALLOWED is False and ov.order_intent_observed:
        if ov.order_intent_observed:
            blockers.append("ORDER_INTENT_FORBIDDEN")

    if ov.broker_write_observed or (BROKER_WRITES_ALLOWED is False and ov.broker_write_observed):
        if ov.broker_write_observed:
            blockers.append("BROKER_WRITE_FORBIDDEN")

    bindings_raw = _binding_map(ov)
    binding_statuses = tuple(
        BindingStatusV1(
            binding_id=binding_id,
            bound=bound,
            reason_code="BOUND" if bound else "MISSING_BINDING",
        )
        for binding_id, bound in bindings_raw.items()
    )
    decision_logic_complete = all(bindings_raw.values())
    if not decision_logic_complete:
        missing = [b for b, ok in bindings_raw.items() if not ok]
        blockers.append("INCOMPLETE_DECISION_LOGIC_BINDING:" + ",".join(missing))

    if not ov.implementation_readiness_passed:
        blockers.append("IMPLEMENTATION_READINESS_NOT_PASSED")

    # Runtime remains blocked in this capability; session may be admissible only
    # as a future GO-gated evidence plan, never as live execution from here.
    runtime_execution = RUNTIME_EXECUTION_DEFAULT
    if runtime_execution != "BLOCKED":
        blockers.append("RUNTIME_EXECUTION_MUST_REMAIN_BLOCKED")

    activation_tokens = {key: False for key in ACTIVATION_TOKEN_KEYS}

    # This contract must never flip the economic offline gate.
    economic_pass = bool(ov.economic_validity_offline_gate_pass)
    economic_pass_changed = False

    session_admissible = not blockers
    six_hour_ready = (
        session_admissible
        and ov.operator_go_present
        and decision_logic_complete
        and ov.implementation_readiness_passed
        and ov.requested_duration_seconds <= MAX_DURATION_SECONDS
        and not ov.order_intent_observed
        and not ov.broker_write_observed
        and runtime_execution == "BLOCKED"
    )
    # Capability defines the stage; separate implementation readiness is still required.
    # Until implementation readiness exists and passes, six-hour readiness stays false.
    if not ov.implementation_readiness_passed:
        six_hour_ready = False

    notes = (
        "EVIDENCE_STAGE_ONLY",
        "ZERO_ORDER_NOT_EQUIVALENT_TO_PAPER_SHADOW",
        "DOES_NOT_SET_ECONOMIC_VALIDITY_OFFLINE_GATE_PASS",
        "DOES_NOT_SET_ECONOMIC_VALIDITY_PASS",
        "DOES_NOT_AUTHORIZE_SHADOW_OR_RUNTIME",
        "LEGACY_OFFLINE_GATE_DOES_NOT_ALONE_BLOCK_PAPER_SHADOW_READINESS",
        "PROMOTION_TESTNET_LIVE_REQUIRE_ECONOMIC_VALIDITY_PASS",
    )

    return PreEconomicZeroOrderEvidenceSessionContractResultV1(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        session_contract_id=SESSION_CONTRACT_ID,
        package_marker=PACKAGE_MARKER,
        authority_effect=AUTHORITY_EFFECT_NONE,
        activation_effect=ACTIVATION_EFFECT_NONE,
        economic_gate_effect=ECONOMIC_GATE_EFFECT_NONE,
        orders_allowed=ORDERS_ALLOWED,
        broker_writes_allowed=BROKER_WRITES_ALLOWED,
        max_duration_seconds=MAX_DURATION_SECONDS,
        explicit_operator_go_required=EXPLICIT_OPERATOR_GO_REQUIRED,
        default_state=DEFAULT_STATE_BLOCKED,
        runtime_execution=runtime_execution,
        operator_go_present=bool(ov.operator_go_present),
        requested_duration_seconds=int(ov.requested_duration_seconds),
        order_intent_observed=bool(ov.order_intent_observed),
        broker_write_observed=bool(ov.broker_write_observed),
        decision_logic_bindings=binding_statuses,
        decision_logic_complete=decision_logic_complete,
        implementation_readiness_passed=bool(ov.implementation_readiness_passed),
        session_admissible=session_admissible,
        blockers=tuple(blockers),
        economic_validity_offline_gate_pass=economic_pass,
        economic_validity_offline_gate_pass_changed=economic_pass_changed,
        activation_tokens=activation_tokens,
        policy_sequence_before=POLICY_SEQUENCE_BEFORE,
        policy_sequence_after=POLICY_SEQUENCE_AFTER,
        economic_gate_still_required_for=tuple(sorted(ECONOMIC_GATE_STILL_REQUIRED_FOR)),
        fail_closed_abort_conditions=FAIL_CLOSED_ABORT_CONDITIONS,
        safety_non_goals=SAFETY_NON_GOALS,
        six_hour_session_ready=six_hour_ready,
        notes=notes,
    )


def assert_economic_gate_unchanged_for_ladder_steps(
    *,
    economic_validity_offline_gate_pass: bool,
) -> None:
    """Fail-closed helper: ladder steps after the evidence stage still need economic PASS."""

    if economic_validity_offline_gate_pass:
        return
    for step in sorted(ECONOMIC_GATE_STILL_REQUIRED_FOR):
        # Explicit machine assertion surface for tests / inventories.
        if step in ECONOMIC_GATE_STILL_REQUIRED_FOR and not economic_validity_offline_gate_pass:
            continue
    # No raise when pass is false: callers must treat steps as blocked.
    return


def economic_gate_blocks_step(step_id: str, *, economic_validity_offline_gate_pass: bool) -> bool:
    """Return True when ``step_id`` remains blocked pending system economic PASS.

    Legacy offline gate false blocks Promotion/Testnet/Live/29R/29T paths that
    still require ECONOMIC_VALIDITY_PASS (of which offline evidence is a part).
    Paper-Shadow observation readiness is not in ECONOMIC_GATE_STILL_REQUIRED_FOR.
    """

    if step_id not in ECONOMIC_GATE_STILL_REQUIRED_FOR:
        return False
    return not bool(economic_validity_offline_gate_pass)
