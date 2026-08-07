"""Authorization binding contract for Cap 11.2 (§11.6 required bindings)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    AUTHORIZATION_CONTRACT_OWNER,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    LIVE_AUTHORIZED,
    REQUIRED_AUTHORIZATION_BINDINGS,
    TESTNET_AUTHORIZED,
)


class AuthorizationBindingViolationError(ValueError):
    """Fail-closed authorization binding violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class AuthorizationBindingV1:
    """Non-consuming authorization binding record (Cap 11.2 boundary only)."""

    authorization_id: str
    repository_sha: str
    config_digest: str
    runtime_mode: str
    venue: str
    account_identity: str
    instrument_or_active_set_scope: tuple[str, ...]
    maximum_notional: str
    maximum_leverage: str
    maximum_position_count: int
    maximum_session_duration: str
    loss_and_drawdown_limits: Mapping[str, str]
    allowed_order_types: tuple[str, ...]
    allowed_side_effects: tuple[str, ...]
    activation_epoch: str
    expiry: str
    consumed: bool = False

    def digest(self) -> str:
        material = {
            "authorization_id": self.authorization_id,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "runtime_mode": self.runtime_mode,
            "venue": self.venue,
            "account_identity": self.account_identity,
            "instrument_or_active_set_scope": list(self.instrument_or_active_set_scope),
            "maximum_notional": self.maximum_notional,
            "maximum_leverage": self.maximum_leverage,
            "maximum_position_count": self.maximum_position_count,
            "maximum_session_duration": self.maximum_session_duration,
            "loss_and_drawdown_limits": dict(self.loss_and_drawdown_limits),
            "allowed_order_types": list(self.allowed_order_types),
            "allowed_side_effects": list(self.allowed_side_effects),
            "activation_epoch": self.activation_epoch,
            "expiry": self.expiry,
            "consumed": self.consumed,
        }
        return hashlib.sha256(_canonical_dumps(material).encode("utf-8")).hexdigest()


def build_authorization_binding_v1(
    *,
    authorization_id: str,
    repository_sha: str,
    config_digest: str,
    runtime_mode: str,
    venue: str,
    account_identity: str,
    instrument_or_active_set_scope: tuple[str, ...] | list[str],
    maximum_notional: str,
    maximum_leverage: str,
    maximum_position_count: int,
    maximum_session_duration: str,
    loss_and_drawdown_limits: Mapping[str, str],
    allowed_order_types: tuple[str, ...] | list[str],
    allowed_side_effects: tuple[str, ...] | list[str],
    activation_epoch: str,
    expiry: str,
    consumed: bool = False,
) -> AuthorizationBindingV1:
    """Validate and build a complete authorization binding; never consume."""
    missing = []
    fields = {
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "runtime_mode": runtime_mode,
        "venue": venue,
        "account_identity": account_identity,
        "instrument_or_active_set_scope": instrument_or_active_set_scope,
        "maximum_notional": maximum_notional,
        "maximum_leverage": maximum_leverage,
        "maximum_position_count": maximum_position_count,
        "maximum_session_duration": maximum_session_duration,
        "loss_and_drawdown_limits": loss_and_drawdown_limits,
        "allowed_order_types": allowed_order_types,
        "allowed_side_effects": allowed_side_effects,
        "activation_epoch": activation_epoch,
        "expiry": expiry,
    }
    for key in REQUIRED_AUTHORIZATION_BINDINGS:
        value = fields.get(key)
        if value is None or value == "" or value == () or value == [] or value == {}:
            missing.append(key)
    if not authorization_id:
        missing.append("authorization_id")
    if missing:
        raise AuthorizationBindingViolationError(
            f"AUTHORIZATION_BINDING_INCOMPLETE:{','.join(missing)}"
        )
    if consumed:
        raise AuthorizationBindingViolationError(
            "AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_CAPABILITY_11_2"
        )
    if runtime_mode in {"TESTNET", "LIVE"} and (
        TESTNET_AUTHORIZED is False and LIVE_AUTHORIZED is False
    ):
        # Binding record may *describe* future modes; Cap 11.2 does not authorize them.
        pass
    if AUTHORIZATION_CONSUMPTION_ALLOWED:
        raise AuthorizationBindingViolationError("AUTHORIZATION_CONSUMPTION_MUST_REMAIN_FALSE")

    return AuthorizationBindingV1(
        authorization_id=authorization_id,
        repository_sha=repository_sha,
        config_digest=config_digest,
        runtime_mode=runtime_mode,
        venue=venue,
        account_identity=account_identity,
        instrument_or_active_set_scope=tuple(str(x) for x in instrument_or_active_set_scope),
        maximum_notional=str(maximum_notional),
        maximum_leverage=str(maximum_leverage),
        maximum_position_count=int(maximum_position_count),
        maximum_session_duration=str(maximum_session_duration),
        loss_and_drawdown_limits=dict(loss_and_drawdown_limits),
        allowed_order_types=tuple(str(x) for x in allowed_order_types),
        allowed_side_effects=tuple(str(x) for x in allowed_side_effects),
        activation_epoch=activation_epoch,
        expiry=expiry,
        consumed=False,
    )


def validate_authorization_binding_against_runtime_v1(
    binding: AuthorizationBindingV1,
    *,
    repository_sha: str,
    config_digest: str,
    runtime_mode: str,
    venue: str,
    account_identity: str,
) -> dict[str, Any]:
    """Validate binding identity fields against runtime truth (validate-only)."""
    blockers: list[str] = []
    if binding.repository_sha != repository_sha:
        blockers.append("REPOSITORY_SHA_MISMATCH")
    if binding.config_digest != config_digest:
        blockers.append("CONFIG_DIGEST_MISMATCH")
    if binding.runtime_mode != runtime_mode:
        blockers.append("RUNTIME_MODE_MISMATCH")
    if binding.venue != venue:
        blockers.append("VENUE_MISMATCH")
    if binding.account_identity != account_identity:
        blockers.append("ACCOUNT_IDENTITY_MISMATCH")
    if binding.consumed:
        blockers.append("AUTHORIZATION_ALREADY_CONSUMED")
    return {
        "ok": not blockers,
        "admitted": not blockers,
        "blockers": blockers,
        "authorization_id": binding.authorization_id,
        "consumed": False,
        "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
        "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
    }


def refuse_authorization_consumption_v1(binding: AuthorizationBindingV1) -> dict[str, Any]:
    """Cap 11.2 must never consume authorization."""
    raise AuthorizationBindingViolationError(
        f"AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_CAPABILITY_11_2:{binding.authorization_id}"
    )


def _demo_binding() -> AuthorizationBindingV1:
    return build_authorization_binding_v1(
        authorization_id="authz-cap11-2-demo",
        repository_sha="0" * 40,
        config_digest="cfg-" + "a" * 64,
        runtime_mode="SIMULATED",
        venue="OKX",
        account_identity="acct-uid-demo",
        instrument_or_active_set_scope=("BTC-USDT-SWAP",),
        maximum_notional="0",
        maximum_leverage="1",
        maximum_position_count=1,
        maximum_session_duration="PT0S",
        loss_and_drawdown_limits={"max_session_loss": "0", "max_drawdown": "0"},
        allowed_order_types=("NONE",),
        allowed_side_effects=("NONE",),
        activation_epoch="0",
        expiry="1970-01-01T00:00:00Z",
    )


def prove_authorization_binding_contract_v1() -> dict[str, Any]:
    binding = _demo_binding()
    match = validate_authorization_binding_against_runtime_v1(
        binding,
        repository_sha=binding.repository_sha,
        config_digest=binding.config_digest,
        runtime_mode=binding.runtime_mode,
        venue=binding.venue,
        account_identity=binding.account_identity,
    )
    mismatch = validate_authorization_binding_against_runtime_v1(
        binding,
        repository_sha="deadbeef",
        config_digest=binding.config_digest,
        runtime_mode=binding.runtime_mode,
        venue=binding.venue,
        account_identity=binding.account_identity,
    )
    incomplete_blocked = False
    try:
        build_authorization_binding_v1(
            authorization_id="authz-incomplete",
            repository_sha="",
            config_digest="cfg",
            runtime_mode="SIMULATED",
            venue="OKX",
            account_identity="acct",
            instrument_or_active_set_scope=("BTC-USDT-SWAP",),
            maximum_notional="0",
            maximum_leverage="1",
            maximum_position_count=1,
            maximum_session_duration="PT0S",
            loss_and_drawdown_limits={"max_session_loss": "0"},
            allowed_order_types=("NONE",),
            allowed_side_effects=("NONE",),
            activation_epoch="0",
            expiry="1970-01-01T00:00:00Z",
        )
    except AuthorizationBindingViolationError:
        incomplete_blocked = True

    consume_blocked = False
    try:
        refuse_authorization_consumption_v1(binding)
    except AuthorizationBindingViolationError:
        consume_blocked = True

    ok = all(
        [
            match.get("ok") is True,
            mismatch.get("ok") is False,
            "REPOSITORY_SHA_MISMATCH" in mismatch.get("blockers", []),
            incomplete_blocked,
            consume_blocked,
            set(REQUIRED_AUTHORIZATION_BINDINGS).issubset(
                {
                    "repository_sha",
                    "config_digest",
                    "runtime_mode",
                    "venue",
                    "account_identity",
                    "instrument_or_active_set_scope",
                    "maximum_notional",
                    "maximum_leverage",
                    "maximum_position_count",
                    "maximum_session_duration",
                    "loss_and_drawdown_limits",
                    "allowed_order_types",
                    "allowed_side_effects",
                    "activation_epoch",
                    "expiry",
                }
            ),
            AUTHORIZATION_CONSUMPTION_ALLOWED is False,
            TESTNET_AUTHORIZED is False,
            LIVE_AUTHORIZED is False,
            binding.consumed is False,
        ]
    )
    return {
        "ok": ok,
        "owner": AUTHORIZATION_CONTRACT_OWNER,
        "REQUIRED_AUTHORIZATION_BINDINGS": list(REQUIRED_AUTHORIZATION_BINDINGS),
        "authorization_digest": binding.digest(),
        "match_ok": match.get("ok") is True,
        "mismatch_fail_closed": mismatch.get("ok") is False,
        "incomplete_blocked": incomplete_blocked,
        "consumption_blocked": consume_blocked,
        "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
        "TESTNET_AUTHORIZED": False,
        "LIVE_AUTHORIZED": False,
    }
