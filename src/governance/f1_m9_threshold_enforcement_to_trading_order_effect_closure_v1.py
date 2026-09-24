"""Bounded closure: threshold enforcement → MV2+DP trading decision → offline order intent."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

from src.governance.authorized_productive_parameter_seam_v1 import (
    AuthorizedProductiveParameterSeamBindRequestV1,
    bind_authorized_productive_parameter_seam_v1,
    STATUS_BOUND as SEAM_STATUS_BOUND,
)
from src.governance.canonical_order_intent_v1 import (
    AUTHORITY_EFFECT_NONE,
    CanonicalOrderIntentBuildInputV1,
    IntentAction,
    build_canonical_order_intent_v1,
)
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingInputV1,
    InstrumentQuantityConstraintsV1,
    evaluate_capital_risk_sizing_v1,
)
from src.governance.f1_m9_bounded_threshold_enforcement_mv2_consumer_v1 import (
    apply_bounded_enforcement_to_double_play_alpha_v1,
    evaluate_bounded_threshold_enforcement_at_mv2_consumer_v1,
    load_threshold_enforcement_closure_decision_v1,
    threshold_enforcement_authorized_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    parse_aware_utc_datetime_v1,
)
from src.governance.f1_m9_owner_threshold_value_authorization_record_v1 import (
    build_owner_threshold_value_authorization_input_v1,
)
from src.governance.f1_m9_per_ingress_authorization_chain_resolver_v1 import (
    resolve_f1_m9_per_ingress_authorization_chain_v1,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_artifacts_v1 import (
    post_real_campaign_handoff_bounded_complete_v1,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_bounded_completion_v1 import (
    DEFAULT_RUNTIME_AUTHORIZATION_ID,
    DEFAULT_SELECTED_CANDIDATE_ID,
    DEFAULT_SELECTED_MAX_AGE_SECONDS,
    evaluate_f1_m9_post_real_campaign_productive_handoff_v1,
)
from src.governance.f1_m9_post_real_campaign_optimization_governance_ingress_v1 import (
    build_f1_m9_post_real_campaign_optimization_governance_ingress_v1,
)
from src.governance.f1_m9_prospective_real_campaign_durable_evidence_verification_v1 import (
    verify_f1_m9_prospective_real_campaign_durable_evidence_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1
from src.governance.f1_m9_scoped_owner_threshold_value_authority_v1 import (
    F1M9ScopedOwnerThresholdValueAdjudicationRequestV1,
    evaluate_f1_m9_scoped_owner_threshold_value_authority_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationEvaluateRequestV1,
    build_owner_explicit_productive_authorization_input_v1,
    evaluate_explicit_productive_authorization_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.f1_m9_owner_apply_record_materialization_v1 import (
    STATUS_MATERIALIZED as OWNER_APPLY_RECORD_MATERIALIZED,
    materialize_owner_apply_record_when_canonical_candidate_resolved_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
)
from src.trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    VolatilityMaxAgeReasonCodeV1,
    derive_presence_status_for_age_policy_v1,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)
from trading.master_v2.canonical_market_context_v1 import with_computed_input_digest

SCHEMA_VERSION: Final[str] = "f1_m9_threshold_enforcement_to_trading_order_effect_closure/v1"
WORKPACKAGE_ID: Final[str] = "THRESHOLD_ENFORCEMENT_TO_TRADING_ORDER_EFFECT_CLOSURE_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/F1_M9_THRESHOLD_ENFORCEMENT_TO_TRADING_ORDER_EFFECT_CLOSURE_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1_decision_v1.json"
)

STATUS_CLOSURE_COMPLETE: Final[str] = "THRESHOLD_ENFORCEMENT_TO_ORDER_INTENT_CLOSURE_COMPLETE"
STATUS_DENIED: Final[str] = "DENIED_FAIL_CLOSED"

EARLIEST_BLOCKER_EXTERNAL: Final[str] = "EXTERNAL_ORDER_EFFECT_WIRE_SEND_LIVE_BOUNDARY"


@dataclass(frozen=True, slots=True)
class F1M9ThresholdEnforcementToTradingOrderEffectClosureResultV1:
    closure_status: str
    reason_codes: tuple[str, ...]
    handoff_complete: bool
    threshold_value_authorized: bool
    threshold_enforcement_authorized: bool
    threshold_enforcement_occurred: bool
    trading_decision_effect_occurred: bool
    order_intent_effect_occurred: bool
    external_order_effect_authorized: bool
    earliest_blocker: str | None
    alpha_after_enforcement: bool | None
    order_intent_authority_effect: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "alpha_after_enforcement": self.alpha_after_enforcement,
            "closure_status": self.closure_status,
            "earliest_blocker": self.earliest_blocker,
            "external_order_effect_authorized": self.external_order_effect_authorized,
            "handoff_complete": self.handoff_complete,
            "order_intent_authority_effect": self.order_intent_authority_effect,
            "order_intent_effect_occurred": self.order_intent_effect_occurred,
            "reason_codes": list(self.reason_codes),
            "threshold_enforcement_authorized": self.threshold_enforcement_authorized,
            "threshold_enforcement_occurred": self.threshold_enforcement_occurred,
            "threshold_value_authorized": self.threshold_value_authorized,
            "trading_decision_effect_occurred": self.trading_decision_effect_occurred,
        }


def _deny(
    reasons: list[str],
    *,
    handoff_complete: bool = False,
) -> F1M9ThresholdEnforcementToTradingOrderEffectClosureResultV1:
    decision = load_threshold_enforcement_closure_decision_v1()
    return F1M9ThresholdEnforcementToTradingOrderEffectClosureResultV1(
        closure_status=STATUS_DENIED,
        reason_codes=tuple(dict.fromkeys(reasons)),
        handoff_complete=handoff_complete,
        threshold_value_authorized=False,
        threshold_enforcement_authorized=threshold_enforcement_authorized_v1(),
        threshold_enforcement_occurred=False,
        trading_decision_effect_occurred=False,
        order_intent_effect_occurred=False,
        external_order_effect_authorized=decision.get("external_order_effect_authorized") is True,
        earliest_blocker=None,
        alpha_after_enforcement=None,
        order_intent_authority_effect=None,
    )


def _threshold_window_from_handoff_v1(*, repo_root: Path) -> tuple[str, str]:
    handoff_path = repo_root / (
        "config/governance/f1_m9_post_real_campaign_productive_handoff_v1_decision_v1.json"
    )
    payload = json.loads(handoff_path.read_text(encoding="utf-8"))
    return str(payload["owner_apply_not_before_utc"]), str(payload["owner_apply_expires_at_utc"])


def _build_threshold_input_from_handoff_apply_v1(
    *,
    applied_configuration: Any,
    apply_input: OwnerApplyAuthorizationInputV1,
    registry_digest: str,
    binding_digest: str,
    repo_root: Path,
) -> Any:
    record = applied_configuration.configuration_record
    assert record is not None
    contract = build_productive_target_contract_v1()
    not_before, expires_at = _threshold_window_from_handoff_v1(repo_root=repo_root)
    apply_digest = str(apply_input.owner_apply_authorization_record_digest)
    return build_owner_threshold_value_authorization_input_v1(
        registry_digest=registry_digest,
        ingress_digest=str(record["ingress_digest"]),
        per_ingress_binding_digest=binding_digest,
        owner_authorization_record_digest=str(record["owner_authorization_record_digest"]),
        authorization_id=str(record["authorization_id"]),
        authorization_digest=str(record["authorization_digest"]),
        configuration_id=str(record["configuration_id"]),
        configuration_digest=str(record["configuration_digest"]),
        candidate_parameter_value_digest=str(record["candidate_parameter_value_digest"]),
        productive_target_id=str(record["productive_target_id"]),
        productive_target_version=str(record["productive_target_version"]),
        productive_target_contract_digest=str(contract["contract_digest"]),
        ratified_threshold_capability_id=str(record["threshold_capability_id"]),
        ratified_threshold_capability_version=str(record["threshold_capability_version"]),
        owner_apply_authorization_record_digest=apply_digest,
        productive_apply_authorization_digest=apply_digest,
        threshold_numeric_max_age_seconds=float(record["numeric_max_age_seconds"]),
        not_before=not_before,
        expires_at=expires_at,
    )


def _offline_order_intent_effect_v1(*, alpha_allowed: bool) -> tuple[bool, str | None]:
    """Offline STEP 29Q intent build; no venue or credential effect."""
    if not alpha_allowed:
        return False, None
    from decimal import Decimal

    instrument = InstrumentQuantityConstraintsV1(
        instrument_id="ETH-USD-PERP",
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("1"),
        lot_size=Decimal("0.01"),
        minimum_quantity=Decimal("0.01"),
        maximum_quantity=Decimal("100"),
        minimum_notional=Decimal("5"),
        tick_size=Decimal("0.01"),
        instrument_metadata_version="f1_m9_closure_offline_fixture_v1",
    )
    sizing_input = CapitalRiskSizingInputV1(
        decision_id="f1-m9-closure-decision-001",
        instrument_id=instrument.instrument_id,
        selected_side="LONG",
        reference_price=Decimal("2000"),
        protective_stop_price=Decimal("1900"),
        stop_distance=None,
        account_equity=Decimal("500"),
        scope_capital_limit=Decimal("25"),
        per_trade_risk_limit=Decimal("25"),
        total_capital_limit=Decimal("500"),
        daily_loss_remaining_budget=Decimal("25"),
        current_reconciled_exposure=Decimal("0"),
        maximum_positions=1,
        current_open_positions_count=0,
        current_open_side=None,
        configured_quantity_cap=None,
        leverage_ceiling=Decimal("5"),
        reconciliation_status="RECONCILED",
        policy_version="capital_risk_sizing_policy_v1",
        config_digest="b" * 64,
        input_digest="a" * 64,
        instrument=instrument,
    )
    sizing_decision = evaluate_capital_risk_sizing_v1(sizing_input)
    build_input = CanonicalOrderIntentBuildInputV1(
        sizing_input=sizing_input,
        sizing_decision=sizing_decision,
        intent_id="f1-m9-closure-intent-001",
        trading_epoch="f1-m9-closure-epoch",
        canonical_trading_logic_version="f1_m9_closure_offline_v1",
        intent_action=IntentAction.ENTER_LONG.value,
        policy_digest="f1_m9_closure_policy_digest",
        order_type_policy="MARKET_ONLY",
        price_policy="EXPLICIT_NONE",
        time_in_force_policy="GTC",
        max_slippage_policy="ZERO",
        expected_position_side="LONG",
        current_reconciled_exposure=sizing_input.current_reconciled_exposure,
        current_open_side=sizing_input.current_open_side,
    )
    from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentBuildOutcome

    result = build_canonical_order_intent_v1(build_input)
    if result.outcome is not CanonicalOrderIntentBuildOutcome.PASS:
        return False, None
    return True, result.authority_effect


def evaluate_f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1(
    *,
    repo_root: Path | None = None,
    apply_ledger_paths: F1M9ProductiveApplyLedgerPathsV1,
    threshold_ledger_paths: F1M9ThresholdValueAuthorizationLedgerPathsV1,
    market_context_fresh: Any,
    market_context_stale: Any,
    estimate_fresh: Any,
    estimate_stale: Any,
) -> F1M9ThresholdEnforcementToTradingOrderEffectClosureResultV1:
    """Run bounded closure with injected MV2 market contexts (tests supply fixtures)."""
    root = repo_root or Path(__file__).resolve().parents[2]
    reasons: list[str] = []

    if not post_real_campaign_handoff_bounded_complete_v1(repo_root=root):
        return _deny(["POST_REAL_HANDOFF_NOT_COMPLETE"])

    decision = load_threshold_enforcement_closure_decision_v1(repo_root=root)
    if decision.get("closure_implemented") is not True:
        return _deny(["CLOSURE_DECISION_NOT_IMPLEMENTED"])

    handoff = evaluate_f1_m9_post_real_campaign_productive_handoff_v1(
        repo_root=root,
        ledger_paths=apply_ledger_paths,
    )
    if handoff.handoff_status != "F1_M9_POST_REAL_CAMPAIGN_PRODUCTIVE_HANDOFF_BOUNDED_COMPLETE":
        return _deny(list(handoff.reason_codes), handoff_complete=False)

    verification = verify_f1_m9_prospective_real_campaign_durable_evidence_v1(
        repo_root=root,
        expected_runtime_authorization_id=DEFAULT_RUNTIME_AUTHORIZATION_ID,
        expected_selected_candidate_id=DEFAULT_SELECTED_CANDIDATE_ID,
        expected_selected_max_age_seconds=DEFAULT_SELECTED_MAX_AGE_SECONDS,
    )
    if not verification.verified:
        return _deny(list(verification.reason_codes), handoff_complete=True)

    ingress = build_f1_m9_post_real_campaign_optimization_governance_ingress_v1(
        verification=verification,
        repo_root=root,
    )
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
        authorizer_identity="THRESHOLD_ENFORCEMENT_TO_TRADING_ORDER_EFFECT_CLOSURE_V1_OWNER_GO",
    )
    authorization = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    configuration = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=ingress,
        )
    )
    registry = load_scoped_join_registry_v1(repo_root=root)
    binding = evaluate_f1_m9_per_ingress_authorization_binding_v1(
        ingress=ingress,
        owner_input=owner_input,
        registry_digest=str(registry["registry_digest"]),
    )
    not_before = parse_aware_utc_datetime_v1(
        _threshold_window_from_handoff_v1(repo_root=root)[0],
        field_name="owner_apply_not_before_utc",
    )
    expires_at = parse_aware_utc_datetime_v1(
        _threshold_window_from_handoff_v1(repo_root=root)[1],
        field_name="owner_apply_expires_at_utc",
    )
    mat = materialize_owner_apply_record_when_canonical_candidate_resolved_v1(
        registry_digest=str(registry["registry_digest"]),
        ingress_digest=str(ingress["ingress_digest"]),
        binding=binding,
        authorization=authorization,
        configuration=configuration,
        not_before=not_before,
        expires_at=expires_at,
        repo_root=root,
    )
    if (
        mat.materialization_status != OWNER_APPLY_RECORD_MATERIALIZED
        or mat.owner_apply_input is None
    ):
        return _deny(list(mat.reason_codes), handoff_complete=True)

    apply_input = mat.owner_apply_input
    from src.governance.f1_m9_scoped_owner_apply_authority_v1 import (
        F1M9ScopedOwnerApplyAdjudicationRequestV1,
        evaluate_f1_m9_scoped_owner_productive_apply_v1,
    )

    apply_result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=configuration,
            registry_digest=str(registry["registry_digest"]),
            ledger_paths=apply_ledger_paths,
        )
    )
    if (
        not apply_result.productive_apply_authorized
        or apply_result.configuration_after_apply is None
    ):
        return _deny(list(apply_result.reason_codes), handoff_complete=True)
    applied_config = apply_result.configuration_after_apply

    threshold_input = _build_threshold_input_from_handoff_apply_v1(
        applied_configuration=applied_config,
        apply_input=apply_input,
        registry_digest=str(registry["registry_digest"]),
        binding_digest=binding.binding_digest,
        repo_root=root,
    )

    threshold_result = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
        F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
            owner_threshold_input=threshold_input,
            per_ingress_binding=binding,
            authorization=authorization,
            configuration=applied_config,
            registry_digest=str(registry["registry_digest"]),
            apply_ledger_paths=apply_ledger_paths,
            threshold_ledger_paths=threshold_ledger_paths,
            evaluation_time_utc=datetime.now(timezone.utc),
        )
    )
    if not threshold_result.threshold_value_authorized:
        return _deny(list(threshold_result.reason_codes), handoff_complete=True)

    config_after_threshold = threshold_result.configuration_after_threshold
    if config_after_threshold is None:
        return _deny(["THRESHOLD_CONFIGURATION_MISSING"], handoff_complete=True)

    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=config_after_threshold)
    )
    if seam.seam_status != SEAM_STATUS_BOUND or seam.seam_record is None:
        return _deny(list(seam.reason_codes), handoff_complete=True)

    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=ingress,
        admission=admission,
        owner_input=owner_input,
        registry_digest=str(registry["registry_digest"]),
        owner_apply_input=apply_input,
        ledger_paths=apply_ledger_paths,
        owner_threshold_input=threshold_input,
        threshold_ledger_paths=threshold_ledger_paths,
    )
    if not chain.threshold_value_authorized:
        return _deny(list(chain.reason_codes), handoff_complete=True)

    seam_record = dict(seam.seam_record)

    def _evaluate_path(context: Any, estimate: Any) -> tuple[Any, Any, Any]:
        ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
            with_computed_input_digest(context),
            estimate,
        )
        elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
        gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
            ctx,
            eligibility=elig,
            authorized_productive_parameter_seam=seam_record,
        )
        presence = derive_presence_status_for_age_policy_v1(
            typed_estimate_present=gate.typed_estimate_present,
            typed_validation_ok=gate.typed_validation_ok,
        )
        enforcement = evaluate_bounded_threshold_enforcement_at_mv2_consumer_v1(
            seam_record=seam_record,
            estimate=ctx.canonical_volatility_estimate,
            reference_market_event_time=ctx.market_event_time,
            presence_status=presence,
            repo_root=root,
        )
        alpha, alpha_reasons = apply_bounded_enforcement_to_double_play_alpha_v1(
            baseline_alpha_allowed=gate.alpha_scope_entry_authority_allowed,
            enforcement=enforcement,
        )
        return gate, enforcement, (alpha, alpha_reasons)

    _, enforcement_stale, (alpha_stale, _) = _evaluate_path(market_context_stale, estimate_stale)
    gate_fresh, enforcement_fresh, (alpha_fresh, _) = _evaluate_path(
        market_context_fresh, estimate_fresh
    )

    enforcement_occurred = (
        enforcement_stale.enforcement_applied
        and enforcement_stale.age_evidence.reason_code
        == VolatilityMaxAgeReasonCodeV1.VOLATILITY_ESTIMATE_STALE.value
    )
    trading_effect = alpha_stale is False and enforcement_stale.enforcement_applied

    order_intent_occurred = False
    order_intent_authority: str | None = None
    if alpha_fresh:
        order_intent_occurred, order_intent_authority = _offline_order_intent_effect_v1(
            alpha_allowed=True
        )

    external_auth = decision.get("external_order_effect_authorized") is True

    return F1M9ThresholdEnforcementToTradingOrderEffectClosureResultV1(
        closure_status=STATUS_CLOSURE_COMPLETE,
        reason_codes=tuple(reasons),
        handoff_complete=True,
        threshold_value_authorized=True,
        threshold_enforcement_authorized=threshold_enforcement_authorized_v1(repo_root=root),
        threshold_enforcement_occurred=enforcement_occurred,
        trading_decision_effect_occurred=trading_effect,
        order_intent_effect_occurred=order_intent_occurred,
        external_order_effect_authorized=external_auth,
        earliest_blocker=EARLIEST_BLOCKER_EXTERNAL if not external_auth else None,
        alpha_after_enforcement=alpha_fresh,
        order_intent_authority_effect=order_intent_authority,
    )


__all__ = [
    "DECISION_CONFIG",
    "EARLIEST_BLOCKER_EXTERNAL",
    "F1M9ThresholdEnforcementToTradingOrderEffectClosureResultV1",
    "NORMATIVE_SPEC",
    "SCHEMA_VERSION",
    "STATUS_CLOSURE_COMPLETE",
    "STATUS_DENIED",
    "WORKPACKAGE_ID",
    "evaluate_f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1",
]
