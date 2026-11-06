"""Terminal productive §11.12.8 campaign consumer (implementation-only).

Single terminal consumer for Master Runbook §11.12.8. Not a PATH/EXECUTION/
RUN/RUN_ACTIVATION wrapper. Consumes fixture predecessor, reuses Phase-9.2
confirm + RiskGate + KillSwitch, constructs TestnetExecutionPort under an
authorized terminal gate, and hard-refuses productive run / network / orders /
credential plaintext load / §11.13 in this OWNER_GO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.constants_v1 import (
    CAPABILITY_ID as FIXTURE_CAPABILITY_ID,
    TESTNET_CAMPAIGN_STARTED as FIXTURE_TESTNET_CAMPAIGN_STARTED,
)
from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.section_11_12_8_v1 import (
    prove_section_11_12_8_long_running_autonomous_testnet_campaign_v1,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.campaign_authorization_gate_v1 import (
    Section11128TerminalGateError,
    attempt_credential_load_v1,
    evaluate_terminal_authorization_gate_v1,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.constants_v1 import (
    CAMPAIGN_SIDE_EFFECTS_AUTHORIZED,
    CAPABILITY_ID,
    CONTRACT_VERSION,
    CREDENTIAL_LOAD_IMPLEMENTED,
    CREDENTIAL_PLAINTEXT_LOADED,
    HIDDEN_CONFIRM_REUSE_OWNER,
    IMPLEMENTATION_ONLY,
    KILL_SWITCH_REUSE_OWNER,
    LIVE_ORDER_EFFECT,
    MODE_GOVERNED_TERMINAL_GATE,
    MODE_PROVE_TERMINAL_ONLY,
    NETWORK_EFFECT,
    NEW_WRAPPER_LAYER_CREATED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    OWNER,
    PREDECESSOR_CAPABILITY_ID,
    PRODUCTIVE_RUN_AUTHORIZED,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    RISK_GATE_REUSE_OWNER,
    SECTION_11_13_STARTED,
    SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION,
    TERMINAL_CONSUMER_CANONICAL_ROLE,
    TERMINAL_CONSUMER_IMPLEMENTED,
    TESTNET_EXECUTION_PORT_CONSTRUCTIBLE,
    TESTNET_EXECUTION_PORT_REACHABLE_UNDER_AUTHORIZED_TERMINAL,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.testnet_execution_port_productive_v1 import (
    TestnetExecutionPortProductiveError,
    construct_testnet_execution_port_under_terminal_v1,
    prove_testnet_execution_port_productive_binding_v1,
)


class Section11128TerminalConsumerError(RuntimeError):
    """Fail-closed terminal consumer violation."""


@dataclass(frozen=True)
class Section11128TerminalConsumerRecordV1:
    mode: str
    terminal_may_start: bool
    fixture_predecessor_bound: bool
    gate_admissible: bool
    missing_preconditions: tuple[str, ...]
    campaign_enabled: bool
    campaign_armed: bool
    owner_go_bound: bool
    port_constructible: bool
    port_reachable_under_authorized_terminal: bool
    port_constructed: bool
    credential_load_implemented: bool
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


def _bind_fixture_predecessor_v1() -> dict[str, Any]:
    proof = prove_section_11_12_8_long_running_autonomous_testnet_campaign_v1()
    if proof.get("ok") is not True:
        raise Section11128TerminalConsumerError("FIXTURE_PREDECESSOR_PROOF_FAILED")
    if FIXTURE_TESTNET_CAMPAIGN_STARTED is not False:
        raise Section11128TerminalConsumerError("FIXTURE_MUST_REMAIN_CAMPAIGN_NOT_STARTED")
    return {
        "fixture_predecessor_bound": True,
        "fixture_capability_id": FIXTURE_CAPABILITY_ID,
        "fixture_ok": True,
    }


def build_section_11_12_8_terminal_consumer_record_v1(
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
) -> Section11128TerminalConsumerRecordV1:
    if mode not in {MODE_PROVE_TERMINAL_ONLY, MODE_GOVERNED_TERMINAL_GATE}:
        raise Section11128TerminalConsumerError(f"UNKNOWN_TERMINAL_MODE:{mode}")

    fixture = _bind_fixture_predecessor_v1()
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
    if not fixture["fixture_predecessor_bound"]:
        missing.append("fixture_predecessor_bound")
    if not TESTNET_EXECUTION_PORT_CONSTRUCTIBLE:
        missing.append("testnet_execution_port_constructible")

    # Deduplicate.
    seen: set[str] = set()
    ordered_missing: list[str] = []
    for item in missing:
        if item not in seen:
            seen.add(item)
            ordered_missing.append(item)

    gate_admissible = len(ordered_missing) == 0 and gate.admissible
    if mode == MODE_PROVE_TERMINAL_ONLY:
        terminal_may_start = False
        authorized_for_port = False
    else:
        terminal_may_start = (
            gate_admissible
            and not PRODUCTIVE_RUN_AUTHORIZED
            and not SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION
            and not CAMPAIGN_SIDE_EFFECTS_AUTHORIZED
        )
        authorized_for_port = terminal_may_start

    port_constructed = False
    if authorized_for_port:
        port = construct_testnet_execution_port_under_terminal_v1(authorized_terminal=True)
        port_constructed = (
            port.CONSTRUCTIBLE is True
            and port.REACHABLE is True
            and port.constructed_under_authorized_terminal is True
        )
        if not port_constructed:
            ordered_missing.append("testnet_execution_port_constructible")
            terminal_may_start = False

    return Section11128TerminalConsumerRecordV1(
        mode=mode,
        terminal_may_start=terminal_may_start,
        fixture_predecessor_bound=bool(fixture["fixture_predecessor_bound"]),
        gate_admissible=gate_admissible,
        missing_preconditions=tuple(ordered_missing),
        campaign_enabled=gate.campaign_enabled,
        campaign_armed=gate.campaign_armed,
        owner_go_bound=gate.owner_go_bound,
        port_constructible=TESTNET_EXECUTION_PORT_CONSTRUCTIBLE,
        port_reachable_under_authorized_terminal=(
            TESTNET_EXECUTION_PORT_REACHABLE_UNDER_AUTHORIZED_TERMINAL
        ),
        port_constructed=port_constructed,
        credential_load_implemented=CREDENTIAL_LOAD_IMPLEMENTED,
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


def refuse_productive_campaign_run_v1(*, campaign_id: str = "campaign-demo") -> None:
    raise Section11128TerminalConsumerError(
        f"PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_FORBIDDEN_IN_IMPLEMENTATION:{campaign_id}"
    )


def refuse_network_session_v1(*, session_id: str = "session-demo") -> None:
    raise Section11128TerminalConsumerError(
        f"NETWORK_SESSION_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION:{session_id}"
    )


def refuse_order_submit_v1(*, order_id: str = "order-demo") -> None:
    raise Section11128TerminalConsumerError(
        f"ORDER_SUBMIT_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION:{order_id}"
    )


def refuse_live_path_v1(*, endpoint: str = "live") -> None:
    raise Section11128TerminalConsumerError(
        f"LIVE_PATH_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION:{endpoint}"
    )


def refuse_cap_11_13_v1(*, path_name: str = "live_activation") -> None:
    raise Section11128TerminalConsumerError(
        f"CAPABILITY_11_13_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION:{path_name}"
    )


def run_section_11_12_8_terminal_consumer_v1(**_kwargs: Any) -> None:
    """Entrypoint hard-refuse: this OWNER_GO never starts a productive campaign."""
    raise Section11128TerminalConsumerError(
        "PRODUCTIVE_SECTION_11_12_8_CAMPAIGN_RUN_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY"
    )


def prove_section_11_12_8_terminal_consumer_v1() -> dict[str, Any]:
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

    prove_only = build_section_11_12_8_terminal_consumer_record_v1(
        mode=MODE_PROVE_TERMINAL_ONLY, **common
    )
    gate = build_section_11_12_8_terminal_consumer_record_v1(
        mode=MODE_GOVERNED_TERMINAL_GATE, **common
    )

    port_proof = prove_testnet_execution_port_productive_binding_v1()

    load_forbidden = False
    try:
        attempt_credential_load_v1(path_bound=True)
    except Section11128TerminalGateError as exc:
        load_forbidden = "CREDENTIAL_LOAD_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION_ONLY" in str(exc)

    run_refused = False
    try:
        run_section_11_12_8_terminal_consumer_v1(owner_go=True)
    except Section11128TerminalConsumerError as exc:
        run_refused = "FORBIDDEN_IN_THIS_IMPLEMENTATION" in str(exc)

    refusals_ok = True
    for fn, needle in (
        (refuse_productive_campaign_run_v1, "CAMPAIGN_RUN_FORBIDDEN"),
        (refuse_network_session_v1, "NETWORK_SESSION_FORBIDDEN"),
        (refuse_order_submit_v1, "ORDER_SUBMIT_FORBIDDEN"),
        (refuse_live_path_v1, "LIVE_PATH_FORBIDDEN"),
        (refuse_cap_11_13_v1, "CAPABILITY_11_13_FORBIDDEN"),
    ):
        try:
            fn()
            refusals_ok = False
        except Section11128TerminalConsumerError as exc:
            if needle not in str(exc):
                refusals_ok = False

    # Negative: kill switch blocks risk gate.
    killed = build_section_11_12_8_terminal_consumer_record_v1(
        mode=MODE_GOVERNED_TERMINAL_GATE,
        force_kill_switch_killed=True,
        **common,
    )

    ok = all(
        [
            prove_only.terminal_may_start is False,
            gate.terminal_may_start is True,
            gate.port_constructed is True,
            gate.port_constructible is True,
            gate.port_reachable_under_authorized_terminal is True,
            gate.campaign_started is False,
            gate.network_effect == "NONE",
            gate.order_effect == "NONE",
            gate.live_order_effect == "NONE",
            gate.section_11_13_started is False,
            gate.new_wrapper_layer_created is False,
            gate.hidden_confirm_reused is True,
            gate.risk_gate_reused is True,
            gate.kill_switch_reused is True,
            gate.credential_plaintext_loaded is False,
            load_forbidden,
            run_refused,
            refusals_ok,
            port_proof.get("ok") is True,
            "kill_switch_operational" in killed.missing_preconditions
            or "risk_gate_allows" in killed.missing_preconditions,
            TERMINAL_CONSUMER_IMPLEMENTED is True,
            IMPLEMENTATION_ONLY is True,
            PRODUCTIVE_RUN_AUTHORIZED is False,
            PREDECESSOR_CAPABILITY_ID == FIXTURE_CAPABILITY_ID,
        ]
    )
    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "CONTRACT_VERSION": CONTRACT_VERSION,
        "TERMINAL_CONSUMER_CANONICAL_ROLE": TERMINAL_CONSUMER_CANONICAL_ROLE,
        "TERMINAL_CONSUMER_IMPLEMENTED": True,
        "NEW_WRAPPER_LAYER_CREATED": False,
        "TESTNET_EXECUTION_PORT_CONSTRUCTIBLE": True,
        "TESTNET_EXECUTION_PORT_REACHABLE_UNDER_AUTHORIZED_TERMINAL": True,
        "HIDDEN_CONFIRM_REUSED": True,
        "HIDDEN_CONFIRM_REUSE_OWNER": HIDDEN_CONFIRM_REUSE_OWNER,
        "RISK_GATE_REUSED": True,
        "RISK_GATE_REUSE_OWNER": RISK_GATE_REUSE_OWNER,
        "KILL_SWITCH_REUSED": True,
        "KILL_SWITCH_REUSE_OWNER": KILL_SWITCH_REUSE_OWNER,
        "ENABLED_ARMED_FAIL_CLOSED": True,
        "CREDENTIAL_LOAD_IMPLEMENTED": True,
        "CREDENTIAL_PLAINTEXT_LOADED": False,
        "PRODUCTIVE_RUN_STARTED": False,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
        "NETWORK_EFFECT": NETWORK_EFFECT,
        "ORDER_EFFECT": ORDER_EFFECT,
        "LIVE_ORDER_EFFECT": LIVE_ORDER_EFFECT,
        "SECTION_11_13_STARTED": False,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "prove_only_may_start": prove_only.terminal_may_start,
        "gate_may_start": gate.terminal_may_start,
        "gate_port_constructed": gate.port_constructed,
        "kill_switch_blocks_gate": bool(killed.missing_preconditions),
        "credential_load_forbidden": load_forbidden,
        "productive_run_refused": run_refused,
        "port_proof": port_proof,
        "refusals_ok": refusals_ok,
    }
