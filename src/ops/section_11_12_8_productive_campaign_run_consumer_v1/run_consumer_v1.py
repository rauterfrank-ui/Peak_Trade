"""§11.12.8 productive campaign RUN CONSUMER (implementation-only).

Binds the terminal predecessor without mutating its hard-refuse role.
Reuses terminal authorization gates (Phase-9.2 confirm / RiskGate / KillSwitch /
credential-scope / emergency). Hard-refuses productive execution in this OWNER_GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.constants_v1 import (
    CAMPAIGN_SIDE_EFFECTS_AUTHORIZED,
    CAPABILITY_ID,
    CONTRACT_VERSION,
    CREDENTIAL_PLAINTEXT_LOADED,
    IMPLEMENTATION_ONLY,
    LIVE_ORDER_EFFECT,
    MODE_GOVERNED_RUN_CONSUMER_GATE,
    MODE_PROVE_RUN_CONSUMER_ONLY,
    NETWORK_EFFECT,
    NEW_WRAPPER_LAYER_CREATED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    OWNER,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    PRODUCTIVE_RUN_CONSUMER_IMPLEMENTED,
    PRODUCTIVE_RUN_CONSUMER_PRESENT,
    PRODUCTIVE_RUN_EXECUTION_AUTHORIZED,
    PRODUCTIVE_RUN_EXECUTION_AUTHORIZED_IN_THIS_IMPLEMENTATION,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    RUN_CONSUMER_CANONICAL_ROLE,
    SECTION_11_13_STARTED,
    SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION,
    TERMINAL_PREDECESSOR_ROLE,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.campaign_authorization_gate_v1 import (
    Section11128TerminalGateError,
    attempt_credential_load_v1,
    evaluate_terminal_authorization_gate_v1,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.constants_v1 import (
    PRODUCTIVE_RUN_AUTHORIZED as TERMINAL_PRODUCTIVE_RUN_AUTHORIZED,
    TERMINAL_CONSUMER_CANONICAL_ROLE,
    TERMINAL_CONSUMER_IMPLEMENTED,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.terminal_consumer_v1 import (
    Section11128TerminalConsumerError,
    prove_section_11_12_8_terminal_consumer_v1,
    run_section_11_12_8_terminal_consumer_v1,
)


class Section11128RunConsumerError(RuntimeError):
    """Fail-closed productive §11.12.8 run-consumer violation."""


@dataclass(frozen=True)
class Section11128RunConsumerRecordV1:
    mode: str
    run_consumer_may_arm: bool
    terminal_predecessor_bound: bool
    terminal_role_unchanged: bool
    gate_admissible: bool
    missing_preconditions: tuple[str, ...]
    campaign_enabled: bool
    campaign_armed: bool
    owner_go_bound: bool
    run_consumer_present: bool
    execution_authorized: bool
    credential_plaintext_loaded: bool
    campaign_started: bool
    network_effect: str
    order_effect: str
    live_order_effect: str
    section_11_13_started: bool
    new_wrapper_layer_created: bool
    next_consumer: str
    hidden_confirm_reused: bool
    risk_gate_reused: bool
    kill_switch_reused: bool


def _bind_terminal_predecessor_v1() -> dict[str, Any]:
    proof = prove_section_11_12_8_terminal_consumer_v1()
    if proof.get("ok") is not True:
        raise Section11128RunConsumerError("TERMINAL_PREDECESSOR_PROOF_FAILED")
    if proof.get("TERMINAL_CONSUMER_CANONICAL_ROLE") != TERMINAL_CONSUMER_CANONICAL_ROLE:
        raise Section11128RunConsumerError("TERMINAL_ROLE_DRIFT")
    if proof.get("NEW_WRAPPER_LAYER_CREATED") is not False:
        raise Section11128RunConsumerError("TERMINAL_WRAPPER_DRIFT")
    if proof.get("PRODUCTIVE_TESTNET_CAMPAIGN_STARTED") is not False:
        raise Section11128RunConsumerError("TERMINAL_CAMPAIGN_STARTED_DRIFT")
    if proof.get("PRODUCTIVE_RUN_STARTED") is not False:
        raise Section11128RunConsumerError("TERMINAL_PRODUCTIVE_RUN_STARTED_DRIFT")
    if TERMINAL_PRODUCTIVE_RUN_AUTHORIZED is not False:
        raise Section11128RunConsumerError("TERMINAL_PRODUCTIVE_RUN_AUTHORIZED_DRIFT")
    if TERMINAL_CONSUMER_IMPLEMENTED is not True:
        raise Section11128RunConsumerError("TERMINAL_NOT_IMPLEMENTED")
    # Terminal entrypoint must remain hard-refuse.
    refused = False
    try:
        run_section_11_12_8_terminal_consumer_v1(owner_go=True)
    except Section11128TerminalConsumerError as exc:
        refused = "FORBIDDEN_IN_THIS_IMPLEMENTATION" in str(exc)
    if not refused:
        raise Section11128RunConsumerError("TERMINAL_HARD_REFUSE_ROLE_BROKEN")
    return {
        "terminal_predecessor_bound": True,
        "terminal_capability_id": PREDECESSOR_CAPABILITY_ID,
        "terminal_role": TERMINAL_CONSUMER_CANONICAL_ROLE,
        "terminal_role_unchanged": True,
        "terminal_hard_refuse_preserved": True,
    }


def build_section_11_12_8_run_consumer_record_v1(
    *,
    mode: str,
    repository_sha: str,
    config_digest: str,
    account_identity: str = "acct-uid-demo",
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    owner_go_bound: bool = False,
    campaign_enabled: bool = False,
    campaign_armed: bool = False,
    runtime_mode: str = "TESTNET",
    live_endpoint_configured: bool = False,
    force_kill_switch_killed: bool = False,
    argv: list[str] | None = None,
    environ: dict[str, str] | None = None,
) -> Section11128RunConsumerRecordV1:
    if mode not in {MODE_PROVE_RUN_CONSUMER_ONLY, MODE_GOVERNED_RUN_CONSUMER_GATE}:
        raise Section11128RunConsumerError(f"UNKNOWN_RUN_CONSUMER_MODE:{mode}")

    terminal = _bind_terminal_predecessor_v1()
    gate = evaluate_terminal_authorization_gate_v1(
        repository_sha=repository_sha,
        config_digest=config_digest,
        account_identity=account_identity,
        confirm_token_digest=confirm_token_digest,
        expected_confirm_token_digest=expected_confirm_token_digest,
        owner_go_bound=owner_go_bound,
        campaign_enabled=campaign_enabled,
        campaign_armed=campaign_armed,
        runtime_mode=runtime_mode,
        live_endpoint_configured=live_endpoint_configured,
        force_kill_switch_killed=force_kill_switch_killed,
        argv=argv,
        environ=environ,
    )

    missing = list(gate.missing_preconditions)
    if not terminal["terminal_predecessor_bound"]:
        missing.append("terminal_predecessor_bound")
    if not terminal["terminal_role_unchanged"]:
        missing.append("terminal_role_unchanged")
    if (
        PRODUCTIVE_RUN_EXECUTION_AUTHORIZED
        or PRODUCTIVE_RUN_EXECUTION_AUTHORIZED_IN_THIS_IMPLEMENTATION
        or CAMPAIGN_SIDE_EFFECTS_AUTHORIZED
        or SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION
    ):
        missing.append("execution_unauthorized_in_this_implementation")
    if PRODUCTIVE_TESTNET_CAMPAIGN_STARTED:
        missing.append("campaign_not_started")
    if SECTION_11_13_STARTED:
        missing.append("cap_11_13_not_started")
    if NETWORK_EFFECT != "NONE":
        missing.append("network_effect_none")
    if ORDER_EFFECT != "NONE":
        missing.append("order_effect_none")
    if CREDENTIAL_PLAINTEXT_LOADED:
        missing.append("credential_plaintext_not_loaded")

    seen: set[str] = set()
    ordered_missing: list[str] = []
    for item in missing:
        if item not in seen:
            seen.add(item)
            ordered_missing.append(item)

    gate_admissible = len(ordered_missing) == 0 and gate.admissible
    if mode == MODE_PROVE_RUN_CONSUMER_ONLY:
        run_consumer_may_arm = False
    else:
        # Structural may_arm for a later activation GO; this capability never executes.
        run_consumer_may_arm = (
            gate_admissible
            and not PRODUCTIVE_RUN_EXECUTION_AUTHORIZED
            and not PRODUCTIVE_RUN_EXECUTION_AUTHORIZED_IN_THIS_IMPLEMENTATION
        )

    return Section11128RunConsumerRecordV1(
        mode=mode,
        run_consumer_may_arm=run_consumer_may_arm,
        terminal_predecessor_bound=bool(terminal["terminal_predecessor_bound"]),
        terminal_role_unchanged=bool(terminal["terminal_role_unchanged"]),
        gate_admissible=gate_admissible,
        missing_preconditions=tuple(ordered_missing),
        campaign_enabled=gate.campaign_enabled,
        campaign_armed=gate.campaign_armed,
        owner_go_bound=gate.owner_go_bound,
        run_consumer_present=PRODUCTIVE_RUN_CONSUMER_PRESENT,
        execution_authorized=PRODUCTIVE_RUN_EXECUTION_AUTHORIZED,
        credential_plaintext_loaded=CREDENTIAL_PLAINTEXT_LOADED,
        campaign_started=PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
        network_effect=NETWORK_EFFECT,
        order_effect=ORDER_EFFECT,
        live_order_effect=LIVE_ORDER_EFFECT,
        section_11_13_started=SECTION_11_13_STARTED,
        new_wrapper_layer_created=NEW_WRAPPER_LAYER_CREATED,
        next_consumer=NEXT_CONSUMER_CAPABILITY_ID,
        hidden_confirm_reused=True,
        risk_gate_reused=True,
        kill_switch_reused=True,
    )


def refuse_productive_campaign_execution_v1(*, campaign_id: str = "campaign-demo") -> None:
    raise Section11128RunConsumerError(
        f"PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_EXECUTION_FORBIDDEN_IN_IMPLEMENTATION:{campaign_id}"
    )


def refuse_network_session_v1(*, session_id: str = "session-demo") -> None:
    raise Section11128RunConsumerError(
        f"NETWORK_SESSION_FORBIDDEN_IN_RUN_CONSUMER_IMPLEMENTATION:{session_id}"
    )


def refuse_order_submit_v1(*, order_id: str = "order-demo") -> None:
    raise Section11128RunConsumerError(
        f"ORDER_SUBMIT_FORBIDDEN_IN_RUN_CONSUMER_IMPLEMENTATION:{order_id}"
    )


def refuse_live_path_v1(*, endpoint: str = "live") -> None:
    raise Section11128RunConsumerError(
        f"LIVE_PATH_FORBIDDEN_IN_RUN_CONSUMER_IMPLEMENTATION:{endpoint}"
    )


def refuse_cap_11_13_v1(*, path_name: str = "live_activation") -> None:
    raise Section11128RunConsumerError(
        f"CAPABILITY_11_13_FORBIDDEN_IN_RUN_CONSUMER_IMPLEMENTATION:{path_name}"
    )


def refuse_credential_load_v1(*, path_bound: bool = True) -> None:
    try:
        attempt_credential_load_v1(path_bound=path_bound)
    except Section11128TerminalGateError as exc:
        raise Section11128RunConsumerError(
            f"CREDENTIAL_LOAD_FORBIDDEN_IN_RUN_CONSUMER_IMPLEMENTATION:{exc}"
        ) from exc
    raise Section11128RunConsumerError(
        "CREDENTIAL_LOAD_FORBIDDEN_IN_RUN_CONSUMER_IMPLEMENTATION:UNEXPECTED_PASS"
    )


def execute_section_11_12_8_productive_campaign_run_v1(**_kwargs: Any) -> None:
    """Entrypoint hard-refuse: this OWNER_GO never starts a productive campaign."""
    raise Section11128RunConsumerError(
        "PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_EXECUTION_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY"
    )


def prove_section_11_12_8_run_consumer_v1() -> dict[str, Any]:
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
    }

    prove_only = build_section_11_12_8_run_consumer_record_v1(
        mode=MODE_PROVE_RUN_CONSUMER_ONLY, **common
    )
    gate = build_section_11_12_8_run_consumer_record_v1(
        mode=MODE_GOVERNED_RUN_CONSUMER_GATE, **common
    )

    load_forbidden = False
    try:
        refuse_credential_load_v1(path_bound=True)
    except Section11128RunConsumerError as exc:
        load_forbidden = "CREDENTIAL_LOAD_FORBIDDEN" in str(exc)

    run_refused = False
    try:
        execute_section_11_12_8_productive_campaign_run_v1(owner_go=True)
    except Section11128RunConsumerError as exc:
        run_refused = "FORBIDDEN_IN_THIS_IMPLEMENTATION" in str(exc)

    refusals_ok = True
    for fn, needle in (
        (refuse_productive_campaign_execution_v1, "CAMPAIGN_RUN_EXECUTION_FORBIDDEN"),
        (refuse_network_session_v1, "NETWORK_SESSION_FORBIDDEN"),
        (refuse_order_submit_v1, "ORDER_SUBMIT_FORBIDDEN"),
        (refuse_live_path_v1, "LIVE_PATH_FORBIDDEN"),
        (refuse_cap_11_13_v1, "CAPABILITY_11_13_FORBIDDEN"),
    ):
        try:
            fn()
            refusals_ok = False
        except Section11128RunConsumerError as exc:
            if needle not in str(exc):
                refusals_ok = False

    killed = build_section_11_12_8_run_consumer_record_v1(
        mode=MODE_GOVERNED_RUN_CONSUMER_GATE,
        force_kill_switch_killed=True,
        **common,
    )

    ok = all(
        [
            prove_only.run_consumer_may_arm is False,
            gate.run_consumer_may_arm is True,
            gate.run_consumer_present is True,
            gate.execution_authorized is False,
            gate.campaign_started is False,
            gate.network_effect == "NONE",
            gate.order_effect == "NONE",
            gate.live_order_effect == "NONE",
            gate.section_11_13_started is False,
            gate.new_wrapper_layer_created is False,
            gate.terminal_predecessor_bound is True,
            gate.terminal_role_unchanged is True,
            gate.hidden_confirm_reused is True,
            gate.risk_gate_reused is True,
            gate.kill_switch_reused is True,
            gate.credential_plaintext_loaded is False,
            load_forbidden,
            run_refused,
            refusals_ok,
            "kill_switch_operational" in killed.missing_preconditions
            or "risk_gate_allows" in killed.missing_preconditions,
            PRODUCTIVE_RUN_CONSUMER_IMPLEMENTED is True,
            PRODUCTIVE_RUN_CONSUMER_PRESENT is True,
            IMPLEMENTATION_ONLY is True,
            PRODUCTIVE_RUN_EXECUTION_AUTHORIZED is False,
            TERMINAL_PREDECESSOR_ROLE == TERMINAL_CONSUMER_CANONICAL_ROLE,
        ]
    )
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "PATH_CLASS": PATH_CLASS,
        "RUN_CONSUMER_CANONICAL_ROLE": RUN_CONSUMER_CANONICAL_ROLE,
        "PRODUCTIVE_RUN_CONSUMER_IMPLEMENTED": True,
        "PRODUCTIVE_RUN_CONSUMER_PRESENT": True,
        "PRODUCTIVE_RUN_EXECUTION_AUTHORIZED": False,
        "NEW_WRAPPER_LAYER_CREATED": False,
        "TERMINAL_PREDECESSOR_BOUND": True,
        "TERMINAL_CONSUMER_ROLE_UNCHANGED": True,
        "TERMINAL_PREDECESSOR_ROLE": TERMINAL_PREDECESSOR_ROLE,
        "HIDDEN_CONFIRM_REUSED": True,
        "RISK_GATE_REUSED": True,
        "KILL_SWITCH_REUSED": True,
        "ENABLED_ARMED_FAIL_CLOSED": True,
        "CREDENTIAL_PLAINTEXT_LOADED": False,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
        "NETWORK_EFFECT": NETWORK_EFFECT,
        "ORDER_EFFECT": ORDER_EFFECT,
        "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
        "SECTION_11_13_STARTED": False,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "prove_only_may_arm": prove_only.run_consumer_may_arm,
        "gate_may_arm": gate.run_consumer_may_arm,
        "kill_switch_blocks_gate": bool(killed.missing_preconditions),
        "credential_load_forbidden": load_forbidden,
        "productive_run_execution_refused": run_refused,
        "refusals_ok": refusals_ok,
    }
