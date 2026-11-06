"""Fail-closed productive §11.12.8 Testnet campaign PATH (no execution).

Implements gates for a later separate Owner-GO productive campaign run.
This capability never starts the campaign, never submits orders, and never
opens network sessions. Fixture §11.12.8 proof remains unchanged and required.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.constants_v1 import (
    CAPABILITY_ID as FIXTURE_CAPABILITY_ID,
    TESTNET_CAMPAIGN_STARTED as FIXTURE_TESTNET_CAMPAIGN_STARTED,
)
from src.ops.capability_11_section_11_12_8_long_running_autonomous_testnet_campaign_v1.section_11_12_8_v1 import (
    prove_section_11_12_8_long_running_autonomous_testnet_campaign_v1,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1.confirm_token_binding_v1 import (
    Productive11128ConfirmTokenBindingError,
    bind_confirm_token_digest_v1,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1.constants_v1 import (
    ACTIVATION_STATE,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_CONSUMED,
    CAMPAIGN_ARMED_DEFAULT,
    CAMPAIGN_ENABLED_DEFAULT,
    CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA,
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
    EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA,
    FIXTURE_PROOF_PRESERVED,
    KILL_SWITCH_BINDING_STATUS_REQUIRED,
    KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME,
    KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT,
    KILL_SWITCH_CONTRACT_ACTIVATED,
    KILL_SWITCH_FAIL_CLOSED,
    KILL_SWITCH_PERSISTED,
    KILL_SWITCH_SURVIVES_RESTART,
    LIVE_AUTHORIZED,
    LIVE_EXECUTION_REACHABLE,
    MODE_GOVERNED_START_GATE,
    MODE_PROVE_PATH_ONLY,
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
    OWNER_AUTHORITY_REQUIRED_TO_CLEAR,
    PATH_CLASS,
    PREDECESSOR_CAPABILITY_ID,
    PRODUCTIVE_TESTNET_CAMPAIGN_ACTIVATED,
    PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED,
    PRODUCTIVE_TESTNET_CAMPAIGN_PATH_ABSENT,
    PRODUCTIVE_TESTNET_CAMPAIGN_PATH_PRESENT,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    PRODUCTIVE_TESTNET_CAPABILITY_IMPLEMENTED,
    PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED,
    REAL_EXECUTION_ADAPTER_CONSTRUCTED,
    REFERENCE_ONLY,
    REQUIRED_PRECONDITIONS,
    SECTION_11_13_STARTED,
    TESTNET_AUTHORIZED,
    TESTNET_EXECUTION_REACHABLE,
    TESTNET_ORDER_SUBMIT_PERFORMED,
)


class Productive11128CampaignPathError(RuntimeError):
    """Fail-closed productive §11.12.8 campaign path violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _is_secret_reference_only(secret_reference: str) -> bool:
    if not secret_reference:
        return False
    if secret_reference.startswith("plaintext:") or secret_reference.startswith("sk-"):
        return False
    if secret_reference.startswith("secretref:"):
        return True
    return "://" in secret_reference


@dataclass(frozen=True)
class Productive11128CampaignPathRecordV1:
    """Path-binding / start-gate evaluation record (never starts campaign)."""

    mode: str
    runtime_mode: str
    venue: str
    account_identity: str
    instrument_scope: tuple[str, ...]
    allowed_order_types: tuple[str, ...]
    position_count_limit: int
    repository_sha: str
    config_digest: str
    credential_scope: str
    secret_reference: str
    confirm_token_digest: str
    campaign_enabled: bool
    campaign_armed: bool
    owner_go_bound: bool
    kill_switch_operational: bool
    emergency_control_operational: bool
    fixture_predecessor_bound: bool
    missing_preconditions: tuple[str, ...]
    campaign_may_start: bool
    campaign_started: bool
    network_effect: str
    order_effect: str
    path_binding_digest: str
    contract_version: str = CONTRACT_VERSION
    owner: str = OWNER
    path_class: str = PATH_CLASS
    reference_only: bool = False


def bind_fixture_predecessor_v1() -> dict[str, Any]:
    """Reuse fixture §11.12.8 proof without mutation or campaign start."""
    proof = prove_section_11_12_8_long_running_autonomous_testnet_campaign_v1()
    if proof.get("ok") is not True:
        raise Productive11128CampaignPathError("FIXTURE_11_12_8_PROOF_NOT_OK")
    if proof.get("testnet_campaign_started") is not False:
        raise Productive11128CampaignPathError("FIXTURE_CAMPAIGN_STARTED_DRIFT")
    if FIXTURE_TESTNET_CAMPAIGN_STARTED is not False:
        raise Productive11128CampaignPathError("FIXTURE_CONSTANT_CAMPAIGN_STARTED_DRIFT")
    if proof.get("network_effect") != "NONE" or proof.get("order_effect") != "NONE":
        raise Productive11128CampaignPathError("FIXTURE_NETWORK_OR_ORDER_EFFECT_DRIFT")
    return {
        "fixture_predecessor_bound": True,
        "fixture_capability_id": FIXTURE_CAPABILITY_ID,
        "fixture_proof_ok": True,
        "fixture_testnet_campaign_started": False,
        "fixture_network_effect": "NONE",
        "fixture_order_effect": "NONE",
        "fixture_kill_switch_binding_status": proof.get("kill_switch_binding_status"),
    }


def evaluate_productive_campaign_path_preconditions_v1(
    *,
    runtime_mode: str,
    venue: str,
    account_identity: str,
    instrument_scope: tuple[str, ...] | list[str],
    allowed_order_types: tuple[str, ...] | list[str],
    position_count_limit: int,
    repository_sha: str,
    config_digest: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_account_identity: str,
    expected_venue: str,
    credential_scope: str,
    secret_reference: str,
    owner_go_bound: bool,
    confirm_token_digest_bound: bool,
    campaign_enabled: bool,
    campaign_armed: bool,
    kill_switch_operational: bool,
    emergency_control_operational: bool,
    fixture_predecessor_bound: bool,
    live_endpoint_configured: bool = False,
    orders_authorized: bool = False,
    order_send_disabled: bool = True,
    network_writes_authorized: bool = False,
    network_effect: str = NETWORK_EFFECT,
    campaign_started: bool = False,
    execution_authorized: bool = False,
    cap_11_13_started: bool = False,
) -> dict[str, Any]:
    """Evaluate productive path start-gate preconditions (fail-closed)."""
    missing: list[str] = []
    scope = tuple(str(x) for x in instrument_scope)
    order_types = tuple(str(x) for x in allowed_order_types)

    if not fixture_predecessor_bound:
        missing.append("fixture_predecessor_bound")
    if runtime_mode != CANONICAL_RUNTIME_MODE or live_endpoint_configured:
        missing.append("testnet_only_scope")
    if live_endpoint_configured or LIVE_AUTHORIZED or LIVE_EXECUTION_REACHABLE:
        missing.append("live_path_blocked")
    if not venue:
        missing.append("venue_explicit")
    if not account_identity:
        missing.append("account_identity_explicit")
    if not scope or any(i not in CANONICAL_INSTRUMENT_SCOPE for i in scope):
        missing.append("instrument_scope_within_authority")
    if set(scope) != set(CANONICAL_INSTRUMENT_SCOPE):
        # Exact authority match — no subset/superset expansion.
        if "instrument_scope_within_authority" not in missing:
            missing.append("instrument_scope_within_authority")
    if not order_types or any(t not in CANONICAL_ALLOWED_ORDER_TYPES for t in order_types):
        missing.append("order_types_within_authority")
    if set(order_types) != set(CANONICAL_ALLOWED_ORDER_TYPES):
        if "order_types_within_authority" not in missing:
            missing.append("order_types_within_authority")
    if position_count_limit != CANONICAL_POSITION_COUNT_LIMIT:
        missing.append("position_count_within_authority")
    if credential_scope != "TESTNET":
        missing.append("credential_scope_testnet")
    if not _is_secret_reference_only(secret_reference):
        missing.append("secret_reference_only")
    if not repository_sha or repository_sha != expected_repository_sha:
        missing.append("repository_sha_bound")
    if not config_digest or config_digest != expected_config_digest:
        missing.append("config_digest_bound")
    if not account_identity or account_identity != expected_account_identity:
        missing.append("account_identity_bound")
    if not venue or venue != expected_venue or venue != CANONICAL_VENUE:
        missing.append("venue_bound")
    if not owner_go_bound:
        missing.append("owner_authorization_bound")
    if not confirm_token_digest_bound:
        missing.append("confirm_token_digest_bound")
    if not campaign_enabled or CAMPAIGN_ENABLED_DEFAULT is True:
        # Default must remain false; ephemeral enabled must be explicit true.
        if not campaign_enabled:
            missing.append("campaign_enabled")
        if CAMPAIGN_ENABLED_DEFAULT is True:
            missing.append("campaign_enabled")
    if not campaign_armed or CAMPAIGN_ARMED_DEFAULT is True:
        if not campaign_armed:
            missing.append("campaign_armed")
        if CAMPAIGN_ARMED_DEFAULT is True:
            missing.append("campaign_armed")
    if not kill_switch_operational:
        missing.append("kill_switch_operational")
    if not emergency_control_operational:
        missing.append("emergency_control_operational")
    if not order_send_disabled or ORDER_SEND_DISABLED is not True:
        missing.append("order_send_disabled_default")
    if orders_authorized or ORDERS_AUTHORIZED is True:
        missing.append("orders_unauthorized_default")
    if network_writes_authorized or NETWORK_WRITES_AUTHORIZED is True:
        missing.append("network_writes_unauthorized")
    if network_effect != "NONE" or NETWORK_EFFECT != "NONE":
        missing.append("network_effect_none")
    if (
        campaign_started
        or PRODUCTIVE_TESTNET_CAMPAIGN_STARTED
        or PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED
        or PRODUCTIVE_TESTNET_CAMPAIGN_ACTIVATED
    ):
        missing.append("campaign_not_started")
    if execution_authorized or PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED:
        missing.append("execution_not_authorized")
    if cap_11_13_started or CAPABILITY_11_13_STARTED or SECTION_11_13_STARTED:
        missing.append("cap_11_13_not_started")

    ordered = tuple(name for name in REQUIRED_PRECONDITIONS if name in missing)
    for name in missing:
        if name not in ordered:
            ordered = (*ordered, name)
    return {
        "admissible": len(ordered) == 0,
        "missing_preconditions": list(ordered),
        "REQUIRED_PRECONDITIONS": list(REQUIRED_PRECONDITIONS),
    }


def evaluate_kill_switch_operational_v1(
    *,
    kill_switch_binding_status: str = KILL_SWITCH_BINDING_STATUS_REQUIRED,
    kill_switch_persisted: bool = KILL_SWITCH_PERSISTED,
    kill_switch_fail_closed: bool = KILL_SWITCH_FAIL_CLOSED,
    kill_switch_checked_before_every_side_effect: bool = (
        KILL_SWITCH_CHECKED_BEFORE_EVERY_SIDE_EFFECT
    ),
    kill_switch_survives_restart: bool = KILL_SWITCH_SURVIVES_RESTART,
    kill_switch_cannot_be_cleared_by_runtime: bool = (KILL_SWITCH_CANNOT_BE_CLEARED_BY_RUNTIME),
    owner_authority_required_to_clear: bool = OWNER_AUTHORITY_REQUIRED_TO_CLEAR,
) -> bool:
    return (
        kill_switch_binding_status == KILL_SWITCH_BINDING_STATUS_REQUIRED
        and kill_switch_persisted is True
        and kill_switch_fail_closed is True
        and kill_switch_checked_before_every_side_effect is True
        and kill_switch_survives_restart is True
        and kill_switch_cannot_be_cleared_by_runtime is True
        and owner_authority_required_to_clear is True
        and KILL_SWITCH_CONTRACT_ACTIVATED is False
    )


def evaluate_emergency_control_operational_v1(
    *,
    emergency_commands: tuple[str, ...] | list[str] = CANONICAL_EMERGENCY_COMMANDS,
    cancel_all_independent_of_alpha: bool = CANCEL_ALL_PATH_INDEPENDENT_OF_ALPHA,
    exit_or_reduce_independent_of_alpha: bool = EXIT_OR_REDUCE_POLICY_INDEPENDENT_OF_ALPHA,
) -> bool:
    cmds = tuple(str(x) for x in emergency_commands)
    return (
        cmds == CANONICAL_EMERGENCY_COMMANDS
        and cancel_all_independent_of_alpha is True
        and exit_or_reduce_independent_of_alpha is True
    )


def build_productive_campaign_path_record_v1(
    *,
    mode: str,
    runtime_mode: str,
    venue: str,
    account_identity: str,
    instrument_scope: tuple[str, ...] | list[str],
    allowed_order_types: tuple[str, ...] | list[str],
    position_count_limit: int,
    repository_sha: str,
    config_digest: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_account_identity: str,
    expected_venue: str,
    credential_scope: str,
    secret_reference: str,
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    owner_go_bound: bool,
    campaign_enabled: bool = False,
    campaign_armed: bool = False,
    live_endpoint_configured: bool = False,
    orders_authorized: bool = False,
    order_send_disabled: bool = True,
    network_writes_authorized: bool = False,
    campaign_started: bool = False,
    execution_authorized: bool = False,
    cap_11_13_started: bool = False,
    kill_switch_binding_status: str | None = None,
    emergency_commands: tuple[str, ...] | list[str] | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Productive11128CampaignPathRecordV1:
    """Build path record. Never starts campaign / network / orders."""
    fixture = bind_fixture_predecessor_v1()
    try:
        confirm = bind_confirm_token_digest_v1(
            confirm_token_digest=confirm_token_digest,
            expected_confirm_token_digest=expected_confirm_token_digest,
            plaintext=None,
            argv=argv,
            environ=environ,
        )
    except Productive11128ConfirmTokenBindingError as exc:
        raise Productive11128CampaignPathError(str(exc)) from exc

    kill_ok = evaluate_kill_switch_operational_v1(
        kill_switch_binding_status=(
            KILL_SWITCH_BINDING_STATUS_REQUIRED
            if kill_switch_binding_status is None
            else kill_switch_binding_status
        )
    )
    emergency_ok = evaluate_emergency_control_operational_v1(
        emergency_commands=(
            CANONICAL_EMERGENCY_COMMANDS if emergency_commands is None else emergency_commands
        )
    )
    scope = tuple(str(x) for x in instrument_scope)
    order_types = tuple(str(x) for x in allowed_order_types)

    evaluation = evaluate_productive_campaign_path_preconditions_v1(
        runtime_mode=runtime_mode,
        venue=venue,
        account_identity=account_identity,
        instrument_scope=scope,
        allowed_order_types=order_types,
        position_count_limit=position_count_limit,
        repository_sha=repository_sha,
        config_digest=config_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_account_identity=expected_account_identity,
        expected_venue=expected_venue,
        credential_scope=credential_scope,
        secret_reference=secret_reference,
        owner_go_bound=owner_go_bound,
        confirm_token_digest_bound=bool(confirm.get("confirm_token_digest_bound")),
        campaign_enabled=campaign_enabled,
        campaign_armed=campaign_armed,
        kill_switch_operational=kill_ok,
        emergency_control_operational=emergency_ok,
        fixture_predecessor_bound=bool(fixture.get("fixture_predecessor_bound")),
        live_endpoint_configured=live_endpoint_configured,
        orders_authorized=orders_authorized,
        order_send_disabled=order_send_disabled,
        network_writes_authorized=network_writes_authorized,
        campaign_started=campaign_started,
        execution_authorized=execution_authorized,
        cap_11_13_started=cap_11_13_started,
    )

    may_start = False
    if mode == MODE_PROVE_PATH_ONLY:
        may_start = False
    elif mode == MODE_GOVERNED_START_GATE:
        may_start = bool(evaluation["admissible"])
    else:
        raise Productive11128CampaignPathError(f"UNKNOWN_PATH_MODE:{mode}")

    # Permanent: this capability never starts even when may_start is true.
    if PRODUCTIVE_TESTNET_CAMPAIGN_STARTED or NETWORK_SESSION_STARTED:
        raise Productive11128CampaignPathError("PATH_CONSTANT_STARTED_DRIFT")
    if AUTHORIZATION_CONSUMPTION_ALLOWED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        raise Productive11128CampaignPathError("PATH_CONSUMPTION_CONSTANT_DRIFT")

    digest_payload = {
        "capability_id": CAPABILITY_ID,
        "mode": mode,
        "runtime_mode": runtime_mode,
        "venue": venue,
        "account_identity": account_identity,
        "instrument_scope": list(scope),
        "allowed_order_types": list(order_types),
        "position_count_limit": position_count_limit,
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "credential_scope": credential_scope,
        "confirm_token_digest": confirm["confirm_token_digest"],
        "campaign_enabled": campaign_enabled,
        "campaign_armed": campaign_armed,
        "owner_go_bound": owner_go_bound,
        "campaign_may_start": may_start,
        "campaign_started": False,
        "network_effect": NETWORK_EFFECT,
        "order_effect": ORDER_EFFECT,
        "missing_preconditions": evaluation["missing_preconditions"],
    }
    path_digest = hashlib.sha256(_canonical_dumps(digest_payload).encode("utf-8")).hexdigest()

    return Productive11128CampaignPathRecordV1(
        mode=mode,
        runtime_mode=runtime_mode,
        venue=venue,
        account_identity=account_identity,
        instrument_scope=scope,
        allowed_order_types=order_types,
        position_count_limit=position_count_limit,
        repository_sha=repository_sha,
        config_digest=config_digest,
        credential_scope=credential_scope,
        secret_reference=secret_reference,
        confirm_token_digest=str(confirm["confirm_token_digest"]),
        campaign_enabled=campaign_enabled,
        campaign_armed=campaign_armed,
        owner_go_bound=owner_go_bound,
        kill_switch_operational=kill_ok,
        emergency_control_operational=emergency_ok,
        fixture_predecessor_bound=True,
        missing_preconditions=tuple(evaluation["missing_preconditions"]),
        campaign_may_start=may_start,
        campaign_started=False,
        network_effect=NETWORK_EFFECT,
        order_effect=ORDER_EFFECT,
        path_binding_digest=path_digest,
    )


def refuse_campaign_start_v1(*, campaign_id: str = "campaign-demo") -> None:
    raise Productive11128CampaignPathError(
        f"PRODUCTIVE_TESTNET_CAMPAIGN_START_FORBIDDEN_IN_PATH_CAPABILITY:{campaign_id}"
    )


def refuse_network_session_v1(*, session_id: str = "session-demo") -> None:
    raise Productive11128CampaignPathError(
        f"NETWORK_SESSION_FORBIDDEN_IN_PATH_CAPABILITY:{session_id}"
    )


def refuse_order_submit_v1(*, order_id: str = "order-demo") -> None:
    raise Productive11128CampaignPathError(f"ORDER_SUBMIT_FORBIDDEN_IN_PATH_CAPABILITY:{order_id}")


def refuse_live_path_v1(*, endpoint: str = "live") -> None:
    raise Productive11128CampaignPathError(f"LIVE_PATH_FORBIDDEN_IN_PATH_CAPABILITY:{endpoint}")


def refuse_cap_11_13_v1(*, path_name: str = "live_activation") -> None:
    raise Productive11128CampaignPathError(
        f"CAPABILITY_11_13_FORBIDDEN_IN_PATH_CAPABILITY:{path_name}"
    )


def refuse_scope_escalation_v1(*, claimed_scope: str) -> None:
    raise Productive11128CampaignPathError(
        f"SCOPE_ESCALATION_FORBIDDEN_IN_PATH_CAPABILITY:{claimed_scope}"
    )


def attempt_productive_campaign_execution_v1(**kwargs: Any) -> None:
    """Hard refuse any execution attempt inside this implementation capability."""
    _ = kwargs
    raise Productive11128CampaignPathError(
        "PRODUCTIVE_TESTNET_EXECUTION_FORBIDDEN_IN_PATH_IMPLEMENTATION_CAPABILITY"
    )


def prove_productive_testnet_campaign_path_v1() -> dict[str, Any]:
    """Contract proof: path present, fixture preserved, execution never starts."""
    sha = "a" * 40
    cfg = "cfg-" + ("b" * 64)
    digest = "c" * 64

    common = {
        "runtime_mode": CANONICAL_RUNTIME_MODE,
        "venue": CANONICAL_VENUE,
        "account_identity": "acct-uid-demo",
        "instrument_scope": CANONICAL_INSTRUMENT_SCOPE,
        "allowed_order_types": CANONICAL_ALLOWED_ORDER_TYPES,
        "position_count_limit": CANONICAL_POSITION_COUNT_LIMIT,
        "repository_sha": sha,
        "config_digest": cfg,
        "expected_repository_sha": sha,
        "expected_config_digest": cfg,
        "expected_account_identity": "acct-uid-demo",
        "expected_venue": CANONICAL_VENUE,
        "credential_scope": "TESTNET",
        "secret_reference": "secretref://vault/testnet/okx-demo",
        "confirm_token_digest": digest,
        "expected_confirm_token_digest": digest,
        "owner_go_bound": True,
        "campaign_enabled": True,
        "campaign_armed": True,
    }

    path_only = build_productive_campaign_path_record_v1(mode=MODE_PROVE_PATH_ONLY, **common)
    start_gate = build_productive_campaign_path_record_v1(mode=MODE_GOVERNED_START_GATE, **common)

    live_blocked = False
    try:
        build_productive_campaign_path_record_v1(
            mode=MODE_GOVERNED_START_GATE,
            **{**common, "runtime_mode": "LIVE", "live_endpoint_configured": True},
        )
    except Productive11128CampaignPathError:
        live_blocked = True
    # LIVE mode fails preconditions (may_start false) without exception in build —
    # rebuild and check missing.
    live_record = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "runtime_mode": "LIVE", "live_endpoint_configured": True},
    )
    live_blocked = live_blocked or (
        live_record.campaign_may_start is False
        and "testnet_only_scope" in live_record.missing_preconditions
    )

    bad_cred = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "credential_scope": "LIVE"},
    )
    enabled_false = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "campaign_enabled": False},
    )
    armed_false = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "campaign_armed": False},
    )
    no_owner = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "owner_go_bound": False},
    )

    bad_confirm = False
    try:
        build_productive_campaign_path_record_v1(
            mode=MODE_GOVERNED_START_GATE,
            **{**common, "confirm_token_digest": "deadbeef"},
        )
    except Productive11128CampaignPathError as exc:
        bad_confirm = "CONFIRM_TOKEN_DIGEST_INVALID" in str(exc)

    confirm_mismatch = False
    try:
        build_productive_campaign_path_record_v1(
            mode=MODE_GOVERNED_START_GATE,
            **{**common, "expected_confirm_token_digest": "d" * 64},
        )
    except Productive11128CampaignPathError as exc:
        confirm_mismatch = "CONFIRM_TOKEN_DIGEST_MISMATCH" in str(exc)

    confirm_argv = False
    try:
        build_productive_campaign_path_record_v1(
            mode=MODE_GOVERNED_START_GATE,
            **{**common, "argv": ["--confirm-token", "leak"]},
        )
    except Productive11128CampaignPathError as exc:
        confirm_argv = "CONFIRM_TOKEN_ARGV_FORBIDDEN" in str(exc)

    scope_escalation = False
    try:
        refuse_scope_escalation_v1(claimed_scope="MULTI_INSTRUMENT")
    except Productive11128CampaignPathError as exc:
        scope_escalation = "SCOPE_ESCALATION_FORBIDDEN" in str(exc)

    start_refused = False
    try:
        refuse_campaign_start_v1()
    except Productive11128CampaignPathError as exc:
        start_refused = "CAMPAIGN_START_FORBIDDEN" in str(exc)

    exec_refused = False
    try:
        attempt_productive_campaign_execution_v1(owner_go=True)
    except Productive11128CampaignPathError as exc:
        exec_refused = "EXECUTION_FORBIDDEN" in str(exc)

    cap_11_13_refused = False
    try:
        refuse_cap_11_13_v1()
    except Productive11128CampaignPathError as exc:
        cap_11_13_refused = "CAPABILITY_11_13_FORBIDDEN" in str(exc)

    order_refused = False
    try:
        refuse_order_submit_v1()
    except Productive11128CampaignPathError as exc:
        order_refused = "ORDER_SUBMIT_FORBIDDEN" in str(exc)

    network_refused = False
    try:
        refuse_network_session_v1()
    except Productive11128CampaignPathError as exc:
        network_refused = "NETWORK_SESSION_FORBIDDEN" in str(exc)

    live_refuse = False
    try:
        refuse_live_path_v1()
    except Productive11128CampaignPathError as exc:
        live_refuse = "LIVE_PATH_FORBIDDEN" in str(exc)

    instrument_out = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "instrument_scope": ("ETH-USDT-SWAP",)},
    )
    order_type_out = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "allowed_order_types": ("MARKET",)},
    )
    position_out = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "position_count_limit": 2},
    )
    kill_bad = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "kill_switch_binding_status": "UNBOUND"},
    )
    emergency_bad = build_productive_campaign_path_record_v1(
        mode=MODE_GOVERNED_START_GATE,
        **{**common, "emergency_commands": ("HALT_ONLY",)},
    )

    ok = all(
        [
            PRODUCTIVE_TESTNET_CAPABILITY_IMPLEMENTED is True,
            PRODUCTIVE_TESTNET_CAMPAIGN_PATH_PRESENT is True,
            PRODUCTIVE_TESTNET_CAMPAIGN_PATH_ABSENT is False,
            FIXTURE_PROOF_PRESERVED is True,
            path_only.campaign_may_start is False,
            path_only.campaign_started is False,
            start_gate.campaign_may_start is True,
            start_gate.campaign_started is False,
            start_gate.network_effect == "NONE",
            start_gate.order_effect == "NONE",
            live_blocked,
            "credential_scope_testnet" in bad_cred.missing_preconditions,
            "campaign_enabled" in enabled_false.missing_preconditions,
            "campaign_armed" in armed_false.missing_preconditions,
            "owner_authorization_bound" in no_owner.missing_preconditions,
            bad_confirm,
            confirm_mismatch,
            confirm_argv,
            scope_escalation,
            start_refused,
            exec_refused,
            cap_11_13_refused,
            order_refused,
            network_refused,
            live_refuse,
            "instrument_scope_within_authority" in instrument_out.missing_preconditions,
            "order_types_within_authority" in order_type_out.missing_preconditions,
            "position_count_within_authority" in position_out.missing_preconditions,
            "kill_switch_operational" in kill_bad.missing_preconditions,
            "emergency_control_operational" in emergency_bad.missing_preconditions,
            ORDER_SEND_DISABLED is True,
            ORDERS_AUTHORIZED is False,
            NETWORK_WRITES_AUTHORIZED is False,
            NETWORK_WRITE_PERFORMED is False,
            EXCHANGE_ORDER_SUBMIT_REACHABLE is False,
            TESTNET_ORDER_SUBMIT_PERFORMED is False,
            PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False,
            PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED is False,
            SECTION_11_13_STARTED is False,
            CAPABILITY_11_13_STARTED is False,
            AUTHORIZATION_CONSUMED is False,
            CONFIRM_TOKEN_ISSUANCE_ALLOWED is False,
            CONFIRM_TOKEN_CONSUMPTION_ALLOWED is False,
            TESTNET_AUTHORIZED is False,
            LIVE_AUTHORIZED is False,
            CORE_LOGIC_CHANGE is False,
            REFERENCE_ONLY is False,
            ACTIVATION_STATE == "not_activated",
        ]
    )

    return {
        "ok": ok,
        "CAPABILITY_ID": CAPABILITY_ID,
        "PREDECESSOR_CAPABILITY_ID": PREDECESSOR_CAPABILITY_ID,
        "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        "path_class": PATH_CLASS,
        "PRODUCTIVE_TESTNET_CAPABILITY_IMPLEMENTED": True,
        "FIXTURE_PROOF_PRESERVED": True,
        "PRODUCTIVE_TESTNET_CAMPAIGN_PATH_PRESENT": True,
        "PRODUCTIVE_TESTNET_CAMPAIGN_PATH_ABSENT": False,
        "PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED": False,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
        "PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED": False,
        "NETWORK_EFFECT": NETWORK_EFFECT,
        "ORDER_EFFECT": ORDER_EFFECT,
        "SECTION_11_13_STARTED": False,
        "path_only_may_start": path_only.campaign_may_start,
        "start_gate_may_start": start_gate.campaign_may_start,
        "start_gate_started": start_gate.campaign_started,
        "path_binding_digest": start_gate.path_binding_digest,
        "live_blocked": live_blocked,
        "credential_scope_blocked": "credential_scope_testnet" in bad_cred.missing_preconditions,
        "enabled_false_blocked": "campaign_enabled" in enabled_false.missing_preconditions,
        "armed_false_blocked": "campaign_armed" in armed_false.missing_preconditions,
        "owner_auth_blocked": "owner_authorization_bound" in no_owner.missing_preconditions,
        "confirm_invalid_blocked": bad_confirm,
        "confirm_mismatch_blocked": confirm_mismatch,
        "confirm_argv_blocked": confirm_argv,
        "scope_escalation_blocked": scope_escalation,
        "campaign_start_refused": start_refused,
        "execution_refused": exec_refused,
        "cap_11_13_refused": cap_11_13_refused,
        "order_submit_refused": order_refused,
        "network_session_refused": network_refused,
        "live_path_refused": live_refuse,
        "instrument_scope_blocked": (
            "instrument_scope_within_authority" in instrument_out.missing_preconditions
        ),
        "order_type_blocked": (
            "order_types_within_authority" in order_type_out.missing_preconditions
        ),
        "position_limit_blocked": (
            "position_count_within_authority" in position_out.missing_preconditions
        ),
        "kill_switch_blocked": "kill_switch_operational" in kill_bad.missing_preconditions,
        "emergency_control_blocked": (
            "emergency_control_operational" in emergency_bad.missing_preconditions
        ),
        "ORDER_PATH_STARTED": ORDER_PATH_STARTED,
        "ORDER_SUBMIT_PERFORMED": ORDER_SUBMIT_PERFORMED,
        "MUTATING_EXCHANGE_CALLS": MUTATING_EXCHANGE_CALLS,
        "TESTNET_EXECUTION_REACHABLE": TESTNET_EXECUTION_REACHABLE,
        "LIVE_EXECUTION_REACHABLE": LIVE_EXECUTION_REACHABLE,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": REAL_EXECUTION_ADAPTER_CONSTRUCTED,
        "owner": OWNER,
        "contract_version": CONTRACT_VERSION,
    }
