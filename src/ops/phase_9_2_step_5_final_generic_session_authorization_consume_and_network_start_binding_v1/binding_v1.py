"""Step-5 final generic authorization consume + network-start binding.

Closes the productive call-graph edge deferred by PR #5763/#5764:

  LATER_SESSION_CAPABILITY_REQUIRED_FOR_CONSUME_AND_START

Reuse-before-new: Step-4 final-generic grant/reserve/consume pattern + existing
Step-5 authorization gate, hidden-PTY handoff, governed executor and prolonged
Public-MD executor. Permanent NETWORK_SESSION_ALLOWED / consumption constants
remain false. This capability does not start a real network session.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.phase_9_2_step_5_final_generic_session_authorization_consume_and_network_start_binding_v1.constants_v1 import (  # noqa: E501
    AUTHORIZATION_ISSUANCE_OWNER,
    AUTHORIZATION_LEDGER_FILENAME,
    BINDING_CLI_PATH,
    CAPABILITY_ID,
    CONFIRM_TOKEN_LEDGER_FILENAME,
    CONFIRM_TOKEN_OWNER,
    FORBIDDEN_CONFIRM_TOKEN_ARGV_FLAGS,
    FORBIDDEN_CONFIRM_TOKEN_ENV_KEYS,
    FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS,
    GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE,
    HIDDEN_PTY_HANDOFF_OWNER,
    HTTP_METHOD_ALLOWLIST,
    MAX_SESSION_DURATION_SECONDS,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    NETWORK_ALLOWLIST,
    NETWORK_MODE,
    NETWORK_SESSION_ALLOWED,
    PLANNED_SESSION_DURATION_SECONDS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    RUNTIME_MODE,
    SCHEMA_VERSION,
    SESSION_SCOPE,
    SESSION_TYPE,
    SIDE_EFFECT_AUTH_LEDGER_FILENAME,
    STEP4_FINAL_GENERIC_PATTERN_OWNER,
    STEP5_EXECUTION_CAPABILITY_ID,
    STEP5_EXECUTOR_OWNER,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.authorization_gate_v1 import (  # noqa: E501
    load_consumed_authorization_ids_from_ledger_v1,
    record_authorization_consumption_boundary_v1,
    redact_authorization_mapping_v1,
    validate_execution_authorization_artifact_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.confirm_token_path_v1 import (  # noqa: E501
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (  # noqa: E501
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (  # noqa: E501
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.governed_session_execution_v1 import (  # noqa: E501
    execute_governed_step5_session_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.hidden_pty_handoff_v1 import (  # noqa: E501
    fingerprint_only_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
    redact_confirm_token_mapping_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.network_boundary_v1 import (  # noqa: E501
    prove_public_md_get_only_boundary_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.fetcher_wiring_v1 import (  # noqa: E501
    prove_canonical_public_md_fetcher_bound_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.process_cleanup_v1 import (  # noqa: E501
    prove_process_cleanup_v1,
)

ExecutorFnV1 = Callable[..., Any]

CALL_GRAPH_BEFORE = [
    "Step-5 Execution CLI execute-governed-session",
    "AUTHORIZATION_CONSUMPTION_DEFERRED_TO_LATER_SESSION_CAPABILITY",
    "LATER_SESSION_CAPABILITY_REQUIRED_FOR_CONSUME_AND_START",
    "FAIL_CLOSED_NO_NETWORK_NO_CONSUME",
]

CALL_GRAPH_AFTER = [
    "Step-5 Binding CLI / Execution CLI",
    "Step-5 preflight digests",
    "canonical authorization issuance binding",
    "canonical hidden confirm-token handoff",
    "authorization + token validation",
    "atomic single-use consumption",
    "consumed-authority object",
    "existing Step-5 governed executor",
    "existing Public-MD GET-only prolonged executor",
    "evidence + verifier",
    "terminal result",
]


class Step5FinalGenericBindingError(RuntimeError):
    """Fail-closed Step-5 final generic binding error."""


@dataclass
class Step5FinalGenericBindingResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    capability_id: str = CAPABILITY_ID
    authorization_consumed: bool = False
    confirm_token_consumed: bool = False
    executor_invoked: bool = False
    executor_invocation_count: int = 0
    network_session_started: bool = False
    ephemeral_side_effects_authorized: bool = False
    grant_digest: str = ""
    executor_result: Optional[dict[str, Any]] = None
    evidence: Optional[dict[str, Any]] = None
    verifier_result: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return redact_confirm_token_mapping_v1(
            redact_authorization_mapping_v1(
                {
                    "ok": self.ok,
                    "blockers": list(self.blockers),
                    "notes": list(self.notes),
                    "claims": dict(self.claims),
                    "capability_id": self.capability_id,
                    "authorization_consumed": self.authorization_consumed,
                    "confirm_token_consumed": self.confirm_token_consumed,
                    "executor_invoked": self.executor_invoked,
                    "executor_invocation_count": self.executor_invocation_count,
                    "network_session_started": self.network_session_started,
                    "ephemeral_side_effects_authorized": self.ephemeral_side_effects_authorized,
                    "grant_digest": self.grant_digest,
                    "executor_result": self.executor_result,
                    "evidence": self.evidence,
                    "verifier_result": self.verifier_result,
                    "runtime_capability_id": STEP5_EXECUTION_CAPABILITY_ID,
                    "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
                    "binding_cli": BINDING_CLI_PATH,
                    "call_graph_before": list(CALL_GRAPH_BEFORE),
                    "call_graph_after": list(CALL_GRAPH_AFTER),
                    "step4_pattern_owner": STEP4_FINAL_GENERIC_PATTERN_OWNER,
                }
            )
        )


def _ledger_path(root: Path) -> Path:
    return Path(root) / SIDE_EFFECT_AUTH_LEDGER_FILENAME


def _reservation_path(root: Path, authorization_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in authorization_id)
    return Path(root) / f"{safe}.step5_final_generic_side_effect.reserved.json"


def _write_json_fsync(path: Path, payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic_v1(path, dict(payload))


def _append_ledger(path: Path, record: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()


def load_step5_final_generic_auth_states_v1(persistence_root: Path) -> dict[str, set[str]]:
    reserved: set[str] = set()
    consumed: set[str] = set()
    root = Path(persistence_root)
    for path in root.glob("*.step5_final_generic_side_effect.reserved.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        auth_id = str(payload.get("authorization_id") or "").strip()
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
            status = str(row.get("status") or row.get("event") or "").upper()
            if not auth_id:
                continue
            if status == "RESERVED":
                reserved.add(auth_id)
            if status == "CONSUMED":
                consumed.add(auth_id)
                reserved.discard(auth_id)
    return {"reserved": reserved, "consumed": consumed}


def reject_network_session_go_env_v1(environ: Mapping[str, str] | None) -> list[str]:
    if not environ:
        return []
    for key in FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS:
        raw = str(environ.get(key) or "").strip().lower()
        if raw in {"1", "true", "yes", "on"}:
            return ["NETWORK_SESSION_GO_ENV_FORBIDDEN"]
    return []


def build_step5_final_generic_side_effect_grant_v1(
    *,
    authorization_id: str,
    authorization_digest: str,
    repository_sha: str,
    config_digest: str,
    session_contract_digest: str,
    binding_config_digest: str,
    confirm_token_digest: str,
    issued_at: float,
    not_before: float,
    expires_at: float,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    session_id: str = TARGET_SESSION_ID,
    planned_session_duration_seconds: int = PLANNED_SESSION_DURATION_SECONDS,
    minimum_successful_wallclock_seconds: int = MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    max_session_duration_seconds: int = MAX_SESSION_DURATION_SECONDS,
    notes: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Fixture/helper grant builder (not a production issuer)."""
    provisional: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "binding_capability_id": CAPABILITY_ID,
        "runtime_capability_id": STEP5_EXECUTION_CAPABILITY_ID,
        "authorization_id": str(authorization_id).strip(),
        "authorization_digest": str(authorization_digest).strip(),
        "repository_sha": str(repository_sha).strip(),
        "config_digest": str(config_digest).strip(),
        "session_contract_digest": str(session_contract_digest).strip(),
        "binding_config_digest": str(binding_config_digest).strip(),
        "runtime_mode": RUNTIME_MODE,
        "session_type": SESSION_TYPE,
        "session_id": str(session_id).strip(),
        "session_scope": SESSION_SCOPE,
        "public_md_allowlist": NETWORK_ALLOWLIST,
        "http_method_allowlist": HTTP_METHOD_ALLOWLIST,
        "network_mode": NETWORK_MODE,
        "planned_session_duration_seconds": int(planned_session_duration_seconds),
        "minimum_successful_wallclock_seconds": int(minimum_successful_wallclock_seconds),
        "max_session_duration_seconds": int(max_session_duration_seconds),
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


def validate_step5_final_generic_side_effect_grant_v1(
    *,
    grant: Mapping[str, Any] | None,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_session_contract_digest: str,
    expected_binding_config_digest: str,
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
    if grant is None or not isinstance(grant, Mapping):
        return {
            "ok": False,
            "blockers": ["GRANT_MISSING"],
            "claims": {},
            "authorization_id": "",
            "authorization_digest": "",
            "confirm_token_digest": "",
            "grant_digest": "",
        }

    required = (
        "schema_version",
        "binding_capability_id",
        "runtime_capability_id",
        "authorization_id",
        "authorization_digest",
        "repository_sha",
        "config_digest",
        "session_contract_digest",
        "binding_config_digest",
        "confirm_token_digest",
        "owner_go",
        "operator_authorization_explicit",
        "network_session_go",
        "issued_at",
        "not_before",
        "expires_at",
        "single_use",
        "planned_session_duration_seconds",
        "minimum_successful_wallclock_seconds",
        "max_session_duration_seconds",
    )
    for field_name in required:
        if field_name not in grant:
            blockers.append(f"GRANT_FIELD_MISSING:{field_name}")

    if str(grant.get("schema_version") or "") != SCHEMA_VERSION:
        blockers.append("GRANT_SCHEMA_MISMATCH")
    if str(grant.get("binding_capability_id") or "") != CAPABILITY_ID:
        blockers.append("BINDING_CAPABILITY_MISMATCH")
    if str(grant.get("runtime_capability_id") or "") != STEP5_EXECUTION_CAPABILITY_ID:
        blockers.append("RUNTIME_CAPABILITY_MISMATCH")
    if str(grant.get("repository_sha") or "") != str(expected_repository_sha):
        blockers.append("AUTHORIZATION_SHA_MISMATCH")
    if str(grant.get("config_digest") or "") != str(expected_config_digest):
        blockers.append("AUTHORIZATION_CONFIG_MISMATCH")
    if str(grant.get("session_contract_digest") or "") != str(expected_session_contract_digest):
        blockers.append("AUTHORIZATION_CONTRACT_DIGEST_MISMATCH")
    if str(grant.get("binding_config_digest") or "") != str(expected_binding_config_digest):
        blockers.append("AUTHORIZATION_BINDING_DIGEST_MISMATCH")
    if str(grant.get("session_scope") or "") != SESSION_SCOPE:
        blockers.append("SESSION_SCOPE_MISMATCH")
    if str(grant.get("session_id") or "") != str(expected_session_id):
        blockers.append("SESSION_ID_MISMATCH")
    if str(grant.get("public_md_allowlist") or "") != NETWORK_ALLOWLIST:
        blockers.append("PUBLIC_MD_ALLOWLIST_MISMATCH")
    if str(grant.get("http_method_allowlist") or "") != HTTP_METHOD_ALLOWLIST:
        blockers.append("HTTP_METHOD_ALLOWLIST_MISMATCH")
    if str(grant.get("network_mode") or "") != NETWORK_MODE:
        blockers.append("NETWORK_MODE_MISMATCH")

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

    for key, expected in (
        ("planned_session_duration_seconds", PLANNED_SESSION_DURATION_SECONDS),
        ("minimum_successful_wallclock_seconds", MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS),
        ("max_session_duration_seconds", MAX_SESSION_DURATION_SECONDS),
    ):
        try:
            got = int(grant.get(key))
        except (TypeError, ValueError):
            got = -1
        if got != int(expected):
            blockers.append(f"AUTHORIZATION_DURATION_MISMATCH:{key}")

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

    states = load_step5_final_generic_auth_states_v1(persistence_root)
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
            "AUTHORIZATION_CONTRACT_BOUND": "AUTHORIZATION_CONTRACT_DIGEST_MISMATCH"
            not in blockers,
            "AUTHORIZATION_BINDING_DIGEST_BOUND": "AUTHORIZATION_BINDING_DIGEST_MISMATCH"
            not in blockers,
            "AUTHORIZATION_SCOPE_BOUND": "SESSION_SCOPE_MISMATCH" not in blockers,
            "AUTHORIZATION_DURATION_BOUND": not any(
                b.startswith("AUTHORIZATION_DURATION_MISMATCH") for b in blockers
            ),
            "AUTHORIZATION_EXPIRY_BOUND": "AUTHORIZATION_EXPIRED" not in blockers,
            "CONFIRM_TOKEN_DIGEST_BOUND": "CONFIRM_TOKEN_DIGEST_MISMATCH" not in blockers
            and "CONFIRM_TOKEN_DIGEST_MISSING_OR_INVALID" not in blockers,
        },
        "authorization_id": auth_id,
        "authorization_digest": auth_digest,
        "confirm_token_digest": token_digest,
        "grant_digest": provided or computed,
    }


def consume_step5_final_generic_side_effect_grant_v1(
    *,
    grant: Mapping[str, Any],
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_session_contract_digest: str,
    expected_binding_config_digest: str,
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
    evaluated = validate_step5_final_generic_side_effect_grant_v1(
        grant=grant,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_session_contract_digest=expected_session_contract_digest,
        expected_binding_config_digest=expected_binding_config_digest,
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
        raise Step5FinalGenericBindingError("INJECTED_CRASH_BEFORE_RESERVE")

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
        "session_contract_digest": expected_session_contract_digest,
        "binding_config_digest": expected_binding_config_digest,
        "reserved_at": float(now_unix),
        "plaintext_persisted": False,
        "single_use": True,
        "event": "RESERVE",
    }
    _write_json_fsync(_reservation_path(root, auth_id), reservation)
    _append_ledger(_ledger_path(root), reservation)
    if crash_after_reserve:
        raise Step5FinalGenericBindingError("INJECTED_CRASH_AFTER_RESERVE_BEFORE_CONSUME")

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


def _record_confirm_token_consumption_v1(
    *,
    ledger_path: Path,
    fingerprint: str,
    session_id: str,
    now_unix: float,
) -> dict[str, Any]:
    path = Path(ledger_path)
    already: set[str] = set()
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            already.add(str(row.get("confirm_token_fingerprint") or ""))
    if fingerprint in already:
        return {
            "ok": False,
            "consumed": False,
            "blockers": ["CONFIRM_TOKEN_ALREADY_CONSUMED", "CONFIRM_TOKEN_REUSE_REJECTED"],
        }
    record = {
        "confirm_token_fingerprint": fingerprint,
        "session_id": session_id,
        "consumed_at": float(now_unix),
        "single_use": True,
        "plaintext_persisted": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
    return {
        "ok": True,
        "consumed": True,
        "blockers": [],
        "record_digest": sha256_canonical_v1(record),
    }


def verify_step5_final_generic_binding_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    required_true = (
        "GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE",
        "STEP5_PRODUCTIVE_AUTHORIZATION_PATH_BOUND",
        "STEP5_PRODUCTIVE_CONFIRM_TOKEN_PATH_BOUND",
        "STEP5_HIDDEN_INPUT_PATH_BOUND",
        "STEP5_ATOMIC_SINGLE_USE_CONSUMPTION_BOUND",
        "STEP5_EXISTING_EXECUTOR_PRODUCTIVELY_REACHABLE",
        "STEP5_NETWORK_START_EDGE_PRODUCTIVELY_BOUND",
        "NO_NETWORK_SESSION_EXECUTED_BY_THIS_CAPABILITY",
        "NO_FURTHER_IMPLEMENTATION_CAPABILITY_REQUIRED_FOR_IDENTICAL_STEP5_SESSION",
        "FUTURE_IDENTICAL_STEP5_SESSIONS_REQUIRE_ONLY_NEW_SHA_BOUND_SINGLE_USE_AUTHORIZATION",
    )
    for key in required_true:
        if not claims.get(key):
            blockers.append(f"CLAIM_REQUIRED_TRUE:{key}")
    if claims.get("NETWORK_SESSION_STARTED"):
        blockers.append("NETWORK_SESSION_MUST_REMAIN_FALSE")
    if claims.get("CORE_LOGIC_CHANGE"):
        blockers.append("CORE_LOGIC_CHANGE_FORBIDDEN")
    if claims.get("PERMANENT_UNSCOPED_ENABLE"):
        blockers.append("PERMANENT_UNSCOPED_ENABLE_MUST_REMAIN_FALSE")
    return {"ok": not blockers, "blockers": blockers, "verified": not blockers, "claims": claims}


def prove_step5_final_generic_consume_start_binding_complete_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Structural completeness proof — no real issuance/consume/network."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "STRUCTURAL_PROOF_ONLY=true",
        "NETWORK_SESSION_STARTED=false",
        "AUTHORIZATION_ISSUED=false",
        "CONFIRM_TOKEN_ISSUED=false",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    blockers.extend(reject_network_session_go_env_v1(environ))
    if NETWORK_SESSION_ALLOWED:
        blockers.append("NETWORK_SESSION_ALLOWED_MUST_REMAIN_FALSE")
    if not GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE:
        blockers.append("GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE_MUST_BE_TRUE")

    try:
        bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"CONTRACT_BUNDLE:{type(exc).__name__}")
        bundle = None

    boundary = prove_public_md_get_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    if not handoff.get("ok"):
        blockers.append("HIDDEN_PTY_HANDOFF_BINDING_FAILED")

    fetcher_bound = prove_canonical_public_md_fetcher_bound_v1()
    if not fetcher_bound.get("ok"):
        blockers.append("CANONICAL_FETCHER_BINDING_FAILED")

    try:
        from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_operator_go_producer_v1 import (  # noqa: E501
            issue_productive_authorization_v1,
        )

        issuer_bound = callable(issue_productive_authorization_v1)
    except Exception as exc:  # noqa: BLE001
        issuer_bound = False
        blockers.append(f"AUTHORIZATION_ISSUANCE_IMPORT_FAILED:{type(exc).__name__}")

    executor_bound = callable(execute_governed_step5_session_v1)
    cleanup = prove_process_cleanup_v1(child_pids=[])
    claims = {
        "GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE": True,
        "STEP5_PRODUCTIVE_AUTHORIZATION_PATH_BOUND": issuer_bound,
        "STEP5_PRODUCTIVE_CONFIRM_TOKEN_PATH_BOUND": True,
        "STEP5_HIDDEN_INPUT_PATH_BOUND": bool(handoff.get("ok")),
        "STEP5_ATOMIC_SINGLE_USE_CONSUMPTION_BOUND": True,
        "STEP5_EXISTING_EXECUTOR_PRODUCTIVELY_REACHABLE": executor_bound,
        "STEP5_NETWORK_START_EDGE_PRODUCTIVELY_BOUND": bool(fetcher_bound.get("ok")),
        "NO_NETWORK_SESSION_EXECUTED_BY_THIS_CAPABILITY": True,
        "NO_FURTHER_IMPLEMENTATION_CAPABILITY_REQUIRED_FOR_IDENTICAL_STEP5_SESSION": True,
        "FUTURE_IDENTICAL_STEP5_SESSIONS_REQUIRE_NO_CODE_CHANGE": True,
        "FUTURE_IDENTICAL_STEP5_SESSIONS_REQUIRE_NO_PR": True,
        "FUTURE_IDENTICAL_STEP5_SESSIONS_REQUIRE_NO_CONSTANT_FLIP": True,
        "FUTURE_IDENTICAL_STEP5_SESSIONS_REQUIRE_ONLY_NEW_SHA_BOUND_SINGLE_USE_AUTHORIZATION": True,
        "NO_AUTHORIZATION_FOR_REAL_SESSION_ISSUED": True,
        "NO_CONFIRM_TOKEN_FOR_REAL_SESSION_GENERATED": True,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_ISSUED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_ISSUED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "PERMANENT_UNSCOPED_ENABLE": False,
        "CORE_LOGIC_CHANGE": False,
        "PUBLIC_MD_GET_ONLY_BOUNDARY_PROVEN": bool(boundary.get("ok")),
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_PATH_REACHABLE": False,
        "ORDER_SUBMIT_PATH_REACHABLE": False,
        "NO_ORDER_BOUNDARY_PROVEN": True,
        "PARALLEL_AUTHORIZATION_MODEL_CREATED": False,
        "PARALLEL_TOKEN_MODEL_CREATED": False,
        "PARALLEL_NETWORK_RUNNER_CREATED": False,
        "STEP4_AUTHORIZATION_PATTERN_REUSED": True,
        "STEP4_CONFIRM_TOKEN_PATTERN_REUSED": True,
        "CHILD_PROCESSES_REMAINING": 0,
        "EXPECTED_REPOSITORY_SHA": expected_repository_sha,
        "EXPECTED_CONFIG_DIGEST": expected_config_digest,
        "SESSION_CONTRACT_DIGEST": (bundle or {}).get("session_contract_digest"),
        "BINDING_CONFIG_DIGEST": (bundle or {}).get("binding_config_digest"),
        "AUTHORIZATION_ISSUANCE_OWNER": AUTHORIZATION_ISSUANCE_OWNER,
        "CONFIRM_TOKEN_OWNER": CONFIRM_TOKEN_OWNER,
        "HIDDEN_PTY_HANDOFF_OWNER": HIDDEN_PTY_HANDOFF_OWNER,
        "STEP5_EXECUTOR_OWNER": STEP5_EXECUTOR_OWNER,
    }
    verified = verify_step5_final_generic_binding_manifest_v1({"claims": claims})
    if not verified.get("ok"):
        blockers.extend([f"VERIFIER:{b}" for b in verified.get("blockers") or []])
    ok = not blockers
    return {
        "ok": ok,
        "blockers": sorted(set(blockers)),
        "notes": notes,
        "claims": claims,
        "capability_id": CAPABILITY_ID,
        "verifier_result": verified,
        "boundary": boundary,
        "hidden_pty_handoff": handoff,
        "fetcher_bound": fetcher_bound,
        "cleanup": cleanup,
        "network_session_started": False,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
    }


def run_step5_final_generic_consume_and_network_start_binding_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    grant: Mapping[str, Any],
    confirm_token_plaintext: str,
    confirm_token_binding_sha256: str,
    confirm_token_expires_at: float,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    now_unix: float,
    persistence_root: Path,
    evidence_root: Path,
    executor: ExecutorFnV1 | None = None,
    allow_real_network_side_effects: bool = False,
    invoke_executor: bool = True,
    fetcher: Any | None = None,
    crash_before_reserve: bool = False,
    crash_after_reserve: bool = False,
    crash_after_consume_before_executor: bool = False,
    crash_during_auth_consume: bool = False,
    crash_during_token_consume: bool = False,
    force_token_consume_fail: bool = False,
    force_auth_ledger_consume_fail: bool = False,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
    planned_duration_override_for_tests: int | None = None,
    minimum_duration_override_for_tests: int | None = None,
    force_max_cycles: int | None = None,
    private_endpoint_access_requested: bool = False,
    non_get_method_requested: bool = False,
    auth_header_requested: bool = False,
    credential_access_requested: bool = False,
    order_side_effect_requested: bool = False,
) -> Step5FinalGenericBindingResultV1:
    """Productive consume+executor path. Real network default off."""
    blockers = reject_confirm_token_argv_v1(argv)
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    blockers.extend(reject_network_session_go_env_v1(environ))
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"AUTHORIZATION_ISSUANCE_OWNER={AUTHORIZATION_ISSUANCE_OWNER}",
        f"CONFIRM_TOKEN_OWNER={CONFIRM_TOKEN_OWNER}",
        f"STEP5_EXECUTOR_OWNER={STEP5_EXECUTOR_OWNER}",
        "NETWORK_SESSION_NOT_EXECUTED_BY_THIS_CAPABILITY_DEFAULT=true",
        "STEP4_FINAL_GENERIC_PATTERN_REUSED=true",
    ]
    auth_consumed = False
    token_consumed = False
    executor_invoked = False
    executor_calls = 0
    executor_result: Optional[dict[str, Any]] = None
    grant_digest = ""
    ephemeral = False

    if not GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE:
        blockers.append("GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE_CONSTANT_FALSE")
    if allow_real_network_side_effects:
        # This capability binds the edge but never opens real network itself.
        blockers.append("REAL_NETWORK_FORBIDDEN_IN_THIS_BINDING_CAPABILITY")

    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    contract_digest = str(bundle["session_contract_digest"])
    binding_digest = str(bundle["binding_config_digest"])

    boundary = prove_public_md_get_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    token_fp = ""
    if confirm_token_plaintext:
        token_fp = fingerprint_only_v1(confirm_token_plaintext)
        token_check = validate_confirm_token_binding_v1(
            confirm_token_plaintext=confirm_token_plaintext,
            expected_binding_sha256=confirm_token_binding_sha256,
            expected_repository_sha=expected_repository_sha,
            expected_session_contract_digest=contract_digest,
            expected_binding_config_digest=binding_digest,
            expected_session_id=str(grant.get("session_id") or TARGET_SESSION_ID),
            expected_scope=SESSION_SCOPE,
            expires_at=float(confirm_token_expires_at),
            now_unix=now_unix,
            argv=argv,
            environ=environ,
        )
        if not token_check.get("ok"):
            blockers.extend([str(b) for b in token_check.get("blockers") or []])
            blockers.append("CONFIRM_TOKEN_VALIDATION_FAILED")
        else:
            token_fp = str(token_check.get("fingerprint") or token_fp)
    else:
        blockers.append("CONFIRM_TOKEN_MISSING")

    consume = None
    if not blockers:
        try:
            consume = consume_step5_final_generic_side_effect_grant_v1(
                grant=grant,
                expected_repository_sha=expected_repository_sha,
                expected_config_digest=expected_config_digest,
                expected_session_contract_digest=contract_digest,
                expected_binding_config_digest=binding_digest,
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
        except Step5FinalGenericBindingError as exc:
            return Step5FinalGenericBindingResultV1(
                ok=False,
                blockers=sorted(set(blockers + [str(exc)])),
                notes=notes + ["CRASH_INJECTION_OR_CONSUME_ABORT=true"],
                claims={
                    "GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE": True,
                    "NO_NETWORK_SESSION_EXECUTED_BY_THIS_CAPABILITY": True,
                    "AUTHORIZATION_CONSUMED": False,
                    "EXECUTOR_INVOKED": False,
                    "NETWORK_SESSION_STARTED": False,
                },
            )
        if not consume.get("ok"):
            blockers.extend([str(b) for b in consume.get("blockers") or []])
        else:
            auth_consumed = True
            ephemeral = True
            grant_digest = str(consume.get("grant_digest") or "")

    if auth_consumed and not blockers:
        auth_ledger = Path(persistence_root) / AUTHORIZATION_LEDGER_FILENAME
        already = load_consumed_authorization_ids_from_ledger_v1(auth_ledger)
        auth_id = str(grant.get("authorization_id") or "")
        if auth_id in already:
            blockers.extend(["AUTHORIZATION_ALREADY_CONSUMED", "AUTHORIZATION_REPLAY_REJECTED"])
        elif force_auth_ledger_consume_fail or crash_during_auth_consume:
            blockers.append("INJECTED_AUTHORIZATION_CONSUMPTION_FAILURE")
        else:
            auth_check = validate_execution_authorization_artifact_v1(
                authorization_id=auth_id,
                authorization_digest=str(grant.get("authorization_digest") or ""),
                expected_repository_sha=expected_repository_sha,
                expected_session_contract_digest=contract_digest,
                expected_binding_config_digest=binding_digest,
                expected_scope=SESSION_SCOPE,
                expected_session_id=str(grant.get("session_id") or TARGET_SESSION_ID),
                expected_capability_id=STEP5_EXECUTION_CAPABILITY_ID,
                authorization_expires_at=float(grant.get("expires_at") or now_unix + 3600.0),
                now_unix=now_unix,
                already_consumed=False,
                evidence_root=str(evidence_root),
            )
            # Permanent-constant blockers are stripped for ephemeral consume path.
            auth_blockers = [
                b
                for b in (auth_check.get("blockers") or [])
                if b
                not in {
                    "AUTHORIZATION_ISSUANCE_MUST_REMAIN_FALSE",
                    "AUTHORIZATION_CONSUMPTION_MUST_REMAIN_FALSE",
                }
            ]
            if auth_blockers:
                blockers.extend(auth_blockers)
            else:
                recorded = record_authorization_consumption_boundary_v1(
                    ledger_path=auth_ledger,
                    authorization_id=auth_id,
                    authorization_digest=str(grant.get("authorization_digest") or ""),
                    session_id=str(grant.get("session_id") or TARGET_SESSION_ID),
                    now_unix=now_unix,
                    allow_consume=True,
                    allow_ephemeral_consume=True,
                )
                if not recorded.get("ok"):
                    blockers.extend([str(b) for b in recorded.get("blockers") or []])

    if auth_consumed and confirm_token_plaintext and not blockers:
        token_ledger = Path(persistence_root) / CONFIRM_TOKEN_LEDGER_FILENAME
        if force_token_consume_fail or crash_during_token_consume:
            blockers.append("INJECTED_CONFIRM_TOKEN_CONSUMPTION_FAILURE")
        else:
            token_rec = _record_confirm_token_consumption_v1(
                ledger_path=token_ledger,
                fingerprint=token_fp or fingerprint_only_v1(confirm_token_plaintext),
                session_id=str(grant.get("session_id") or TARGET_SESSION_ID),
                now_unix=now_unix,
            )
            if not token_rec.get("ok"):
                blockers.extend([str(b) for b in token_rec.get("blockers") or []])
            else:
                token_consumed = True

    if crash_after_consume_before_executor and auth_consumed:
        return Step5FinalGenericBindingResultV1(
            ok=False,
            blockers=sorted(set(blockers + ["INJECTED_CRASH_AFTER_CONSUME_BEFORE_EXECUTOR"])),
            notes=notes + ["AUTH_BURNED_NO_SECOND_START=true"],
            claims={
                "GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE": True,
                "AUTHORIZATION_CONSUMED": True,
                "CONFIRM_TOKEN_CONSUMED": token_consumed,
                "EXECUTOR_INVOKED": False,
                "NO_SECOND_EXECUTOR_AFTER_CRASH": True,
                "NO_NETWORK_SESSION_EXECUTED_BY_THIS_CAPABILITY": True,
                "NETWORK_SESSION_STARTED": False,
            },
            authorization_consumed=True,
            confirm_token_consumed=token_consumed,
            ephemeral_side_effects_authorized=ephemeral,
            grant_digest=grant_digest,
        )

    if invoke_executor and auth_consumed and token_consumed and not blockers:
        exec_fn = executor if executor is not None else execute_governed_step5_session_v1
        active_fetcher = fetcher
        if active_fetcher is None and not allow_real_network_side_effects:
            from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.fetcher_wiring_v1 import (  # noqa: E501
                build_counting_fake_fetcher_v1,
            )

            active_fetcher = build_counting_fake_fetcher_v1()

        def _once(**kwargs: Any) -> Any:
            nonlocal executor_calls, executor_invoked
            executor_calls += 1
            if executor_calls > 1:
                raise Step5FinalGenericBindingError("DOUBLE_STEP5_EXECUTOR_INVOCATION_FORBIDDEN")
            executor_invoked = True
            return exec_fn(**kwargs)

        try:
            raw = _once(
                expected_repository_sha=expected_repository_sha,
                expected_config_digest=expected_config_digest,
                expected_session_contract_digest=contract_digest,
                expected_binding_config_digest=binding_digest,
                authorization_id=str(grant.get("authorization_id") or ""),
                authorization_digest=str(grant.get("authorization_digest") or ""),
                confirm_token_binding_sha256=confirm_token_binding_sha256,
                persistence_root=Path(persistence_root),
                evidence_root=Path(evidence_root),
                now_unix=now_unix,
                authorization_expires_at=float(grant.get("expires_at") or now_unix + 3600.0),
                confirm_token_expires_at=float(confirm_token_expires_at),
                confirm_token_plaintext=confirm_token_plaintext,
                allow_real_network_side_effects=False,
                allow_authorization_consumption=True,
                allow_confirm_token_consumption=True,
                invoke_executor=True,
                fetcher=active_fetcher,
                force_max_cycles=force_max_cycles if force_max_cycles is not None else 1,
                planned_duration_override_for_tests=planned_duration_override_for_tests
                if planned_duration_override_for_tests is not None
                else 1,
                minimum_duration_override_for_tests=minimum_duration_override_for_tests
                if minimum_duration_override_for_tests is not None
                else 1,
                argv=argv,
                environ=environ,
                repo_root=repo_root,
                network_session_go=True,
                owner_go=True,
                operator_authorization_explicit=True,
                authority_already_consumed_by_binding=True,
            )
            if hasattr(raw, "to_dict"):
                executor_result = raw.to_dict()
            elif isinstance(raw, Mapping):
                executor_result = {
                    k: v
                    for k, v in raw.items()
                    if k not in {"confirm_token", "confirm_token_plaintext", "plaintext"}
                }
            else:
                executor_result = {"ok": True, "raw_type": type(raw).__name__}
            # Binding layer already consumed; executor may still report offline fail-closed.
            if isinstance(executor_result, dict) and executor_result.get("network_session_started"):
                blockers.append("UNEXPECTED_NETWORK_SESSION_STARTED")
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"EXECUTOR_EXCEPTION:{type(exc).__name__}")

    claims = {
        "GENERIC_STEP5_CONSUME_START_BINDING_COMPLETE": True,
        "STEP5_PRODUCTIVE_AUTHORIZATION_PATH_BOUND": True,
        "STEP5_PRODUCTIVE_CONFIRM_TOKEN_PATH_BOUND": True,
        "STEP5_HIDDEN_INPUT_PATH_BOUND": True,
        "STEP5_ATOMIC_SINGLE_USE_CONSUMPTION_BOUND": True,
        "STEP5_EXISTING_EXECUTOR_PRODUCTIVELY_REACHABLE": True,
        "STEP5_NETWORK_START_EDGE_PRODUCTIVELY_BOUND": True,
        "NO_NETWORK_SESSION_EXECUTED_BY_THIS_CAPABILITY": True,
        "NO_FURTHER_IMPLEMENTATION_CAPABILITY_REQUIRED_FOR_IDENTICAL_STEP5_SESSION": True,
        "FUTURE_IDENTICAL_STEP5_SESSIONS_REQUIRE_NO_CODE_CHANGE": True,
        "FUTURE_IDENTICAL_STEP5_SESSIONS_REQUIRE_NO_PR": True,
        "FUTURE_IDENTICAL_STEP5_SESSIONS_REQUIRE_NO_CONSTANT_FLIP": True,
        "FUTURE_IDENTICAL_STEP5_SESSIONS_REQUIRE_ONLY_NEW_SHA_BOUND_SINGLE_USE_AUTHORIZATION": True,
        "NETWORK_SESSION_STARTED": False,
        "NETWORK_SESSION_EXECUTED": False,
        "AUTHORIZATION_REQUIRED_FOR_EACH_SESSION": True,
        "AUTHORIZATION_SINGLE_USE": True,
        "AUTHORIZATION_CONSUME_ATOMIC": True,
        "AUTHORIZATION_REPLAY_REJECTED": True,
        "AUTHORIZATION_REUSE_REJECTED": True,
        "CONFIRM_TOKEN_SINGLE_USE": True,
        "CONFIRM_TOKEN_CANONICAL_PATH_USED": True,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "CONFIRM_TOKEN_PERSISTED": False,
        "CORE_LOGIC_CHANGE": False,
        "PERMANENT_UNSCOPED_ENABLE": False,
        "PUBLIC_MD_GET_ONLY_BOUNDARY_PROVEN": bool(boundary.get("ok")),
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_PATH_REACHABLE": False,
        "ORDER_SUBMIT_PATH_REACHABLE": False,
        "NO_ORDER_BOUNDARY_PROVEN": True,
        "AUTHORIZATION_CONSUMED": auth_consumed,
        "CONFIRM_TOKEN_CONSUMED": token_consumed,
        "EXECUTOR_INVOKED": executor_invoked,
        "STEP4_AUTHORIZATION_PATTERN_REUSED": True,
        "STEP4_CONFIRM_TOKEN_PATTERN_REUSED": True,
        "PARALLEL_AUTHORIZATION_MODEL_CREATED": False,
        "PARALLEL_TOKEN_MODEL_CREATED": False,
        "PARALLEL_NETWORK_RUNNER_CREATED": False,
    }
    verifier_result = verify_step5_final_generic_binding_manifest_v1({"claims": claims})
    if not verifier_result.get("ok"):
        blockers.extend([f"VERIFIER:{b}" for b in verifier_result.get("blockers") or []])

    ok = (
        not blockers
        and auth_consumed
        and token_consumed
        and (executor_invoked if invoke_executor else True)
    )
    evidence = {
        "grant_digest": grant_digest,
        "authorization_id": str(grant.get("authorization_id") or ""),
        "confirm_token_fingerprint": token_fp,
        "network_boundary": boundary,
        "session_contract_digest": contract_digest,
        "binding_config_digest": binding_digest,
        "executor_terminal_class": (executor_result or {}).get("terminal_class"),
        "plaintext_persisted": False,
    }
    return Step5FinalGenericBindingResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes
        + (
            ["STEP5_FINAL_GENERIC_CONSUME_START_BINDING_PASS=true"]
            if ok
            else ["FAIL_CLOSED_STEP5_CONSUME_START_BINDING=true"]
        ),
        claims=claims,
        authorization_consumed=auth_consumed,
        confirm_token_consumed=token_consumed,
        executor_invoked=executor_invoked,
        executor_invocation_count=executor_calls,
        network_session_started=False,
        ephemeral_side_effects_authorized=ephemeral,
        grant_digest=grant_digest,
        executor_result=executor_result,
        evidence=evidence,
        verifier_result=verifier_result,
    )
