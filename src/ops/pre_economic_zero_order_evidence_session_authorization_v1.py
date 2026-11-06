"""Authorization + Operator-GO contract for Pre-Economic Zero-Order Evidence v1.

Capability: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION

This module defines a fail-closed, one-time, time-bounded authorization contract
for a *future* 6h zero-order observation session. It never starts a session,
never grants Shadow/Paper/Testnet/Live/Economic/Order authority, and never
commits GO token secrets.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION=true"
CAPABILITY_ID = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION"
SESSION_CONTRACT_ID = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1"
SCHEMA_VERSION = "v1"
VENUE_OKX = "OKX"
MARKET_TYPE_SWAP = "SWAP"
MARKET_TYPE_FUTURES = "FUTURES"
ALLOWED_MARKET_TYPES = frozenset({MARKET_TYPE_SWAP, MARKET_TYPE_FUTURES})
PRODUCTION_SESSION_DURATION_SECONDS = 21600
DEFAULT_MAX_CLOCK_SKEW_SECONDS = 30
CANONICAL_GO_TOKEN_PREFIX = "GO_PEZ_SESSION_AUTH_EXEC_V1_"

_BTC_RE = re.compile(r"(^|[-_/])BTC([-_/]|$)", re.IGNORECASE)
_SPOT_HINTS = frozenset({"SPOT", "SPOT_MARGIN", "CASH"})
_SENSITIVE = frozenset(
    {"secret", "token", "password", "api_key", "apikey", "passphrase", "credential"}
)


class AuthorizationContractError(ValueError):
    """Fail-closed authorization / GO validation error."""


@dataclass(frozen=True)
class AuthorizationContractV1:
    schema_version: str
    capability_id: str
    session_contract_id: str
    authorization_id: str
    venue: str
    market_type: str
    instrument_allowlist: tuple[str, ...]
    btc_forbidden: bool
    spot_forbidden: bool
    zero_order_only: bool
    orders_allowed: bool
    session_duration_seconds: int
    session_execution_authorized: bool
    enabled: bool
    armed: bool
    dry_run: bool
    issued_at: float
    not_before: float
    expires_at: float
    one_time_use: bool
    config_digest: str
    revision_sha: str
    go_token_binding_sha256: str
    revocation_state: str
    revocation_reference: str
    max_clock_skew_seconds: float
    host_binding: str
    environment_binding: str
    authority_effect: str = "NONE"
    activation_effect: str = "NONE"
    economic_gate_effect: str = "NONE"
    consumer_eligibility: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["instrument_allowlist"] = list(self.instrument_allowlist)
        return payload


@dataclass
class AuthorizationValidationResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    contract: Optional[AuthorizationContractV1] = None
    go_token_fingerprint: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "go_token_fingerprint": self.go_token_fingerprint,
            "notes": list(self.notes),
            "contract": None if self.contract is None else self.contract.to_dict(),
            "session_execution_authorized": False,
            "operator_go_granted": False,
            "authority_effect": "NONE",
            "activation_effect": "NONE",
            "economic_gate_effect": "NONE",
        }


def _canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fingerprint_go_token(token: str) -> str:
    """Non-reversible fingerprint; never persist the raw token."""

    return sha256_text(f"PEZ_GO_FP_V1|{token}")


def compute_go_token_binding_sha256(
    *,
    authorization_id: str,
    config_digest: str,
    revision_sha: str,
    go_token: str,
) -> str:
    material = "|".join(
        [
            "PEZ_GO_BINDING_V1",
            authorization_id,
            config_digest,
            revision_sha,
            go_token,
        ]
    )
    return sha256_text(material)


def assert_instrument_allowed(
    *,
    instrument_id: str,
    allowlist: tuple[str, ...],
    btc_forbidden: bool = True,
    spot_forbidden: bool = True,
    market_type: str = MARKET_TYPE_SWAP,
) -> None:
    inst = str(instrument_id or "").strip()
    if not inst:
        raise AuthorizationContractError("INSTRUMENT_EMPTY")
    if btc_forbidden and _BTC_RE.search(inst):
        raise AuthorizationContractError(f"BTC_INSTRUMENT_FORBIDDEN:{inst}")
    if spot_forbidden and (market_type.upper() in _SPOT_HINTS or inst.upper().endswith("-SPOT")):
        raise AuthorizationContractError(f"SPOT_INSTRUMENT_FORBIDDEN:{inst}")
    if market_type.upper() not in ALLOWED_MARKET_TYPES:
        raise AuthorizationContractError(f"MARKET_TYPE_FORBIDDEN:{market_type}")
    if inst not in allowlist:
        raise AuthorizationContractError(f"INSTRUMENT_NOT_ALLOWLISTED:{inst}")


def load_authorization_contract_v1(
    path: Path,
    *,
    expected_config_digest: Optional[str] = None,
    expected_revision_sha: Optional[str] = None,
) -> AuthorizationContractV1:
    if not path.is_file():
        raise AuthorizationContractError("AUTHORIZATION_CONTRACT_MISSING")
    raw_text = path.read_text(encoding="utf-8")
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise AuthorizationContractError(f"AUTHORIZATION_CONTRACT_PARSE_ERROR:{exc}") from exc
    if not isinstance(raw, dict):
        raise AuthorizationContractError("AUTHORIZATION_CONTRACT_NOT_OBJECT")

    # Secrets must never appear in committed contracts.
    for key in raw:
        key_l = str(key).lower()
        if any(frag in key_l for frag in _SENSITIVE) and key_l not in {
            "go_token_binding_sha256",
        }:
            raise AuthorizationContractError(f"SENSITIVE_FIELD_FORBIDDEN:{key}")

    def _req(name: str) -> Any:
        if name not in raw:
            raise AuthorizationContractError(f"AUTHORIZATION_FIELD_MISSING:{name}")
        return raw[name]

    allowlist_raw = _req("instrument_allowlist")
    if not isinstance(allowlist_raw, list) or not allowlist_raw:
        raise AuthorizationContractError("INSTRUMENT_ALLOWLIST_EMPTY")
    allowlist = tuple(str(x) for x in allowlist_raw)

    contract = AuthorizationContractV1(
        schema_version=str(_req("schema_version")),
        capability_id=str(_req("capability_id")),
        session_contract_id=str(_req("session_contract_id")),
        authorization_id=str(_req("authorization_id")),
        venue=str(_req("venue")).upper(),
        market_type=str(_req("market_type")).upper(),
        instrument_allowlist=allowlist,
        btc_forbidden=bool(_req("btc_forbidden")),
        spot_forbidden=bool(_req("spot_forbidden")),
        zero_order_only=bool(_req("zero_order_only")),
        orders_allowed=bool(_req("orders_allowed")),
        session_duration_seconds=int(_req("session_duration_seconds")),
        session_execution_authorized=bool(_req("session_execution_authorized")),
        enabled=bool(_req("enabled")),
        armed=bool(_req("armed")),
        dry_run=bool(_req("dry_run")),
        issued_at=float(_req("issued_at")),
        not_before=float(_req("not_before")),
        expires_at=float(_req("expires_at")),
        one_time_use=bool(_req("one_time_use")),
        config_digest=str(_req("config_digest")),
        revision_sha=str(_req("revision_sha")),
        go_token_binding_sha256=str(_req("go_token_binding_sha256")),
        revocation_state=str(_req("revocation_state")).upper(),
        revocation_reference=str(raw.get("revocation_reference") or ""),
        max_clock_skew_seconds=float(
            raw.get("max_clock_skew_seconds", DEFAULT_MAX_CLOCK_SKEW_SECONDS)
        ),
        host_binding=str(raw.get("host_binding") or ""),
        environment_binding=str(raw.get("environment_binding") or ""),
        authority_effect=str(raw.get("authority_effect") or "NONE"),
        activation_effect=str(raw.get("activation_effect") or "NONE"),
        economic_gate_effect=str(raw.get("economic_gate_effect") or "NONE"),
        consumer_eligibility=bool(raw.get("consumer_eligibility", False)),
    )
    validate_authorization_contract_invariants(
        contract,
        expected_config_digest=expected_config_digest,
        expected_revision_sha=expected_revision_sha,
    )
    return contract


def validate_authorization_contract_invariants(
    contract: AuthorizationContractV1,
    *,
    expected_config_digest: Optional[str] = None,
    expected_revision_sha: Optional[str] = None,
) -> None:
    if contract.schema_version != SCHEMA_VERSION:
        raise AuthorizationContractError("AUTHORIZATION_SCHEMA_MISMATCH")
    if contract.capability_id != CAPABILITY_ID:
        raise AuthorizationContractError("AUTHORIZATION_CAPABILITY_MISMATCH")
    if contract.session_contract_id != SESSION_CONTRACT_ID:
        raise AuthorizationContractError("AUTHORIZATION_SESSION_CONTRACT_MISMATCH")
    if contract.venue != VENUE_OKX:
        raise AuthorizationContractError(f"VENUE_FORBIDDEN:{contract.venue}")
    if contract.market_type not in ALLOWED_MARKET_TYPES:
        raise AuthorizationContractError(f"MARKET_TYPE_FORBIDDEN:{contract.market_type}")
    if not contract.btc_forbidden:
        raise AuthorizationContractError("BTC_FORBIDDEN_MUST_BE_TRUE")
    if not contract.spot_forbidden:
        raise AuthorizationContractError("SPOT_FORBIDDEN_MUST_BE_TRUE")
    if not contract.zero_order_only:
        raise AuthorizationContractError("ZERO_ORDER_ONLY_MUST_BE_TRUE")
    if contract.orders_allowed is not False:
        raise AuthorizationContractError("ORDERS_ALLOWED_MUST_BE_FALSE")
    if contract.session_duration_seconds != PRODUCTION_SESSION_DURATION_SECONDS:
        raise AuthorizationContractError("SESSION_DURATION_MUST_BE_21600")
    if contract.authority_effect != "NONE":
        raise AuthorizationContractError("AUTHORITY_EFFECT_MUST_BE_NONE")
    if contract.activation_effect != "NONE":
        raise AuthorizationContractError("ACTIVATION_EFFECT_MUST_BE_NONE")
    if contract.economic_gate_effect != "NONE":
        raise AuthorizationContractError("ECONOMIC_GATE_EFFECT_MUST_BE_NONE")
    if contract.consumer_eligibility is not False:
        raise AuthorizationContractError("CONSUMER_ELIGIBILITY_MUST_BE_FALSE")
    if not contract.one_time_use:
        raise AuthorizationContractError("ONE_TIME_USE_MUST_BE_TRUE")
    if contract.expires_at <= contract.not_before:
        raise AuthorizationContractError("AUTHORIZATION_EXPIRY_INVALID")
    if contract.issued_at > contract.expires_at:
        raise AuthorizationContractError("AUTHORIZATION_ISSUED_AFTER_EXPIRY")
    if len(contract.go_token_binding_sha256) != 64:
        raise AuthorizationContractError("GO_TOKEN_BINDING_DIGEST_INVALID")
    if expected_config_digest is not None and contract.config_digest != expected_config_digest:
        raise AuthorizationContractError("CONFIG_DIGEST_MISMATCH")
    if expected_revision_sha is not None and contract.revision_sha != expected_revision_sha:
        raise AuthorizationContractError("REVISION_SHA_MISMATCH")
    for inst in contract.instrument_allowlist:
        assert_instrument_allowed(
            instrument_id=inst,
            allowlist=contract.instrument_allowlist,
            btc_forbidden=True,
            spot_forbidden=True,
            market_type=contract.market_type,
        )


def collect_authorization_binding_blockers(
    contract: AuthorizationContractV1,
    *,
    expected_config_digest: Optional[str] = None,
    expected_revision_sha: Optional[str] = None,
) -> list[str]:
    blockers: list[str] = []
    try:
        validate_authorization_contract_invariants(contract)
    except AuthorizationContractError as exc:
        blockers.append(str(exc))
    if expected_config_digest is not None and contract.config_digest != expected_config_digest:
        blockers.append("CONFIG_DIGEST_MISMATCH")
    if expected_revision_sha is not None and contract.revision_sha != expected_revision_sha:
        blockers.append("REVISION_SHA_MISMATCH")
    return blockers


def current_host_binding() -> str:
    return socket.gethostname()


def current_environment_binding() -> str:
    return os.environ.get("PEZ_ENVIRONMENT_BINDING", "UNSET")


def validate_operator_go_and_contract_v1(
    *,
    contract: AuthorizationContractV1,
    go_token: Optional[str],
    now: Optional[float] = None,
    expected_config_digest: Optional[str] = None,
    expected_revision_sha: Optional[str] = None,
    require_enabled_armed_authorized: bool = True,
    host_binding: Optional[str] = None,
    environment_binding: Optional[str] = None,
    consumption_store: Optional[Path] = None,
) -> AuthorizationValidationResultV1:
    """Validate contract + GO. Never grants downstream activation."""

    blockers: list[str] = []
    notes: list[str] = [
        "AUTHORITY_EFFECT=NONE",
        "ACTIVATION_EFFECT=NONE",
        "ECONOMIC_GATE_EFFECT=NONE",
        "OPERATOR_GO_DOES_NOT_START_SESSION",
        "DOWNSTREAM_GATES_REMAIN_BLOCKED",
    ]
    ts = float(time.time() if now is None else now)
    fp = ""

    try:
        validate_authorization_contract_invariants(contract)
    except AuthorizationContractError as exc:
        blockers.append(str(exc))
    if expected_config_digest is not None and contract.config_digest != expected_config_digest:
        if "CONFIG_DIGEST_MISMATCH" not in blockers:
            blockers.append("CONFIG_DIGEST_MISMATCH")
    if expected_revision_sha is not None and contract.revision_sha != expected_revision_sha:
        if "REVISION_SHA_MISMATCH" not in blockers:
            blockers.append("REVISION_SHA_MISMATCH")

    if contract.revocation_state not in {"ACTIVE", "NOT_REVOKED"}:
        blockers.append(f"AUTHORIZATION_REVOKED:{contract.revocation_state}")

    skew = float(contract.max_clock_skew_seconds)
    if ts + skew < contract.not_before:
        blockers.append("AUTHORIZATION_NOT_YET_VALID")
    if ts - skew > contract.expires_at:
        blockers.append("AUTHORIZATION_EXPIRED")

    if require_enabled_armed_authorized:
        if not contract.enabled:
            blockers.append("AUTHORIZATION_NOT_ENABLED")
        if not contract.armed:
            blockers.append("AUTHORIZATION_NOT_ARMED")
        if not contract.session_execution_authorized:
            blockers.append("SESSION_EXECUTION_NOT_AUTHORIZED")
        if contract.dry_run:
            blockers.append("PRODUCTION_REQUIRES_DRY_RUN_FALSE")

    if contract.host_binding:
        actual_host = host_binding if host_binding is not None else current_host_binding()
        if actual_host != contract.host_binding:
            blockers.append("HOST_BINDING_MISMATCH")
    if contract.environment_binding:
        actual_env = (
            environment_binding
            if environment_binding is not None
            else current_environment_binding()
        )
        if actual_env != contract.environment_binding:
            blockers.append("ENVIRONMENT_BINDING_MISMATCH")

    token = (go_token or "").strip()
    if not token:
        blockers.append("OPERATOR_GO_TOKEN_ABSENT")
    else:
        if not token.startswith(CANONICAL_GO_TOKEN_PREFIX):
            blockers.append("OPERATOR_GO_TOKEN_PREFIX_INVALID")
        fp = fingerprint_go_token(token)
        expected = compute_go_token_binding_sha256(
            authorization_id=contract.authorization_id,
            config_digest=contract.config_digest,
            revision_sha=contract.revision_sha,
            go_token=token,
        )
        if expected != contract.go_token_binding_sha256:
            blockers.append("OPERATOR_GO_TOKEN_BINDING_MISMATCH")

        if consumption_store is not None and contract.one_time_use:
            if _is_authorization_consumed(consumption_store, contract.authorization_id):
                blockers.append("AUTHORIZATION_ALREADY_CONSUMED")

    ok = not blockers
    return AuthorizationValidationResultV1(
        ok=ok,
        blockers=blockers,
        contract=contract,
        go_token_fingerprint=fp,
        notes=notes,
    )


def _is_authorization_consumed(store: Path, authorization_id: str) -> bool:
    path = store / f"{authorization_id}.consumed.json"
    return path.is_file()


def consume_authorization_one_time_v1(
    *,
    store: Path,
    contract: AuthorizationContractV1,
    go_token_fingerprint: str,
    revision_sha: str,
    now: Optional[float] = None,
) -> Path:
    """Atomically mark authorization as consumed (one-time use)."""

    store.mkdir(parents=True, exist_ok=True)
    target = store / f"{contract.authorization_id}.consumed.json"
    if target.exists():
        raise AuthorizationContractError("AUTHORIZATION_ALREADY_CONSUMED")
    payload = {
        "authorization_id": contract.authorization_id,
        "consumed_at": float(time.time() if now is None else now),
        "go_token_fingerprint": go_token_fingerprint,
        "revision_sha": revision_sha,
        "config_digest": contract.config_digest,
        "one_time_use": True,
        "revocation_state": "CONSUMED",
    }
    text = _canonical_json(payload)
    fd, tmp = tempfile.mkstemp(dir=store, prefix=".tmp_consume_", suffix=".partial")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    except Exception:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise
    if not target.is_file():
        raise AuthorizationContractError("AUTHORIZATION_CONSUME_FAILED")
    return target


def build_authorization_contract_dict_v1(
    *,
    authorization_id: str,
    config_digest: str,
    revision_sha: str,
    go_token: str,
    instrument_allowlist: tuple[str, ...] = ("ETH-USDT-SWAP",),
    enabled: bool = False,
    armed: bool = False,
    session_execution_authorized: bool = False,
    dry_run: bool = True,
    issued_at: Optional[float] = None,
    not_before: Optional[float] = None,
    expires_at: Optional[float] = None,
    revocation_state: str = "ACTIVE",
    host_binding: str = "",
    environment_binding: str = "",
    market_type: str = MARKET_TYPE_SWAP,
) -> dict[str, Any]:
    """Helper for tests / offline materialization. Never commits the GO token."""

    now = time.time()
    issued = float(now if issued_at is None else issued_at)
    nbf = float(issued if not_before is None else not_before)
    exp = float((issued + 3600.0) if expires_at is None else expires_at)
    binding = compute_go_token_binding_sha256(
        authorization_id=authorization_id,
        config_digest=config_digest,
        revision_sha=revision_sha,
        go_token=go_token,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "session_contract_id": SESSION_CONTRACT_ID,
        "authorization_id": authorization_id,
        "venue": VENUE_OKX,
        "market_type": market_type,
        "instrument_allowlist": list(instrument_allowlist),
        "btc_forbidden": True,
        "spot_forbidden": True,
        "zero_order_only": True,
        "orders_allowed": False,
        "session_duration_seconds": PRODUCTION_SESSION_DURATION_SECONDS,
        "session_execution_authorized": session_execution_authorized,
        "enabled": enabled,
        "armed": armed,
        "dry_run": dry_run,
        "issued_at": issued,
        "not_before": nbf,
        "expires_at": exp,
        "one_time_use": True,
        "config_digest": config_digest,
        "revision_sha": revision_sha,
        "go_token_binding_sha256": binding,
        "revocation_state": revocation_state,
        "revocation_reference": "",
        "max_clock_skew_seconds": DEFAULT_MAX_CLOCK_SKEW_SECONDS,
        "host_binding": host_binding,
        "environment_binding": environment_binding,
        "authority_effect": "NONE",
        "activation_effect": "NONE",
        "economic_gate_effect": "NONE",
        "consumer_eligibility": False,
    }
