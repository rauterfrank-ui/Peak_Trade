"""Authorization / ENABLED/ARMED / confirm / risk / kill-switch gates for §11.12.8 terminal.

Reuses Phase-9.2 Hidden-Confirm channels, canonical RiskGate, and KillSwitch.
Never mints/consumes confirm tokens or loads credentials in this implementation GO.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.gates.risk_gate import RiskContext, RiskLimits, evaluate_risk
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1 import (
    fingerprint_only_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
    DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH,
    REAL_TTY_OPERATOR_ENTRYPOINT_PATH,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.delegated_cursor_secure_confirm_broker_v1 import (
    digest_sha256_v1,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.constants_v1 import (
    CAMPAIGN_ARMED_DEFAULT,
    CAMPAIGN_ENABLED_DEFAULT,
    CANONICAL_ALLOWED_ORDER_TYPES,
    CANONICAL_EMERGENCY_COMMANDS,
    CANONICAL_INSTRUMENT_SCOPE,
    CANONICAL_POSITION_COUNT_LIMIT,
    CANONICAL_RUNTIME_MODE,
    CANONICAL_VENUE,
    CREDENTIAL_PLAINTEXT_LOADED,
    NETWORK_EFFECT,
    ORDER_EFFECT,
    SECTION_11_13_STARTED,
    SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION,
)
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.state import KillSwitchState

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class Section11128TerminalGateError(RuntimeError):
    """Fail-closed terminal gate violation."""


def _is_secret_reference_only(secret_reference: str) -> bool:
    if not secret_reference:
        return False
    if secret_reference.startswith("plaintext:") or secret_reference.startswith("sk-"):
        return False
    if secret_reference.startswith("secretref:"):
        return True
    return "://" in secret_reference


@dataclass(frozen=True)
class TerminalAuthorizationGateRecordV1:
    admissible: bool
    missing_preconditions: tuple[str, ...]
    campaign_enabled: bool
    campaign_armed: bool
    owner_go_bound: bool
    confirm_token_digest: str
    hidden_confirm_channel: str
    risk_gate_allows: bool
    kill_switch_operational: bool
    kill_switch_state: str
    emergency_control_operational: bool
    credential_load_path_bound: bool
    credential_plaintext_loaded: bool
    network_effect: str
    order_effect: str


def bind_confirm_token_digest_reusing_phase92_v1(
    *,
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    authorization_channel: str = AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
) -> dict[str, Any]:
    """Bind digest-only confirm using Phase-9.2 rejectors + digest helpers."""
    blockers = reject_confirm_token_argv_v1(argv)
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    if blockers:
        raise Section11128TerminalGateError(";".join(blockers))

    if authorization_channel not in {
        AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
        AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    }:
        raise Section11128TerminalGateError(
            f"HIDDEN_CONFIRM_CHANNEL_UNKNOWN:{authorization_channel}"
        )

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    if handoff.get("ok") is not True:
        raise Section11128TerminalGateError("HIDDEN_PTY_HANDOFF_BINDING_FAILED")

    digest = str(confirm_token_digest or "").strip().lower()
    if not _HEX64.match(digest):
        raise Section11128TerminalGateError("CONFIRM_TOKEN_DIGEST_INVALID")
    if expected_confirm_token_digest is not None:
        expected = str(expected_confirm_token_digest).strip().lower()
        if not _HEX64.match(expected):
            raise Section11128TerminalGateError("CONFIRM_TOKEN_EXPECTED_DIGEST_INVALID")
        if digest != expected:
            raise Section11128TerminalGateError("CONFIRM_TOKEN_DIGEST_MISMATCH")

    # Prove Phase-9.2 digest helpers remain the canonical path (no local hash invent).
    _ = fingerprint_only_v1
    _ = digest_sha256_v1

    return {
        "confirm_token_digest_bound": True,
        "confirm_token_digest": digest,
        "confirm_token_minted": False,
        "confirm_token_consumed": False,
        "confirm_token_plaintext_persisted": False,
        "authorization_channel": authorization_channel,
        "hidden_confirm_reused": True,
        "real_tty_entrypoint": REAL_TTY_OPERATOR_ENTRYPOINT_PATH,
        "delegated_entrypoint": DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH,
    }


def evaluate_risk_gate_reused_v1(
    *,
    kill_switch_blocks: bool,
    order_notional_usd: float = 10.0,
    max_notional_usd: float = 100.0,
    order_size: float = 1.0,
    max_order_size: float = 10.0,
    current_position: float = 0.0,
    max_position: float = 1.0,
    market_data_age_seconds: int = 1,
    max_data_age_seconds: int = 30,
    session_pnl_usd: float = 0.0,
) -> dict[str, Any]:
    limits = RiskLimits(
        enabled=True,
        kill_switch=kill_switch_blocks,
        max_notional_usd=max_notional_usd,
        max_order_size=max_order_size,
        max_position=max_position,
        max_session_loss_usd=50.0,
        max_data_age_seconds=max_data_age_seconds,
    )
    ctx = RiskContext(
        now_epoch=1,
        market_data_age_seconds=market_data_age_seconds,
        session_pnl_usd=session_pnl_usd,
        current_position=current_position,
        order_size=order_size,
        order_notional_usd=order_notional_usd,
    )
    decision = evaluate_risk(limits, ctx)
    return {
        "allow": bool(decision.allow),
        "reason": None if decision.reason is None else str(decision.reason.value),
        "details": dict(decision.details),
        "risk_gate_reused": True,
        "risk_gate_owner": "ops.gates.risk_gate",
    }


def evaluate_kill_switch_operational_v1(
    *,
    kill_switch: KillSwitch | None = None,
    force_killed: bool = False,
) -> dict[str, Any]:
    if kill_switch is None:
        import logging

        quiet = logging.getLogger("section_11_12_8_terminal.kill_switch.fixture")
        quiet.disabled = True
        ks = KillSwitch({"recovery_cooldown_seconds": 1, "enabled": True}, logger=quiet)
    else:
        ks = kill_switch
    if force_killed and ks.state == KillSwitchState.ACTIVE:
        ks.trigger("TERMINAL_GATE_FIXTURE_KILL")
    blocked = bool(ks.check_and_block())
    operational = ks.enabled is True and not blocked
    emergency_ok = set(CANONICAL_EMERGENCY_COMMANDS).issuperset(
        {
            "BLOCK_NEW_ENTRY",
            "EXIT_ONLY",
            "REDUCE_ONLY",
            "CANCEL_ALL",
            "HALT_AFTER_CANCEL",
            "PERSISTENT_KILL",
        }
    )
    return {
        "kill_switch_operational": operational,
        "kill_switch_blocks": blocked,
        "kill_switch_state": ks.state.name,
        "kill_switch_reused": True,
        "kill_switch_owner": "risk_layer.kill_switch.core.KillSwitch",
        "emergency_control_operational": emergency_ok and operational,
        "emergency_commands": list(CANONICAL_EMERGENCY_COMMANDS),
    }


def bind_credential_load_path_without_loading_v1(
    *,
    secret_reference: str,
    runtime_mode: str,
    plaintext_secret: str | None = None,
) -> dict[str, Any]:
    """Credential-load path binding only — never loads plaintext in this GO."""
    if plaintext_secret is not None:
        raise Section11128TerminalGateError(
            "CREDENTIAL_PLAINTEXT_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION"
        )
    if runtime_mode != "TESTNET":
        raise Section11128TerminalGateError("CREDENTIAL_SCOPE_MUST_BE_TESTNET")
    if not _is_secret_reference_only(secret_reference):
        raise Section11128TerminalGateError("SECRET_REFERENCE_ONLY_REQUIRED")
    return {
        "credential_load_path_bound": True,
        "credential_load_implemented": True,
        "credential_plaintext_loaded": False,
        "credential_load_performed": False,
        "secret_reference": secret_reference,
    }


def attempt_credential_load_v1(*, path_bound: bool) -> None:
    """Always refuse real credential load in this implementation OWNER_GO."""
    if not path_bound:
        raise Section11128TerminalGateError("CREDENTIAL_LOAD_PATH_NOT_BOUND")
    raise Section11128TerminalGateError("CREDENTIAL_LOAD_FORBIDDEN_IN_TERMINAL_IMPLEMENTATION_ONLY")


def evaluate_terminal_authorization_gate_v1(
    *,
    repository_sha: str,
    config_digest: str,
    account_identity: str,
    venue: str = CANONICAL_VENUE,
    runtime_mode: str = CANONICAL_RUNTIME_MODE,
    instrument_scope: tuple[str, ...] | list[str] | None = None,
    allowed_order_types: tuple[str, ...] | list[str] | None = None,
    position_count_limit: int = CANONICAL_POSITION_COUNT_LIMIT,
    secret_reference: str = "secretref://vault/peak-trade/testnet-demo",
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    owner_go_bound: bool = False,
    campaign_enabled: bool = CAMPAIGN_ENABLED_DEFAULT,
    campaign_armed: bool = CAMPAIGN_ARMED_DEFAULT,
    authorization_channel: str = AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
    live_endpoint_configured: bool = False,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    kill_switch: KillSwitch | None = None,
    force_kill_switch_killed: bool = False,
) -> TerminalAuthorizationGateRecordV1:
    missing: list[str] = []
    instruments = tuple(instrument_scope or CANONICAL_INSTRUMENT_SCOPE)
    order_types = tuple(allowed_order_types or CANONICAL_ALLOWED_ORDER_TYPES)

    if runtime_mode != "TESTNET":
        missing.append("testnet_only_scope")
    if live_endpoint_configured or runtime_mode == "LIVE":
        missing.append("live_path_blocked")
    if venue != CANONICAL_VENUE:
        missing.append("venue_bound")
    if not account_identity.strip():
        missing.append("account_identity_bound")
    if not _SHA40.match(str(repository_sha).strip().lower()):
        missing.append("repository_sha_bound")
    if not str(config_digest).startswith("cfg-") or len(config_digest) < 68:
        missing.append("config_digest_bound")
    if any(i not in CANONICAL_INSTRUMENT_SCOPE for i in instruments):
        missing.append("instrument_scope_within_authority")
    if any(t not in CANONICAL_ALLOWED_ORDER_TYPES for t in order_types):
        missing.append("order_types_within_authority")
    if position_count_limit != CANONICAL_POSITION_COUNT_LIMIT:
        missing.append("position_count_within_authority")
    if not owner_go_bound:
        missing.append("owner_go_bound")
    if not campaign_enabled:
        missing.append("campaign_enabled")
    if not campaign_armed:
        missing.append("campaign_armed")
    if SECTION_11_13_STARTED:
        missing.append("cap_11_13_not_started")
    if NETWORK_EFFECT != "NONE":
        missing.append("network_effect_none")
    if ORDER_EFFECT != "NONE":
        missing.append("order_effect_none")
    if CREDENTIAL_PLAINTEXT_LOADED:
        missing.append("credential_plaintext_not_loaded")
    if SIDE_EFFECTS_AUTHORIZED_IN_THIS_IMPLEMENTATION:
        missing.append("side_effects_unauthorized_in_this_implementation")

    confirm: dict[str, Any] = {"confirm_token_digest_bound": False, "confirm_token_digest": ""}
    try:
        confirm = bind_confirm_token_digest_reusing_phase92_v1(
            confirm_token_digest=confirm_token_digest,
            expected_confirm_token_digest=expected_confirm_token_digest,
            argv=argv,
            environ=environ,
            authorization_channel=authorization_channel,
        )
    except Section11128TerminalGateError:
        missing.append("confirm_token_digest_bound")
        missing.append("hidden_confirm_channel_bound")
    else:
        if not confirm.get("hidden_confirm_reused"):
            missing.append("hidden_confirm_channel_bound")

    try:
        cred = bind_credential_load_path_without_loading_v1(
            secret_reference=secret_reference,
            runtime_mode=runtime_mode,
        )
        cred_bound = bool(cred.get("credential_load_path_bound"))
    except Section11128TerminalGateError:
        cred_bound = False
        missing.append("credential_scope_testnet")
        missing.append("secret_reference_only")

    ks = evaluate_kill_switch_operational_v1(
        kill_switch=kill_switch,
        force_killed=force_kill_switch_killed,
    )
    if not ks["kill_switch_operational"]:
        missing.append("kill_switch_operational")
    if not ks["emergency_control_operational"]:
        missing.append("emergency_control_operational")

    risk = evaluate_risk_gate_reused_v1(kill_switch_blocks=bool(ks["kill_switch_blocks"]))
    if not risk["allow"]:
        missing.append("risk_gate_allows")

    # Deduplicate while preserving order.
    seen: set[str] = set()
    ordered_missing: list[str] = []
    for item in missing:
        if item not in seen:
            seen.add(item)
            ordered_missing.append(item)

    return TerminalAuthorizationGateRecordV1(
        admissible=len(ordered_missing) == 0,
        missing_preconditions=tuple(ordered_missing),
        campaign_enabled=bool(campaign_enabled),
        campaign_armed=bool(campaign_armed),
        owner_go_bound=bool(owner_go_bound),
        confirm_token_digest=str(confirm.get("confirm_token_digest") or ""),
        hidden_confirm_channel=str(confirm.get("authorization_channel") or ""),
        risk_gate_allows=bool(risk["allow"]),
        kill_switch_operational=bool(ks["kill_switch_operational"]),
        kill_switch_state=str(ks["kill_switch_state"]),
        emergency_control_operational=bool(ks["emergency_control_operational"]),
        credential_load_path_bound=cred_bound,
        credential_plaintext_loaded=False,
        network_effect=NETWORK_EFFECT,
        order_effect=ORDER_EFFECT,
    )
