"""Versioned session preregistration contract (non-executing, non-authorizing)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    ALLOWED_PREREG_NETWORK_POLICIES,
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    MARKET_TYPE_FUTURES,
    MAX_TTL_SECONDS,
    MIN_TTL_SECONDS,
    NETWORK_SCOPE_OKX_EEA_FUTURES_PUBLIC_MD_OBSERVE_V1,
    OBSERVATION_CAPABILITY_ID,
    PREREGISTRATION_SCHEMA_VERSION,
    REQUIRED_MODE,
    SESSION_EXECUTION_SCOPE_PAPER_SHADOW_OBSERVATION_WALLCLOCK_V1,
    VENUE_OKX,
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
        "contract_version",
        "schema_version",
        "capability_id",
        "session_id",
        "purpose",
        "venue",
        "market_type",
        "instrument_allowlist",
        "instrument_denylist",
        "strategy_portfolio_id",
        "strategy_component_identities",
        "config_identity",
        "code_identity",
        "expected_repository_sha",
        "observation_mode",
        "no_order_invariant",
        "network_policy",
        "network_scope",
        "session_execution_scope",
        "credential_policy",
        "planned_duration_seconds",
        "earliest_start",
        "expires_at",
        "evidence_root",
        "evidence_target_paths",
        "required_evidence_schema_versions",
        "killstate_policy",
        "timeout_policy",
        "lock_policy",
        "retry_policy",
        "no_auto_promotion",
        "no_testnet",
        "no_live",
        "no_orders",
        "operator_identity",
        "approval_identity",
        "confirm_token_hash_reference",
        "confirm_token_binding_sha256",
        "enabled",
        "armed",
        "arming_state",
        "single_use",
        "consumed",
        "revoked",
        "revocation_state",
        "fixture_non_authoritative",
        "notes",
    }
)


class PreregistrationContractError(ValueError):
    """Fail-closed preregistration error."""


@dataclass(frozen=True)
class SessionPreregistrationContractV1:
    contract_version: str
    schema_version: str
    capability_id: str
    session_id: str
    purpose: str
    venue: str
    market_type: str
    instrument_allowlist: tuple[str, ...]
    instrument_denylist: tuple[str, ...]
    strategy_portfolio_id: str
    strategy_component_identities: tuple[str, ...]
    config_identity: str
    code_identity: str
    expected_repository_sha: str
    observation_mode: str
    no_order_invariant: bool
    network_policy: str
    network_scope: str
    session_execution_scope: str
    credential_policy: str
    planned_duration_seconds: int
    earliest_start: float
    expires_at: float
    evidence_root: str
    evidence_target_paths: tuple[str, ...]
    required_evidence_schema_versions: tuple[str, ...]
    killstate_policy: str
    timeout_policy: str
    lock_policy: str
    retry_policy: str
    no_auto_promotion: bool
    no_testnet: bool
    no_live: bool
    no_orders: bool
    operator_identity: str
    approval_identity: str
    confirm_token_hash_reference: str
    confirm_token_binding_sha256: str
    enabled: bool
    armed: bool
    arming_state: str
    single_use: bool
    consumed: bool
    revoked: bool
    revocation_state: str
    fixture_non_authoritative: bool = False
    notes: tuple[str, ...] = ()

    def scope_digest(self) -> str:
        material = "|".join(
            [
                self.session_id,
                self.venue,
                self.market_type,
                ",".join(self.instrument_allowlist),
                ",".join(self.instrument_denylist),
                self.strategy_portfolio_id,
                ",".join(self.strategy_component_identities),
                self.config_identity,
                self.code_identity,
                self.expected_repository_sha,
                self.observation_mode,
                str(self.planned_duration_seconds),
                f"{self.earliest_start:.6f}",
                f"{self.expires_at:.6f}",
                self.evidence_root,
            ]
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "instrument_allowlist",
            "instrument_denylist",
            "strategy_component_identities",
            "evidence_target_paths",
            "required_evidence_schema_versions",
            "notes",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass
class PreregistrationValidationResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    contract: Optional[SessionPreregistrationContractV1] = None
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
        raise PreregistrationContractError(f"PREREG_FIELD_MISSING:{name}")
    return raw[name]


def _as_str_tuple(value: Any, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise PreregistrationContractError(f"PREREG_FIELD_NOT_LIST:{field_name}")
    out = tuple(str(x).strip() for x in value)
    if any(not x for x in out):
        raise PreregistrationContractError(f"PREREG_FIELD_EMPTY_ENTRY:{field_name}")
    return out


def load_preregistration_contract_dict_v1(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PreregistrationContractError("PREREGISTRATION_CONTRACT_MISSING")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreregistrationContractError(f"PREREGISTRATION_PARSE_ERROR:{exc}") from exc
    if not isinstance(raw, dict):
        raise PreregistrationContractError("PREREGISTRATION_NOT_OBJECT")
    assert_no_plaintext_token_fields(raw)
    unknown = sorted(set(raw) - _KNOWN_FIELDS)
    if unknown:
        raise PreregistrationContractError("PREREG_UNKNOWN_FIELDS:" + ",".join(unknown))
    return raw


def parse_preregistration_contract_v1(raw: Mapping[str, Any]) -> SessionPreregistrationContractV1:
    assert_no_plaintext_token_fields(raw)
    unknown = sorted(set(raw) - _KNOWN_FIELDS)
    if unknown:
        raise PreregistrationContractError("PREREG_UNKNOWN_FIELDS:" + ",".join(unknown))

    allowlist = _as_str_tuple(_req(raw, "instrument_allowlist"), field_name="instrument_allowlist")
    denylist = _as_str_tuple(raw.get("instrument_denylist", ()), field_name="instrument_denylist")
    components = _as_str_tuple(
        _req(raw, "strategy_component_identities"),
        field_name="strategy_component_identities",
    )
    evidence_paths = _as_str_tuple(
        _req(raw, "evidence_target_paths"), field_name="evidence_target_paths"
    )
    evidence_schemas = _as_str_tuple(
        _req(raw, "required_evidence_schema_versions"),
        field_name="required_evidence_schema_versions",
    )
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

    return SessionPreregistrationContractV1(
        contract_version=str(_req(raw, "contract_version")),
        schema_version=str(_req(raw, "schema_version")),
        capability_id=str(_req(raw, "capability_id")),
        session_id=str(_req(raw, "session_id")),
        purpose=str(_req(raw, "purpose")),
        venue=str(_req(raw, "venue")),
        market_type=str(_req(raw, "market_type")),
        instrument_allowlist=allowlist,
        instrument_denylist=denylist,
        strategy_portfolio_id=str(_req(raw, "strategy_portfolio_id")),
        strategy_component_identities=components,
        config_identity=str(_req(raw, "config_identity")),
        code_identity=str(_req(raw, "code_identity")),
        expected_repository_sha=str(_req(raw, "expected_repository_sha")),
        observation_mode=str(_req(raw, "observation_mode")),
        no_order_invariant=bool(_req(raw, "no_order_invariant")),
        network_policy=str(_req(raw, "network_policy")),
        network_scope=str(raw.get("network_scope") or "").strip(),
        session_execution_scope=str(raw.get("session_execution_scope") or "").strip(),
        credential_policy=str(_req(raw, "credential_policy")),
        planned_duration_seconds=int(_req(raw, "planned_duration_seconds")),
        earliest_start=float(_req(raw, "earliest_start")),
        expires_at=float(_req(raw, "expires_at")),
        evidence_root=str(_req(raw, "evidence_root")),
        evidence_target_paths=evidence_paths,
        required_evidence_schema_versions=evidence_schemas,
        killstate_policy=str(_req(raw, "killstate_policy")),
        timeout_policy=str(_req(raw, "timeout_policy")),
        lock_policy=str(_req(raw, "lock_policy")),
        retry_policy=str(_req(raw, "retry_policy")),
        no_auto_promotion=bool(_req(raw, "no_auto_promotion")),
        no_testnet=bool(_req(raw, "no_testnet")),
        no_live=bool(_req(raw, "no_live")),
        no_orders=bool(_req(raw, "no_orders")),
        operator_identity=str(_req(raw, "operator_identity")),
        approval_identity=str(_req(raw, "approval_identity")),
        confirm_token_hash_reference=str(_req(raw, "confirm_token_hash_reference")),
        confirm_token_binding_sha256=str(_req(raw, "confirm_token_binding_sha256")),
        enabled=enabled,
        armed=armed,
        arming_state=arming_state,
        single_use=bool(_req(raw, "single_use")),
        consumed=consumed,
        revoked=revoked,
        revocation_state=str(_req(raw, "revocation_state")),
        fixture_non_authoritative=bool(raw.get("fixture_non_authoritative", False)),
        notes=notes,
    )


def validate_preregistration_contract_v1(
    contract: SessionPreregistrationContractV1,
    *,
    now_unix: Optional[float] = None,
    expected_repository_sha: Optional[str] = None,
) -> PreregistrationValidationResultV1:
    blockers: list[str] = []
    notes = [
        "PREREGISTRATION_IS_NOT_AUTHORIZATION",
        "PREREGISTRATION_DOES_NOT_START_SESSION",
        f"DEFAULT_ALLOWLIST_HINT={PRODUCTION_INSTRUMENT_ID}",
    ]

    if contract.schema_version != PREREGISTRATION_SCHEMA_VERSION:
        blockers.append("PREREG_SCHEMA_VERSION_MISMATCH")
    if contract.contract_version != "v1":
        blockers.append("PREREG_CONTRACT_VERSION_MISMATCH")
    if contract.capability_id not in {
        "PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1",
        OBSERVATION_CAPABILITY_ID,
    }:
        # Must bind to this GO capability or the observation capability it authorizes for.
        if "PAPER_SHADOW_OBSERVATION" not in contract.capability_id:
            blockers.append("PREREG_CAPABILITY_ID_MISMATCH")

    if not contract.session_id.strip():
        blockers.append("SESSION_ID_REQUIRED")
    if not contract.purpose.strip():
        blockers.append("PURPOSE_REQUIRED")
    if contract.venue.upper() != VENUE_OKX:
        blockers.append(f"VENUE_FORBIDDEN:{contract.venue}")
    if contract.market_type.upper() != MARKET_TYPE_FUTURES:
        blockers.append(f"MARKET_TYPE_FORBIDDEN:{contract.market_type}")
    if contract.observation_mode.strip().lower() != REQUIRED_MODE:
        blockers.append("OBSERVATION_MODE_REQUIRED")

    if not contract.instrument_allowlist:
        blockers.append("INSTRUMENT_ALLOWLIST_EMPTY")
    for inst in contract.instrument_allowlist:
        if _BTC_RE.search(inst):
            blockers.append(f"BTC_INSTRUMENT_FORBIDDEN:{inst}")
        if any(h in inst.upper() for h in _SPOT_HINTS) or "/EUR" in inst.upper():
            if (
                "XPERP" not in inst.upper()
                and "PERP" not in inst.upper()
                and "SWAP" not in inst.upper()
            ):
                blockers.append(f"SPOT_INSTRUMENT_FORBIDDEN:{inst}")
        if inst in contract.instrument_denylist:
            blockers.append(f"INSTRUMENT_ON_DENYLIST:{inst}")

    if not contract.strategy_portfolio_id.strip():
        blockers.append("STRATEGY_PORTFOLIO_ID_REQUIRED")
    if not contract.strategy_component_identities:
        blockers.append("STRATEGY_COMPONENT_IDENTITIES_REQUIRED")
    if not contract.config_identity.strip():
        blockers.append("CONFIG_IDENTITY_REQUIRED")
    if not contract.code_identity.strip():
        blockers.append("CODE_IDENTITY_REQUIRED")
    if len(contract.expected_repository_sha.strip()) < 7:
        blockers.append("EXPECTED_REPOSITORY_SHA_INVALID")
    if (
        expected_repository_sha is not None
        and contract.expected_repository_sha != expected_repository_sha
    ):
        blockers.append("REPOSITORY_SHA_MISMATCH")

    if not contract.no_order_invariant or not contract.no_orders:
        blockers.append("NO_ORDER_INVARIANT_REQUIRED")
    net_pol = contract.network_policy.strip().lower()
    if net_pol not in {p.lower() for p in ALLOWED_PREREG_NETWORK_POLICIES}:
        blockers.append("NETWORK_POLICY_FORBIDDEN")
    if net_pol == NETWORK_SCOPE_OKX_EEA_FUTURES_PUBLIC_MD_OBSERVE_V1:
        if contract.network_scope != NETWORK_SCOPE_OKX_EEA_FUTURES_PUBLIC_MD_OBSERVE_V1:
            blockers.append("PREREG_NETWORK_SCOPE_MISMATCH")
        if (
            contract.session_execution_scope
            != SESSION_EXECUTION_SCOPE_PAPER_SHADOW_OBSERVATION_WALLCLOCK_V1
        ):
            blockers.append("PREREG_SESSION_EXECUTION_SCOPE_REQUIRED_FOR_MD_OBSERVE")
    elif contract.network_scope or contract.session_execution_scope:
        # Offline/deny policies must not carry wallclock scopes.
        if contract.network_scope not in {"", "deny", "forbidden", "offline_only"}:
            blockers.append("PREREG_NETWORK_SCOPE_WITHOUT_MD_OBSERVE_POLICY")
        if contract.session_execution_scope and net_pol in {
            "deny",
            "forbidden",
            "offline_only",
        }:
            blockers.append("PREREG_SESSION_EXECUTION_SCOPE_WITHOUT_MD_OBSERVE_POLICY")
    if contract.credential_policy.strip().lower() not in {"deny", "forbidden", "none"}:
        blockers.append("CREDENTIAL_POLICY_MUST_DENY")
    if not contract.no_testnet:
        blockers.append("NO_TESTNET_REQUIRED")
    if not contract.no_live:
        blockers.append("NO_LIVE_REQUIRED")
    if not contract.no_auto_promotion:
        blockers.append("NO_AUTO_PROMOTION_REQUIRED")

    if (
        contract.planned_duration_seconds <= 0
        or contract.planned_duration_seconds > DEFAULT_MAX_SESSION_DURATION_SECONDS
    ):
        blockers.append("PLANNED_DURATION_OUT_OF_BOUNDS")
    ttl = contract.expires_at - contract.earliest_start
    if ttl < MIN_TTL_SECONDS or ttl > MAX_TTL_SECONDS:
        blockers.append("PREREG_TTL_OUT_OF_BOUNDS")
    if contract.expires_at <= contract.earliest_start:
        blockers.append("EXPIRES_BEFORE_EARLIEST_START")
    if now_unix is not None and now_unix > contract.expires_at:
        blockers.append("PREREGISTRATION_EXPIRED")

    if not contract.evidence_root.strip():
        blockers.append("EVIDENCE_ROOT_REQUIRED")
    if not contract.evidence_target_paths:
        blockers.append("EVIDENCE_TARGET_PATHS_REQUIRED")
    if not contract.required_evidence_schema_versions:
        blockers.append("REQUIRED_EVIDENCE_SCHEMA_VERSIONS_MISSING")

    for policy_name, value in (
        ("killstate_policy", contract.killstate_policy),
        ("timeout_policy", contract.timeout_policy),
        ("lock_policy", contract.lock_policy),
        ("retry_policy", contract.retry_policy),
    ):
        if not str(value).strip():
            blockers.append(f"{policy_name.upper()}_REQUIRED")

    if not contract.operator_identity.strip():
        blockers.append("OPERATOR_IDENTITY_REQUIRED")
    if not contract.approval_identity.strip():
        blockers.append("APPROVAL_IDENTITY_REQUIRED")
    if len(contract.confirm_token_binding_sha256.strip()) != 64:
        blockers.append("CONFIRM_TOKEN_BINDING_HASH_INVALID")
    if not contract.confirm_token_hash_reference.strip():
        blockers.append("CONFIRM_TOKEN_HASH_REFERENCE_REQUIRED")
    if not contract.single_use:
        blockers.append("SINGLE_USE_REQUIRED")
    if contract.consumed:
        blockers.append("PREREGISTRATION_CONSUMED")
    if contract.revoked or contract.revocation_state.strip().lower() not in {
        "none",
        "active",
        "",
    }:
        if contract.revoked or contract.revocation_state.strip().lower() == "revoked":
            blockers.append("PREREGISTRATION_REVOKED")

    try:
        state = parse_arming_state(contract.arming_state)
    except Exception:  # noqa: BLE001
        blockers.append("UNKNOWN_ARMING_STATE")
        state = AuthorizationArmingState.REJECTED
    if state in {
        AuthorizationArmingState.EXPIRED,
        AuthorizationArmingState.REVOKED,
        AuthorizationArmingState.REJECTED,
        AuthorizationArmingState.CONSUMED,
    }:
        blockers.append(f"PREREG_ARMING_TERMINAL:{state.value}")

    return PreregistrationValidationResultV1(
        ok=not blockers,
        blockers=blockers,
        contract=contract,
        notes=notes,
    )


def validate_preregistration_path_v1(
    path: Path,
    *,
    now_unix: Optional[float] = None,
    expected_repository_sha: Optional[str] = None,
) -> PreregistrationValidationResultV1:
    try:
        raw = load_preregistration_contract_dict_v1(path)
        contract = parse_preregistration_contract_v1(raw)
    except PreregistrationContractError as exc:
        return PreregistrationValidationResultV1(ok=False, blockers=[str(exc)])
    return validate_preregistration_contract_v1(
        contract,
        now_unix=now_unix,
        expected_repository_sha=expected_repository_sha,
    )
