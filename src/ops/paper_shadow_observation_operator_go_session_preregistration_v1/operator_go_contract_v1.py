"""Scoped Operator-GO contract for Paper-Shadow Observation (non-executing)."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    ALLOWED_NETWORK_SCOPES,
    ALLOWED_SESSION_EXECUTION_SCOPES,
    CAPABILITY_ID,
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    MARKET_TYPE_FUTURES,
    MAX_TTL_SECONDS,
    MIN_TTL_SECONDS,
    NETWORK_SCOPE_OKX_EEA_FUTURES_PUBLIC_MD_OBSERVE_V1,
    OPERATOR_GO_SCHEMA_VERSION,
    REQUIRED_MODE,
    SESSION_EXECUTION_SCOPE_PAPER_SHADOW_OBSERVATION_WALLCLOCK_V1,
    VENUE_OKX,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.state_machine_v1 import (
    AuthorizationArmingState,
    derive_arming_state,
    parse_arming_state,
)

_BTC_RE = re.compile(r"(^|[-_/])BTC([-_/]|$)|XBT|BITCOIN", re.IGNORECASE)
_SPOT_HINTS = frozenset({"SPOT", "CASH", "SPOT_MARGIN"})
_KNOWN_FIELDS = frozenset(
    {
        "schema_version",
        "capability_id",
        "go_id",
        "session_id",
        "venue",
        "market_type",
        "instrument_allowlist",
        "strategy_portfolio_id",
        "planned_duration_seconds",
        "observation_mode",
        "orders_authorized",
        "broker_writes_authorized",
        "testnet_authorized",
        "live_authorized",
        "auto_promotion_authorized",
        "network_authorized",
        "credentials_authorized",
        "session_execution_authorized",
        "network_scope",
        "session_execution_scope",
        "paper_execution_authorized",
        "enabled",
        "armed",
        "arming_state",
        "issued_at",
        "not_before",
        "expires_at",
        "single_use",
        "consumed",
        "revoked",
        "revocation_state",
        "confirm_token_binding_sha256",
        "confirm_token_hash_reference",
        "expected_repository_sha",
        "config_identity",
        "code_identity",
        "operator_identity",
        "approval_identity",
        "scope_digest",
        "fixture_non_authoritative",
        "notes",
    }
)


class OperatorGoContractError(ValueError):
    """Fail-closed Operator-GO contract error."""


@dataclass(frozen=True)
class OperatorGoContractV1:
    schema_version: str
    capability_id: str
    go_id: str
    session_id: str
    venue: str
    market_type: str
    instrument_allowlist: tuple[str, ...]
    strategy_portfolio_id: str
    planned_duration_seconds: int
    observation_mode: str
    orders_authorized: bool
    broker_writes_authorized: bool
    testnet_authorized: bool
    live_authorized: bool
    auto_promotion_authorized: bool
    network_authorized: bool
    credentials_authorized: bool
    session_execution_authorized: bool
    network_scope: str
    session_execution_scope: str
    paper_execution_authorized: bool
    enabled: bool
    armed: bool
    arming_state: str
    issued_at: float
    not_before: float
    expires_at: float
    single_use: bool
    consumed: bool
    revoked: bool
    revocation_state: str
    confirm_token_binding_sha256: str
    confirm_token_hash_reference: str
    expected_repository_sha: str
    config_identity: str
    code_identity: str
    operator_identity: str
    approval_identity: str
    scope_digest: str
    fixture_non_authoritative: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["instrument_allowlist"] = list(self.instrument_allowlist)
        payload["notes"] = list(self.notes)
        return payload


@dataclass
class OperatorGoValidationResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    contract: Optional[OperatorGoContractV1] = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "contract": None if self.contract is None else self.contract.to_dict(),
            "paper_shadow_observation_authorized": False,
            "session_executed": False,
        }


def _req(raw: Mapping[str, Any], name: str) -> Any:
    if name not in raw:
        raise OperatorGoContractError(f"GO_FIELD_MISSING:{name}")
    return raw[name]


def load_operator_go_contract_dict_v1(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise OperatorGoContractError("OPERATOR_GO_CONTRACT_MISSING")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OperatorGoContractError(f"OPERATOR_GO_PARSE_ERROR:{exc}") from exc
    if not isinstance(raw, dict):
        raise OperatorGoContractError("OPERATOR_GO_NOT_OBJECT")
    assert_no_plaintext_token_fields(raw)
    unknown = sorted(set(raw) - _KNOWN_FIELDS)
    if unknown:
        raise OperatorGoContractError("GO_UNKNOWN_FIELDS:" + ",".join(unknown))
    return raw


def parse_operator_go_contract_v1(raw: Mapping[str, Any]) -> OperatorGoContractV1:
    assert_no_plaintext_token_fields(raw)
    unknown = sorted(set(raw) - _KNOWN_FIELDS)
    if unknown:
        raise OperatorGoContractError("GO_UNKNOWN_FIELDS:" + ",".join(unknown))
    allow_raw = _req(raw, "instrument_allowlist")
    if not isinstance(allow_raw, (list, tuple)):
        raise OperatorGoContractError("GO_ALLOWLIST_NOT_LIST")
    allowlist = tuple(str(x).strip() for x in allow_raw)
    notes_raw = raw.get("notes", ())
    notes = tuple(str(x) for x in notes_raw) if isinstance(notes_raw, (list, tuple)) else ()
    enabled = bool(_req(raw, "enabled"))
    armed = bool(_req(raw, "armed"))
    consumed = bool(_req(raw, "consumed"))
    revoked = bool(_req(raw, "revoked"))
    arming_state_raw = str(raw.get("arming_state") or "").strip()
    if arming_state_raw:
        arming_state = parse_arming_state(arming_state_raw).value
    else:
        arming_state = derive_arming_state(
            enabled=enabled,
            armed=armed,
            authorized=False,
            consumed=consumed,
            expired=False,
            revoked=revoked,
            rejected=False,
        ).value
    return OperatorGoContractV1(
        schema_version=str(_req(raw, "schema_version")),
        capability_id=str(_req(raw, "capability_id")),
        go_id=str(_req(raw, "go_id")),
        session_id=str(_req(raw, "session_id")),
        venue=str(_req(raw, "venue")),
        market_type=str(_req(raw, "market_type")),
        instrument_allowlist=allowlist,
        strategy_portfolio_id=str(_req(raw, "strategy_portfolio_id")),
        planned_duration_seconds=int(_req(raw, "planned_duration_seconds")),
        observation_mode=str(_req(raw, "observation_mode")),
        orders_authorized=bool(_req(raw, "orders_authorized")),
        broker_writes_authorized=bool(_req(raw, "broker_writes_authorized")),
        testnet_authorized=bool(_req(raw, "testnet_authorized")),
        live_authorized=bool(_req(raw, "live_authorized")),
        auto_promotion_authorized=bool(_req(raw, "auto_promotion_authorized")),
        network_authorized=bool(_req(raw, "network_authorized")),
        credentials_authorized=bool(_req(raw, "credentials_authorized")),
        session_execution_authorized=bool(_req(raw, "session_execution_authorized")),
        network_scope=str(raw.get("network_scope") or "").strip(),
        session_execution_scope=str(raw.get("session_execution_scope") or "").strip(),
        paper_execution_authorized=bool(raw.get("paper_execution_authorized", False)),
        enabled=enabled,
        armed=armed,
        arming_state=arming_state,
        issued_at=float(_req(raw, "issued_at")),
        not_before=float(_req(raw, "not_before")),
        expires_at=float(_req(raw, "expires_at")),
        single_use=bool(_req(raw, "single_use")),
        consumed=consumed,
        revoked=revoked,
        revocation_state=str(_req(raw, "revocation_state")),
        confirm_token_binding_sha256=str(_req(raw, "confirm_token_binding_sha256")),
        confirm_token_hash_reference=str(_req(raw, "confirm_token_hash_reference")),
        expected_repository_sha=str(_req(raw, "expected_repository_sha")),
        config_identity=str(_req(raw, "config_identity")),
        code_identity=str(_req(raw, "code_identity")),
        operator_identity=str(_req(raw, "operator_identity")),
        approval_identity=str(_req(raw, "approval_identity")),
        scope_digest=str(_req(raw, "scope_digest")),
        fixture_non_authoritative=bool(raw.get("fixture_non_authoritative", False)),
        notes=notes,
    )


def validate_operator_go_contract_v1(
    go: OperatorGoContractV1,
    *,
    prereg: Optional[SessionPreregistrationContractV1] = None,
    now_unix: Optional[float] = None,
    expected_repository_sha: Optional[str] = None,
) -> OperatorGoValidationResultV1:
    blockers: list[str] = []
    notes = [
        "OPERATOR_GO_DOES_NOT_START_SESSION",
        "OPERATOR_GO_IS_SCOPED_OBSERVATION_ONLY",
        "AUTHORIZATION_IS_NOT_EXECUTION",
    ]

    if go.schema_version != OPERATOR_GO_SCHEMA_VERSION:
        blockers.append("GO_SCHEMA_VERSION_MISMATCH")
    if go.capability_id != CAPABILITY_ID:
        blockers.append("GO_CAPABILITY_ID_MISMATCH")
    if not go.go_id.strip() or not go.session_id.strip():
        blockers.append("GO_IDS_REQUIRED")

    if go.venue.upper() != VENUE_OKX:
        blockers.append(f"VENUE_FORBIDDEN:{go.venue}")
    if go.market_type.upper() != MARKET_TYPE_FUTURES:
        blockers.append(f"MARKET_TYPE_FORBIDDEN:{go.market_type}")
    if go.observation_mode.strip().lower() != REQUIRED_MODE:
        blockers.append("OBSERVATION_MODE_REQUIRED")

    if not go.instrument_allowlist:
        blockers.append("GO_ALLOWLIST_EMPTY")
    for inst in go.instrument_allowlist:
        if _BTC_RE.search(inst):
            blockers.append(f"BTC_INSTRUMENT_FORBIDDEN:{inst}")
        upper = inst.upper()
        if any(h in upper for h in _SPOT_HINTS) and "XPERP" not in upper and "PERP" not in upper:
            blockers.append(f"SPOT_INSTRUMENT_FORBIDDEN:{inst}")

    if go.orders_authorized or go.broker_writes_authorized:
        blockers.append("ORDERS_OR_BROKER_WRITES_AUTHORIZED_FORBIDDEN")
    if go.testnet_authorized:
        blockers.append("TESTNET_AUTHORIZED_FORBIDDEN")
    if go.live_authorized:
        blockers.append("LIVE_AUTHORIZED_FORBIDDEN")
    if go.auto_promotion_authorized:
        blockers.append("AUTO_PROMOTION_AUTHORIZED_FORBIDDEN")
    if go.credentials_authorized:
        blockers.append("CREDENTIALS_AUTHORIZED_FORBIDDEN")
    if go.paper_execution_authorized:
        blockers.append("PAPER_EXECUTION_AUTHORIZED_FORBIDDEN")
    if go.network_authorized:
        if go.network_scope not in ALLOWED_NETWORK_SCOPES:
            blockers.append("NETWORK_AUTHORIZED_WITHOUT_EXACT_SCOPE")
        elif go.network_scope != NETWORK_SCOPE_OKX_EEA_FUTURES_PUBLIC_MD_OBSERVE_V1:
            blockers.append(f"NETWORK_SCOPE_FORBIDDEN:{go.network_scope}")
    elif go.network_scope:
        blockers.append("NETWORK_SCOPE_WITHOUT_NETWORK_AUTHORIZED")
    if go.session_execution_authorized:
        if go.session_execution_scope not in ALLOWED_SESSION_EXECUTION_SCOPES:
            blockers.append("SESSION_EXECUTION_AUTHORIZED_WITHOUT_EXACT_SCOPE")
        elif (
            go.session_execution_scope
            != SESSION_EXECUTION_SCOPE_PAPER_SHADOW_OBSERVATION_WALLCLOCK_V1
        ):
            blockers.append(f"SESSION_EXECUTION_SCOPE_FORBIDDEN:{go.session_execution_scope}")
    elif go.session_execution_scope:
        blockers.append("SESSION_EXECUTION_SCOPE_WITHOUT_SESSION_EXECUTION_AUTHORIZED")
    if go.session_execution_authorized and not go.network_authorized:
        blockers.append("WALLCLOCK_SESSION_REQUIRES_NETWORK_SCOPE")
    if go.network_authorized and not go.session_execution_authorized:
        blockers.append("NETWORK_SCOPE_REQUIRES_WALLCLOCK_SESSION_EXECUTION")

    if (
        go.planned_duration_seconds <= 0
        or go.planned_duration_seconds > DEFAULT_MAX_SESSION_DURATION_SECONDS
    ):
        blockers.append("GO_DURATION_OUT_OF_BOUNDS")
    ttl = go.expires_at - go.issued_at
    if ttl < MIN_TTL_SECONDS or ttl > MAX_TTL_SECONDS:
        blockers.append("GO_TTL_OUT_OF_BOUNDS")
    if go.expires_at <= go.not_before:
        blockers.append("GO_EXPIRES_BEFORE_NOT_BEFORE")
    if now_unix is not None:
        if now_unix < go.not_before:
            blockers.append("GO_NOT_YET_VALID")
        if now_unix > go.expires_at:
            blockers.append("GO_EXPIRED")

    if not go.single_use:
        blockers.append("GO_SINGLE_USE_REQUIRED")
    if go.consumed:
        blockers.append("GO_CONSUMED")
    if go.revoked or go.revocation_state.strip().lower() == "revoked":
        blockers.append("GO_REVOKED")

    if len(go.confirm_token_binding_sha256.strip()) != 64:
        blockers.append("CONFIRM_TOKEN_BINDING_HASH_INVALID")
    if not go.confirm_token_hash_reference.strip():
        blockers.append("CONFIRM_TOKEN_HASH_REFERENCE_REQUIRED")
    if (
        expected_repository_sha is not None
        and go.expected_repository_sha != expected_repository_sha
    ):
        blockers.append("GO_REPOSITORY_SHA_MISMATCH")

    try:
        state = parse_arming_state(go.arming_state)
    except Exception:  # noqa: BLE001
        blockers.append("UNKNOWN_ARMING_STATE")
        state = AuthorizationArmingState.REJECTED
    if state in {
        AuthorizationArmingState.EXPIRED,
        AuthorizationArmingState.REVOKED,
        AuthorizationArmingState.REJECTED,
        AuthorizationArmingState.CONSUMED,
    }:
        blockers.append(f"GO_ARMING_TERMINAL:{state.value}")

    if prereg is not None:
        if go.session_id != prereg.session_id:
            blockers.append("GO_SESSION_ID_MISMATCH")
        if go.venue.upper() != prereg.venue.upper():
            blockers.append("GO_VENUE_SCOPE_MISMATCH")
        if go.market_type.upper() != prereg.market_type.upper():
            blockers.append("GO_MARKET_TYPE_SCOPE_MISMATCH")
        if set(go.instrument_allowlist) - set(prereg.instrument_allowlist):
            blockers.append("GO_SCOPE_EXPANSION_INSTRUMENTS")
        if go.planned_duration_seconds > prereg.planned_duration_seconds:
            blockers.append("GO_SCOPE_EXPANSION_DURATION")
        if go.strategy_portfolio_id != prereg.strategy_portfolio_id:
            blockers.append("GO_STRATEGY_PORTFOLIO_MISMATCH")
        if go.expected_repository_sha != prereg.expected_repository_sha:
            blockers.append("GO_PREREG_SHA_MISMATCH")
        if go.config_identity != prereg.config_identity:
            blockers.append("GO_CONFIG_IDENTITY_MISMATCH")
        if go.code_identity != prereg.code_identity:
            blockers.append("GO_CODE_IDENTITY_MISMATCH")
        if go.confirm_token_binding_sha256 != prereg.confirm_token_binding_sha256:
            blockers.append("GO_CONFIRM_BINDING_MISMATCH")
        if go.scope_digest and go.scope_digest != prereg.scope_digest():
            blockers.append("GO_SCOPE_DIGEST_MISMATCH")
        if go.expires_at > prereg.expires_at:
            blockers.append("GO_SCOPE_EXPANSION_EXPIRY")

    return OperatorGoValidationResultV1(
        ok=not blockers,
        blockers=blockers,
        contract=go,
        notes=notes,
    )


def validate_operator_go_path_v1(
    path: Path,
    *,
    prereg: Optional[SessionPreregistrationContractV1] = None,
    now_unix: Optional[float] = None,
    expected_repository_sha: Optional[str] = None,
) -> OperatorGoValidationResultV1:
    try:
        raw = load_operator_go_contract_dict_v1(path)
        go = parse_operator_go_contract_v1(raw)
    except OperatorGoContractError as exc:
        return OperatorGoValidationResultV1(ok=False, blockers=[str(exc)])
    return validate_operator_go_contract_v1(
        go,
        prereg=prereg,
        now_unix=now_unix,
        expected_repository_sha=expected_repository_sha,
    )
