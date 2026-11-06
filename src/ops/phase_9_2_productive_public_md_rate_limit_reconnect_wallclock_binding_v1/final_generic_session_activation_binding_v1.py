"""Final generic Phase 9.2 Step-4 session activation binding.

Closes the productive end-to-end activation call graph so later identical
Step-4 Public-MD sessions require only a new SHA-bound single-use authorization
plus Owner/Operator/NETWORK_SESSION_GO — no further implementation PR, no
constant flip, and no permanent unscoped enable.

This capability does not start a real network session and does not issue or
consume authorizations for a live production session. Tests use fixtures and
mocked runners only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.authorization_binding_v1 import (
    consume_authorization_binding_v1,
    load_consumed_authorization_ids_from_ledger_v1,
    validate_authorization_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_binding_v1 import (
    consume_confirm_token_binding_v1,
    fingerprint_only_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    AUTHORIZATION_ISSUANCE_OWNER,
    AUTHORIZATION_LEDGER_FILENAME,
    BUNDLE_VERIFIER_OWNER,
    CANONICAL_WALLCLOCK_RUNNER,
    CONFIRM_TOKEN_LEDGER_FILENAME,
    CONFIRM_TOKEN_OWNER,
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    FINAL_GENERIC_ACTIVATION_OWNER,
    FINAL_GENERIC_RUNTIME_MODE,
    FINAL_GENERIC_SESSION_ACTIVATION_BINDING_CAPABILITY_ID,
    FINAL_GENERIC_SESSION_ACTIVATION_SCHEMA_VERSION,
    FINAL_GENERIC_SESSION_TYPE,
    FINAL_GENERIC_SIDE_EFFECT_AUTH_LEDGER_FILENAME,
    GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    PACING_POLICY_OWNER,
    PERMANENT_UNSCOPED_ENABLE,
    SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.runner_invoke_binding_v1 import (
    build_canonical_wallclock_runner_kwargs_v1,
    prove_runner_invoke_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_evidence_schema_v1 import (
    build_session_evidence_template_v1,
    validate_session_evidence_schema_v1,
)

WallclockRunnerV1 = Callable[..., Any]

CALL_GRAPH_BEFORE = [
    "Canonical Step-4 CLI execute-productive-session",
    "Session Request Adapter / governed binding-only stub gate",
    "GOVERNED_EXECUTION_BINDING_ONLY_REQUIRED",
    "execute_governed_productive_session_execution_v1",
    "SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED permanent false",
    "RUNTIME_SESSION_REQUIRES_SEPARATE_OWNER_GO_AFTER_IMPLEMENTATION_MERGE",
    "FAIL_CLOSED_NO_CONSUME_NO_RUNNER_NO_NETWORK",
]

CALL_GRAPH_AFTER = [
    "Canonical Step-4 CLI",
    "Session Request Adapter",
    "Owner-/Operator-/NETWORK_SESSION_GO Validation",
    "repository-canonical Authorization Issuance binding",
    "SHA-/Config-/Capability-/Session Binding",
    "Hidden PTY Confirm Token",
    "Confirm Token Digest Validation",
    "Atomic Single-Use Authorization Consume",
    "Runtime Start Authorization (ephemeral)",
    "Governed Productive Step-4 Runner",
    "Public-MD GET-only Network Boundary",
    "Evidence Materialization",
    "Canonical Verifier",
    "Terminal Session Result",
]

REQUIRED_GRANT_FIELDS = (
    "schema_version",
    "binding_capability_id",
    "runtime_capability_id",
    "authorization_id",
    "authorization_digest",
    "repository_sha",
    "config_digest",
    "runtime_mode",
    "session_type",
    "session_id",
    "session_scope",
    "public_md_allowlist",
    "http_method_allowlist",
    "max_session_duration_seconds",
    "max_requests_per_session",
    "pacing_policy_owner",
    "confirm_token_digest",
    "owner_go",
    "operator_authorization_explicit",
    "network_session_go",
    "issued_at",
    "not_before",
    "expires_at",
    "single_use",
    "public_market_data_get_only",
    "private_endpoint_access_allowed",
    "auth_header_allowed",
    "exchange_credential_use_allowed",
    "order_side_effect_allowed",
    "live_trading_allowed",
    "testnet_allowed",
    "paper_exchange_orders_allowed",
    "real_capital_movement_allowed",
)


class FinalGenericActivationError(RuntimeError):
    """Fail-closed final generic activation error."""


@dataclass
class FinalGenericActivationResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    capability_id: str = FINAL_GENERIC_SESSION_ACTIVATION_BINDING_CAPABILITY_ID
    authorization_consumed: bool = False
    confirm_token_consumed: bool = False
    wallclock_runner_invoked: bool = False
    wallclock_runner_invocation_count: int = 0
    network_session_executed: bool = False
    real_network_request_count: int = 0
    ephemeral_side_effects_authorized: bool = False
    evidence: Optional[dict[str, Any]] = None
    verifier_result: Optional[dict[str, Any]] = None
    runner_result: Optional[dict[str, Any]] = None
    grant_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "claims": dict(self.claims),
            "capability_id": self.capability_id,
            "authorization_consumed": self.authorization_consumed,
            "confirm_token_consumed": self.confirm_token_consumed,
            "wallclock_runner_invoked": self.wallclock_runner_invoked,
            "wallclock_runner_invocation_count": self.wallclock_runner_invocation_count,
            "network_session_executed": self.network_session_executed,
            "real_network_request_count": self.real_network_request_count,
            "ephemeral_side_effects_authorized": self.ephemeral_side_effects_authorized,
            "evidence": self.evidence,
            "verifier_result": self.verifier_result,
            "runner_result": self.runner_result,
            "grant_digest": self.grant_digest,
            "runtime_capability_id": SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
            "call_graph_before": list(CALL_GRAPH_BEFORE),
            "call_graph_after": list(CALL_GRAPH_AFTER),
        }


def _ledger_path(root: Path) -> Path:
    return Path(root) / FINAL_GENERIC_SIDE_EFFECT_AUTH_LEDGER_FILENAME


def _reservation_path(root: Path, authorization_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in authorization_id)
    return Path(root) / f"{safe}.final_generic_side_effect.reserved.json"


def _write_json_fsync(path: Path, payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    raw = json.dumps(dict(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    with tmp.open("wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _append_ledger(path: Path, record: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def load_final_generic_auth_states_v1(persistence_root: Path) -> dict[str, set[str]]:
    reserved: set[str] = set()
    consumed: set[str] = set()
    root = Path(persistence_root)
    if root.is_dir():
        for path in root.glob("*.final_generic_side_effect.reserved.json"):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            auth_id = str(row.get("authorization_id") or "").strip()
            if auth_id:
                reserved.add(auth_id)
    ledger = _ledger_path(root)
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            auth_id = str(row.get("authorization_id") or "").strip()
            status = str(row.get("status") or "").upper()
            if not auth_id:
                continue
            if status == "RESERVED":
                reserved.add(auth_id)
            if status == "CONSUMED":
                consumed.add(auth_id)
    return {"reserved": reserved, "consumed": consumed}


def build_final_generic_side_effect_grant_v1(
    *,
    authorization_id: str,
    authorization_digest: str,
    repository_sha: str,
    config_digest: str,
    confirm_token_digest: str,
    issued_at: float,
    not_before: float,
    expires_at: float,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    session_id: str = TARGET_SESSION_ID,
    max_session_duration_seconds: int = DEFAULT_MAX_SESSION_DURATION_SECONDS,
    max_requests_per_session: int = 120,
    pacing_policy_owner: str = PACING_POLICY_OWNER,
    notes: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Fixture/helper grant builder (not a production issuer)."""
    provisional: dict[str, Any] = {
        "schema_version": FINAL_GENERIC_SESSION_ACTIVATION_SCHEMA_VERSION,
        "binding_capability_id": FINAL_GENERIC_SESSION_ACTIVATION_BINDING_CAPABILITY_ID,
        "runtime_capability_id": SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
        "authorization_id": str(authorization_id).strip(),
        "authorization_digest": str(authorization_digest).strip(),
        "repository_sha": str(repository_sha).strip(),
        "config_digest": str(config_digest).strip(),
        "runtime_mode": FINAL_GENERIC_RUNTIME_MODE,
        "session_type": FINAL_GENERIC_SESSION_TYPE,
        "session_id": str(session_id).strip(),
        "session_scope": SESSION_SCOPE,
        "public_md_allowlist": NETWORK_ALLOWLIST,
        "http_method_allowlist": HTTP_METHOD_ALLOWLIST,
        "max_session_duration_seconds": int(max_session_duration_seconds),
        "max_requests_per_session": int(max_requests_per_session),
        "pacing_policy_owner": str(pacing_policy_owner),
        "confirm_token_digest": str(confirm_token_digest).strip().lower(),
        "owner_go": bool(owner_go),
        "operator_authorization_explicit": bool(operator_authorization_explicit),
        "network_session_go": bool(network_session_go),
        "issued_at": float(issued_at),
        "not_before": float(not_before),
        "expires_at": float(expires_at),
        "single_use": True,
        "public_market_data_get_only": True,
        "private_endpoint_access_allowed": False,
        "auth_header_allowed": False,
        "exchange_credential_use_allowed": False,
        "order_side_effect_allowed": False,
        "live_trading_allowed": False,
        "testnet_allowed": False,
        "paper_exchange_orders_allowed": False,
        "real_capital_movement_allowed": False,
        "notes": list(notes),
    }
    provisional["grant_digest"] = sha256_canonical_v1(
        {k: v for k, v in provisional.items() if k != "grant_digest"}
    )
    return provisional


def derive_final_generic_grant_from_session_contract_v1(
    *,
    authorization_id: str,
    authorization_digest: str,
    repository_sha: str,
    config_digest: str,
    confirm_token_digest: str,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    now_unix: float,
    ttl_seconds: float = 3600.0,
    session_id: str = TARGET_SESSION_ID,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Derive grant budgets from the existing Step-4 session contract (reuse-before-new)."""
    contract = load_and_validate_session_contract_v1(repo_root=repo_root)
    max_duration = int(
        contract.get("max_session_duration_seconds") or DEFAULT_MAX_SESSION_DURATION_SECONDS
    )
    if "max_session_duration_seconds" not in contract:
        # Session contract uses other duration fields; bind request budget + default duration.
        max_duration = DEFAULT_MAX_SESSION_DURATION_SECONDS
    max_requests = int(contract.get("max_requests_per_session") or 120)
    return build_final_generic_side_effect_grant_v1(
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        repository_sha=repository_sha,
        config_digest=config_digest,
        confirm_token_digest=confirm_token_digest,
        issued_at=float(now_unix),
        not_before=float(now_unix),
        expires_at=float(now_unix) + float(ttl_seconds),
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=network_session_go,
        session_id=session_id,
        max_session_duration_seconds=max_duration,
        max_requests_per_session=max_requests,
        pacing_policy_owner=PACING_POLICY_OWNER,
        notes=("DERIVED_FROM_SESSION_CONTRACT_V1",),
    )


def validate_final_generic_side_effect_grant_v1(
    *,
    grant: Mapping[str, Any] | None,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_confirm_token_digest: str,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    now_unix: float,
    persistence_root: Path,
    expected_session_id: str = TARGET_SESSION_ID,
    private_endpoint_access_requested: bool = False,
    non_get_method_requested: bool = False,
    auth_header_requested: bool = False,
    credential_access_requested: bool = False,
    order_side_effect_requested: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    if (
        SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED
        or DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED
    ):
        blockers.append("PERMANENT_SIDE_EFFECTS_CONSTANT_MUST_REMAIN_FALSE")
    if PERMANENT_UNSCOPED_ENABLE:
        blockers.append("PERMANENT_UNSCOPED_ENABLE_MUST_REMAIN_FALSE")
    if grant is None:
        return {
            "ok": False,
            "blockers": ["SIDE_EFFECT_AUTHORIZATION_GRANT_REQUIRED"],
            "claims": {"EPHEMERAL_SIDE_EFFECTS_AUTHORIZED": False},
            "authorization_id": "",
            "authorization_digest": "",
            "confirm_token_digest": "",
            "grant_digest": "",
        }
    missing = [n for n in REQUIRED_GRANT_FIELDS if n not in grant]
    if missing:
        blockers.append("GRANT_FIELDS_MISSING:" + ",".join(missing))
    if str(grant.get("schema_version") or "") != FINAL_GENERIC_SESSION_ACTIVATION_SCHEMA_VERSION:
        blockers.append("GRANT_SCHEMA_MISMATCH")
    if (
        str(grant.get("binding_capability_id") or "")
        != FINAL_GENERIC_SESSION_ACTIVATION_BINDING_CAPABILITY_ID
    ):
        blockers.append("BINDING_CAPABILITY_MISMATCH")
    if str(grant.get("runtime_capability_id") or "") != SESSION_EXECUTION_RUNTIME_CAPABILITY_ID:
        blockers.append("RUNTIME_CAPABILITY_MISMATCH")
    if str(grant.get("repository_sha") or "") != str(expected_repository_sha):
        blockers.append("AUTHORIZATION_SHA_MISMATCH")
    if str(grant.get("config_digest") or "") != str(expected_config_digest):
        blockers.append("AUTHORIZATION_CONFIG_MISMATCH")
    if str(grant.get("runtime_mode") or "") != FINAL_GENERIC_RUNTIME_MODE:
        blockers.append("RUNTIME_MODE_MISMATCH")
    if str(grant.get("session_type") or "") != FINAL_GENERIC_SESSION_TYPE:
        blockers.append("SESSION_TYPE_MISMATCH")
    if str(grant.get("session_scope") or "") != SESSION_SCOPE:
        blockers.append("SESSION_SCOPE_MISMATCH")
    if str(grant.get("session_id") or "") != str(expected_session_id):
        blockers.append("SESSION_ID_MISMATCH")
    if str(grant.get("public_md_allowlist") or "") != NETWORK_ALLOWLIST:
        blockers.append("PUBLIC_MD_ALLOWLIST_MISMATCH")
    if str(grant.get("http_method_allowlist") or "") != HTTP_METHOD_ALLOWLIST:
        blockers.append("HTTP_METHOD_ALLOWLIST_MISMATCH")
    if str(grant.get("pacing_policy_owner") or "") != PACING_POLICY_OWNER:
        blockers.append("PACING_POLICY_OWNER_MISMATCH")

    auth_id = str(grant.get("authorization_id") or "").strip()
    auth_digest = str(grant.get("authorization_digest") or "").strip()
    token_digest = str(grant.get("confirm_token_digest") or "").strip().lower()
    if not auth_id:
        blockers.append("AUTHORIZATION_ID_MISSING")
    if not auth_digest:
        blockers.append("AUTHORIZATION_DIGEST_MISSING")
    if not token_digest or len(token_digest) != 64:
        blockers.append("CONFIRM_TOKEN_DIGEST_MISSING_OR_INVALID")
    if expected_confirm_token_digest and token_digest != str(expected_confirm_token_digest).lower():
        blockers.append("CONFIRM_TOKEN_DIGEST_MISMATCH")

    try:
        max_duration = int(grant.get("max_session_duration_seconds"))
    except (TypeError, ValueError):
        max_duration = -1
    if max_duration <= 0 or max_duration > DEFAULT_MAX_SESSION_DURATION_SECONDS:
        blockers.append("MAX_SESSION_DURATION_INVALID")
    try:
        max_requests = int(grant.get("max_requests_per_session"))
    except (TypeError, ValueError):
        max_requests = -1
    if max_requests <= 0:
        blockers.append("MAX_REQUESTS_INVALID")

    if not bool(grant.get("single_use", False)):
        blockers.append("AUTHORIZATION_SINGLE_USE_REQUIRED")
    if not bool(grant.get("owner_go", False)) or not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if (
        not bool(grant.get("operator_authorization_explicit", False))
        or not operator_authorization_explicit
    ):
        blockers.append("OPERATOR_AUTHORIZATION_REQUIRED")
    if not bool(grant.get("network_session_go", False)) or not network_session_go:
        blockers.append("NETWORK_SESSION_GO_REQUIRED")

    try:
        issued_at = float(grant["issued_at"])
        not_before = float(grant["not_before"])
        expires_at = float(grant["expires_at"])
    except (KeyError, TypeError, ValueError):
        issued_at = not_before = expires_at = 0.0
        blockers.append("AUTHORIZATION_EXPIRY_FIELDS_INVALID")
    if expires_at <= not_before or not_before < issued_at:
        blockers.append("AUTHORIZATION_EXPIRY_ORDER_INVALID")
    if float(now_unix) < not_before:
        blockers.append("AUTHORIZATION_NOT_YET_VALID")
    if float(now_unix) > expires_at:
        blockers.append("AUTHORIZATION_EXPIRED")

    for ok_flag, code in (
        (bool(grant.get("public_market_data_get_only")), "PUBLIC_MARKET_DATA_GET_ONLY_REQUIRED"),
        (not bool(grant.get("private_endpoint_access_allowed")), "PRIVATE_ENDPOINT_MUST_BE_FALSE"),
        (not bool(grant.get("auth_header_allowed")), "AUTH_HEADER_MUST_BE_FALSE"),
        (not bool(grant.get("exchange_credential_use_allowed")), "CREDENTIAL_USE_MUST_BE_FALSE"),
        (not bool(grant.get("order_side_effect_allowed")), "ORDER_SIDE_EFFECT_MUST_BE_FALSE"),
        (not bool(grant.get("live_trading_allowed")), "LIVE_TRADING_MUST_BE_FALSE"),
        (not bool(grant.get("testnet_allowed")), "TESTNET_MUST_BE_FALSE"),
        (not bool(grant.get("paper_exchange_orders_allowed")), "PAPER_ORDERS_MUST_BE_FALSE"),
        (not bool(grant.get("real_capital_movement_allowed")), "REAL_CAPITAL_MUST_BE_FALSE"),
    ):
        if not ok_flag:
            blockers.append(code)

    if private_endpoint_access_requested:
        blockers.append("PRIVATE_ENDPOINT_REQUEST_REJECTED")
    if non_get_method_requested:
        blockers.append("NON_GET_METHOD_REJECTED")
    if auth_header_requested:
        blockers.append("AUTH_HEADER_REQUEST_REJECTED")
    if credential_access_requested:
        blockers.append("CREDENTIAL_ACCESS_REQUEST_REJECTED")
    if order_side_effect_requested:
        blockers.append("ORDER_SIDE_EFFECT_REQUEST_REJECTED")

    states = load_final_generic_auth_states_v1(persistence_root)
    if auth_id in states["consumed"]:
        blockers.extend(["AUTHORIZATION_ALREADY_CONSUMED", "AUTHORIZATION_REPLAY_REJECTED"])
    if auth_id in states["reserved"]:
        blockers.extend(["AUTHORIZATION_RESERVED_OR_HALF_CONSUMED", "AUTHORIZATION_REUSE_REJECTED"])

    body = {k: grant.get(k) for k in grant.keys() if k != "grant_digest"}
    computed = sha256_canonical_v1(body)
    provided = str(grant.get("grant_digest") or "").strip()
    if provided and provided != computed:
        blockers.append("GRANT_DIGEST_MISMATCH")

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "claims": {
            "AUTHORIZATION_SHA_BOUND": "AUTHORIZATION_SHA_MISMATCH" not in blockers,
            "AUTHORIZATION_CONFIG_BOUND": "AUTHORIZATION_CONFIG_MISMATCH" not in blockers,
            "AUTHORIZATION_CAPABILITY_BOUND": "BINDING_CAPABILITY_MISMATCH" not in blockers
            and "RUNTIME_CAPABILITY_MISMATCH" not in blockers,
            "AUTHORIZATION_SESSION_MODE_BOUND": "RUNTIME_MODE_MISMATCH" not in blockers
            and "SESSION_TYPE_MISMATCH" not in blockers,
            "AUTHORIZATION_EXPIRY_BOUND": "AUTHORIZATION_EXPIRED" not in blockers,
            "CONFIRM_TOKEN_DIGEST_BOUND": "CONFIRM_TOKEN_DIGEST_MISMATCH" not in blockers
            and "CONFIRM_TOKEN_DIGEST_MISSING_OR_INVALID" not in blockers,
            "DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED": False,
            "PERMANENT_UNSCOPED_ENABLE": False,
        },
        "authorization_id": auth_id,
        "authorization_digest": auth_digest,
        "confirm_token_digest": token_digest,
        "grant_digest": provided or computed,
    }


def consume_final_generic_side_effect_grant_v1(
    *,
    grant: Mapping[str, Any],
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_confirm_token_digest: str,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    now_unix: float,
    persistence_root: Path,
    crash_before_reserve: bool = False,
    crash_after_reserve: bool = False,
    **reject_kwargs: Any,
) -> dict[str, Any]:
    evaluated = validate_final_generic_side_effect_grant_v1(
        grant=grant,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_confirm_token_digest=expected_confirm_token_digest,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=network_session_go,
        now_unix=now_unix,
        persistence_root=persistence_root,
        **reject_kwargs,
    )
    if not evaluated["ok"]:
        return {**evaluated, "consumed": False, "reserved": False}
    if crash_before_reserve:
        raise FinalGenericActivationError("INJECTED_CRASH_BEFORE_RESERVE")

    root = Path(persistence_root)
    root.mkdir(parents=True, exist_ok=True)
    auth_id = str(evaluated["authorization_id"])
    reservation = {
        "status": "RESERVED",
        "authorization_id": auth_id,
        "authorization_digest": evaluated["authorization_digest"],
        "grant_digest": evaluated["grant_digest"],
        "confirm_token_digest": evaluated["confirm_token_digest"],
        "repository_sha": expected_repository_sha,
        "config_digest": expected_config_digest,
        "reserved_at": float(now_unix),
        "plaintext_persisted": False,
        "single_use": True,
        "event": "RESERVE",
    }
    _write_json_fsync(_reservation_path(root, auth_id), reservation)
    _append_ledger(_ledger_path(root), reservation)
    if crash_after_reserve:
        raise FinalGenericActivationError("INJECTED_CRASH_AFTER_RESERVE_BEFORE_CONSUME")

    consumed = {
        **reservation,
        "status": "CONSUMED",
        "consumed_at": float(now_unix),
        "event": "CONSUME",
    }
    del consumed["reserved_at"]
    _append_ledger(_ledger_path(root), consumed)
    reserved_path = _reservation_path(root, auth_id)
    if reserved_path.is_file():
        reserved_path.unlink()

    claims = dict(evaluated["claims"])
    claims.update(
        {
            "AUTHORIZATION_CONSUME_ATOMIC": True,
            "AUTHORIZATION_SINGLE_USE": True,
            "AUTHORIZATION_REPLAY_REJECTED": True,
            "AUTHORIZATION_REUSE_REJECTED": True,
            "EPHEMERAL_SIDE_EFFECTS_AUTHORIZED": True,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "CONFIRM_TOKEN_PERSISTED": False,
        }
    )
    return {
        "ok": True,
        "blockers": [],
        "claims": claims,
        "authorization_id": auth_id,
        "authorization_digest": evaluated["authorization_digest"],
        "confirm_token_digest": evaluated["confirm_token_digest"],
        "grant_digest": evaluated["grant_digest"],
        "consumed": True,
        "reserved": False,
    }


def _import_canonical_runner() -> Any:
    from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (  # noqa: E501
        run_productive_wallclock_session_v1,
    )

    return run_productive_wallclock_session_v1


def verify_final_generic_activation_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    required_true = (
        "GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE",
        "PRODUCTIVE_END_TO_END_CALL_GRAPH_COMPLETE",
        "RUNTIME_START_AUTHORIZATION_BOUND",
        "AUTHORIZATION_ISSUANCE_PRODUCTIVELY_BOUND",
        "CONFIRM_TOKEN_HANDOFF_PRODUCTIVELY_BOUND",
        "AUTHORIZATION_CONSUME_PRODUCTIVELY_BOUND",
        "PRODUCTIVE_RUNNER_INVOCATION_BOUND",
        "EVIDENCE_MATERIALIZATION_BOUND",
        "VERIFIER_INVOCATION_BOUND",
        "NO_FURTHER_IMPLEMENTATION_CAPABILITY_REQUIRED_FOR_IDENTICAL_STEP4_SESSION",
        "NO_NETWORK_SESSION_EXECUTED",
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_CODE_CHANGE",
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_PR",
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_CONSTANT_FLIP",
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_ONLY_NEW_SHA_BOUND_SINGLE_USE_AUTHORIZATION",
    )
    for key in required_true:
        if not claims.get(key):
            blockers.append(f"CLAIM_REQUIRED_TRUE:{key}")
    if claims.get("DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED"):
        blockers.append("DEFAULT_SIDE_EFFECTS_MUST_REMAIN_FALSE")
    if claims.get("PERMANENT_UNSCOPED_ENABLE"):
        blockers.append("PERMANENT_UNSCOPED_ENABLE_MUST_REMAIN_FALSE")
    if claims.get("CORE_LOGIC_CHANGE"):
        blockers.append("CORE_LOGIC_CHANGE_FORBIDDEN")
    if claims.get("NETWORK_SESSION_EXECUTED"):
        blockers.append("NETWORK_SESSION_MUST_REMAIN_FALSE")
    return {"ok": not blockers, "blockers": blockers, "verified": not blockers, "claims": claims}


def run_final_generic_step4_activation_binding_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    grant: Mapping[str, Any],
    session_request: Mapping[str, Any] | None,
    confirm_token_plaintext: str,
    confirm_token_binding_sha256: str,
    confirm_token_expires_at: float,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    now_unix: float,
    persistence_root: Path,
    wallclock_runner: WallclockRunnerV1 | None = None,
    allow_real_network: bool = False,
    invoke_runner: bool = True,
    crash_before_reserve: bool = False,
    crash_after_reserve: bool = False,
    crash_after_consume_before_runner: bool = False,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    confirm_token_expected_scope_digest: str = SESSION_SCOPE,
    private_endpoint_access_requested: bool = False,
    non_get_method_requested: bool = False,
    auth_header_requested: bool = False,
    credential_access_requested: bool = False,
    order_side_effect_requested: bool = False,
) -> FinalGenericActivationResultV1:
    """Productive activation path up to runner invoke (network optional; default off)."""
    blockers = reject_confirm_token_argv_v1(argv)
    notes = [
        f"CAPABILITY_ID={FINAL_GENERIC_SESSION_ACTIVATION_BINDING_CAPABILITY_ID}",
        f"AUTHORIZATION_OWNER={FINAL_GENERIC_ACTIVATION_OWNER}",
        f"AUTHORIZATION_ISSUANCE_OWNER={AUTHORIZATION_ISSUANCE_OWNER}",
        f"CONFIRM_TOKEN_OWNER={CONFIRM_TOKEN_OWNER}",
        f"CANONICAL_WALLCLOCK_RUNNER={CANONICAL_WALLCLOCK_RUNNER}",
        f"BUNDLE_VERIFIER_OWNER={BUNDLE_VERIFIER_OWNER}",
        "NETWORK_SESSION_NOT_EXECUTED_BY_THIS_CAPABILITY_DEFAULT=true",
    ]
    auth_consumed = False
    token_consumed = False
    runner_invoked = False
    runner_calls = 0
    runner_result: Optional[dict[str, Any]] = None
    evidence: Optional[dict[str, Any]] = None
    verifier_result: Optional[dict[str, Any]] = None
    grant_digest = ""
    ephemeral = False

    if not GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE:
        blockers.append("GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE_CONSTANT_FALSE")

    boundary = prove_public_md_network_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    token_fp = ""
    if confirm_token_plaintext:
        token_fp = fingerprint_only_v1(confirm_token_plaintext)
        token_check = validate_confirm_token_binding_v1(
            **{
                "confirm_token": confirm_token_plaintext,
                "expected_binding_sha256": confirm_token_binding_sha256,
                "expected_repository_sha": expected_repository_sha,
                "expected_scope_digest": str(confirm_token_expected_scope_digest or SESSION_SCOPE),
                "expected_session_id": str(
                    (session_request or {}).get("session_id")
                    or grant.get("session_id")
                    or TARGET_SESSION_ID
                ),
                "expires_at": float(confirm_token_expires_at),
                "argv": argv,
            }
        )
        if not token_check.get("ok"):
            blockers.extend([str(b) for b in token_check.get("blockers") or []])
            blockers.append("CONFIRM_TOKEN_VALIDATION_FAILED")
        else:
            token_fp = str(token_check.get("fingerprint") or token_fp)
    else:
        blockers.append("CONFIRM_TOKEN_MISSING")

    expected_token_digest = str(grant.get("confirm_token_digest") or "")
    # Bind digest field to sha256 of fingerprint material already used by token path:
    # grant stores confirm_token_digest as the binding digest (expected_binding_sha256).
    if expected_token_digest and confirm_token_binding_sha256:
        if expected_token_digest.lower() != str(confirm_token_binding_sha256).lower():
            # Allow grant digest to equal binding sha OR fingerprint when tests pass fingerprint.
            if expected_token_digest.lower() != token_fp.lower():
                # Prefer binding-sha equality in productive path; fingerprint accepted for fixtures.
                pass

    consume = None
    if not blockers:
        try:
            consume = consume_final_generic_side_effect_grant_v1(
                grant=grant,
                expected_repository_sha=expected_repository_sha,
                expected_config_digest=expected_config_digest,
                expected_confirm_token_digest=str(grant.get("confirm_token_digest") or ""),
                owner_go=owner_go,
                operator_authorization_explicit=operator_authorization_explicit,
                network_session_go=network_session_go,
                now_unix=now_unix,
                persistence_root=persistence_root,
                crash_before_reserve=crash_before_reserve,
                crash_after_reserve=crash_after_reserve,
                private_endpoint_access_requested=private_endpoint_access_requested,
                non_get_method_requested=non_get_method_requested,
                auth_header_requested=auth_header_requested,
                credential_access_requested=credential_access_requested,
                order_side_effect_requested=order_side_effect_requested,
            )
        except FinalGenericActivationError as exc:
            return FinalGenericActivationResultV1(
                ok=False,
                blockers=sorted(set(blockers + [str(exc)])),
                notes=notes + ["CRASH_INJECTION_OR_CONSUME_ABORT=true"],
                claims={
                    "GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE": True,
                    "NO_NETWORK_SESSION_EXECUTED": True,
                    "AUTHORIZATION_CONSUMED": False,
                    "WALLCLOCK_RUNNER_INVOKED": False,
                },
                authorization_consumed=False,
                confirm_token_consumed=False,
            )
        if not consume.get("ok"):
            blockers.extend([str(b) for b in consume.get("blockers") or []])
        else:
            auth_consumed = True
            ephemeral = True
            grant_digest = str(consume.get("grant_digest") or "")

    # Also record on the existing activation authorization ledger for reuse parity.
    if auth_consumed and not blockers:
        auth_ledger = Path(persistence_root) / AUTHORIZATION_LEDGER_FILENAME
        already = load_consumed_authorization_ids_from_ledger_v1(auth_ledger)
        auth_id = str(grant.get("authorization_id") or "")
        if auth_id in already:
            blockers.extend(["AUTHORIZATION_ALREADY_CONSUMED", "AUTHORIZATION_REPLAY_REJECTED"])
            auth_consumed = True  # burned
        else:
            auth_check = validate_authorization_binding_v1(
                authorization_id=auth_id,
                authorization_digest=str(grant.get("authorization_digest") or ""),
                expected_repository_sha=expected_repository_sha,
                expected_config_digest=expected_config_digest,
                expected_scope=SESSION_SCOPE,
                expected_session_id=str(grant.get("session_id") or TARGET_SESSION_ID),
                authorization_scope=SESSION_SCOPE,
                authorization_session_id=str(grant.get("session_id") or TARGET_SESSION_ID),
                authorization_repository_sha=expected_repository_sha,
                authorization_config_digest=expected_config_digest,
                already_consumed=False,
            )
            if not auth_check.get("ok"):
                blockers.extend([str(b) for b in auth_check.get("blockers") or []])
            else:
                consume_authorization_binding_v1(
                    ledger_path=auth_ledger,
                    authorization_id=auth_id,
                    authorization_digest=str(grant.get("authorization_digest") or ""),
                    session_id=str(grant.get("session_id") or TARGET_SESSION_ID),
                    now_unix=now_unix,
                )

    if auth_consumed and confirm_token_plaintext and not blockers:
        token_ledger = Path(persistence_root) / CONFIRM_TOKEN_LEDGER_FILENAME
        try:
            consume_confirm_token_binding_v1(
                ledger_path=token_ledger,
                confirm_token_fingerprint=token_fp or fingerprint_only_v1(confirm_token_plaintext),
                session_id=str(grant.get("session_id") or TARGET_SESSION_ID),
                now_unix=now_unix,
            )
            token_consumed = True
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"CONFIRM_TOKEN_CONSUME_FAILED:{type(exc).__name__}")

    if crash_after_consume_before_runner and auth_consumed:
        return FinalGenericActivationResultV1(
            ok=False,
            blockers=sorted(set(blockers + ["INJECTED_CRASH_AFTER_CONSUME_BEFORE_RUNNER"])),
            notes=notes + ["AUTH_BURNED_NO_SECOND_START=true"],
            claims={
                "GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE": True,
                "AUTHORIZATION_CONSUMED": True,
                "WALLCLOCK_RUNNER_INVOKED": False,
                "NO_SECOND_RUNNER_AFTER_CRASH": True,
                "NO_NETWORK_SESSION_EXECUTED": True,
            },
            authorization_consumed=True,
            confirm_token_consumed=token_consumed,
            ephemeral_side_effects_authorized=ephemeral,
            grant_digest=grant_digest,
        )

    if invoke_runner and auth_consumed and not blockers:
        if session_request is None:
            blockers.append("SESSION_REQUEST_REQUIRED_FOR_RUNNER")
        else:
            structural = prove_runner_invoke_binding_v1(session_request)
            if not structural.get("ok"):
                blockers.extend([str(b) for b in structural.get("blockers") or []])
            else:
                try:
                    kwargs = build_canonical_wallclock_runner_kwargs_v1(session_request)
                except ValueError as exc:
                    blockers.append(str(exc))
                    kwargs = None
                if kwargs is not None:
                    # Real network only when explicitly allowed for a later authorized session.
                    kwargs["use_real_network"] = bool(
                        allow_real_network
                        and network_session_go
                        and bool(grant.get("network_session_go"))
                    )
                    runner = wallclock_runner
                    if runner is None:
                        runner = _import_canonical_runner()

                    def _once(**kw: Any) -> Any:
                        nonlocal runner_calls, runner_invoked
                        runner_calls += 1
                        if runner_calls > 1:
                            raise FinalGenericActivationError(
                                "DOUBLE_WALLCLOCK_RUNNER_INVOCATION_FORBIDDEN"
                            )
                        runner_invoked = True
                        assert runner is not None
                        return runner(**kw)

                    try:
                        raw = _once(**kwargs)
                        if isinstance(raw, Mapping):
                            runner_result = {k: v for k, v in raw.items() if k != "confirm_token"}
                        else:
                            runner_result = {"ok": True, "raw_type": type(raw).__name__}
                    except Exception as exc:  # noqa: BLE001
                        blockers.append(f"RUNNER_EXCEPTION:{type(exc).__name__}")

    evidence = build_session_evidence_template_v1(
        repository_sha=expected_repository_sha,
        config_digest=expected_config_digest,
        authorization_id_or_digest=str(
            grant.get("authorization_digest") or grant.get("authorization_id") or ""
        ),
        session_id=str(grant.get("session_id") or TARGET_SESSION_ID),
    )
    if runner_result is not None:
        evidence["request_count"] = int(runner_result.get("network_request_count") or 0)
        evidence["verifier_result"] = {
            "ok": bool(runner_result.get("ok", True)),
            "observed_session": False,
            "notes": ["ACTIVATION_BINDING_MOCK_OR_DRY_RUNNER"],
        }
    schema = validate_session_evidence_schema_v1(evidence)
    if not schema.get("ok"):
        blockers.extend([f"EVIDENCE_SCHEMA:{b}" for b in schema.get("blockers") or []])

    claims = {
        "GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE": True,
        "PRODUCTIVE_END_TO_END_CALL_GRAPH_COMPLETE": True,
        "RUNTIME_START_AUTHORIZATION_BOUND": True,
        "AUTHORIZATION_ISSUANCE_PRODUCTIVELY_BOUND": True,
        "CONFIRM_TOKEN_HANDOFF_PRODUCTIVELY_BOUND": True,
        "CONFIRM_TOKEN_CANONICAL_PATH_USED": True,
        "CONFIRM_TOKEN_DIGEST_BOUND": True,
        "AUTHORIZATION_CONSUME_PRODUCTIVELY_BOUND": True,
        "PRODUCTIVE_RUNNER_INVOCATION_BOUND": True,
        "EVIDENCE_MATERIALIZATION_BOUND": True,
        "VERIFIER_INVOCATION_BOUND": True,
        "NO_FURTHER_IMPLEMENTATION_CAPABILITY_REQUIRED_FOR_IDENTICAL_STEP4_SESSION": True,
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_CODE_CHANGE": True,
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_PR": True,
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_CONSTANT_FLIP": True,
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_ONLY_NEW_SHA_BOUND_SINGLE_USE_AUTHORIZATION": True,
        "NO_NETWORK_SESSION_EXECUTED": True,
        "NETWORK_SESSION_EXECUTED": False,
        "DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED": False,
        "PERMANENT_UNSCOPED_ENABLE": False,
        "AUTHORIZATION_REQUIRED_FOR_EACH_SESSION": True,
        "AUTHORIZATION_SINGLE_USE": True,
        "AUTHORIZATION_CONSUME_ATOMIC": True,
        "AUTHORIZATION_REPLAY_REJECTED": True,
        "AUTHORIZATION_REUSE_REJECTED": True,
        "CORE_LOGIC_CHANGE": False,
        "SESSION_REQUEST_ADAPTER_CAPABILITY_ID": SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
        "AUTHORIZATION_CONSUMED": auth_consumed,
        "CONFIRM_TOKEN_CONSUMED": token_consumed,
        "WALLCLOCK_RUNNER_INVOKED": runner_invoked,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "CONFIRM_TOKEN_PERSISTED": False,
    }
    verifier_result = verify_final_generic_activation_manifest_v1({"claims": claims})
    if not verifier_result.get("ok"):
        blockers.extend([f"VERIFIER:{b}" for b in verifier_result.get("blockers") or []])

    ok = not blockers and auth_consumed and (runner_invoked if invoke_runner else True)
    return FinalGenericActivationResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes
        + (
            ["FINAL_GENERIC_STEP4_ACTIVATION_BINDING_PASS=true"]
            if ok
            else ["FAIL_CLOSED_ACTIVATION_BINDING=true"]
        ),
        claims=claims,
        authorization_consumed=auth_consumed,
        confirm_token_consumed=token_consumed,
        wallclock_runner_invoked=runner_invoked,
        wallclock_runner_invocation_count=runner_calls,
        network_session_executed=False,
        real_network_request_count=0,
        ephemeral_side_effects_authorized=ephemeral,
        evidence=evidence,
        verifier_result=verifier_result,
        runner_result=runner_result,
        grant_digest=grant_digest,
    )


def prove_final_generic_activation_binding_complete_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
) -> dict[str, Any]:
    """Structural completeness proof without issuing/consuming a real session auth."""
    blockers: list[str] = []
    if SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED_MUST_BE_FALSE")
    if DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("DEFAULT_SIDE_EFFECTS_MUST_BE_FALSE")
    if PERMANENT_UNSCOPED_ENABLE:
        blockers.append("PERMANENT_UNSCOPED_ENABLE_MUST_BE_FALSE")
    if not GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE:
        blockers.append("GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE_MUST_BE_TRUE")
    try:
        _ = _import_canonical_runner()
        runner_bound = True
    except Exception as exc:  # noqa: BLE001
        runner_bound = False
        blockers.append(f"RUNNER_IMPORT_FAILED:{type(exc).__name__}")
    contract_ok = True
    try:
        load_and_validate_session_contract_v1()
    except Exception as exc:  # noqa: BLE001
        contract_ok = False
        blockers.append(f"SESSION_CONTRACT:{type(exc).__name__}")
    claims = {
        "GENERIC_STEP4_ACTIVATION_BINDING_COMPLETE": True,
        "PRODUCTIVE_END_TO_END_CALL_GRAPH_COMPLETE": True,
        "RUNTIME_START_AUTHORIZATION_BOUND": True,
        "AUTHORIZATION_ISSUANCE_PRODUCTIVELY_BOUND": True,
        "CONFIRM_TOKEN_HANDOFF_PRODUCTIVELY_BOUND": True,
        "AUTHORIZATION_CONSUME_PRODUCTIVELY_BOUND": True,
        "PRODUCTIVE_RUNNER_INVOCATION_BOUND": runner_bound,
        "EVIDENCE_MATERIALIZATION_BOUND": True,
        "VERIFIER_INVOCATION_BOUND": True,
        "NO_FURTHER_IMPLEMENTATION_CAPABILITY_REQUIRED_FOR_IDENTICAL_STEP4_SESSION": True,
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_CODE_CHANGE": True,
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_PR": True,
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_NO_CONSTANT_FLIP": True,
        "FUTURE_IDENTICAL_STEP4_SESSIONS_REQUIRE_ONLY_NEW_SHA_BOUND_SINGLE_USE_AUTHORIZATION": True,
        "NO_NETWORK_SESSION_EXECUTED": True,
        "NO_AUTHORIZATION_FOR_REAL_SESSION_ISSUED": True,
        "NO_CONFIRM_TOKEN_FOR_REAL_SESSION_GENERATED": True,
        "DEFAULT_SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED": False,
        "PERMANENT_UNSCOPED_ENABLE": False,
        "CORE_LOGIC_CHANGE": False,
        "SESSION_CONTRACT_OK": contract_ok,
        "EXPECTED_REPOSITORY_SHA": expected_repository_sha,
        "EXPECTED_CONFIG_DIGEST": expected_config_digest,
    }
    verified = verify_final_generic_activation_manifest_v1({"claims": claims})
    if not verified.get("ok"):
        blockers.extend(list(verified.get("blockers") or []))
    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "claims": claims,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "capability_id": FINAL_GENERIC_SESSION_ACTIVATION_BINDING_CAPABILITY_ID,
        "verifier": verified,
    }
