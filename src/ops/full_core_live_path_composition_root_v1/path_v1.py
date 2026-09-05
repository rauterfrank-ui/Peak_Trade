"""Offline full Core→Live path: Replay result → composition → venue → pretrade → halt."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CURRENT_LIVE_CORE_PATH_PROVEN,
    FULL_CORE_RESTART_TEST_AUTHORIZED,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    PATH_KIND,
    PRE_SUBMIT_RECON,
    UNKNOWN_OUTCOME_RECON,
)
from src.ops.full_core_live_path_composition_root_v1.execution_boundary_v1 import (
    halt_at_live_execution_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CompositionStatusV1,
    FullCoreLivePathInputV1,
    FullCoreLivePathResultV1,
    PathStageV1,
)
from src.ops.full_core_live_path_composition_root_v1.pretrade_conjunction_v1 import (
    evaluate_frozen_pretrade_conjunction_v1,
)
from src.ops.full_core_live_path_composition_root_v1.venue_translation_v1 import (
    translate_core_live_intent_to_venue_plan_v1,
)


def _empty_result(
    *,
    status: CompositionStatusV1,
    stage: PathStageV1,
    reasons: tuple[str, ...],
    canonical_intent=None,
    intent=None,
    venue_plan=None,
    pretrade=None,
    boundary=None,
    recon: tuple[str, ...] = (),
) -> FullCoreLivePathResultV1:
    return FullCoreLivePathResultV1(
        status=status,
        stage=stage,
        reason_codes=reasons,
        intent=intent,
        canonical_intent=canonical_intent,
        venue_plan=venue_plan,
        pretrade=pretrade,
        boundary=boundary,
        wire_send_occurred=False,
        path_kind=PATH_KIND,
        canary_venue_proof_path=False,
        full_core_system_e2e_proven=FULL_CORE_SYSTEM_E2E_PROVEN,
        current_live_core_path_proven=CURRENT_LIVE_CORE_PATH_PROVEN,
        full_core_restart_test_authorized=FULL_CORE_RESTART_TEST_AUTHORIZED,
        recon_classes_reached=recon,
    )


def run_full_core_live_path_offline_v1(
    payload: FullCoreLivePathInputV1,
    *,
    attempt_wire_send: bool = False,
    attempt_construct_live_port: bool = False,
    injected_instrument_id: str | None = None,
    injected_side: str | None = None,
    injected_quantity: str | None = None,
) -> FullCoreLivePathResultV1:
    canonical = None
    if payload.replay is not None and payload.replay.intermediate is not None:
        canonical = payload.replay.intermediate.canonical_order_intent
    status, reasons, intent = compose_core_live_execution_intent_v1(
        replay=payload.replay,
        bound_instrument=payload.bound_instrument,
        mode=payload.mode,
        composed_epoch=payload.composed_epoch,
        seen_semantic_digests=payload.seen_semantic_digests,
        expected_trading_epoch=payload.expected_trading_epoch,
        injected_instrument_id=injected_instrument_id,
        injected_side=injected_side,
    )
    if status is not CompositionStatusV1.PASS or intent is None:
        return _empty_result(
            status=status,
            stage=PathStageV1.COMPOSITION,
            reasons=reasons,
            canonical_intent=canonical,
            recon=(UNKNOWN_OUTCOME_RECON,),
        )
    t_status, t_reasons, plan = translate_core_live_intent_to_venue_plan_v1(
        intent,
        session_id=payload.session_id,
        run_id=payload.run_id,
        td_mode=payload.td_mode,
        injected_instrument_id=injected_instrument_id,
        injected_side=injected_side,
        injected_quantity=injected_quantity,
    )
    if t_status is not CompositionStatusV1.PASS or plan is None:
        return _empty_result(
            status=t_status,
            stage=PathStageV1.VENUE_TRANSLATION,
            reasons=t_reasons,
            canonical_intent=canonical,
            intent=intent,
            recon=(UNKNOWN_OUTCOME_RECON,),
        )
    pretrade = evaluate_frozen_pretrade_conjunction_v1(
        plan=plan,
        frozen=payload.frozen_pretrade,
        owner_go=payload.owner_go,
    )
    if not pretrade.pretrade_valid or not pretrade.core_intent_valid:
        return _empty_result(
            status=CompositionStatusV1.DENY,
            stage=PathStageV1.PRETRADE,
            reasons=pretrade.reason_codes,
            canonical_intent=canonical,
            intent=intent,
            venue_plan=plan,
            pretrade=pretrade,
            recon=(UNKNOWN_OUTCOME_RECON, PRE_SUBMIT_RECON),
        )
    frozen = payload.frozen_pretrade
    capital_risk_mode = "OFFLINE_ALGEBRA"
    replay = payload.replay
    if replay is not None:
        mode = str(getattr(replay, "capital_risk_mode", "") or "")
        if not mode and replay.intermediate is not None:
            mode = str(getattr(replay.intermediate, "capital_risk_mode", "") or "")
        if mode:
            capital_risk_mode = mode
    boundary = halt_at_live_execution_boundary_v1(
        plan=plan,
        pretrade=pretrade,
        attempt_wire_send=attempt_wire_send,
        attempt_construct_live_port=attempt_construct_live_port,
        capital_risk_mode=capital_risk_mode,
        pretrade_source_kind=str(frozen.source_kind or "FROZEN_OFFLINE_PRETRADE_EVIDENCE"),
        pretrade_freshness_status=str(getattr(frozen, "freshness_status", "") or "FROZEN_OFFLINE"),
        path_mode=payload.mode,
        owner_go=payload.owner_go,
    )
    halt_reasons = boundary.reason_codes
    if not pretrade.owner_go_valid:
        return _empty_result(
            status=CompositionStatusV1.HALT,
            stage=PathStageV1.EXECUTION_BOUNDARY,
            reasons=halt_reasons,
            canonical_intent=canonical,
            intent=intent,
            venue_plan=plan,
            pretrade=pretrade,
            boundary=boundary,
            recon=(UNKNOWN_OUTCOME_RECON, PRE_SUBMIT_RECON),
        )
    return FullCoreLivePathResultV1(
        status=boundary.status,
        stage=PathStageV1.EXECUTION_BOUNDARY,
        reason_codes=halt_reasons,
        intent=intent,
        canonical_intent=canonical,
        venue_plan=plan,
        pretrade=pretrade,
        boundary=boundary,
        wire_send_occurred=False,
        path_kind=PATH_KIND,
        canary_venue_proof_path=False,
        full_core_system_e2e_proven=False,
        current_live_core_path_proven=False,
        full_core_restart_test_authorized=False,
        recon_classes_reached=(UNKNOWN_OUTCOME_RECON, PRE_SUBMIT_RECON),
    )
