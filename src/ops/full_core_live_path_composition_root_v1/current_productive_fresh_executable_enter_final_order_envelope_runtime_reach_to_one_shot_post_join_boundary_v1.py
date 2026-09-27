"""PRE_EXTERNAL → fresh EXECUTABLE Enter FinalOrderEnvelopeV1 → #6900 join boundary.

Proves runtime reachability of the typed envelope for the governed one-shot POST join.
Does not consume POST Owner-GO. Does not POST. Does not mint durable permit consume.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    prove_one_shot_join_standing_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    CurrentProductiveFullCorePreExternalClosureResultV1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_"
    "RUNTIME_REACH_TO_ONE_SHOT_POST_JOIN_BOUNDARY_V1"
)
THIS_SLICE = (
    "11.2.1.DN.FULL_CORE_CURRENT_PRODUCTIVE_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_"
    "ENVELOPE_RUNTIME_REACH_TO_ONE_SHOT_POST_JOIN_BOUNDARY_V1"
)
BLOCKER_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_UNAVAILABLE_AT_RUNTIME = (
    "FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_UNAVAILABLE_AT_RUNTIME"
)
EXPECTED_BASELINE_ORIGIN_MAIN_SHA = "c93ea739848963b0c971161d44538be19292317c"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"


class FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError(RuntimeError):
    """Fail-closed runtime reach to one-shot POST join boundary."""


@dataclass(frozen=True)
class FreshExecutableEnterFinalOrderEnvelopeRuntimeReachResultV1:
    envelope_id: str
    envelope_digest: str
    decision_result: str
    terminal_disposition: str
    one_shot_post_join_boundary_reachable: str
    post_go_consumed: str
    real_post_execution: str


def _assert_standing_pins_v1() -> None:
    prove_one_shot_join_standing_boundary_v1()
    if (
        EXTERNAL_EFFECT_AUTHORIZED is True
        or POST_ALLOWED is True
        or REAL_VENUE_POST_ALLOWED is True
    ):
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError(
            "STANDING_POST_PINS_MUST_REMAIN_FALSE"
        )
    if str(STEP_29Q_PLAN_ONLY) != "PLAN_ONLY":
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError(
            "STEP_29Q_MUST_REMAIN_PLAN_ONLY"
        )
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError(
            "MAX_POSITIONS_EFFECTIVE_MUST_REMAIN_ONE"
        )
    if current_productive_first_real_blocker_v1() != (
        "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
    ):
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError("FIRST_REAL_BLOCKER_DRIFT")


def resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1(
    closure: CurrentProductiveFullCorePreExternalClosureResultV1,
) -> FinalOrderEnvelopeV1:
    """Earliest fail-closed resolver for typed Enter envelope at PRE_EXTERNAL."""
    if str(closure.current_productive_decision_result or "") != "EXECUTABLE_VENUE_PLAN_BOUND":
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError("DECISION_NOT_EXECUTABLE")
    if str(closure.decision_execution_eligible or "").lower() != "true":
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError("DECISION_NOT_ELIGIBLE")
    if str(closure.envelope_readiness or "").lower() != "true":
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError("ENVELOPE_NOT_READY")
    if str(closure.pre_external_effect_boundary_reached or "").lower() != "true":
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError("PRE_EXTERNAL_NOT_REACHED")
    if str(closure.terminal_disposition or "") != DISPOSITION_PRE_EXTERNAL_EFFECT:
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError("TERMINAL_NOT_PRE_EXTERNAL")
    if int(closure.post_count) != 0 or closure.permit_created or closure.external_effect_occurred:
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError(
            "EXTERNAL_EFFECT_OR_POST_LEAK"
        )
    envelope = closure.fresh_executable_enter_final_order_envelope
    if envelope is None:
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError(
            BLOCKER_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_UNAVAILABLE_AT_RUNTIME
        )
    assert_envelope_unmodified_v1(envelope)
    return envelope


def prove_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_v1(
    *,
    owner_go: str,
    baseline_origin_main_sha: str,
    closure: CurrentProductiveFullCorePreExternalClosureResultV1,
    store_root: Path | str | None = None,
) -> FreshExecutableEnterFinalOrderEnvelopeRuntimeReachResultV1:
    if str(owner_go or "") != OWNER_GO:
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError("OWNER_GO_MISMATCH")
    if str(baseline_origin_main_sha or "") != EXPECTED_BASELINE_ORIGIN_MAIN_SHA:
        raise FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError("BASELINE_SHA_MISMATCH")
    _assert_standing_pins_v1()
    envelope = resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1(
        closure
    )
    if store_root is not None:
        root = Path(store_root)
        root.mkdir(parents=True, exist_ok=True)
        from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
            _assert_no_secrets,
            _persist_json,
        )

        reach_claims: Mapping[str, Any] = {
            "DOCUMENT_CLASS": THIS_SLICE,
            "OWNER_GO": OWNER_GO,
            "BASELINE_ORIGIN_MAIN_SHA": baseline_origin_main_sha,
            "ENVELOPE_ID": envelope.envelope_id,
            "ENVELOPE_DIGEST": envelope.envelope_digest,
            "ONE_SHOT_POST_JOIN_BOUNDARY_REACHABLE": TRUE_TOKEN,
            "POST_GO_CONSUMED": FALSE_TOKEN,
            "REAL_POST_EXECUTION": FALSE_TOKEN,
        }
        _assert_no_secrets(dict(reach_claims))
        _persist_json(path=root / "RUNTIME_REACH_TO_ONE_SHOT_POST_JOIN.json", payload=reach_claims)
    return FreshExecutableEnterFinalOrderEnvelopeRuntimeReachResultV1(
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        decision_result=str(closure.current_productive_decision_result),
        terminal_disposition=str(closure.terminal_disposition),
        one_shot_post_join_boundary_reachable=TRUE_TOKEN,
        post_go_consumed=FALSE_TOKEN,
        real_post_execution=FALSE_TOKEN,
    )


__all__ = [
    "BLOCKER_FRESH_EXECUTABLE_ENTER_FINAL_ORDER_ENVELOPE_UNAVAILABLE_AT_RUNTIME",
    "EXPECTED_BASELINE_ORIGIN_MAIN_SHA",
    "OWNER_GO",
    "THIS_SLICE",
    "FreshExecutableEnterFinalOrderEnvelopeRuntimeReachError",
    "FreshExecutableEnterFinalOrderEnvelopeRuntimeReachResultV1",
    "prove_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_v1",
    "resolve_fresh_executable_enter_final_order_envelope_from_pre_external_closure_v1",
]
