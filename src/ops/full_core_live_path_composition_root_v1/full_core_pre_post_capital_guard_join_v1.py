"""PRE_EXTERNAL → Full-Core capital guard join (fail-closed, no POST).

Boundary: after canonical decision, sizing, venue plan, FinalOrderEnvelopeV1, and
PRE_EXTERNAL terminal evidence; before any external POST or exchange submission.

Default join mode DISABLED — productive PRE_EXTERNAL semantics unchanged unless an
explicit scoped mode is supplied (OFFLINE_STUB / OBSERVE_ONLY). LIVE_POST forbidden.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    FullCoreCapitalGuardConfigV1,
    FullCoreCapitalGuardError,
    FullCoreCapitalGuardEvaluationV1,
    FullCoreCapitalGuardOrderPlanV1,
    OWNER_GO_FULL_CORE_PRE_POST,
    evaluate_full_core_capital_guard_entry_v1,
    load_full_core_capital_guard_config_v1,
    ratified_offline_full_core_guard_config_v1,
    refuse_full_core_capital_guard_entry_unless_pass_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    adapt_full_core_guard_config_to_canary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_completed_hook_evidence_v1 import (
    FULL_CORE_ATOMIC_CONSUMPTION_KEY,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
    FullCoreAtomicOneShotError,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    assert_full_core_entry_authorization_available_v1,
    default_full_core_atomic_state_dir_v1,
    full_core_atomic_mark_submit_boundary_v1,
    full_core_atomic_reserve_owner_go_authorization_v1,
    full_core_durable_entry_state_for_guard_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_full_core_capital_guard_observability_v1 import (
    STAGE_CURRENT_DECISION_BOUND,
    STAGE_FINAL_ENVELOPE_BOUND,
    STAGE_ONE_SHOT_RESERVATION,
    STAGE_PRE_EXTERNAL_REACHED,
    STAGE_SUBMIT_BOUNDARY,
    STAGE_VENUE_PLAN_BOUND,
    build_full_core_capital_guard_ghv_bundle_v1,
    record_full_core_capital_guard_ghv_stage_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    OWNER_GO_EXECUTE as CANARY_OWNER_GO_EXECUTE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.current_live_canary_capital_guard_v1 import (
    CanaryCapitalGuardExposureEvidenceV1,
    CanaryCapitalGuardMarginEvidenceV1,
    CanaryCapitalGuardSessionV1,
    IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
    build_default_guard_session_v1,
)

CONTRACT_ID = "FULL_CORE_PRE_POST_CAPITAL_GUARD_JOIN_V1"
JOIN_ENV_VAR = "PEAK_TRADE_FULL_CORE_CAPITAL_GUARD_JOIN_MODE"
ATOMIC_STATE_DIR_ENV_VAR = "PEAK_TRADE_FULL_CORE_CAPITAL_GUARD_ATOMIC_STATE_DIR"

POST_COUNT = 0


class FullCoreCapitalGuardJoinMode(str, Enum):
    DISABLED = "DISABLED"
    OFFLINE_STUB = "OFFLINE_STUB"
    OBSERVE_ONLY = "OBSERVE_ONLY"
    LIVE_POST = "LIVE_POST"


class FullCorePrePostCapitalGuardJoinError(RuntimeError):
    """Fail-closed join binding or guard violation."""


@dataclass(frozen=True)
class FullCorePrePostCapitalGuardJoinBindingV1:
    canonical_decision_id: str
    native_id: str
    instrument_id: str
    selected_direction: str
    order_side: str
    final_quantity: str
    order_type: str
    order_price: str
    venue_plan_digest: str
    envelope_digest: str
    account_identity: str
    environment: str
    execution_mode: str
    owner_go: str
    origin_main_sha: str
    guard_config_digest: str
    clordid: str
    pre_external_reached: bool
    terminal_disposition: str
    ct_val: str
    min_sz: str
    lot_sz: str

    def validate_against_envelope_v1(self, envelope: FinalOrderEnvelopeV1) -> tuple[str, ...]:
        reasons: list[str] = []
        assert_envelope_unmodified_v1(envelope)
        if envelope.envelope_digest != self.envelope_digest:
            reasons.append("ENVELOPE_DIGEST_MISMATCH")
        if envelope.instrument_id != self.instrument_id:
            reasons.append("INSTRUMENT_ID_MISMATCH")
        if envelope.side.upper() != self.order_side.upper():
            reasons.append("ORDER_SIDE_MISMATCH")
        if envelope.quantity != self.final_quantity:
            reasons.append("QUANTITY_MISMATCH")
        if envelope.order_type.upper() != self.order_type.upper():
            reasons.append("ORDER_TYPE_MISMATCH")
        if envelope.price != self.order_price:
            reasons.append("ORDER_PRICE_MISMATCH")
        if envelope.client_order_id != self.clordid:
            reasons.append("CLORDID_MISMATCH")
        return tuple(reasons)


@dataclass(frozen=True)
class FullCorePrePostCapitalGuardJoinResultV1:
    join_mode: str
    guard_allowed: bool | None
    guard_blocked: bool
    reasons: tuple[str, ...]
    binding_digest: str | None
    atomic_state: str | None
    ghv_bundle: dict[str, Any]
    post_count: int
    reservation_created: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": CONTRACT_ID,
            "join_mode": self.join_mode,
            "guard_allowed": self.guard_allowed,
            "guard_blocked": self.guard_blocked,
            "reasons": list(self.reasons),
            "binding_digest": self.binding_digest,
            "atomic_state": self.atomic_state,
            "post_count": self.post_count,
            "reservation_created": self.reservation_created,
            "ghv_bundle": self.ghv_bundle,
        }


def resolve_full_core_capital_guard_join_mode_v1(
    *,
    explicit_mode: str | FullCoreCapitalGuardJoinMode | None = None,
) -> FullCoreCapitalGuardJoinMode:
    if isinstance(explicit_mode, FullCoreCapitalGuardJoinMode):
        if explicit_mode is FullCoreCapitalGuardJoinMode.LIVE_POST:
            return FullCoreCapitalGuardJoinMode.DISABLED
        return explicit_mode
    if explicit_mode is not None:
        parsed = FullCoreCapitalGuardJoinMode(str(explicit_mode).strip().upper())
        if parsed is FullCoreCapitalGuardJoinMode.LIVE_POST:
            return FullCoreCapitalGuardJoinMode.DISABLED
        return parsed
    raw = str(os.environ.get(JOIN_ENV_VAR) or FullCoreCapitalGuardJoinMode.DISABLED.value).strip()
    try:
        mode = FullCoreCapitalGuardJoinMode(raw.upper())
    except ValueError:
        return FullCoreCapitalGuardJoinMode.DISABLED
    if mode is FullCoreCapitalGuardJoinMode.LIVE_POST:
        return FullCoreCapitalGuardJoinMode.DISABLED
    return mode


def _authorization_binding_v1(
    binding: FullCorePrePostCapitalGuardJoinBindingV1,
    *,
    session_id: str,
) -> FullCoreAuthorizationBindingV1:
    return FullCoreAuthorizationBindingV1(
        owner_go=binding.owner_go,
        origin_main_sha=binding.origin_main_sha,
        account_scope=binding.account_identity,
        environment=binding.environment,
        execution_mode=binding.execution_mode,
        canonical_decision_id=binding.canonical_decision_id,
        instrument_id=binding.instrument_id,
        native_id=binding.native_id,
        selected_direction=binding.selected_direction,
        order_side=binding.order_side,
        final_quantity=binding.final_quantity,
        order_type=binding.order_type,
        order_price=binding.order_price,
        venue_plan_digest=binding.venue_plan_digest,
        envelope_digest=binding.envelope_digest,
        guard_config_digest=binding.guard_config_digest,
        session_id=session_id,
        clordid=binding.clordid,
    )


def run_full_core_pre_post_capital_guard_join_v1(
    *,
    binding: FullCorePrePostCapitalGuardJoinBindingV1,
    envelope: FinalOrderEnvelopeV1 | None,
    guard_config: FullCoreCapitalGuardConfigV1 | None = None,
    margin_evidence: CanaryCapitalGuardMarginEvidenceV1 | None = None,
    exposure_evidence: CanaryCapitalGuardExposureEvidenceV1 | None = None,
    guard_session: CanaryCapitalGuardSessionV1 | None = None,
    observed_leverage: str | None = None,
    existing_exposure_notional_usdc: str | None = None,
    join_mode: str | FullCoreCapitalGuardJoinMode | None = None,
    atomic_state_dir: Path | None = None,
    simulate_submit_boundary_crash: bool = False,
    session_id: str = "full-core-capital-guard-join",
    account_evidence_scope: str | None = None,
    authoritative_environment: str | None = None,
    authoritative_venue_plan_digest: str | None = None,
    pretrade_reference_mark_px: str | None = None,
) -> FullCorePrePostCapitalGuardJoinResultV1:
    mode = resolve_full_core_capital_guard_join_mode_v1(explicit_mode=join_mode)
    if mode is FullCoreCapitalGuardJoinMode.DISABLED:
        return FullCorePrePostCapitalGuardJoinResultV1(
            join_mode=mode.value,
            guard_allowed=None,
            guard_blocked=False,
            reasons=(),
            binding_digest=None,
            atomic_state=None,
            ghv_bundle={},
            post_count=0,
            reservation_created=False,
        )

    reasons: list[str] = []
    ghv_stages: list[dict[str, Any]] = []

    if binding.owner_go == CANARY_OWNER_GO_EXECUTE:
        reasons.append("CANARY_OWNER_GO_FORBIDDEN")
    if binding.owner_go != OWNER_GO_FULL_CORE_PRE_POST:
        reasons.append(f"OWNER_GO_MISMATCH:{binding.owner_go}")
    if not binding.pre_external_reached:
        reasons.append("PRE_EXTERNAL_NOT_REACHED")
    if binding.terminal_disposition != DISPOSITION_PRE_EXTERNAL_EFFECT:
        reasons.append("TERMINAL_NOT_PRE_EXTERNAL")
    if binding.environment.upper() == "LIVE":
        reasons.append("LIVE_ENVIRONMENT_FORBIDDEN")
    if account_evidence_scope is not None and account_evidence_scope != binding.account_identity:
        reasons.append("ACCOUNT_IDENTITY_MISMATCH")
    if (
        authoritative_environment is not None
        and authoritative_environment.upper() != binding.environment.upper()
    ):
        reasons.append("ENVIRONMENT_MISMATCH")
    if (
        authoritative_venue_plan_digest is not None
        and authoritative_venue_plan_digest != binding.venue_plan_digest
    ):
        reasons.append("VENUE_PLAN_DIGEST_MISMATCH")
    if envelope is None:
        reasons.append("ENVELOPE_MISSING")
    else:
        reasons.extend(binding.validate_against_envelope_v1(envelope))

    ghv_stages.append(
        record_full_core_capital_guard_ghv_stage_v1(
            stage=STAGE_CURRENT_DECISION_BOUND,
            session_id=session_id,
            binding_digest="",
            guard_config_digest=binding.guard_config_digest,
            payload={"canonical_decision_id": binding.canonical_decision_id},
        )
    )
    ghv_stages.append(
        record_full_core_capital_guard_ghv_stage_v1(
            stage=STAGE_VENUE_PLAN_BOUND,
            session_id=session_id,
            binding_digest="",
            guard_config_digest=binding.guard_config_digest,
            payload={"venue_plan_digest": binding.venue_plan_digest},
        )
    )
    if envelope is not None:
        ghv_stages.append(
            record_full_core_capital_guard_ghv_stage_v1(
                stage=STAGE_FINAL_ENVELOPE_BOUND,
                session_id=session_id,
                binding_digest=envelope.envelope_digest,
                guard_config_digest=binding.guard_config_digest,
                payload={"envelope_id": envelope.envelope_id},
            )
        )
    if binding.pre_external_reached:
        ghv_stages.append(
            record_full_core_capital_guard_ghv_stage_v1(
                stage=STAGE_PRE_EXTERNAL_REACHED,
                session_id=session_id,
                binding_digest=binding.envelope_digest,
                guard_config_digest=binding.guard_config_digest,
                payload={"terminal_disposition": binding.terminal_disposition},
            )
        )

    if reasons:
        bundle = build_full_core_capital_guard_ghv_bundle_v1(
            session_id=session_id,
            guard_config={},
            guard_input={"binding_digest": None, "block_reasons": reasons},
            evaluation=None,
            stages_observed=ghv_stages,
        )
        return FullCorePrePostCapitalGuardJoinResultV1(
            join_mode=mode.value,
            guard_allowed=False,
            guard_blocked=True,
            reasons=tuple(dict.fromkeys(reasons)),
            binding_digest=None,
            atomic_state=None,
            ghv_bundle=bundle,
            post_count=0,
            reservation_created=False,
        )

    if mode is FullCoreCapitalGuardJoinMode.OBSERVE_ONLY and not reasons:
        bundle = build_full_core_capital_guard_ghv_bundle_v1(
            session_id=session_id,
            guard_config={},
            guard_input={
                "binding_digest": binding.envelope_digest,
                "observe_only": True,
            },
            evaluation=None,
            stages_observed=ghv_stages,
        )
        return FullCorePrePostCapitalGuardJoinResultV1(
            join_mode=mode.value,
            guard_allowed=True,
            guard_blocked=False,
            reasons=(),
            binding_digest=binding.envelope_digest,
            atomic_state=None,
            ghv_bundle=bundle,
            post_count=0,
            reservation_created=False,
        )

    offline_stub_isolated = mode is FullCoreCapitalGuardJoinMode.OFFLINE_STUB
    skip_config_digest_mismatch = False
    if offline_stub_isolated:
        if guard_config is None:
            guard_config = ratified_offline_full_core_guard_config_v1()
            skip_config_digest_mismatch = True
        if margin_evidence is None:
            margin_evidence = CanaryCapitalGuardMarginEvidenceV1(
                avail_eq_usdc="100000",
                imr_rate="0.05",
                imr_source_class=IMR_SOURCE_PUBLIC_POSITION_TIERS_QTY_ONE,
                pretrade_decision_id=binding.canonical_decision_id,
                expected_pretrade_decision_id=binding.canonical_decision_id,
            )
        if exposure_evidence is None:
            exposure_evidence = CanaryCapitalGuardExposureEvidenceV1(
                open_order_count=0,
                open_position_count=0,
                unknown_submit_active=False,
                recovery_state_clear=True,
                transport_retry_count=0,
            )
        if atomic_state_dir is None:
            raw_atomic = str(os.environ.get(ATOMIC_STATE_DIR_ENV_VAR) or "").strip()
            if raw_atomic:
                atomic_state_dir = Path(raw_atomic)
        if observed_leverage is None or not str(observed_leverage).strip():
            observed_leverage = "5"

    cfg = guard_config or load_full_core_capital_guard_config_v1()
    if not skip_config_digest_mismatch and cfg.config_digest != binding.guard_config_digest:
        reasons.append("GUARD_CONFIG_DIGEST_MISMATCH")

    plan_limit_price = binding.order_price
    if (
        not str(plan_limit_price or "").strip()
        and str(binding.order_type).lower() == "market"
        and pretrade_reference_mark_px
        and str(pretrade_reference_mark_px).strip()
    ):
        plan_limit_price = str(pretrade_reference_mark_px).strip()

    plan = FullCoreCapitalGuardOrderPlanV1(
        instrument_id=binding.instrument_id,
        native_id=binding.native_id,
        side=binding.order_side,
        order_type=binding.order_type,
        quantity=binding.final_quantity,
        limit_price=plan_limit_price,
        min_sz=binding.min_sz,
        lot_sz=binding.lot_sz,
        ct_val=binding.ct_val,
        clordid=binding.clordid,
    )
    margin = margin_evidence or CanaryCapitalGuardMarginEvidenceV1(
        avail_eq_usdc=None,
        imr_rate=None,
        imr_source_class=None,
    )
    exposure = exposure_evidence or CanaryCapitalGuardExposureEvidenceV1(
        open_order_count=0,
        open_position_count=0,
        unknown_submit_active=False,
        recovery_state_clear=True,
        transport_retry_count=0,
    )
    session = guard_session or build_default_guard_session_v1(
        session_id=session_id,
        account_scope=binding.account_identity,
        instrument_id=binding.instrument_id,
        owner_go=binding.owner_go,
        guard_config=adapt_full_core_guard_config_to_canary_v1(cfg),
    )
    auth_binding = _authorization_binding_v1(binding, session_id=session_id)
    state_dir = atomic_state_dir or default_full_core_atomic_state_dir_v1()
    durable_state = full_core_durable_entry_state_for_guard_v1(
        state_dir=state_dir,
        consumption_key=auth_binding.consumption_key(),
    )

    evaluation: FullCoreCapitalGuardEvaluationV1 | None = None
    if not reasons:
        evaluation = evaluate_full_core_capital_guard_entry_v1(
            plan=plan,
            guard_config=cfg,
            margin_evidence=margin,
            exposure_evidence=exposure,
            owner_go=binding.owner_go,
            account_scope=binding.account_identity,
            session=session,
            observed_leverage=observed_leverage,
            durable_entry_state=durable_state,
            existing_exposure_notional_usdc=existing_exposure_notional_usdc,
        )
        if not evaluation.guard_allowed:
            reasons.extend(list(evaluation.reasons))

    bundle = build_full_core_capital_guard_ghv_bundle_v1(
        session_id=session_id,
        guard_config=cfg.to_dict(),
        guard_input={
            "binding_digest": auth_binding.binding_digest(),
            "envelope_digest": binding.envelope_digest,
            "venue_plan_digest": binding.venue_plan_digest,
        },
        evaluation=evaluation,
        stages_observed=ghv_stages,
    )

    if reasons or evaluation is None or not evaluation.guard_allowed:
        return FullCorePrePostCapitalGuardJoinResultV1(
            join_mode=mode.value,
            guard_allowed=False,
            guard_blocked=True,
            reasons=tuple(dict.fromkeys(reasons)),
            binding_digest=auth_binding.binding_digest(),
            atomic_state=durable_state,
            ghv_bundle=bundle,
            post_count=0,
            reservation_created=False,
        )

    if mode is FullCoreCapitalGuardJoinMode.OBSERVE_ONLY:
        return FullCorePrePostCapitalGuardJoinResultV1(
            join_mode=mode.value,
            guard_allowed=True,
            guard_blocked=False,
            reasons=(),
            binding_digest=auth_binding.binding_digest(),
            atomic_state=durable_state,
            ghv_bundle=bundle,
            post_count=0,
            reservation_created=False,
        )

    reservation_created = False
    atomic_state: str | None = durable_state
    try:
        assert_full_core_entry_authorization_available_v1(
            state_dir=state_dir,
            binding=auth_binding,
        )
        reserved = full_core_atomic_reserve_owner_go_authorization_v1(
            state_dir=state_dir,
            binding=auth_binding,
        )
        reservation_created = True
        atomic_state = reserved.state
        ghv_stages.append(
            record_full_core_capital_guard_ghv_stage_v1(
                stage=STAGE_ONE_SHOT_RESERVATION,
                session_id=session_id,
                binding_digest=auth_binding.binding_digest(),
                guard_config_digest=cfg.config_digest,
                payload={"state": reserved.state},
            )
        )
        if simulate_submit_boundary_crash:
            marked = full_core_atomic_mark_submit_boundary_v1(
                state_dir=state_dir,
                binding=auth_binding,
            )
            atomic_state = marked.state
            ghv_stages.append(
                record_full_core_capital_guard_ghv_stage_v1(
                    stage=STAGE_SUBMIT_BOUNDARY,
                    session_id=session_id,
                    binding_digest=auth_binding.binding_digest(),
                    guard_config_digest=cfg.config_digest,
                    payload={"state": STATE_SUBMIT_MAY_HAVE_OCCURRED},
                )
            )
            bundle = build_full_core_capital_guard_ghv_bundle_v1(
                session_id=session_id,
                guard_config=cfg.to_dict(),
                guard_input={"binding_digest": auth_binding.binding_digest()},
                evaluation=evaluation,
                stages_observed=ghv_stages,
            )
            return FullCorePrePostCapitalGuardJoinResultV1(
                join_mode=mode.value,
                guard_allowed=True,
                guard_blocked=False,
                reasons=("SUBMIT_BOUNDARY_UNKNOWN_HALTED",),
                binding_digest=auth_binding.binding_digest(),
                atomic_state=atomic_state,
                ghv_bundle=bundle,
                post_count=0,
                reservation_created=reservation_created,
            )
    except (FullCoreAtomicOneShotError, FullCoreCapitalGuardError) as exc:
        reasons.append(str(exc))
        return FullCorePrePostCapitalGuardJoinResultV1(
            join_mode=mode.value,
            guard_allowed=False,
            guard_blocked=True,
            reasons=tuple(dict.fromkeys(reasons)),
            binding_digest=auth_binding.binding_digest(),
            atomic_state=atomic_state,
            ghv_bundle=bundle,
            post_count=0,
            reservation_created=reservation_created,
        )

    if mode is FullCoreCapitalGuardJoinMode.OFFLINE_STUB:
        try:
            refuse_full_core_capital_guard_entry_unless_pass_v1(evaluation)
        except FullCoreCapitalGuardError as exc:
            raise FullCorePrePostCapitalGuardJoinError(str(exc)) from exc

    return FullCorePrePostCapitalGuardJoinResultV1(
        join_mode=mode.value,
        guard_allowed=True,
        guard_blocked=False,
        reasons=(),
        binding_digest=auth_binding.binding_digest(),
        atomic_state=atomic_state,
        ghv_bundle=bundle,
        post_count=0,
        reservation_created=reservation_created,
    )


def maybe_record_full_core_capital_guard_join_at_pre_external_v1(
    *,
    binding: FullCorePrePostCapitalGuardJoinBindingV1 | None,
    envelope: FinalOrderEnvelopeV1 | None,
    **kwargs: Any,
) -> dict[str, str]:
    """Productive handoff hook — default DISABLED; records join outcome in extra fields only."""
    if binding is None:
        return {}
    result = run_full_core_pre_post_capital_guard_join_v1(
        binding=binding,
        envelope=envelope,
        **kwargs,
    )
    if result.join_mode == FullCoreCapitalGuardJoinMode.DISABLED.value:
        return {}
    fields = {
        "FULL_CORE_CAPITAL_GUARD_JOIN_MODE": result.join_mode,
        "FULL_CORE_CAPITAL_GUARD_BLOCKED": "true" if result.guard_blocked else "false",
        "FULL_CORE_CAPITAL_GUARD_POST_COUNT": str(result.post_count),
    }
    if result.binding_digest:
        fields["FULL_CORE_CAPITAL_GUARD_BINDING_DIGEST"] = result.binding_digest
    if result.reasons:
        fields["FULL_CORE_CAPITAL_GUARD_REASONS"] = ",".join(result.reasons)
    auth_binding = _authorization_binding_v1(binding, session_id="full-core-capital-guard-join")
    fields[FULL_CORE_ATOMIC_CONSUMPTION_KEY] = auth_binding.consumption_key()
    return fields


__all__ = [
    "CONTRACT_ID",
    "FullCoreCapitalGuardJoinMode",
    "FullCorePrePostCapitalGuardJoinBindingV1",
    "FullCorePrePostCapitalGuardJoinError",
    "FullCorePrePostCapitalGuardJoinResultV1",
    "ATOMIC_STATE_DIR_ENV_VAR",
    "JOIN_ENV_VAR",
    "POST_COUNT",
    "maybe_record_full_core_capital_guard_join_at_pre_external_v1",
    "resolve_full_core_capital_guard_join_mode_v1",
    "run_full_core_pre_post_capital_guard_join_v1",
]
