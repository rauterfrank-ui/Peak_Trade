#!/usr/bin/env python3
"""WP-2 isolated side executor — CURRENT or historical worktree only.

RUNTIME_AUTHORIZATION_EFFECT=NONE
Writes JSON to path from WP2_OUTPUT_JSON env or argv[1].
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(os.environ.get("WP2_REPO_ROOT", Path(__file__).resolve().parents[4]))
SIDE = os.environ.get("WP2_SIDE", "current").strip().lower()
OUTPUT = os.environ.get("WP2_OUTPUT_JSON") or (sys.argv[1] if len(sys.argv) > 1 else "")


def _sha() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True)
            .strip()
            .lower()
        )
    except subprocess.CalledProcessError:
        return "unknown"


def _apply_single_lane_lifecycle_v1(**kwargs: Any):
    import inspect

    from trading.master_v2.single_lane_confirmation_activation_v1 import (
        apply_single_lane_confirmation_lifecycle_v1,
        inactive_single_lane_presence_v1,
        prior_presence_from_dual_carrier_v1,
        selected_lane_from_elementary_direction_v1,
    )

    sig = inspect.signature(apply_single_lane_confirmation_lifecycle_v1)
    if "prior_carrier" in sig.parameters:
        return apply_single_lane_confirmation_lifecycle_v1(**kwargs)
    prior_carrier = kwargs.pop("prior_carrier", None)
    elementary = kwargs["elementary"]
    selected = selected_lane_from_elementary_direction_v1(elementary)
    pp_sig = inspect.signature(prior_presence_from_dual_carrier_v1)
    if "active_evaluation_side" in pp_sig.parameters:
        prior_presence = prior_presence_from_dual_carrier_v1(
            prior_carrier,
            active_evaluation_side=selected,
        )
    else:
        prior_presence = prior_presence_from_dual_carrier_v1(prior_carrier)
    if prior_presence.kind.value == "inactive" and prior_carrier is None:
        prior_presence = inactive_single_lane_presence_v1()
    return apply_single_lane_confirmation_lifecycle_v1(
        prior_presence=prior_presence,
        **kwargs,
    )


def _json_safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_json_safe(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if is_dataclass(obj) and not isinstance(obj, type):
        return _json_safe(asdict(obj))
    if hasattr(obj, "value"):
        return str(getattr(obj, "value"))
    return str(obj)


def _carrier_snapshot(carrier: Any) -> dict[str, Any]:
    if carrier is None:
        return {"present": False}
    bull = carrier.bull_confirmation_state
    bear = carrier.bear_confirmation_state
    return {
        "present": True,
        "bull_distinct_count": int(bull.distinct_confirmation_observation_count),
        "bull_assessment_state": str(bull.assessment_state.value),
        "bull_latest_epoch": str(bull.latest_accepted_market_observation_epoch),
        "bear_distinct_count": int(bear.distinct_confirmation_observation_count),
        "bear_assessment_state": str(bear.assessment_state.value),
        "bear_latest_epoch": str(bear.latest_accepted_market_observation_epoch),
    }


def _trace_replay_result(cycle: int, result: Any, side_state_before: str) -> dict[str, Any]:
    im = result.intermediate
    out: dict[str, Any] = {
        "cycle": cycle,
        "replay_pass": bool(result.replay_pass),
        "fail_reasons": list(result.fail_reasons or ()),
        "decision_outcome": str(result.evidence.decision_outcome if result.evidence else ""),
        "side_state_before": side_state_before,
    }
    if im is not None:
        out["side_state_after"] = str(im.state_switch.next_side_state)
        out["runtime_scope_before"] = _json_safe(im.runtime_scope_state_before)
        out["runtime_scope_after"] = _json_safe(im.runtime_scope_state_after)
        out["composition_status"] = str(im.composition_result.composition_status.value)
        c3 = im.directional_confirmation_progress_after
        out["carrier_after"] = _carrier_snapshot(c3)
        if im.bull_assessment is not None:
            out["c3_status"] = str(im.bull_assessment.status.value)
            out["c3_signal_strength"] = float(im.bull_assessment.signal_strength)
        elif im.bear_assessment is not None:
            out["c3_status"] = str(im.bear_assessment.status.value)
            out["c3_signal_strength"] = float(im.bear_assessment.signal_strength)
    return out


def _build_replay_helpers():
    from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
        _market_context,
        _replay_input,
    )
    from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
    from trading.master_v2.double_play_entry_exit_policy_v0 import (
        DecisionOutcome,
        EntryExitDirectionState,
        ReconciliationState,
    )
    from trading.master_v2.double_play_state import SideState
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        run_integrated_offline_trading_logic_replay_v1,
    )

    def market_context(**kw: Any):
        return _market_context(**kw)

    def replay_input(**overrides: Any):
        return _replay_input(**overrides)

    return {
        "market_context": market_context,
        "replay_input": replay_input,
        "run": run_integrated_offline_trading_logic_replay_v1,
        "SideState": SideState,
        "ScopeDirectionState": ScopeDirectionState,
        "EntryExitDirectionState": EntryExitDirectionState,
        "ReconciliationState": ReconciliationState,
        "DecisionOutcome": DecisionOutcome,
    }


def vector_a_bull_enter(h: Mapping[str, Any]) -> dict[str, Any]:
    run = h["run"]
    replay_input = h["replay_input"]
    SideState = h["SideState"]
    DecisionOutcome = h["DecisionOutcome"]
    inp = replay_input(
        side_state=SideState.LONG_ARMED,
        direction_state=h["EntryExitDirectionState"].LONG_ARMED,
    )
    result = run(inp)
    comp = (
        str(result.intermediate.composition_result.composition_status.value)
        if result.intermediate
        else ""
    )
    enter = (
        result.evidence is not None
        and str(result.evidence.decision_outcome) == DecisionOutcome.ENTER_LONG.value
    )
    return {
        "vector_id": "A_BULL_ENTER_LONG",
        "cycles": [_trace_replay_result(0, result, str(inp.side_state.value))],
        "enter_long": enter,
        "composition_status": comp,
        "composition_reached": comp.lower() == "long_selected",
    }


def vector_b_bear_enter(h: Mapping[str, Any]) -> dict[str, Any]:
    run = h["run"]
    replay_input = h["replay_input"]
    SideState = h["SideState"]
    ScopeDirectionState = h["ScopeDirectionState"]
    DecisionOutcome = h["DecisionOutcome"]
    inp = replay_input(
        side_state=SideState.SHORT_ARMED,
        direction_state=h["EntryExitDirectionState"].SHORT_ARMED,
        scope_direction_state=ScopeDirectionState.SHORT,
        price_path=(3600.0, 3530.0),
        canonical_market_context=h["market_context"](
            mark_price=3530.0,
            momentum_feature_set={"rsi": 45.0, "roc": -0.02},
        ),
    )
    result = run(inp)
    enter = (
        result.evidence is not None
        and str(result.evidence.decision_outcome) == DecisionOutcome.ENTER_SHORT.value
    )
    return {
        "vector_id": "B_BEAR_ENTER_SHORT",
        "cycles": [_trace_replay_result(0, result, str(inp.side_state.value))],
        "enter_short": enter,
    }


def vector_c_duplicate_c1(h: Mapping[str, Any]) -> dict[str, Any]:
    from trading.market_state.distinct_market_observation_acceptor_v1 import (
        ObservationCandidateV1,
        ObservationClassification,
        commit_observation_acceptance_v1,
        evaluate_distinct_market_observation_v1,
        initial_observation_acceptance_state_v1,
    )
    from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
    from trading.market_state.directional_confirmation_progress_v1 import (
        ConfirmationAssessmentSignalV1,
        ConfirmationProgressInputV1,
        ConfirmationSideV1,
        evaluate_confirmation_progress_v1,
    )
    from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
        non_advancing_observation_acceptance_result_v1,
    )
    from trading.market_state.elementary_direction_v1 import (
        evaluate_elementary_direction_from_observation_acceptance_v1,
    )
    key = InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="inst-eth-usdt-perp",
        venue_instrument_id="ETH-USDT-SWAP",
    )
    state = initial_observation_acceptance_state_v1(bound_instrument_key=key)

    def eval_c1(mark: float, t: float):
        nonlocal state
        cand = ObservationCandidateV1(
            venue=key.venue,
            canonical_instrument_id=key.canonical_instrument_id,
            venue_instrument_id=key.venue_instrument_id,
            venue_event_time=t,
            mark_price=mark,
        )
        res = evaluate_distinct_market_observation_v1(state, cand)
        if res.classification is ObservationClassification.DISTINCT:
            state = commit_observation_acceptance_v1(current_state=state, result=res)
        return res

    first = eval_c1(3500.0, 1000.0)
    second = eval_c1(3570.0, 1060.0)
    duplicate = non_advancing_observation_acceptance_result_v1(
        bound_instrument_key=key,
        market_observation_epoch=second.state_after.market_observation_epoch,
    )
    third = eval_c1(3580.0, 1120.0)

    cycles = []
    prior_carrier = None
    for idx, (acceptor, label) in enumerate(
        (
            (first, "distinct_1"),
            (second, "distinct_2"),
            (duplicate, "duplicate_noop"),
            (third, "distinct_3"),
        )
    ):
        elem = evaluate_elementary_direction_from_observation_acceptance_v1(
            acceptor,
            bound_instrument_key=key,
            current_mark=(
                acceptor.observation_identity.mark_price
                if acceptor.observation_identity
                else 3570.0
            ),
        )
        life = _apply_single_lane_lifecycle_v1(
            prior_carrier=prior_carrier,
            elementary=elem,
            observation_acceptance_result=acceptor,
            session_id="wp2-c1",
            venue="okx_eea",
            instrument=key,
        )
        prior_carrier = getattr(life, "carrier_after_lifecycle", None)
        prog = None
        if life.presence.is_active:
            prog = evaluate_confirmation_progress_v1(
                ConfirmationProgressInputV1(
                    prior_state=life.presence.authoritative_confirmation_progress(),
                    observation_acceptance_result=acceptor,
                    session_id="wp2-c1",
                    venue="okx_eea",
                    instrument=key,
                    side=life.presence.selected_side or ConfirmationSideV1.LONG,
                    assessment_signal=ConfirmationAssessmentSignalV1.CONFIRMED,
                    confirmation_threshold=2,
                )
            )
        cycles.append(
            {
                "cycle": idx,
                "label": label,
                "c1_classification": str(acceptor.classification.value),
                "lifecycle_reason": life.reason_code,
                "carrier_after": _carrier_snapshot(
                    getattr(life, "carrier_after_lifecycle", None)
                ),
                "distinct_count_after": (
                    int(prog.state_after.distinct_confirmation_observation_count)
                    if prog is not None
                    else None
                ),
                "confirmation_advanced": (
                    bool(prog and not prog.fail_closed and prog.state_after != prog.state_before)
                    if prog is not None
                    else False
                ),
            }
        )

    def _bull_dist(cycle: dict[str, Any]) -> int | None:
        car = cycle.get("carrier_after") or {}
        if not car.get("present"):
            return None
        return int(car.get("bull_distinct_count", 0))

    dup_cycle = cycles[2]
    return {
        "vector_id": "C_DUPLICATE_C1",
        "cycles": cycles,
        "duplicate_advanced_confirmation": bool(dup_cycle.get("confirmation_advanced")),
        "duplicate_distinct_increment": (
            _bull_dist(cycles[1]),
            _bull_dist(cycles[2]),
            _bull_dist(cycles[3]),
        ),
    }


def vector_f1_fresh_stale(h: Mapping[str, Any]) -> dict[str, Any]:  # noqa: ARG001 — replay_input via h
    has_f1_consumer = False
    try:
        from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
            RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
            evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1,
            consumer_wiring_authorized_v1,
        )
        from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
            GovernedF1M9ThresholdConsumerWiringRequestV1,
            run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
        )

        has_f1_consumer = True
    except ImportError:
        RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS = 600
        consumer_wiring_authorized_v1 = lambda **_: False  # type: ignore
    from src.governance.f1_m9_productive_apply_ledger_v1 import (
        F1M9ProductiveApplyLedgerPathsV1,
        initialize_empty_revocation_ledger_v1,
    )
    from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
        F1M9ThresholdValueAuthorizationLedgerPathsV1,
        initialize_empty_threshold_revocation_ledger_v1,
    )
    from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
        bind_typed_canonical_volatility_estimate_into_market_context_v1,
        evaluate_typed_volatility_binding_eligibility_v1,
    )
    from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
        build_canonical_volatility_estimate_v1,
    )
    from trading.master_v2.canonical_market_context_v1 import with_computed_input_digest
    from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
        evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
    )
    from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
        resolve_governed_runtime_seam_for_presence_gate_v1,
    )
    runtime_surface = "F1_M9_INTEGRATED_OFFLINE_REPLAY"
    if has_f1_consumer:
        from src.governance.current_productive_activation_policy_v1 import (
            RUNTIME_SURFACE_F1_M9_INTEGRATED_OFFLINE_REPLAY,
        )

        runtime_surface = RUNTIME_SURFACE_F1_M9_INTEGRATED_OFFLINE_REPLAY
    from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
        _context,
        _valid_estimate,
    )

    run = h["run"]
    replay_input = h["replay_input"]

    with tempfile.TemporaryDirectory(prefix="wp2-f1m9-") as tmp:
        root = Path(tmp)
        rev = root / "apply_rev.jsonl"
        initialize_empty_revocation_ledger_v1(rev)
        apply_paths = F1M9ProductiveApplyLedgerPathsV1(
            apply_ledger_path=root / "apply.jsonl",
            revocation_ledger_path=rev,
        )
        trev = root / "thr_rev.jsonl"
        initialize_empty_threshold_revocation_ledger_v1(trev)
        threshold_paths = F1M9ThresholdValueAuthorizationLedgerPathsV1(
            threshold_ledger_path=root / "thr.jsonl",
            threshold_revocation_ledger_path=trev,
        )
        seam: dict[str, Any] = {}
        if has_f1_consumer:
            cont = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
                GovernedF1M9ThresholdConsumerWiringRequestV1(
                    apply_ledger_paths=apply_paths,
                    threshold_ledger_paths=threshold_paths,
                    repo_root=REPO_ROOT,
                )
            )
            seam = dict(cont.bound_seam_record or {})

        fresh_est = _valid_estimate()
        stale_est = build_canonical_volatility_estimate_v1(
            value=0.004321,
            observation_count=61,
            as_of_event_time=datetime(2026, 6, 30, 10, 0, tzinfo=timezone.utc),
            fallback_used=False,
            source_digest="b" * 64,
        )

        base_ctx = h["market_context"](volatility_estimate=0.0)

        def bound(estimate: Any):
            ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
                base_ctx,
                estimate,
            )
            return ctx, evaluate_typed_volatility_binding_eligibility_v1(ctx)

        fresh_ctx, fresh_elig = bound(fresh_est)
        stale_ctx, stale_elig = bound(stale_est)

        old_fresh_gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
            fresh_ctx,
            eligibility=fresh_elig,
            authorized_productive_parameter_seam=resolve_governed_runtime_seam_for_presence_gate_v1(
                seam
            ).seam_for_consumer,
        )
        old_stale_gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
            stale_ctx,
            eligibility=stale_elig,
            authorized_productive_parameter_seam=resolve_governed_runtime_seam_for_presence_gate_v1(
                seam
            ).seam_for_consumer,
        )

        new_fresh = None
        new_stale = None
        if has_f1_consumer:
            new_fresh = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
                market_context=fresh_ctx,
                eligibility=fresh_elig,
                governed_seam_record=seam,
                require_governed_seam=True,
                runtime_surface=runtime_surface,
                repo_root=REPO_ROOT,
            )
            new_stale = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
                market_context=stale_ctx,
                eligibility=stale_elig,
                governed_seam_record=seam,
                require_governed_seam=True,
                runtime_surface=runtime_surface,
                repo_root=REPO_ROOT,
            )

        def replay_with_gate(ctx: Any, elig: Any, seam_rec: dict) -> dict[str, Any]:
            inp = replay_input(
                canonical_market_context=ctx,
                require_productive_typed_volatility_presence_gate=True,
                productive_typed_volatility_binding_eligibility=elig,
                governed_authorized_productive_parameter_seam_record=seam_rec,
            )
            r = run(inp)
            return {
                "replay_pass": bool(r.replay_pass),
                "decision_outcome": str(r.evidence.decision_outcome if r.evidence else ""),
                "fail_reasons": list(r.fail_reasons or ()),
            }

        def _consumer_alpha(path: Any) -> bool | None:
            if path is None:
                return None
            return bool(path.alpha_scope_entry_authority_allowed)

        return {
            "vector_id": "D_E_F1M9_FRESH_STALE",
            "has_f1_m9_consumer_module": has_f1_consumer,
            "consumer_wiring_authorized": (
                consumer_wiring_authorized_v1(repo_root=REPO_ROOT) if has_f1_consumer else False
            ),
            "ratified_max_age_seconds": RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS,
            "fresh": {
                "old_presence_alpha_allowed": bool(old_fresh_gate.alpha_scope_entry_authority_allowed),
                "new_consumer_alpha_allowed": _consumer_alpha(new_fresh),
                "new_enforcement_applied": (
                    bool(new_fresh.enforcement_applied) if new_fresh is not None else None
                ),
                "integrated_replay": replay_with_gate(fresh_ctx, fresh_elig, seam),
            },
            "stale": {
                "old_presence_alpha_allowed": bool(old_stale_gate.alpha_scope_entry_authority_allowed),
                "new_consumer_alpha_allowed": _consumer_alpha(new_stale),
                "new_enforcement_applied": (
                    bool(new_stale.enforcement_applied) if new_stale is not None else None
                ),
                "integrated_replay": replay_with_gate(stale_ctx, stale_elig, seam),
            },
        }


def vector_f_recon(h: Mapping[str, Any]) -> dict[str, Any]:
    run = h["run"]
    replay_input = h["replay_input"]
    ReconciliationState = h["ReconciliationState"]
    traces = []
    for label, recon in (
        ("reconciled_flat", ReconciliationState.RECONCILED),
        ("reconciliation_required", ReconciliationState.RECONCILIATION_REQUIRED),
    ):
        inp = replay_input(reconciliation_state=recon, venue_flat=True)
        r = run(inp)
        traces.append(
            {
                "label": label,
                "reconciliation_state": str(recon.value),
                "decision_outcome": str(r.evidence.decision_outcome if r.evidence else ""),
                "replay_pass": bool(r.replay_pass),
            }
        )
    return {"vector_id": "F_RECON_POSITION_FLAT", "cases": traces}


def vector_g_integrated_two_cycle(h: Mapping[str, Any]) -> dict[str, Any]:
    from trading.market_state.distinct_market_observation_acceptor_v1 import (
        ObservationCandidateV1,
        ObservationClassification,
        commit_observation_acceptance_v1,
        evaluate_distinct_market_observation_v1,
        initial_observation_acceptance_state_v1,
    )
    from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
    from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
        initial_directional_confirmation_side_state_carrier_v1,
    )

    run = h["run"]
    replay_input = h["replay_input"]
    SideState = h["SideState"]
    key = InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="inst-eth-usdt-perp",
        venue_instrument_id="ETH-USDT-SWAP",
    )
    c1_state = initial_observation_acceptance_state_v1(bound_instrument_key=key)

    def next_distinct(mark: float, t: float):
        nonlocal c1_state
        cand = ObservationCandidateV1(
            venue=key.venue,
            canonical_instrument_id=key.canonical_instrument_id,
            venue_instrument_id=key.venue_instrument_id,
            venue_event_time=t,
            mark_price=mark,
        )
        res = evaluate_distinct_market_observation_v1(c1_state, cand)
        if res.classification is ObservationClassification.DISTINCT:
            c1_state = commit_observation_acceptance_v1(current_state=c1_state, result=res)
        return res

    acc1 = next_distinct(3500.0, 1000.0)
    acc2 = next_distinct(3570.0, 1060.0)
    carrier0 = initial_directional_confirmation_side_state_carrier_v1(
        session_id="wp2-g",
        venue="okx_eea",
        instrument=key,
    )
    inp1 = replay_input(
        trading_epoch=44,
        observation_acceptance_result=acc1,
        directional_confirmation_progress=carrier0,
        confirmation_progress_session_id="wp2-g",
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=key,
    )
    r1 = run(inp1)
    carrier1 = (
        r1.intermediate.directional_confirmation_progress_after
        if r1.intermediate
        else carrier0
    )
    epoch2 = 45
    inp2 = replay_input(
        trading_epoch=epoch2,
        canonical_market_context=h["market_context"](trading_epoch=epoch2),
        observation_acceptance_result=acc2,
        directional_confirmation_progress=carrier1,
        confirmation_progress_session_id="wp2-g",
        confirmation_progress_venue="okx_eea",
        confirmation_progress_instrument=key,
        side_state=(
            SideState(r1.intermediate.state_switch.next_side_state)
            if r1.intermediate
            else inp1.side_state
        ),
    )
    r2 = run(inp2)
    return {
        "vector_id": "G_SINGLE_LANE_TWO_CYCLE",
        "cycles": [
            _trace_replay_result(0, r1, str(inp1.side_state.value)),
            _trace_replay_result(1, r2, str(inp2.side_state.value)),
        ],
    }


def vector_h_layered_init() -> dict[str, Any]:
    """Layered-core observation candidate construction (host bind seam)."""
    try:
        from src.ops.p5_10_productive_activation_and_binding_v1 import productive_cycle_bind_seam_v1 as seam_mod
    except ImportError as exc:
        return {"vector_id": "H_LAYERED_INIT", "error": str(exc), "skipped": True}

    src = Path(seam_mod.__file__).read_text(encoding="utf-8")
    has_cmc_mark_obs = "_observation_candidates_from_cmc_mark_v1" in src
    has_close_grid = "_observation_candidates_from_finalized_closes_v1" in src
    has_carryforward = "side_state_from_transition_carryforward" in src
    return {
        "vector_id": "H_LAYERED_INIT",
        "current_module_markers": {
            "cmc_mark_obs_helper": has_cmc_mark_obs,
            "finalized_closes_grid_helper": has_close_grid,
            "transition_carryforward_param": has_carryforward,
        },
        "note": "Historical side verified via worktree module markers in orchestrator",
    }


def vector_i_canonical_provenance() -> dict[str, Any]:
    try:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
            FORBIDDEN_MARK_SOURCES,
            ProductiveCanonicalPriceProvenanceError,
            ProductiveCycleCanonicalPriceProvenanceV1,
            build_explicit_test_fixture_price_provenance_v1,
        )
    except ImportError:
        return {
            "vector_id": "I_CANONICAL_PRICE_PROVENANCE",
            "module_present": False,
            "old_equivalent_restriction": False,
        }

    valid = build_explicit_test_fixture_price_provenance_v1(
        mark_px=3570.0,
        index_px=3568.0,
        venue_native_id="ETH-USDT-SWAP",
    )
    valid_ok = True
    try:
        valid.validate_against_cycle_inputs_v1(
            mark_px=3570.0, index_px=3568.0, venue_native_id="ETH-USDT-SWAP"
        )
    except ProductiveCanonicalPriceProvenanceError:
        valid_ok = False

    forbidden_ok = False
    try:
        bad = ProductiveCycleCanonicalPriceProvenanceV1(
            mark_price_class="CMC_MARK_PRICE",
            mark_source="ORDINARY_MARKET_CANDLE_CLOSE",
            mark_px=3570.0,
            index_price_class="INDEX_PRICE",
            index_source="EXPLICIT_TEST_FIXTURE_INDEX",
            index_px=3568.0,
            venue_native_id="ETH-USDT-SWAP",
            mark_finalization_state="CURRENT",
            mark_temporal_class="DERIVED_CURRENT_VALUE",
            index_temporal_class="DERIVED_CURRENT_VALUE",
        )
        bad.validate_against_cycle_inputs_v1(
            mark_px=3570.0, index_px=3568.0, venue_native_id="ETH-USDT-SWAP"
        )
    except ProductiveCanonicalPriceProvenanceError:
        forbidden_ok = True

    return {
        "vector_id": "I_CANONICAL_PRICE_PROVENANCE",
        "valid_provenance_passes": valid_ok,
        "forbidden_mark_source_blocked": forbidden_ok,
        "forbidden_sources": sorted(FORBIDDEN_MARK_SOURCES),
        "old_equivalent_restriction": False,
    }


def vector_g17_bind_current_only() -> dict[str, Any]:
    """G17 bind policy markers on this side."""
    try:
        from src.ops.full_core_live_path_composition_root_v1 import (
            current_productive_g17_typed_vol_cmc_bind_v1 as g17,
        )
    except ImportError:
        return {"vector_id": "G17_CMC_BIND", "skipped": True}
    return {
        "vector_id": "G17_CMC_BIND",
        "estimate_absent_policy": getattr(g17, "ESTIMATE_ABSENT_CMC_POLICY", ""),
        "reuse_allowed_outcomes": sorted(
            x.value for x in getattr(g17, "_REUSE_ALLOWED_OUTCOMES", ())
        ),
    }


def main() -> int:
    sha = _sha()
    h = _build_replay_helpers()
    payload: dict[str, Any] = {
        "side": SIDE,
        "repository_sha": sha,
        "repo_root": str(REPO_ROOT),
        "vectors": {},
    }
    payload["vectors"]["A"] = vector_a_bull_enter(h)
    payload["vectors"]["B"] = vector_b_bear_enter(h)
    payload["vectors"]["C"] = vector_c_duplicate_c1(h)
    payload["vectors"]["D_E"] = vector_f1_fresh_stale(h)
    payload["vectors"]["F"] = vector_f_recon(h)
    payload["vectors"]["G"] = vector_g_integrated_two_cycle(h)
    payload["vectors"]["H"] = vector_h_layered_init()
    payload["vectors"]["I"] = vector_i_canonical_provenance()
    payload["vectors"]["G17"] = vector_g17_bind_current_only()

    text = json.dumps(payload, indent=2, sort_keys=True)
    out_path = Path(OUTPUT) if OUTPUT else Path("-")
    if str(out_path) == "-":
        print(text)
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
