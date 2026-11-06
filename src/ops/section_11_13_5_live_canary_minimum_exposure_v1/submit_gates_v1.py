"""Fail-closed submit gates for §11.13.5 LIVE_CANARY_MINIMUM_EXPOSURE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    CONFIRM_TOKEN_CANONICAL,
    FORBIDDEN_ENVIRONMENTS,
    MINIMUM_RATIFIED_NOTIONAL_ONLY,
    ORDER_COUNT_LIMIT,
    OWNER_GO_AUTHORING,
    OWNER_GO_EXECUTE,
    POSITION_COUNT_LIMIT,
    REQUIRED_ENVIRONMENT,
    REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.governance_state_matrix_v1 import (
    MERGE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT,
    NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT,
    PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BINDING,
    refuse_prior_consumed_canary_go_reuse_v1,
)


class LiveCanarySubmitGateError(RuntimeError):
    """Fail-closed canary submit-gate violation."""


@dataclass(frozen=True)
class CanarySubmitGateEvaluationV1:
    submit_allowed: bool
    reasons: tuple[str, ...]
    gates: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "SUBMIT_ALLOWED": self.submit_allowed,
            "REASONS": list(self.reasons),
            "gates": self.gates,
        }


def evaluate_canary_submit_gates_v1(
    *,
    owner_go: str | None,
    owner_go_consumed: bool,
    authorization_scope: str | None,
    bound_origin_main_sha: str | None,
    expected_origin_main_sha: str | None,
    live_canary_authorized: bool,
    live_enabled: bool,
    live_armed: bool,
    confirm_token: str | None,
    blocks_new_entry: bool,
    unresolved_economic_divergence: bool,
    live_reconciliation_proven: bool,
    permission_attestation: Mapping[str, Any] | None,
    environment: str | None,
    fixture_or_demo_or_testnet: bool,
    max_notional: str | None,
    min_executable_notional: str | None,
    order_count: int,
    position_count: int,
    exposure_above_minimum_bound: bool,
    live_canary_cybersecurity_gate: str | None = None,
    rest_host: str | None = None,
    secretref_uri: str | None = None,
    open_order_count: int = 0,
    open_position_count: int = 0,
    require_notional_bounds: bool = True,
    recovery_state_clear: bool = True,
) -> CanarySubmitGateEvaluationV1:
    reasons: list[str] = []
    gates: dict[str, Any] = {}

    go = str(owner_go or "").strip()
    gates["owner_go_present"] = bool(go)
    if not go:
        reasons.append("NO_OWNER_GO")
    elif go == OWNER_GO_AUTHORING:
        reasons.append("AUTHORING_GO_CANNOT_AUTHORIZE_SUBMIT")
    elif any(marker in go.upper() for marker in MERGE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT):
        reasons.append("MERGE_GO_CANNOT_AUTHORIZE_SUBMIT")
    elif any(marker in go for marker in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT):
        reasons.append("REEVALUATION_OR_PREPARATION_GO_CANNOT_AUTHORIZE_SUBMIT")
    elif go == PRIOR_OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_BINDING or go.endswith(
        "@0f21b53e001e94085941c774a43a27562a1743fe"
    ):
        try:
            refuse_prior_consumed_canary_go_reuse_v1(owner_go_binding=go)
        except RuntimeError:
            reasons.append("PRIOR_CONSUMED_CANARY_GO_NOT_REUSABLE")
    elif go != OWNER_GO_EXECUTE:
        reasons.append(f"OWNER_GO_MISMATCH:{go}")
    gates["owner_go_is_execute_token"] = go == OWNER_GO_EXECUTE

    gates["owner_go_consumed"] = bool(owner_go_consumed)
    if owner_go_consumed:
        reasons.append("OWNER_GO_CONSUMED")

    scope = str(authorization_scope or "").strip()
    gates["authorization_scope"] = scope
    if scope != AUTHORIZATION_SCOPE:
        reasons.append(f"AUTHORIZATION_SCOPE_MISMATCH:{scope or '<empty>'}")

    gates["live_canary_authorized"] = bool(live_canary_authorized)
    if not live_canary_authorized:
        reasons.append("LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_FALSE")

    sha = str(bound_origin_main_sha or "").strip().lower()
    expected = str(expected_origin_main_sha or "").strip().lower()
    gates["sha_match"] = bool(sha) and sha == expected
    if not sha or not expected or sha != expected:
        reasons.append("ORIGIN_MAIN_SHA_BINDING_MISMATCH")

    gates["live_enabled"] = bool(live_enabled)
    if not live_enabled:
        reasons.append("LIVE_ENABLED_FALSE")
    gates["live_armed"] = bool(live_armed)
    if not live_armed:
        reasons.append("LIVE_ARMED_FALSE")

    provided_confirm = str(confirm_token or "")
    gates["confirm_token_match"] = provided_confirm == CONFIRM_TOKEN_CANONICAL
    if provided_confirm != CONFIRM_TOKEN_CANONICAL:
        reasons.append("CONFIRM_TOKEN_MISMATCH")

    gates["blocks_new_entry"] = bool(blocks_new_entry)
    if blocks_new_entry:
        reasons.append("BLOCKS_NEW_ENTRY_TRUE")

    gates["unresolved_economic_divergence"] = bool(unresolved_economic_divergence)
    if unresolved_economic_divergence:
        reasons.append("UNRESOLVED_ECONOMIC_DIVERGENCE")

    gates["live_reconciliation_proven"] = bool(live_reconciliation_proven)
    if not live_reconciliation_proven:
        reasons.append("LIVE_RECONCILIATION_PROVEN_FALSE")

    perm = dict(permission_attestation or {})
    trade_ok = (
        perm.get("READ") is True and perm.get("TRADE") is True and perm.get("WITHDRAW") is False
    )
    gates["permission_attestation"] = {
        "READ": perm.get("READ"),
        "TRADE": perm.get("TRADE"),
        "WITHDRAW": perm.get("WITHDRAW"),
        "required": dict(REQUIRED_PERMISSION_ATTESTATION_FOR_SUBMIT),
        "ok": trade_ok,
    }
    if not trade_ok:
        reasons.append("TRADE_ATTESTATION_FALSE_OR_INCOMPLETE")

    env = str(environment or "").strip().upper()
    gates["environment"] = env
    if env != REQUIRED_ENVIRONMENT:
        reasons.append(f"ENVIRONMENT_NOT_LIVE:{env or '<empty>'}")
    if env in FORBIDDEN_ENVIRONMENTS or fixture_or_demo_or_testnet:
        reasons.append("FIXTURE_TESTNET_DEMO_BINDING_FORBIDDEN")

    gates["order_count"] = int(order_count)
    gates["position_count"] = int(position_count)
    if int(order_count) > ORDER_COUNT_LIMIT or int(order_count) < 1:
        reasons.append(f"ORDER_COUNT_LIMIT_VIOLATION:{order_count}")
    if int(position_count) > POSITION_COUNT_LIMIT:
        reasons.append(f"POSITION_COUNT_LIMIT_VIOLATION:{position_count}")

    gates["minimum_ratified_notional_only"] = MINIMUM_RATIFIED_NOTIONAL_ONLY
    gates["max_notional"] = max_notional
    gates["min_executable_notional"] = min_executable_notional
    gates["exposure_above_minimum_bound"] = bool(exposure_above_minimum_bound)
    gates["require_notional_bounds"] = bool(require_notional_bounds)
    if require_notional_bounds:
        if not max_notional or not min_executable_notional:
            reasons.append("NOTIONAL_BOUNDS_UNRESOLVED")
        elif str(max_notional) != str(min_executable_notional):
            reasons.append("MAX_NOTIONAL_MUST_EQUAL_MIN_EXECUTABLE_NOTIONAL")
    if exposure_above_minimum_bound:
        reasons.append("EXPOSURE_ABOVE_CANONICAL_MINIMUM_BOUND")

    cyber = str(live_canary_cybersecurity_gate or "").strip().upper()
    gates["live_canary_cybersecurity_gate"] = cyber or None
    if cyber != "PASS":
        reasons.append("LIVE_CANARY_CYBERSECURITY_GATE_NOT_PASS")

    host = str(rest_host or "").strip().lower()
    gates["rest_host"] = host or None
    if host and host != REUSED_BINDING_REST_HOST:
        reasons.append("REST_HOST_NOT_PRODUCTION_EEA")

    ref = str(secretref_uri or "").strip()
    gates["secretref_uri_present"] = bool(ref)
    if ref and ref != REQUIRED_SECRETREF_URI:
        reasons.append("SECRETREF_URI_BINDING_MISMATCH")

    gates["open_order_count"] = int(open_order_count)
    gates["open_position_count"] = int(open_position_count)
    gates["recovery_state_clear"] = bool(recovery_state_clear)
    if int(open_order_count) > 0:
        reasons.append("OPEN_ORDER_PRESENT")
    if int(open_position_count) > 0:
        reasons.append("OPEN_POSITION_PRESENT")
    if not recovery_state_clear:
        reasons.append("RECOVERY_STATE_UNRESOLVED")

    submit_allowed = len(reasons) == 0
    return CanarySubmitGateEvaluationV1(
        submit_allowed=submit_allowed,
        reasons=tuple(reasons),
        gates=gates,
    )


def refuse_submit_unless_gates_pass_v1(evaluation: CanarySubmitGateEvaluationV1) -> None:
    if evaluation.submit_allowed:
        return
    joined = ",".join(evaluation.reasons) or "UNKNOWN"
    raise LiveCanarySubmitGateError(f"CANARY_SUBMIT_HARD_BLOCKED:{joined}")
