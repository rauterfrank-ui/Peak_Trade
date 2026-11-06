"""Fail-closed productive §11.12.8 Testnet campaign RUN surface (no campaign start).

Implements the run surface after the execution package. This OWNER_GO is
IMPLEMENTATION_ONLY: RUN_AUTHORIZED remains false and no campaign/network/order
side effects may occur. A later separate Owner-GO is required to activate a run.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_execution_v1.constants_v1 import (
    MODE_GOVERNED_EXECUTION_GATE as EXEC_MODE_GOVERNED_EXECUTION_GATE,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_execution_v1.execution_v1 import (
    Productive11128CampaignExecutionError,
    build_productive_campaign_execution_record_v1,
    prove_productive_testnet_campaign_execution_v1,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMED,
    CAMPAIGN_SIDE_EFFECTS_AUTHORIZED,
    CANONICAL_ALLOWED_ORDER_TYPES,
    CANONICAL_EMERGENCY_COMMANDS,
    CANONICAL_INSTRUMENT_SCOPE,
    CANONICAL_POSITION_COUNT_LIMIT,
    CANONICAL_RUNTIME_MODE,
    CANONICAL_VENUE,
    CAPABILITY_11_13_STARTED,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    CONTRACT_VERSION,
    CORE_LOGIC_CHANGE,
    EXCHANGE_ORDER_SUBMIT_REACHABLE,
    EXECUTION_PREDECESSOR_PRESERVED,
    FUTURE_RUN_GO_CONSUMED,
    FUTURE_RUN_GO_CONSUMPTION_ALLOWED,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    LIVE_ORDER_EFFECT,
    MODE_GOVERNED_RUN_GATE,
    MODE_PROVE_RUN_ONLY,
    MUTATING_EXCHANGE_CALLS,
    NETWORK_EFFECT,
    NETWORK_SESSION_STARTED,
    NETWORK_WRITE_PERFORMED,
    NETWORK_WRITES_AUTHORIZED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    ORDER_PATH_STARTED,
    ORDER_SEND_DISABLED,
    ORDER_SUBMIT_PERFORMED,
    ORDERS_AUTHORIZED,
    OWNER,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    PRODUCTIVE_TESTNET_CAMPAIGN_ACTIVATED,
    PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED,
    PRODUCTIVE_TESTNET_CAMPAIGN_RUN_IMPLEMENTED,
    PRODUCTIVE_TESTNET_CAMPAIGN_RUN_SURFACE_ABSENT,
    PRODUCTIVE_TESTNET_CAMPAIGN_RUN_SURFACE_PRESENT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    REQUIRED_PRECONDITIONS,
    RUN_AUTHORIZED,
    SECTION_11_13_STARTED,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ORDER_SUBMIT_PERFORMED,
)


class Productive11128CampaignRunError(RuntimeError):
    """Fail-closed productive §11.12.8 campaign run-surface violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class Productive11128CampaignRunRecordV1:
    """Run-gate record. Never starts campaign / network / orders."""

    mode: str
    execution_predecessor_bound: bool
    execution_may_start: bool
    run_may_start: bool
    campaign_started: bool
    run_authorized_constant: bool
    side_effects_authorized: bool
    network_effect: str
    order_effect: str
    live_order_effect: str
    missing_preconditions: tuple[str, ...]
    run_binding_digest: str
    execution_binding_digest: str
    path_binding_digest: str
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    path_class: str = PATH_CLASS


def bind_execution_predecessor_v1() -> dict[str, Any]:
    proof = prove_productive_testnet_campaign_execution_v1()
    if proof.get("ok") is not True:
        raise Productive11128CampaignRunError("EXECUTION_PREDECESSOR_PROOF_NOT_OK")
    if proof.get("PRODUCTIVE_TESTNET_CAMPAIGN_STARTED") is not False:
        raise Productive11128CampaignRunError("EXECUTION_CAMPAIGN_STARTED_DRIFT")
    if proof.get("RUN_AUTHORIZED") is not False:
        raise Productive11128CampaignRunError("EXECUTION_RUN_AUTHORIZED_DRIFT")
    if proof.get("NETWORK_EFFECT") != "NONE" or proof.get("ORDER_EFFECT") != "NONE":
        raise Productive11128CampaignRunError("EXECUTION_EFFECT_DRIFT")
    if proof.get("LIVE_ORDER_EFFECT") != "NONE":
        raise Productive11128CampaignRunError("EXECUTION_LIVE_EFFECT_DRIFT")
    return {
        "execution_predecessor_bound": True,
        "execution_capability_id": PREDECESSOR_CAPABILITY_ID,
        "execution_proof_ok": True,
        "execution_campaign_started": False,
        "execution_run_authorized": False,
    }


def evaluate_run_preconditions_v1(
    *,
    execution_predecessor_bound: bool,
    execution_may_start: bool,
    runtime_mode: str,
    live_endpoint_configured: bool,
    credential_scope: str,
    owner_go_bound: bool,
    confirm_token_digest_bound: bool,
    campaign_enabled: bool,
    campaign_armed: bool,
    kill_switch_operational: bool,
    emergency_control_operational: bool,
    instrument_scope: tuple[str, ...] | list[str],
    allowed_order_types: tuple[str, ...] | list[str],
    position_count_limit: int,
    run_authorized_ephemeral: bool,
    campaign_started: bool = False,
    future_run_go_consumed: bool = False,
    cap_11_13_started: bool = False,
    network_effect: str = NETWORK_EFFECT,
    order_effect: str = ORDER_EFFECT,
) -> dict[str, Any]:
    missing: list[str] = []
    scope = tuple(str(x) for x in instrument_scope)
    order_types = tuple(str(x) for x in allowed_order_types)

    if not execution_predecessor_bound:
        missing.append("execution_predecessor_bound")
    if not execution_may_start:
        missing.append("execution_gate_admissible")
    if runtime_mode != CANONICAL_RUNTIME_MODE or live_endpoint_configured:
        missing.append("testnet_only_scope")
    if live_endpoint_configured or LIVE_AUTHORIZED or LIVE_EXECUTION_REACHABLE:
        missing.append("live_path_blocked")
    if credential_scope != "TESTNET":
        missing.append("credential_scope_testnet")
    if not owner_go_bound:
        missing.append("owner_authorization_bound")
    if not confirm_token_digest_bound:
        missing.append("confirm_token_digest_bound")
    if not campaign_enabled:
        missing.append("campaign_enabled")
    if not campaign_armed:
        missing.append("campaign_armed")
    if not kill_switch_operational:
        missing.append("kill_switch_operational")
    if not emergency_control_operational:
        missing.append("emergency_control_operational")
    if (
        set(scope) != set(CANONICAL_INSTRUMENT_SCOPE)
        or set(order_types) != set(CANONICAL_ALLOWED_ORDER_TYPES)
        or position_count_limit != CANONICAL_POSITION_COUNT_LIMIT
    ):
        missing.append("risk_scope_within_authority")
    if not run_authorized_ephemeral:
        missing.append("run_authorized_ephemeral")
    if CAMPAIGN_SIDE_EFFECTS_AUTHORIZED or RUN_AUTHORIZED:
        missing.append("side_effects_unauthorized_permanent")
    if (
        campaign_started
        or PRODUCTIVE_TESTNET_CAMPAIGN_STARTED
        or PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED
        or PRODUCTIVE_TESTNET_CAMPAIGN_ACTIVATED
    ):
        missing.append("campaign_not_started")
    if (
        future_run_go_consumed
        or FUTURE_RUN_GO_CONSUMED
        or FUTURE_RUN_GO_CONSUMPTION_ALLOWED
        or AUTHORIZATION_CONSUMED
    ):
        missing.append("future_run_go_not_consumed")
    if cap_11_13_started or CAPABILITY_11_13_STARTED or SECTION_11_13_STARTED:
        missing.append("cap_11_13_not_started")
    if network_effect != "NONE" or NETWORK_EFFECT != "NONE":
        missing.append("network_effect_none")
    if order_effect != "NONE" or ORDER_EFFECT != "NONE" or LIVE_ORDER_EFFECT != "NONE":
        missing.append("order_effect_none")

    ordered = tuple(name for name in REQUIRED_PRECONDITIONS if name in missing)
    for name in missing:
        if name not in ordered:
            ordered = (*ordered, name)
    return {"admissible": len(ordered) == 0, "missing_preconditions": list(ordered)}


def build_productive_campaign_run_record_v1(
    *,
    mode: str,
    runtime_mode: str = CANONICAL_RUNTIME_MODE,
    venue: str = CANONICAL_VENUE,
    account_identity: str = "acct-uid-demo",
    instrument_scope: tuple[str, ...] | list[str] = CANONICAL_INSTRUMENT_SCOPE,
    allowed_order_types: tuple[str, ...] | list[str] = CANONICAL_ALLOWED_ORDER_TYPES,
    position_count_limit: int = CANONICAL_POSITION_COUNT_LIMIT,
    repository_sha: str,
    config_digest: str,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
    expected_account_identity: str | None = None,
    expected_venue: str | None = None,
    credential_scope: str = "TESTNET",
    secret_reference: str = "secretref://vault/testnet/okx-demo",
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    owner_go_bound: bool = True,
    campaign_enabled: bool = True,
    campaign_armed: bool = True,
    run_authorized_ephemeral: bool = False,
    live_endpoint_configured: bool = False,
    campaign_started: bool = False,
    future_run_go_consumed: bool = False,
    cap_11_13_started: bool = False,
    kill_switch_binding_status: str | None = None,
    emergency_commands: tuple[str, ...] | list[str] | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Productive11128CampaignRunRecordV1:
    """Build run-gate record. Never starts the campaign."""
    exec_bind = bind_execution_predecessor_v1()
    expected_sha = expected_repository_sha or repository_sha
    expected_cfg = expected_config_digest or config_digest
    expected_acct = expected_account_identity or account_identity
    expected_ven = expected_venue or venue

    exec_kwargs: dict[str, Any] = {
        "mode": EXEC_MODE_GOVERNED_EXECUTION_GATE,
        "runtime_mode": runtime_mode,
        "venue": venue,
        "account_identity": account_identity,
        "instrument_scope": instrument_scope,
        "allowed_order_types": allowed_order_types,
        "position_count_limit": position_count_limit,
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "expected_repository_sha": expected_sha,
        "expected_config_digest": expected_cfg,
        "expected_account_identity": expected_acct,
        "expected_venue": expected_ven,
        "credential_scope": credential_scope,
        "secret_reference": secret_reference,
        "confirm_token_digest": confirm_token_digest,
        "expected_confirm_token_digest": expected_confirm_token_digest or confirm_token_digest,
        "owner_go_bound": owner_go_bound,
        "campaign_enabled": campaign_enabled,
        "campaign_armed": campaign_armed,
        "run_authorized_ephemeral": True,
        "live_endpoint_configured": live_endpoint_configured,
        "campaign_started": campaign_started,
        "cap_11_13_started": cap_11_13_started,
        "argv": argv,
        "environ": environ,
    }
    if kill_switch_binding_status is not None:
        exec_kwargs["kill_switch_binding_status"] = kill_switch_binding_status
    if emergency_commands is not None:
        exec_kwargs["emergency_commands"] = emergency_commands

    try:
        exec_record = build_productive_campaign_execution_record_v1(**exec_kwargs)
    except Productive11128CampaignExecutionError as exc:
        raise Productive11128CampaignRunError(str(exc)) from exc

    exec_missing = set(exec_record.missing_preconditions)
    kill_ok = "kill_switch_operational" not in exec_missing and (
        kill_switch_binding_status is None or kill_switch_binding_status == "BOUND"
    )
    if emergency_commands is None:
        emergency_ok = "emergency_control_operational" not in exec_missing
    else:
        emergency_ok = set(str(x) for x in emergency_commands) == set(CANONICAL_EMERGENCY_COMMANDS)

    evaluation = evaluate_run_preconditions_v1(
        execution_predecessor_bound=bool(exec_bind.get("execution_predecessor_bound")),
        execution_may_start=bool(exec_record.execution_may_start),
        runtime_mode=runtime_mode,
        live_endpoint_configured=live_endpoint_configured,
        credential_scope=credential_scope,
        owner_go_bound=owner_go_bound,
        confirm_token_digest_bound=bool(exec_record.path_binding_digest),
        campaign_enabled=campaign_enabled,
        campaign_armed=campaign_armed,
        kill_switch_operational=kill_ok,
        emergency_control_operational=emergency_ok,
        instrument_scope=instrument_scope,
        allowed_order_types=allowed_order_types,
        position_count_limit=position_count_limit,
        run_authorized_ephemeral=run_authorized_ephemeral,
        campaign_started=campaign_started,
        future_run_go_consumed=future_run_go_consumed,
        cap_11_13_started=cap_11_13_started,
    )

    if mode == MODE_PROVE_RUN_ONLY:
        run_may_start = False
    elif mode == MODE_GOVERNED_RUN_GATE:
        # Structural may_start for a later activation GO; this capability never starts.
        run_may_start = bool(evaluation["admissible"]) and not RUN_AUTHORIZED
        if RUN_AUTHORIZED or CAMPAIGN_SIDE_EFFECTS_AUTHORIZED:
            run_may_start = False
    else:
        raise Productive11128CampaignRunError(f"UNKNOWN_RUN_MODE:{mode}")

    if PRODUCTIVE_TESTNET_CAMPAIGN_STARTED or NETWORK_SESSION_STARTED:
        raise Productive11128CampaignRunError("RUN_CONSTANT_STARTED_DRIFT")
    if AUTHORIZATION_CONSUMED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED or FUTURE_RUN_GO_CONSUMED:
        raise Productive11128CampaignRunError("RUN_CONSUMPTION_CONSTANT_DRIFT")

    digest_payload = {
        "capability_id": CAPABILITY_ID,
        "mode": mode,
        "execution_binding_digest": exec_record.execution_binding_digest,
        "path_binding_digest": exec_record.path_binding_digest,
        "run_may_start": run_may_start,
        "campaign_started": False,
        "run_authorized": RUN_AUTHORIZED,
        "network_effect": NETWORK_EFFECT,
        "order_effect": ORDER_EFFECT,
        "missing_preconditions": evaluation["missing_preconditions"],
    }
    run_digest = hashlib.sha256(_canonical_dumps(digest_payload).encode("utf-8")).hexdigest()

    return Productive11128CampaignRunRecordV1(
        mode=mode,
        execution_predecessor_bound=True,
        execution_may_start=bool(exec_record.execution_may_start),
        run_may_start=run_may_start,
        campaign_started=False,
        run_authorized_constant=RUN_AUTHORIZED,
        side_effects_authorized=CAMPAIGN_SIDE_EFFECTS_AUTHORIZED,
        network_effect=NETWORK_EFFECT,
        order_effect=ORDER_EFFECT,
        live_order_effect=LIVE_ORDER_EFFECT,
        missing_preconditions=tuple(evaluation["missing_preconditions"]),
        run_binding_digest=run_digest,
        execution_binding_digest=exec_record.execution_binding_digest,
        path_binding_digest=exec_record.path_binding_digest,
    )


def refuse_campaign_start_v1(*, campaign_id: str = "campaign-demo") -> None:
    raise Productive11128CampaignRunError(
        f"PRODUCTIVE_TESTNET_CAMPAIGN_START_FORBIDDEN_IN_RUN_IMPLEMENTATION:{campaign_id}"
    )


def refuse_network_session_v1(*, session_id: str = "session-demo") -> None:
    raise Productive11128CampaignRunError(
        f"NETWORK_SESSION_FORBIDDEN_IN_RUN_IMPLEMENTATION:{session_id}"
    )


def refuse_order_submit_v1(*, order_id: str = "order-demo") -> None:
    raise Productive11128CampaignRunError(
        f"ORDER_SUBMIT_FORBIDDEN_IN_RUN_IMPLEMENTATION:{order_id}"
    )


def refuse_live_path_v1(*, endpoint: str = "live") -> None:
    raise Productive11128CampaignRunError(f"LIVE_PATH_FORBIDDEN_IN_RUN_IMPLEMENTATION:{endpoint}")


def refuse_cap_11_13_v1(*, path_name: str = "live_activation") -> None:
    raise Productive11128CampaignRunError(
        f"CAPABILITY_11_13_FORBIDDEN_IN_RUN_IMPLEMENTATION:{path_name}"
    )


def refuse_future_run_go_consume_v1(*, go_id: str = "future-run-go") -> None:
    raise Productive11128CampaignRunError(
        f"FUTURE_RUN_GO_CONSUMPTION_FORBIDDEN_IN_RUN_IMPLEMENTATION:{go_id}"
    )


def execute_productive_testnet_campaign_run_v1(**kwargs: Any) -> None:
    """Hard refuse any campaign start inside this implementation capability."""
    _ = kwargs
    raise Productive11128CampaignRunError(
        "PRODUCTIVE_TESTNET_CAMPAIGN_RUN_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY"
    )


def prove_productive_testnet_campaign_run_v1() -> dict[str, Any]:
    """Contract proof: run surface present; campaign never starts."""
    sha = "a" * 40
    cfg = "cfg-" + ("b" * 64)
    digest = "c" * 64
    common = {
        "repository_sha": sha,
        "config_digest": cfg,
        "confirm_token_digest": digest,
        "expected_confirm_token_digest": digest,
        "owner_go_bound": True,
        "campaign_enabled": True,
        "campaign_armed": True,
        "run_authorized_ephemeral": True,
    }

    prove_only = build_productive_campaign_run_record_v1(mode=MODE_PROVE_RUN_ONLY, **common)
    gate = build_productive_campaign_run_record_v1(mode=MODE_GOVERNED_RUN_GATE, **common)

    no_run_auth = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "run_authorized_ephemeral": False},
    )
    live = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "runtime_mode": "LIVE", "live_endpoint_configured": True},
    )
    bad_cred = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "credential_scope": "LIVE"},
    )
    disabled = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "campaign_enabled": False},
    )
    unarmed = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "campaign_armed": False},
    )
    no_owner = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "owner_go_bound": False},
    )
    kill_bad = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "kill_switch_binding_status": "UNBOUND"},
    )
    emergency_bad = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "emergency_commands": ("HALT_ONLY",)},
    )
    risk_bad = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "instrument_scope": ("ETH-USDT-SWAP",)},
    )
    future_go = build_productive_campaign_run_record_v1(
        mode=MODE_GOVERNED_RUN_GATE,
        **{**common, "future_run_go_consumed": True},
    )

    confirm_bad = False
    try:
        build_productive_campaign_run_record_v1(
            mode=MODE_GOVERNED_RUN_GATE,
            **{**common, "confirm_token_digest": "nope"},
        )
    except Productive11128CampaignRunError as exc:
        confirm_bad = "CONFIRM_TOKEN_DIGEST_INVALID" in str(exc)

    run_refused = False
    try:
        execute_productive_testnet_campaign_run_v1(owner_go=True)
    except Productive11128CampaignRunError as exc:
        run_refused = "RUN_FORBIDDEN_IN_THIS_IMPLEMENTATION" in str(exc)

    refuse_ok = True
    for fn, needle in (
        (refuse_campaign_start_v1, "CAMPAIGN_START_FORBIDDEN"),
        (refuse_network_session_v1, "NETWORK_SESSION_FORBIDDEN"),
        (refuse_order_submit_v1, "ORDER_SUBMIT_FORBIDDEN"),
        (refuse_live_path_v1, "LIVE_PATH_FORBIDDEN"),
        (refuse_cap_11_13_v1, "CAPABILITY_11_13_FORBIDDEN"),
        (refuse_future_run_go_consume_v1, "FUTURE_RUN_GO_CONSUMPTION_FORBIDDEN"),
    ):
        try:
            fn()
            refuse_ok = False
        except Productive11128CampaignRunError as exc:
            if needle not in str(exc):
                refuse_ok = False

    ok = all(
        [
            PRODUCTIVE_TESTNET_CAMPAIGN_RUN_IMPLEMENTED is True,
            PRODUCTIVE_TESTNET_CAMPAIGN_RUN_SURFACE_PRESENT is True,
            PRODUCTIVE_TESTNET_CAMPAIGN_RUN_SURFACE_ABSENT is False,
            EXECUTION_PREDECESSOR_PRESERVED is True,
            prove_only.run_may_start is False,
            prove_only.campaign_started is False,
            gate.run_may_start is True,
            gate.campaign_started is False,
            gate.network_effect == "NONE",
            gate.order_effect == "NONE",
            gate.live_order_effect == "NONE",
            gate.run_authorized_constant is False,
            "run_authorized_ephemeral" in no_run_auth.missing_preconditions,
            "testnet_only_scope" in live.missing_preconditions,
            "credential_scope_testnet" in bad_cred.missing_preconditions,
            "campaign_enabled" in disabled.missing_preconditions,
            "campaign_armed" in unarmed.missing_preconditions,
            "owner_authorization_bound" in no_owner.missing_preconditions,
            "kill_switch_operational" in kill_bad.missing_preconditions
            or "execution_gate_admissible" in kill_bad.missing_preconditions,
            "emergency_control_operational" in emergency_bad.missing_preconditions
            or "execution_gate_admissible" in emergency_bad.missing_preconditions,
            "risk_scope_within_authority" in risk_bad.missing_preconditions
            or "execution_gate_admissible" in risk_bad.missing_preconditions,
            "future_run_go_not_consumed" in future_go.missing_preconditions,
            confirm_bad,
            run_refused,
            refuse_ok,
            RUN_AUTHORIZED is False,
            CAMPAIGN_SIDE_EFFECTS_AUTHORIZED is False,
            ORDER_SEND_DISABLED is True,
            ORDERS_AUTHORIZED is False,
            NETWORK_WRITES_AUTHORIZED is False,
            NETWORK_WRITE_PERFORMED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            TESTNET_ORDER_SUBMIT_PERFORMED is False,
            PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False,
            SECTION_11_13_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            AUTHORIZATION_CONSUMED is False,
            CONFIRM_TOKEN_ISSUANCE_ALLOWED is False,
            CONFIRM_TOKEN_CONSUMPTION_ALLOWED is False,
            FUTURE_RUN_GO_CONSUMPTION_ALLOWED is False,
            FUTURE_RUN_GO_CONSUMED is False,
            TESTNET_AUTHORIZED is False,
            LIVE_AUTHORIZED is False,
            CORE_LOGIC_CHANGE is False,
            REFERENCE_ONLY is False,
            ACTIVATION_STATE == "not_activated",
            ORDER_PATH_STARTED is False,
            ORDER_SUBMIT_PERFORMED is False,
            MUTATING_EXCHANGE_CALLS is False,
            TESTNET_EXECUTION_REACHABLE is False,
            LIVE_EXECUTION_REACHABLE is False,
            REAL_EXECUTION_ADAPTER_CONSTRUCTED is False,
        ]
    )

    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "path_class": PATH_CLASS,
        "PRODUCTIVE_TESTNET_CAMPAIGN_RUN_IMPLEMENTED": True,
        "EXECUTION_PREDECESSOR_PRESERVED": True,
        "PRODUCTIVE_TESTNET_CAMPAIGN_RUN_SURFACE_PRESENT": True,
        "PRODUCTIVE_TESTNET_CAMPAIGN_RUN_SURFACE_ABSENT": False,
        "RUN_AUTHORIZED": False,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
        "PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED": False,
        "NETWORK_EFFECT": NETWORK_EFFECT,
        "ORDER_EFFECT": ORDER_EFFECT,
        "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
        "SECTION_11_13_STARTED": False,
        "prove_only_may_start": prove_only.run_may_start,
        "gate_may_start": gate.run_may_start,
        "gate_started": gate.campaign_started,
        "run_binding_digest": gate.run_binding_digest,
        "execution_binding_digest": gate.execution_binding_digest,
        "path_binding_digest": gate.path_binding_digest,
        "run_auth_blocked": "run_authorized_ephemeral" in no_run_auth.missing_preconditions,
        "live_blocked": "testnet_only_scope" in live.missing_preconditions,
        "credential_scope_blocked": "credential_scope_testnet" in bad_cred.missing_preconditions,
        "enabled_false_blocked": "campaign_enabled" in disabled.missing_preconditions,
        "armed_false_blocked": "campaign_armed" in unarmed.missing_preconditions,
        "owner_auth_blocked": "owner_authorization_bound" in no_owner.missing_preconditions,
        "kill_switch_blocked": "kill_switch_operational" in kill_bad.missing_preconditions
        or "execution_gate_admissible" in kill_bad.missing_preconditions,
        "emergency_control_blocked": "emergency_control_operational"
        in emergency_bad.missing_preconditions
        or "execution_gate_admissible" in emergency_bad.missing_preconditions,
        "risk_scope_blocked": "risk_scope_within_authority" in risk_bad.missing_preconditions
        or "execution_gate_admissible" in risk_bad.missing_preconditions,
        "future_run_go_blocked": "future_run_go_not_consumed" in future_go.missing_preconditions,
        "confirm_invalid_blocked": confirm_bad,
        "run_refused": run_refused,
        "refuse_ok": refuse_ok,
    }
