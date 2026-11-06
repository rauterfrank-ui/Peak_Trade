"""Integrated Paper-Shadow Economic-Validity Pipeline v1.

Canonical gate-split owner for the system-centered activation ladder:

FULL_CANONICAL_SYSTEM_PARITY
→ INTEGRATED_OFFLINE_REPLAY_AND_CORRECTNESS_PASS
→ INTEGRATED_PAPER_SHADOW_OBSERVATION_READINESS_PASS
→ OPERATOR_PAPER_SHADOW_OBSERVATION_GO
→ INTEGRATED_PAPER_SHADOW_OBSERVATION
→ INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE
→ INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED
→ ECONOMIC_VALIDITY_PASS
→ PROMOTION
→ TESTNET
→ LIVE

Offline economic evidence remains mandatory for ECONOMIC_VALIDITY_PASS, but is
no longer a hard precondition for orderless Paper-Shadow observation readiness.

This module:
- never executes runtime / wallclock / broker sessions;
- never grants Paper-Shadow / Testnet / Live / Orders authority;
- never sets PAPER_SHADOW_OBSERVATION_AUTHORIZED=true;
- never sets ECONOMIC_VALIDITY_PASS from a single run or documentation alone;
- treats ECONOMIC_VALIDITY_OFFLINE_GATE_PASS as legacy offline sub-evidence only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

PACKAGE_MARKER = "INTEGRATED_PAPER_SHADOW_ECONOMIC_VALIDITY_PIPELINE_V1=true"
PRODUCER_FAMILY = "ops.integrated_paper_shadow_economic_validity_pipeline_v1"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v1"
CONTRACT_CONFIG_SCHEMA_VERSION = "integrated_paper_shadow_economic_validity_pipeline.v1"

AUTHORITY_EFFECT_NONE = "NONE"
ACTIVATION_EFFECT_NONE = "NONE"
ECONOMIC_GATE_EFFECT_NONE = "NONE"

LEGACY_OFFLINE_GATE_FIELD_NAME = "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS"
LEGACY_OFFLINE_GATE_ROLE = "LEGACY_OFFLINE_SUB_EVIDENCE_ONLY"

CANONICAL_PIPELINE_SEQUENCE: tuple[str, ...] = (
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

LEGACY_PIPELINE_SEQUENCE: tuple[str, ...] = (
    "INTEGRATED_OFFLINE_REPLAY",
    "ECONOMIC_VALIDITY_OFFLINE_GATE",
    "PROMOTION",
    "STEP_29R_RUNTIME_REWIRE",
    "STEP_29T_ZERO_ORDER_RUNTIME",
    "STEP_29U_SHADOW",
)

PAPER_SHADOW_READINESS_PRECONDITIONS: tuple[str, ...] = (
    "FULL_CANONICAL_SYSTEM_PARITY",
    "SYSTEM_CORRECTNESS_PASS",
    "INTEGRATED_OFFLINE_REPLAY_PASS",
    "BACKTEST_RUNTIME_DECISION_PARITY_PASS",
    "CANONICAL_DECISION_CHAIN_BOUND",
    "MASTER_V2_DOUBLE_PLAY_SOLE_DECISION_AUTHORITY",
    "AI_LAYER_NON_AUTHORITY",
    "SAFETY_KERNEL_KILLSTATE_FAIL_CLOSED",
    "BROKER_WRITE_PATH_UNREACHABLE",
    "ORDER_AUTHORITY_ABSENT",
    "SIMULATED_PORTFOLIO_FILL_FEE_SLIPPAGE_PNL_MODEL_DEFINED",
    "EVIDENCE_DIRECTORY_MANIFEST_SCHEMA_CONFIG_DIGESTS_VERIFIER_DEFINED",
    "SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT",
)

FORBIDDEN_ECONOMIC_PASS_EVIDENCE_CLASSES: frozenset[str] = frozenset(
    {
        "RAW_SIGNAL",
        "STRATEGY_ARCHETYPE",
        "OLS",
        "AI",
        "DASHBOARD",
        "ZERO_ORDER_CONNECTIVITY_OR_RUNTIME_EVIDENCE",
        "SINGLE_POSITIVE_PAPER_SHADOW_RUN",
        "DOCUMENTATION_STATUS_ONLY",
        "HISTORICAL_TERMINAL_NEGATIVE_EVIDENCE_REBADGED",
    }
)

AUTHORITY_FLAG_KEYS: tuple[str, ...] = (
    "PAPER_SHADOW_OBSERVATION_AUTHORIZED",
    "TESTNET_AUTHORIZED",
    "LIVE_AUTHORIZED",
    "ORDERS_AUTHORIZED",
    "PROMOTION_PASS",
)


class IntegratedPaperShadowEconomicValidityPipelineError(ValueError):
    """Fail-closed pipeline evaluation or config error."""


@dataclass(frozen=True)
class IntegratedPaperShadowEconomicValidityEvidenceInputV1:
    """Explicit evidence / precondition input. Missing fields fail closed."""

    full_canonical_system_parity: Optional[bool] = None
    system_correctness_pass: Optional[bool] = None
    integrated_offline_replay_pass: Optional[bool] = None
    backtest_runtime_decision_parity_pass: Optional[bool] = None
    canonical_decision_chain_bound: Optional[bool] = None
    master_v2_double_play_sole_decision_authority: Optional[bool] = None
    ai_layer_non_authority: Optional[bool] = None
    safety_kernel_killstate_fail_closed: Optional[bool] = None
    broker_write_path_unreachable: Optional[bool] = None
    order_authority_absent: Optional[bool] = None
    simulated_portfolio_fill_fee_slippage_pnl_model_defined: Optional[bool] = None
    evidence_directory_manifest_schema_config_digests_verifier_defined: Optional[bool] = None
    session_preregistration_and_operator_go_contract_present: Optional[bool] = None
    paper_shadow_observation_operator_go: Optional[bool] = None
    offline_economic_evidence_complete: Optional[bool] = None
    integrated_paper_shadow_evidence_complete: Optional[bool] = None
    integrated_economic_evidence_bundle_verified: Optional[bool] = None
    economic_validity_operator_ratification: Optional[bool] = None
    fees_slippage_stops_fill_exposure_turnover_drawdown_present: Optional[bool] = None
    walk_forward_monte_carlo_stress_requirements_met: Optional[bool] = None
    digests_manifests_config_bindings_provenance_consistent: Optional[bool] = None
    single_positive_paper_shadow_run_only: bool = False
    historical_terminal_negative_evidence_rebadged: bool = False
    evidence_class: str = ""
    economic_validity_offline_gate_pass: Optional[bool] = None
    promotion_operator_go: Optional[bool] = None
    testnet_operator_go: Optional[bool] = None
    live_operator_go: Optional[bool] = None
    orders_operator_go: Optional[bool] = None


@dataclass(frozen=True)
class IntegratedPaperShadowEconomicValidityPipelineResultV1:
    schema_id: str
    schema_version: str
    package_marker: str
    authority_effect: str
    activation_effect: str
    economic_gate_effect: str
    canonical_pipeline_sequence: tuple[str, ...]
    legacy_pipeline_sequence: tuple[str, ...]
    legacy_offline_gate_field_name: str
    legacy_offline_gate_role: str
    economic_validity_offline_gate_pass: bool
    full_canonical_system_parity: bool
    system_correctness_pass: bool
    integrated_offline_replay_pass: bool
    backtest_runtime_decision_parity_pass: bool
    paper_shadow_observation_readiness_pass: bool
    paper_shadow_observation_authorized: bool
    integrated_paper_shadow_evidence_complete: bool
    offline_economic_evidence_complete: bool
    integrated_economic_evidence_bundle_verified: bool
    economic_validity_pass: bool
    promotion_pass: bool
    testnet_authorized: bool
    live_authorized: bool
    orders_authorized: bool
    readiness_blockers: tuple[str, ...]
    economic_blockers: tuple[str, ...]
    authority_blockers: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "package_marker": self.package_marker,
            "authority_effect": self.authority_effect,
            "activation_effect": self.activation_effect,
            "economic_gate_effect": self.economic_gate_effect,
            "canonical_pipeline_sequence": list(self.canonical_pipeline_sequence),
            "legacy_pipeline_sequence": list(self.legacy_pipeline_sequence),
            "legacy_offline_gate_field_name": self.legacy_offline_gate_field_name,
            "legacy_offline_gate_role": self.legacy_offline_gate_role,
            "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": self.economic_validity_offline_gate_pass,
            "FULL_CANONICAL_SYSTEM_PARITY": self.full_canonical_system_parity,
            "SYSTEM_CORRECTNESS_PASS": self.system_correctness_pass,
            "INTEGRATED_OFFLINE_REPLAY_PASS": self.integrated_offline_replay_pass,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": self.backtest_runtime_decision_parity_pass,
            "PAPER_SHADOW_OBSERVATION_READINESS_PASS": self.paper_shadow_observation_readiness_pass,
            "PAPER_SHADOW_OBSERVATION_AUTHORIZED": self.paper_shadow_observation_authorized,
            "INTEGRATED_PAPER_SHADOW_EVIDENCE_COMPLETE": self.integrated_paper_shadow_evidence_complete,
            "OFFLINE_ECONOMIC_EVIDENCE_COMPLETE": self.offline_economic_evidence_complete,
            "INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED": (
                self.integrated_economic_evidence_bundle_verified
            ),
            "ECONOMIC_VALIDITY_PASS": self.economic_validity_pass,
            "PROMOTION_PASS": self.promotion_pass,
            "TESTNET_AUTHORIZED": self.testnet_authorized,
            "LIVE_AUTHORIZED": self.live_authorized,
            "ORDERS_AUTHORIZED": self.orders_authorized,
            "readiness_blockers": list(self.readiness_blockers),
            "economic_blockers": list(self.economic_blockers),
            "authority_blockers": list(self.authority_blockers),
            "notes": list(self.notes),
        }


def _require_true(value: Optional[bool], *, field: str, blockers: list[str]) -> bool:
    if value is True:
        return True
    if value is False:
        blockers.append(f"{field}_FALSE")
        return False
    blockers.append(f"{field}_MISSING_FAIL_CLOSED")
    return False


def _load_legacy_offline_gate_pass(value: Optional[bool]) -> bool:
    """Legacy token is false-only compatible; true is rejected as migration abuse."""
    if value is None:
        return False
    if value is True:
        raise IntegratedPaperShadowEconomicValidityPipelineError(
            "legacy_economic_validity_offline_gate_pass_true_rejected_in_capability_defaults"
        )
    return False


def evaluate_paper_shadow_observation_readiness_v1(
    evidence: IntegratedPaperShadowEconomicValidityEvidenceInputV1,
) -> tuple[bool, tuple[str, ...]]:
    """Return readiness pass and blockers. Offline economic PASS is intentionally ignored."""
    blockers: list[str] = []
    checks = (
        ("FULL_CANONICAL_SYSTEM_PARITY", evidence.full_canonical_system_parity),
        ("SYSTEM_CORRECTNESS_PASS", evidence.system_correctness_pass),
        ("INTEGRATED_OFFLINE_REPLAY_PASS", evidence.integrated_offline_replay_pass),
        (
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS",
            evidence.backtest_runtime_decision_parity_pass,
        ),
        ("CANONICAL_DECISION_CHAIN_BOUND", evidence.canonical_decision_chain_bound),
        (
            "MASTER_V2_DOUBLE_PLAY_SOLE_DECISION_AUTHORITY",
            evidence.master_v2_double_play_sole_decision_authority,
        ),
        ("AI_LAYER_NON_AUTHORITY", evidence.ai_layer_non_authority),
        (
            "SAFETY_KERNEL_KILLSTATE_FAIL_CLOSED",
            evidence.safety_kernel_killstate_fail_closed,
        ),
        ("BROKER_WRITE_PATH_UNREACHABLE", evidence.broker_write_path_unreachable),
        ("ORDER_AUTHORITY_ABSENT", evidence.order_authority_absent),
        (
            "SIMULATED_PORTFOLIO_FILL_FEE_SLIPPAGE_PNL_MODEL_DEFINED",
            evidence.simulated_portfolio_fill_fee_slippage_pnl_model_defined,
        ),
        (
            "EVIDENCE_DIRECTORY_MANIFEST_SCHEMA_CONFIG_DIGESTS_VERIFIER_DEFINED",
            evidence.evidence_directory_manifest_schema_config_digests_verifier_defined,
        ),
        (
            "SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT",
            evidence.session_preregistration_and_operator_go_contract_present,
        ),
    )
    for field_name, value in checks:
        _require_true(value, field=field_name, blockers=blockers)
    # Explicit non-coupling: legacy offline gate must not appear as readiness blocker.
    return (not blockers), tuple(blockers)


def evaluate_economic_validity_pass_v1(
    evidence: IntegratedPaperShadowEconomicValidityEvidenceInputV1,
) -> tuple[bool, tuple[str, ...]]:
    """ECONOMIC_VALIDITY_PASS only from a verified integrated evidence bundle."""
    blockers: list[str] = []
    _require_true(
        evidence.integrated_economic_evidence_bundle_verified,
        field="INTEGRATED_ECONOMIC_EVIDENCE_BUNDLE_VERIFIED",
        blockers=blockers,
    )
    _require_true(
        evidence.offline_economic_evidence_complete,
        field="OFFLINE_ECONOMIC_EVIDENCE_COMPLETE",
        blockers=blockers,
    )
    _require_true(
        evidence.integrated_paper_shadow_evidence_complete,
        field="INTEGRATED_PAPER_SHADOW_EVIDENCE_COMPLETE",
        blockers=blockers,
    )
    _require_true(
        evidence.fees_slippage_stops_fill_exposure_turnover_drawdown_present,
        field="FEES_SLIPPAGE_STOPS_FILL_EXPOSURE_TURNOVER_DRAWDOWN",
        blockers=blockers,
    )
    _require_true(
        evidence.walk_forward_monte_carlo_stress_requirements_met,
        field="WALK_FORWARD_MONTE_CARLO_STRESS",
        blockers=blockers,
    )
    _require_true(
        evidence.digests_manifests_config_bindings_provenance_consistent,
        field="DIGESTS_MANIFESTS_CONFIG_BINDINGS_PROVENANCE",
        blockers=blockers,
    )
    _require_true(
        evidence.economic_validity_operator_ratification,
        field="ECONOMIC_VALIDITY_OPERATOR_RATIFICATION",
        blockers=blockers,
    )

    if evidence.single_positive_paper_shadow_run_only:
        blockers.append("SINGLE_POSITIVE_PAPER_SHADOW_RUN_INSUFFICIENT")
    if evidence.historical_terminal_negative_evidence_rebadged:
        blockers.append("HISTORICAL_TERMINAL_NEGATIVE_EVIDENCE_REBADGED_REJECTED")

    evidence_class = str(evidence.evidence_class or "").strip().upper()
    if evidence_class in FORBIDDEN_ECONOMIC_PASS_EVIDENCE_CLASSES:
        blockers.append(f"FORBIDDEN_EVIDENCE_CLASS:{evidence_class}")

    # Legacy offline gate alone is never sufficient: missing integrated fields already
    # fail closed above. Explicitly reject offline-only claims when paper/bundle absent.
    if evidence.economic_validity_offline_gate_pass is True and (
        evidence.integrated_economic_evidence_bundle_verified is not True
        or evidence.integrated_paper_shadow_evidence_complete is not True
    ):
        blockers.append("LEGACY_OFFLINE_GATE_ALONE_INSUFFICIENT_FOR_ECONOMIC_VALIDITY_PASS")

    return (not blockers), tuple(blockers)


def evaluate_integrated_paper_shadow_economic_validity_pipeline_v1(
    *,
    evidence: IntegratedPaperShadowEconomicValidityEvidenceInputV1 | None = None,
    allow_legacy_offline_gate_true_for_tests: bool = False,
) -> IntegratedPaperShadowEconomicValidityPipelineResultV1:
    """Evaluate the reconciled gate split. Defaults keep all authority false."""
    ev = evidence or IntegratedPaperShadowEconomicValidityEvidenceInputV1()

    if (
        ev.economic_validity_offline_gate_pass is True
        and not allow_legacy_offline_gate_true_for_tests
    ):
        # Capability defaults / repo truth remain false-only for the legacy token.
        raise IntegratedPaperShadowEconomicValidityPipelineError(
            "legacy_economic_validity_offline_gate_pass_true_rejected_in_capability_defaults"
        )
    legacy_offline = (
        bool(ev.economic_validity_offline_gate_pass)
        if allow_legacy_offline_gate_true_for_tests
        else False
    )
    if (
        ev.economic_validity_offline_gate_pass is False
        or ev.economic_validity_offline_gate_pass is None
    ):
        legacy_offline = False

    readiness_pass, readiness_blockers = evaluate_paper_shadow_observation_readiness_v1(ev)

    # Authorization never implied by readiness; requires separate explicit operator GO.
    # This capability never grants GO; unknown/missing stays false.
    observation_authorized = False
    authority_blockers: list[str] = []
    if readiness_pass and ev.paper_shadow_observation_operator_go is True:
        # Even with GO true in synthetic tests, this capability result surface stays
        # non-authorizing for production defaults; callers must use a separate
        # operator-authorization owner. Capability evaluation always reports false.
        authority_blockers.append(
            "PAPER_SHADOW_OBSERVATION_AUTHORIZED_NOT_GRANTED_BY_THIS_CAPABILITY"
        )
    elif ev.paper_shadow_observation_operator_go is True:
        authority_blockers.append("PAPER_SHADOW_OBSERVATION_GO_WITHOUT_READINESS")
    else:
        authority_blockers.append("PAPER_SHADOW_OBSERVATION_OPERATOR_GO_ABSENT")

    economic_pass, economic_blockers = evaluate_economic_validity_pass_v1(ev)
    # Hard invariant for this capability PR: never emit ECONOMIC_VALIDITY_PASS=true.
    if economic_pass:
        economic_blockers = economic_blockers + (
            "ECONOMIC_VALIDITY_PASS_NOT_EMITTED_BY_THIS_CAPABILITY",
        )
        economic_pass = False

    promotion_pass = False
    if economic_pass is False:
        authority_blockers.append("PROMOTION_BLOCKED_WITHOUT_ECONOMIC_VALIDITY_PASS")
    if ev.promotion_operator_go is not True:
        authority_blockers.append("PROMOTION_OPERATOR_GO_ABSENT")

    testnet_authorized = False
    if ev.testnet_operator_go is not True:
        authority_blockers.append("TESTNET_OPERATOR_GO_ABSENT")
    if economic_pass is False:
        authority_blockers.append("TESTNET_BLOCKED_WITHOUT_ECONOMIC_VALIDITY_PASS")

    live_authorized = False
    if ev.live_operator_go is not True:
        authority_blockers.append("LIVE_OPERATOR_GO_ABSENT")
    if economic_pass is False:
        authority_blockers.append("LIVE_BLOCKED_WITHOUT_ECONOMIC_VALIDITY_PASS")

    orders_authorized = False
    authority_blockers.append("ORDERS_AUTHORIZED_INDEPENDENTLY_BLOCKED")
    if ev.orders_operator_go is True:
        authority_blockers.append("ORDERS_OPERATOR_GO_REJECTED_BY_CAPABILITY_INVARIANT")

    notes = (
        "PAPER_SHADOW_IS_EVIDENCE_GENERATOR_ONLY",
        "ZERO_ORDER_NOT_EQUIVALENT_TO_PAPER_SHADOW",
        "LEGACY_OFFLINE_GATE_DOES_NOT_ALONE_BLOCK_PAPER_SHADOW_READINESS",
        "LEGACY_OFFLINE_GATE_DOES_NOT_ALONE_SET_ECONOMIC_VALIDITY_PASS",
        "NO_RUNTIME",
        "NO_SESSION",
        "NO_BROKER_WRITES",
        "NO_ORDERS",
        "AI_LAYER_NON_AUTHORITY",
        "MASTER_V2_DOUBLE_PLAY_DECISION_AUTHORITY",
        "SAFETY_KERNEL_INDEPENDENT_VETO",
        "DASHBOARD_IS_CONSUMER_NOT_SSOT",
    )

    return IntegratedPaperShadowEconomicValidityPipelineResultV1(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        package_marker=PACKAGE_MARKER,
        authority_effect=AUTHORITY_EFFECT_NONE,
        activation_effect=ACTIVATION_EFFECT_NONE,
        economic_gate_effect=ECONOMIC_GATE_EFFECT_NONE,
        canonical_pipeline_sequence=CANONICAL_PIPELINE_SEQUENCE,
        legacy_pipeline_sequence=LEGACY_PIPELINE_SEQUENCE,
        legacy_offline_gate_field_name=LEGACY_OFFLINE_GATE_FIELD_NAME,
        legacy_offline_gate_role=LEGACY_OFFLINE_GATE_ROLE,
        economic_validity_offline_gate_pass=legacy_offline,
        full_canonical_system_parity=ev.full_canonical_system_parity is True,
        system_correctness_pass=ev.system_correctness_pass is True,
        integrated_offline_replay_pass=ev.integrated_offline_replay_pass is True,
        backtest_runtime_decision_parity_pass=ev.backtest_runtime_decision_parity_pass is True,
        paper_shadow_observation_readiness_pass=readiness_pass,
        paper_shadow_observation_authorized=observation_authorized,
        integrated_paper_shadow_evidence_complete=(
            ev.integrated_paper_shadow_evidence_complete is True
        ),
        offline_economic_evidence_complete=ev.offline_economic_evidence_complete is True,
        integrated_economic_evidence_bundle_verified=(
            ev.integrated_economic_evidence_bundle_verified is True
        ),
        economic_validity_pass=economic_pass,
        promotion_pass=promotion_pass,
        testnet_authorized=testnet_authorized,
        live_authorized=live_authorized,
        orders_authorized=orders_authorized,
        readiness_blockers=readiness_blockers,
        economic_blockers=economic_blockers,
        authority_blockers=tuple(sorted(set(authority_blockers))),
        notes=notes,
    )


def readiness_ignores_legacy_offline_gate(
    *,
    economic_validity_offline_gate_pass: bool,
    evidence: IntegratedPaperShadowEconomicValidityEvidenceInputV1,
) -> bool:
    """Prove offline gate false does not alone block readiness when preconditions hold."""
    ready, blockers = evaluate_paper_shadow_observation_readiness_v1(evidence)
    assert "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS" not in " ".join(blockers)
    assert (
        economic_validity_offline_gate_pass is False or economic_validity_offline_gate_pass is True
    )
    return ready


def load_legacy_offline_gate_false_only(value: Any) -> bool:
    """Deterministic false-only legacy loader. Unknown/contradictory → fail closed."""
    if value is None:
        return False
    if value is False or value == 0 or value == "false" or value == "FALSE":
        return False
    if value is True or value == 1 or value == "true" or value == "TRUE":
        raise IntegratedPaperShadowEconomicValidityPipelineError(
            "legacy_offline_gate_true_not_accepted_by_false_only_loader"
        )
    raise IntegratedPaperShadowEconomicValidityPipelineError(
        f"legacy_offline_gate_unknown_fail_closed:{value!r}"
    )


def default_repo_pipeline_result_v1() -> IntegratedPaperShadowEconomicValidityPipelineResultV1:
    """Repo-truth defaults: all readiness unknown/fail-closed; all authority false."""
    return evaluate_integrated_paper_shadow_economic_validity_pipeline_v1()
