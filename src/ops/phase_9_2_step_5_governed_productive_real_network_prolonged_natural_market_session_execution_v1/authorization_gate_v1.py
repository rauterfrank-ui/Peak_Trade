"""Authorization gate for Step-5 execution (validate-only in this capability)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.authorization_binding_v1 import (
    validate_authorization_binding_v1 as validate_step5_binding_auth_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_ISSUANCE_ALLOWED,
    AUTHORIZATION_LEDGER_FILENAME,
    CAPABILITY_ID,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    NETWORK_MODE,
    PLANNED_SESSION_DURATION_SECONDS,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
)


def load_consumed_authorization_ids_from_ledger_v1(ledger_path: Path) -> set[str]:
    consumed: set[str] = set()
    path = Path(ledger_path)
    if not path.is_file():
        return consumed
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        consumed.add(str(row.get("authorization_id") or ""))
    return consumed


def validate_execution_authorization_artifact_v1(
    *,
    authorization_id: str,
    authorization_digest: str,
    expected_repository_sha: str,
    expected_session_contract_digest: str,
    expected_binding_config_digest: str,
    expected_scope: str = SESSION_SCOPE,
    expected_session_id: str = TARGET_SESSION_ID,
    expected_capability_id: str = CAPABILITY_ID,
    planned_session_duration_seconds: int = PLANNED_SESSION_DURATION_SECONDS,
    network_mode: str = NETWORK_MODE,
    public_md_endpoint_allowlist: str = NETWORK_ALLOWLIST,
    http_method_allowlist: str = HTTP_METHOD_ALLOWLIST,
    evidence_root: str = "",
    authorization_repository_sha: str = "",
    authorization_scope: str = SESSION_SCOPE,
    authorization_session_id: str = TARGET_SESSION_ID,
    authorization_capability_id: str = CAPABILITY_ID,
    authorization_session_contract_digest: str = "",
    authorization_binding_config_digest: str = "",
    authorization_planned_duration_seconds: int | None = None,
    authorization_network_mode: str = "",
    authorization_public_md_allowlist: str = "",
    authorization_http_method_allowlist: str = "",
    authorization_evidence_root: str = "",
    authorization_expires_at: float | None = None,
    now_unix: float = 0.0,
    already_consumed: bool = False,
    live_trading_allowed: bool = False,
    testnet_allowed: bool = False,
    private_endpoint_access_allowed: bool = False,
    exchange_credential_use_allowed: bool = False,
    real_capital_movement_allowed: bool = False,
    step4_authorization_reuse: bool = False,
) -> dict[str, Any]:
    """Full Step-5 execution authorization binding. Does not consume."""
    blockers: list[str] = []
    if AUTHORIZATION_ISSUANCE_ALLOWED:
        blockers.append("AUTHORIZATION_ISSUANCE_MUST_REMAIN_FALSE")
    if AUTHORIZATION_CONSUMPTION_ALLOWED:
        blockers.append("AUTHORIZATION_CONSUMPTION_MUST_REMAIN_FALSE")

    base = validate_step5_binding_auth_v1(
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_binding_config_digest,
        expected_scope=expected_scope,
        expected_session_id=expected_session_id,
        authorization_scope=authorization_scope,
        authorization_session_id=authorization_session_id,
        authorization_repository_sha=authorization_repository_sha or expected_repository_sha,
        authorization_config_digest=expected_binding_config_digest,
        live_trading_allowed=live_trading_allowed,
        testnet_allowed=testnet_allowed,
        private_endpoint_access_allowed=private_endpoint_access_allowed,
        exchange_credential_use_allowed=exchange_credential_use_allowed,
        real_capital_movement_allowed=real_capital_movement_allowed,
        already_consumed=already_consumed,
        step4_authorization_reuse=step4_authorization_reuse,
    )
    blockers.extend(list(base.get("blockers") or []))

    if str(authorization_capability_id) != str(expected_capability_id):
        blockers.append("AUTHORIZATION_CAPABILITY_SCOPE_MISMATCH")
    got_contract = str(
        authorization_session_contract_digest or expected_session_contract_digest
    ).strip()
    if got_contract != str(expected_session_contract_digest):
        blockers.append("AUTHORIZATION_SESSION_CONTRACT_DIGEST_MISMATCH")
    got_binding = str(authorization_binding_config_digest or expected_binding_config_digest).strip()
    if got_binding != str(expected_binding_config_digest):
        blockers.append("AUTHORIZATION_BINDING_CONFIG_DIGEST_MISMATCH")
    got_duration = (
        int(authorization_planned_duration_seconds)
        if authorization_planned_duration_seconds is not None
        else int(planned_session_duration_seconds)
    )
    if got_duration != int(planned_session_duration_seconds):
        blockers.append("AUTHORIZATION_PLANNED_DURATION_MISMATCH")
    if str(authorization_network_mode or network_mode) != str(network_mode):
        blockers.append("AUTHORIZATION_NETWORK_MODE_MISMATCH")
    if str(authorization_public_md_allowlist or public_md_endpoint_allowlist) != str(
        public_md_endpoint_allowlist
    ):
        blockers.append("AUTHORIZATION_PUBLIC_MD_ALLOWLIST_MISMATCH")
    if str(authorization_http_method_allowlist or http_method_allowlist) != str(
        http_method_allowlist
    ):
        blockers.append("AUTHORIZATION_HTTP_METHOD_ALLOWLIST_MISMATCH")
    if evidence_root and str(authorization_evidence_root or evidence_root) != str(evidence_root):
        blockers.append("AUTHORIZATION_EVIDENCE_ROOT_MISMATCH")
    if authorization_expires_at is not None and float(now_unix) > float(authorization_expires_at):
        blockers.append("AUTHORIZATION_EXPIRED")

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "authorization_id": str(authorization_id or "").strip(),
        "authorization_digest": str(authorization_digest or "").strip(),
        "authorization_valid": not blockers,
        "consumed": False,
        "single_use_state": "ALREADY_CONSUMED" if already_consumed else "NOT_CONSUMED",
        "bindings": {
            "capability_id": expected_capability_id,
            "scope": expected_scope,
            "repository_sha": expected_repository_sha,
            "session_contract_digest": expected_session_contract_digest,
            "binding_config_digest": expected_binding_config_digest,
            "planned_session_duration_seconds": planned_session_duration_seconds,
            "network_mode": network_mode,
            "public_md_endpoint_allowlist": public_md_endpoint_allowlist,
            "http_method_allowlist": http_method_allowlist,
            "evidence_root": evidence_root,
            "expires_at": authorization_expires_at,
            "single_use": True,
        },
        "notes": [
            "AUTHORIZATION_VALIDATE_ONLY_NO_CONSUME_IN_THIS_CAPABILITY=true",
            "CANONICAL_STEP5_BINDING_AUTH_REUSED=true",
            f"LEDGER_FILENAME={AUTHORIZATION_LEDGER_FILENAME}",
        ],
    }


def record_authorization_consumption_boundary_v1(
    *,
    ledger_path: Path,
    authorization_id: str,
    authorization_digest: str,
    session_id: str,
    now_unix: float,
    allow_consume: bool = False,
) -> dict[str, Any]:
    """Single-use consumption boundary. Forbidden unless allow_consume (later Owner-GO)."""
    if not allow_consume or not AUTHORIZATION_CONSUMPTION_ALLOWED:
        return {
            "ok": False,
            "consumed": False,
            "blockers": ["AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_THIS_CAPABILITY"],
        }
    already = load_consumed_authorization_ids_from_ledger_v1(ledger_path)
    if authorization_id in already:
        return {
            "ok": False,
            "consumed": False,
            "blockers": ["AUTHORIZATION_ALREADY_CONSUMED"],
        }
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "session_id": session_id,
        "consumed_at": float(now_unix),
        "single_use": True,
        "plaintext_persisted": False,
    }
    with Path(ledger_path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
    return {
        "ok": True,
        "consumed": True,
        "record_digest": sha256_canonical_v1(record),
        "blockers": [],
    }


def redact_authorization_mapping_v1(payload: Mapping[str, Any]) -> dict[str, Any]:
    forbidden = {
        "confirm_token",
        "token_plaintext",
        "raw_token",
        "go_token",
        "operator_go_token",
    }
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if str(key).lower() in forbidden:
            out[key] = "[REDACTED]"
        elif isinstance(value, Mapping):
            out[key] = redact_authorization_mapping_v1(value)
        else:
            out[key] = value
    return out
