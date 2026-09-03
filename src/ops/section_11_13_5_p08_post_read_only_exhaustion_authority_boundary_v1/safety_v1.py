"""Safety analysis for the P08 authority-boundary persist.

Proves no accidental submit, no hidden live-arm mutation, no implicit
authorization from historical GOs, and that closing P08 later would not
silently grant execution readiness.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authorization_v1 import (
    default_authorization_is_false_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CORE_LOGIC_CHANGE,
    GENERAL_LIVE_SUBMIT_UNLOCKED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (
    CORE_CHANGE_ALLOWED,
    FUTURE_GO_AUTHORIZES_FLATTEN,
    FUTURE_GO_AUTHORIZES_POST,
    OWNER_GO,
    P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS,
    POST_ALLOWED,
    SECOND_TRADING_AUTHORITY_INTRODUCED,
)


class P08SafetyAnalysisError(RuntimeError):
    """Fail-closed safety-analysis violation."""


def prove_safety_invariants_v1() -> dict[str, Any]:
    """Return the bound safety proof. Not submit and not flatten."""
    if OWNER_GO not in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        raise P08SafetyAnalysisError("OWNER_GO_MUST_BE_FORBIDDEN_FLATTEN_EXECUTE")
    flatten_ok, flatten_reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=OWNER_GO,
    )
    if flatten_ok:
        raise P08SafetyAnalysisError("THIS_GO_MUST_NOT_ACCEPT_AS_FLATTEN_EXECUTE")
    submit = evaluate_canary_submit_gates_v1(
        owner_go=OWNER_GO,
        owner_go_consumed=False,
        authorization_scope="LIVE_CANARY_MINIMUM_EXPOSURE",
        bound_origin_main_sha="c13d01e20f78cfb4f8d745c1b31a628bba24c275",
        expected_origin_main_sha="c13d01e20f78cfb4f8d745c1b31a628bba24c275",
        live_canary_authorized=True,
        live_enabled=True,
        live_armed=True,
        confirm_token="I_KNOW_WHAT_I_AM_DOING",
        blocks_new_entry=False,
        unresolved_economic_divergence=False,
        live_reconciliation_proven=True,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        environment="LIVE",
        fixture_or_demo_or_testnet=False,
        max_notional="1",
        min_executable_notional="1",
        order_count=1,
        position_count=0,
        exposure_above_minimum_bound=False,
        live_canary_cybersecurity_gate="PASS",
        rest_host="eea.okx.com",
        secretref_uri="secretref://vault/peak-trade/live-canary-minimum-exposure/okx",
        open_order_count=0,
        open_position_count=0,
        require_notional_bounds=False,
        recovery_state_clear=True,
    )
    if submit.submit_allowed:
        raise P08SafetyAnalysisError("THIS_GO_MUST_NOT_PASS_SUBMIT_GATES")
    if LIVE_ENABLED or LIVE_ARMED or LIVE_AUTHORIZED or SUBMIT_UNLOCKED:
        raise P08SafetyAnalysisError("STANDING_LIVE_GATES_MUST_REMAIN_FALSE")
    if TESTNET_AUTHORIZED or GENERAL_LIVE_SUBMIT_UNLOCKED:
        raise P08SafetyAnalysisError("STANDING_TESTNET_OR_GENERAL_SUBMIT_MUST_REMAIN_FALSE")
    if CORE_LOGIC_CHANGE or CORE_CHANGE_ALLOWED:
        raise P08SafetyAnalysisError("CORE_LOGIC_MUST_REMAIN_UNCHANGED")
    if SECOND_TRADING_AUTHORITY_INTRODUCED:
        raise P08SafetyAnalysisError("SECOND_TRADING_AUTHORITY_FORBIDDEN")
    if POST_ALLOWED or FUTURE_GO_AUTHORIZES_POST or FUTURE_GO_AUTHORIZES_FLATTEN:
        raise P08SafetyAnalysisError("POST_OR_FLATTEN_MUST_REMAIN_FALSE")
    if not default_authorization_is_false_v1():
        raise P08SafetyAnalysisError("DEFAULT_CANARY_AUTHORIZATION_MUST_REMAIN_FALSE")
    if not P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS:
        raise P08SafetyAnalysisError("P08_CLOSE_MUST_NOT_GRANT_EXECUTION_READINESS")
    return {
        "NO_ACCIDENTAL_SUBMIT_PATH_UNDER_CURRENT_STATE": True,
        "NO_HIDDEN_LIVE_ENABLED_OR_ARMED_MUTATION": True,
        "NO_IMPLICIT_AUTHORIZATION_FROM_HISTORICAL_GO": True,
        "P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS": True,
        "NO_REQUIREMENT_TO_MODIFY_MASTER_V2_OR_DOUBLE_PLAY_CORE": True,
        "NO_SECOND_TRADING_AUTHORITY_INTRODUCED": True,
        "THIS_GO_FORBIDDEN_AS_FLATTEN_EXECUTE": True,
        "THIS_GO_FORBIDDEN_AS_CANARY_SUBMIT": True,
        "FLATTEN_DENY_REASONS": list(flatten_reasons),
        "SUBMIT_DENY_REASONS": list(submit.reasons),
        "STANDING_LIVE_ENABLED": LIVE_ENABLED,
        "STANDING_LIVE_ARMED": LIVE_ARMED,
        "STANDING_LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "STANDING_SUBMIT_UNLOCKED": SUBMIT_UNLOCKED,
        "CORE_LOGIC_CHANGE": CORE_LOGIC_CHANGE,
    }
