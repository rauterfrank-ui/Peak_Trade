"""Short-lived wallclock arming lease for Pre-Economic Zero-Order Evidence v1.

Capability: PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_V1

Two-stage authority (fail-closed):
1) Valid Operator-GO + authorization contract
2) Separate short-lived wallclock arming lease

Neither stage alone may start a production wallclock session.
This module never places orders and never grants Economic/Shadow/Paper/Testnet/Live.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.pre_economic_zero_order_evidence_session_authorization_v1 import (
    PRODUCTION_SESSION_DURATION_SECONDS,
    SESSION_CONTRACT_ID,
    AuthorizationContractV1,
    fingerprint_go_token,
)

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_V1=true"
CAPABILITY_ID = "PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_V1"
TRUTH_CLAIM = "PRE_ECONOMIC_ZERO_ORDER_WALLCLOCK_EXECUTION_ARMING_IMPLEMENTED"
SCHEMA_VERSION = "v1"
DEFAULT_MAX_ARMING_TTL_SECONDS = 900
DEFAULT_ARMING_TEMPLATE_RELPATH = (
    "config/ops/pre_economic_zero_order_wallclock_arming_lease_template_v1.json"
)
FORBIDDEN_TRUTH_CLAIMS = frozenset(
    {
        "ECONOMIC_VALIDITY_PASS",
        "PROFITABILITY_PROVEN",
        "LOSS_IMPOSSIBLE",
        "SHADOW_READY",
        "PROMOTION_AUTHORIZED",
    }
)


class WallclockArmingError(ValueError):
    """Fail-closed wallclock arming error."""


@dataclass(frozen=True)
class WallclockArmingLeaseV1:
    schema_version: str
    capability_id: str
    session_contract_id: str
    arming_id: str
    authorization_id: str
    config_digest: str
    revision_sha: str
    go_token_fingerprint: str
    issued_at: float
    not_before: float
    expires_at: float
    one_time_use: bool
    wallclock_execution_authorized: bool
    session_duration_seconds: int
    max_arming_ttl_seconds: int
    orders_allowed: bool
    broker_write: bool
    live_authorized: bool
    paper_authorized: bool
    testnet_authorized: bool
    shadow_activation_authorized: bool
    dry_run: bool
    session_execution_authorized: bool
    revocation_state: str
    authority_effect: str = "NONE"
    activation_effect: str = "NONE"
    economic_gate_effect: str = "NONE"
    truth_claim: str = TRUTH_CLAIM

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WallclockArmingValidationResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    lease: Optional[WallclockArmingLeaseV1] = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "lease": None if self.lease is None else self.lease.to_dict(),
            "truth_claim": TRUTH_CLAIM,
            "session_execution_authorized": False,
            "orders": False,
            "downstream_authority_granted": False,
        }


def _canonical_json(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_wallclock_arming_lease_v1(path: Path) -> WallclockArmingLeaseV1:
    if not path.is_file():
        raise WallclockArmingError("WALLCLOCK_ARMING_LEASE_MISSING")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WallclockArmingError(f"WALLCLOCK_ARMING_PARSE_ERROR:{exc}") from exc
    if not isinstance(raw, dict):
        raise WallclockArmingError("WALLCLOCK_ARMING_NOT_OBJECT")

    def _req(name: str) -> Any:
        if name not in raw:
            raise WallclockArmingError(f"WALLCLOCK_ARMING_FIELD_MISSING:{name}")
        return raw[name]

    lease = WallclockArmingLeaseV1(
        schema_version=str(_req("schema_version")),
        capability_id=str(_req("capability_id")),
        session_contract_id=str(_req("session_contract_id")),
        arming_id=str(_req("arming_id")),
        authorization_id=str(_req("authorization_id")),
        config_digest=str(_req("config_digest")),
        revision_sha=str(_req("revision_sha")),
        go_token_fingerprint=str(_req("go_token_fingerprint")),
        issued_at=float(_req("issued_at")),
        not_before=float(_req("not_before")),
        expires_at=float(_req("expires_at")),
        one_time_use=bool(_req("one_time_use")),
        wallclock_execution_authorized=bool(_req("wallclock_execution_authorized")),
        session_duration_seconds=int(_req("session_duration_seconds")),
        max_arming_ttl_seconds=int(_req("max_arming_ttl_seconds")),
        orders_allowed=bool(_req("orders_allowed")),
        broker_write=bool(_req("broker_write")),
        live_authorized=bool(_req("live_authorized")),
        paper_authorized=bool(_req("paper_authorized")),
        testnet_authorized=bool(_req("testnet_authorized")),
        shadow_activation_authorized=bool(_req("shadow_activation_authorized")),
        dry_run=bool(_req("dry_run")),
        session_execution_authorized=bool(_req("session_execution_authorized")),
        revocation_state=str(_req("revocation_state")).upper(),
        authority_effect=str(raw.get("authority_effect") or "NONE"),
        activation_effect=str(raw.get("activation_effect") or "NONE"),
        economic_gate_effect=str(raw.get("economic_gate_effect") or "NONE"),
        truth_claim=str(raw.get("truth_claim") or TRUTH_CLAIM),
    )
    validate_wallclock_arming_lease_invariants(lease)
    return lease


def validate_wallclock_arming_lease_invariants(lease: WallclockArmingLeaseV1) -> None:
    if lease.schema_version != SCHEMA_VERSION:
        raise WallclockArmingError("WALLCLOCK_ARMING_SCHEMA_MISMATCH")
    if lease.capability_id != CAPABILITY_ID:
        raise WallclockArmingError("WALLCLOCK_ARMING_CAPABILITY_MISMATCH")
    if lease.session_contract_id != SESSION_CONTRACT_ID:
        raise WallclockArmingError("WALLCLOCK_ARMING_SESSION_CONTRACT_MISMATCH")
    if lease.truth_claim != TRUTH_CLAIM:
        raise WallclockArmingError("WALLCLOCK_ARMING_TRUTH_CLAIM_MISMATCH")
    if lease.truth_claim in FORBIDDEN_TRUTH_CLAIMS:
        raise WallclockArmingError("FORBIDDEN_TRUTH_CLAIM")
    if not lease.one_time_use:
        raise WallclockArmingError("WALLCLOCK_ARMING_ONE_TIME_USE_REQUIRED")
    if lease.session_duration_seconds != PRODUCTION_SESSION_DURATION_SECONDS:
        raise WallclockArmingError("WALLCLOCK_ARMING_DURATION_MUST_BE_21600")
    if lease.max_arming_ttl_seconds <= 0:
        raise WallclockArmingError("WALLCLOCK_ARMING_TTL_INVALID")
    if lease.max_arming_ttl_seconds > DEFAULT_MAX_ARMING_TTL_SECONDS:
        raise WallclockArmingError("WALLCLOCK_ARMING_TTL_EXCEEDS_MAX")
    if lease.expires_at <= lease.not_before:
        raise WallclockArmingError("WALLCLOCK_ARMING_EXPIRY_INVALID")
    ttl = lease.expires_at - lease.not_before
    if ttl > float(lease.max_arming_ttl_seconds) + 1e-9:
        raise WallclockArmingError("WALLCLOCK_ARMING_WINDOW_EXCEEDS_TTL")
    if lease.orders_allowed is not False:
        raise WallclockArmingError("WALLCLOCK_ARMING_ORDERS_MUST_BE_FALSE")
    if lease.broker_write is not False:
        raise WallclockArmingError("WALLCLOCK_ARMING_BROKER_WRITE_MUST_BE_FALSE")
    if lease.live_authorized is not False:
        raise WallclockArmingError("WALLCLOCK_ARMING_LIVE_MUST_BE_FALSE")
    if lease.paper_authorized is not False:
        raise WallclockArmingError("WALLCLOCK_ARMING_PAPER_MUST_BE_FALSE")
    if lease.testnet_authorized is not False:
        raise WallclockArmingError("WALLCLOCK_ARMING_TESTNET_MUST_BE_FALSE")
    if lease.shadow_activation_authorized is not False:
        raise WallclockArmingError("WALLCLOCK_ARMING_SHADOW_MUST_BE_FALSE")
    if lease.authority_effect != "NONE":
        raise WallclockArmingError("WALLCLOCK_ARMING_AUTHORITY_EFFECT_MUST_BE_NONE")
    if lease.activation_effect != "NONE":
        raise WallclockArmingError("WALLCLOCK_ARMING_ACTIVATION_EFFECT_MUST_BE_NONE")
    if lease.economic_gate_effect != "NONE":
        raise WallclockArmingError("WALLCLOCK_ARMING_ECONOMIC_GATE_EFFECT_MUST_BE_NONE")
    if len(lease.go_token_fingerprint) != 64:
        raise WallclockArmingError("WALLCLOCK_ARMING_GO_FINGERPRINT_INVALID")


def validate_wallclock_arming_against_go_v1(
    *,
    lease: WallclockArmingLeaseV1,
    contract: AuthorizationContractV1,
    go_token: Optional[str],
    now: Optional[float] = None,
    expected_config_digest: Optional[str] = None,
    expected_revision_sha: Optional[str] = None,
    consumption_store: Optional[Path] = None,
    require_production_flags: bool = True,
) -> WallclockArmingValidationResultV1:
    """Stage-2 validation. Requires stage-1 GO binding to match the lease."""

    blockers: list[str] = []
    notes = [
        "TWO_STAGE_AUTHORITY_REQUIRED",
        "OPERATOR_GO_ALONE_DOES_NOT_START_SESSION",
        "ARMING_ALONE_DOES_NOT_START_SESSION",
        "ORDERS=false",
        "DOWNSTREAM_AUTHORITY_GRANTED=false",
        f"TRUTH_CLAIM={TRUTH_CLAIM}",
        "ECONOMIC_VALIDITY_PASS=false",
        "SHADOW_READY=false",
        "PROMOTION_AUTHORIZED=false",
    ]
    ts = float(time.time() if now is None else now)

    try:
        validate_wallclock_arming_lease_invariants(lease)
    except WallclockArmingError as exc:
        blockers.append(str(exc))

    if lease.authorization_id != contract.authorization_id:
        blockers.append("ARMING_AUTHORIZATION_ID_MISMATCH")
    if lease.config_digest != contract.config_digest:
        blockers.append("ARMING_CONFIG_DIGEST_MISMATCH")
    if lease.revision_sha != contract.revision_sha:
        blockers.append("ARMING_REVISION_SHA_MISMATCH")
    if expected_config_digest is not None and lease.config_digest != expected_config_digest:
        blockers.append("ARMING_EXPECTED_CONFIG_DIGEST_MISMATCH")
    if expected_revision_sha is not None and lease.revision_sha != expected_revision_sha:
        blockers.append("ARMING_EXPECTED_REVISION_SHA_MISMATCH")

    token = (go_token or "").strip()
    if not token:
        blockers.append("OPERATOR_GO_TOKEN_ABSENT")
    else:
        fp = fingerprint_go_token(token)
        if fp != lease.go_token_fingerprint:
            blockers.append("ARMING_GO_FINGERPRINT_MISMATCH")

    if lease.revocation_state not in {"ACTIVE", "NOT_REVOKED"}:
        blockers.append(f"WALLCLOCK_ARMING_REVOKED:{lease.revocation_state}")
    if ts < lease.not_before:
        blockers.append("WALLCLOCK_ARMING_NOT_YET_VALID")
    if ts > lease.expires_at:
        blockers.append("WALLCLOCK_ARMING_EXPIRED")

    if require_production_flags:
        if not lease.wallclock_execution_authorized:
            blockers.append("WALLCLOCK_EXECUTION_NOT_AUTHORIZED_ON_LEASE")
        if lease.dry_run:
            blockers.append("WALLCLOCK_ARMING_REQUIRES_DRY_RUN_FALSE")
        if not lease.session_execution_authorized:
            blockers.append("WALLCLOCK_ARMING_SESSION_EXECUTION_NOT_AUTHORIZED")

    if consumption_store is not None and lease.one_time_use:
        if _is_arming_consumed(consumption_store, lease.arming_id):
            blockers.append("WALLCLOCK_ARMING_ALREADY_CONSUMED")

    return WallclockArmingValidationResultV1(
        ok=not blockers,
        blockers=blockers,
        lease=lease,
        notes=notes,
    )


def _is_arming_consumed(store: Path, arming_id: str) -> bool:
    return (store / f"{arming_id}.consumed.json").is_file()


def consume_wallclock_arming_one_time_v1(
    *,
    store: Path,
    lease: WallclockArmingLeaseV1,
    now: Optional[float] = None,
) -> Path:
    store.mkdir(parents=True, exist_ok=True)
    target = store / f"{lease.arming_id}.consumed.json"
    if target.exists():
        raise WallclockArmingError("WALLCLOCK_ARMING_ALREADY_CONSUMED")
    payload = {
        "arming_id": lease.arming_id,
        "authorization_id": lease.authorization_id,
        "consumed_at": float(time.time() if now is None else now),
        "go_token_fingerprint": lease.go_token_fingerprint,
        "config_digest": lease.config_digest,
        "revision_sha": lease.revision_sha,
        "one_time_use": True,
        "revocation_state": "CONSUMED",
        "truth_claim": TRUTH_CLAIM,
    }
    text = _canonical_json(payload)
    fd, tmp = tempfile.mkstemp(dir=store, prefix=".tmp_arming_consume_", suffix=".partial")
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
    return target


def build_wallclock_arming_lease_dict_v1(
    *,
    arming_id: str,
    authorization_id: str,
    config_digest: str,
    revision_sha: str,
    go_token: str,
    issued_at: Optional[float] = None,
    not_before: Optional[float] = None,
    expires_at: Optional[float] = None,
    max_arming_ttl_seconds: int = DEFAULT_MAX_ARMING_TTL_SECONDS,
    wallclock_execution_authorized: bool = False,
    dry_run: bool = True,
    session_execution_authorized: bool = False,
    revocation_state: str = "ACTIVE",
) -> dict[str, Any]:
    """Helper for tests / operator materialization. Never persists the raw GO token."""

    now = time.time()
    issued = float(now if issued_at is None else issued_at)
    nbf = float(issued if not_before is None else not_before)
    ttl = min(int(max_arming_ttl_seconds), DEFAULT_MAX_ARMING_TTL_SECONDS)
    exp = float((nbf + float(ttl)) if expires_at is None else expires_at)
    return {
        "schema_version": SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "session_contract_id": SESSION_CONTRACT_ID,
        "arming_id": arming_id,
        "authorization_id": authorization_id,
        "config_digest": config_digest,
        "revision_sha": revision_sha,
        "go_token_fingerprint": fingerprint_go_token(go_token),
        "issued_at": issued,
        "not_before": nbf,
        "expires_at": exp,
        "one_time_use": True,
        "wallclock_execution_authorized": wallclock_execution_authorized,
        "session_duration_seconds": PRODUCTION_SESSION_DURATION_SECONDS,
        "max_arming_ttl_seconds": ttl,
        "orders_allowed": False,
        "broker_write": False,
        "live_authorized": False,
        "paper_authorized": False,
        "testnet_authorized": False,
        "shadow_activation_authorized": False,
        "dry_run": dry_run,
        "session_execution_authorized": session_execution_authorized,
        "revocation_state": revocation_state,
        "authority_effect": "NONE",
        "activation_effect": "NONE",
        "economic_gate_effect": "NONE",
        "truth_claim": TRUTH_CLAIM,
    }


def wallclock_arming_defaults_blocked_v1() -> dict[str, Any]:
    return {
        "enabled": False,
        "armed": False,
        "dry_run": True,
        "session_execution_authorized": False,
        "wallclock_execution_authorized": False,
        "orders": False,
        "broker_write": False,
        "live_authorized": False,
        "paper_authorized": False,
        "testnet_authorized": False,
        "shadow_activation_authorized": False,
        "truth_claim": TRUTH_CLAIM,
        "forbidden_truth_claims": sorted(FORBIDDEN_TRUTH_CLAIMS),
    }
