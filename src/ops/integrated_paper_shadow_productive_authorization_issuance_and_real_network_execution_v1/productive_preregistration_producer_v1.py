"""Productive session-preregistration producer (non-fixture, immutable artifact)."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E501
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    HOST_ALLOWLIST,
    ISSUANCE_MANIFEST_SCHEMA,
    MARKET_TYPE_FUTURES,
    NETWORK_SCOPE,
    PRODUCER_FAMILY,
    PRODUCTIVE_CODE_IDENTITY,
    REQUIRED_MODE,
    SCHEMA_VERSION,
    SESSION_EXECUTION_SCOPE,
    STRATEGY_COMPONENT_IDENTITIES,
    STRATEGY_PORTFOLIO_ID,
    VENUE_OKX,
    WALLCLOCK_CODE_IDENTITY,
    WALLCLOCK_CONFIG_IDENTITY,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
    compute_confirm_token_binding_sha256,
    fingerprint_confirm_token,
    sha256_text,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    CAPABILITY_ID as GO_CAPABILITY_ID,
    PREREGISTRATION_SCHEMA_VERSION,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
    parse_preregistration_contract_v1,
    validate_preregistration_contract_v1,
)


class ProductivePreregistrationError(ValueError):
    """Fail-closed productive preregistration error."""


@dataclass
class ProductivePreregistrationIssueResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    session_id: str = ""
    preregistration_fingerprint: str = ""
    scope_digest: str = ""
    artifact_path: str = ""
    issuance_manifest_path: str = ""
    contract: Optional[SessionPreregistrationContractV1] = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "session_id": self.session_id,
            "preregistration_fingerprint": self.preregistration_fingerprint,
            "scope_digest": self.scope_digest,
            "artifact_path": self.artifact_path,
            "issuance_manifest_path": self.issuance_manifest_path,
            "notes": list(self.notes),
            "fixture_non_authoritative": False,
            "schema_version": SCHEMA_VERSION,
            "producer_family": PRODUCER_FAMILY,
            "contract": None if self.contract is None else self.contract.to_dict(),
        }


def new_session_id_v1() -> str:
    return f"pso_wallclock_prod_{secrets.token_hex(16)}"


def compute_preregistration_fingerprint_v1(payload: Mapping[str, Any]) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _canonical_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    assert_no_plaintext_token_fields(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def build_productive_preregistration_dict_v1(
    *,
    session_id: str,
    expected_repository_sha: str,
    planned_duration_seconds: int,
    earliest_start: float,
    expires_at: float,
    evidence_root: str,
    operator_identity: str,
    approval_identity: str,
    confirm_token: str,
    purpose: str = "PRODUCTIVE_PAPER_SHADOW_WALLCLOCK_MD_OBSERVE",
    config_identity: str = WALLCLOCK_CONFIG_IDENTITY,
    code_identity: str = WALLCLOCK_CODE_IDENTITY,
) -> dict[str, Any]:
    if planned_duration_seconds != DEFAULT_MAX_SESSION_DURATION_SECONDS:
        # Productive policy allows exactly 21600; tests may call with shorter via
        # allow_noncanonical_duration on the producer entrypoint.
        pass
    provisional = {
        "contract_version": "v1",
        "schema_version": PREREGISTRATION_SCHEMA_VERSION,
        "capability_id": GO_CAPABILITY_ID,
        "session_id": session_id,
        "purpose": purpose,
        "venue": VENUE_OKX,
        "market_type": MARKET_TYPE_FUTURES,
        "instrument_allowlist": [CANONICAL_INSTRUMENT_ID],
        "instrument_denylist": ["BTC-USD_UM_XPERP-1"],
        "strategy_portfolio_id": STRATEGY_PORTFOLIO_ID,
        "strategy_component_identities": list(STRATEGY_COMPONENT_IDENTITIES),
        "config_identity": config_identity,
        "code_identity": code_identity,
        "expected_repository_sha": expected_repository_sha,
        "observation_mode": REQUIRED_MODE,
        "no_order_invariant": True,
        "network_policy": NETWORK_SCOPE,
        "network_scope": NETWORK_SCOPE,
        "session_execution_scope": SESSION_EXECUTION_SCOPE,
        "credential_policy": "deny",
        "planned_duration_seconds": int(planned_duration_seconds),
        "earliest_start": float(earliest_start),
        "expires_at": float(expires_at),
        "evidence_root": evidence_root,
        "evidence_target_paths": [
            "session_manifest.json",
            "no_order_attestation.json",
            "evidence_manifest.sha256",
            "issuance_manifest.json",
        ],
        "required_evidence_schema_versions": [
            "ops.integrated_paper_shadow_observation_wallclock_evidence_v1"
        ],
        "killstate_policy": "ipso_killstate_v1",
        "timeout_policy": "hard_timeout_v1",
        "lock_policy": "single_session_lock_v1",
        "retry_policy": "transient_http_retry_v1",
        "no_auto_promotion": True,
        "no_testnet": True,
        "no_live": True,
        "no_orders": True,
        "operator_identity": operator_identity,
        "approval_identity": approval_identity,
        "confirm_token_hash_reference": "pending",
        "confirm_token_binding_sha256": "0" * 64,
        "enabled": True,
        "armed": True,
        "arming_state": "armed",
        "single_use": True,
        "consumed": False,
        "revoked": False,
        "revocation_state": "none",
        "fixture_non_authoritative": False,
        "notes": [
            "PRODUCTIVE_PREREGISTRATION",
            "NOT_A_FIXTURE",
            f"HOST_ALLOWLIST={','.join(HOST_ALLOWLIST)}",
            "ORDERS=false",
            "PAPER_EXECUTION=false",
            "TESTNET=false",
            "LIVE=false",
            "CREDENTIALS=false",
            "PRIVATE_ENDPOINTS=false",
            "AUTO_PROMOTION=false",
            "ECONOMIC_VALIDITY_MUTATION=false",
        ],
    }
    # Scope digest uses contract method — parse with placeholders then rebind.
    tmp_contract = parse_preregistration_contract_v1(provisional)
    scope_digest = tmp_contract.scope_digest()
    binding = compute_confirm_token_binding_sha256(
        session_id=session_id,
        scope_digest=scope_digest,
        expires_at=float(expires_at),
        repository_sha=expected_repository_sha,
        confirm_token=confirm_token,
    )
    provisional["confirm_token_binding_sha256"] = binding
    provisional["confirm_token_hash_reference"] = f"sha256:{sha256_text(confirm_token)}"
    return provisional


def issue_productive_preregistration_v1(
    *,
    output_dir: Path,
    expected_repository_sha: str,
    confirm_token: str,
    operator_identity: str,
    approval_identity: str,
    evidence_root: str,
    planned_duration_seconds: int = DEFAULT_MAX_SESSION_DURATION_SECONDS,
    earliest_start: Optional[float] = None,
    expires_at: Optional[float] = None,
    session_id: Optional[str] = None,
    now_unix: Optional[float] = None,
    allow_noncanonical_duration: bool = False,
    purpose: str = "PRODUCTIVE_PAPER_SHADOW_WALLCLOCK_MD_OBSERVE",
) -> ProductivePreregistrationIssueResultV1:
    notes = [
        "PRODUCTIVE_PREREGISTRATION_ISSUANCE",
        "FIXTURE_NON_AUTHORITATIVE=false",
        f"HOST_ALLOWLIST={CANONICAL_HOST}",
        "REUSES_PREREG_CONTRACT_SCHEMA",
    ]
    blockers: list[str] = []
    now = float(time.time() if now_unix is None else now_unix)
    sid = session_id or new_session_id_v1()
    start = float(earliest_start) if earliest_start is not None else now
    # End = start + duration; expires_at must cover session window + small auth skew.
    duration = int(planned_duration_seconds)
    if not allow_noncanonical_duration and duration != DEFAULT_MAX_SESSION_DURATION_SECONDS:
        blockers.append("PRODUCTIVE_DURATION_MUST_BE_21600")
    if duration <= 0 or duration > DEFAULT_MAX_SESSION_DURATION_SECONDS:
        blockers.append("PLANNED_DURATION_OUT_OF_BOUNDS")
    end = float(expires_at) if expires_at is not None else start + float(duration)
    if abs((end - start) - float(duration)) > 1e-6 and expires_at is None:
        end = start + float(duration)
    if not operator_identity.strip() or not approval_identity.strip():
        blockers.append("OPERATOR_AND_APPROVAL_IDENTITY_REQUIRED")
    if not evidence_root.strip():
        blockers.append("EVIDENCE_ROOT_REQUIRED")
    if not expected_repository_sha.strip():
        blockers.append("REPOSITORY_SHA_REQUIRED")
    if blockers:
        return ProductivePreregistrationIssueResultV1(ok=False, blockers=blockers, notes=notes)

    raw = build_productive_preregistration_dict_v1(
        session_id=sid,
        expected_repository_sha=expected_repository_sha,
        planned_duration_seconds=duration,
        earliest_start=start,
        expires_at=end,
        evidence_root=evidence_root,
        operator_identity=operator_identity,
        approval_identity=approval_identity,
        confirm_token=confirm_token,
        purpose=purpose,
    )
    contract = parse_preregistration_contract_v1(raw)
    validated = validate_preregistration_contract_v1(
        contract, now_unix=now, expected_repository_sha=expected_repository_sha
    )
    if not validated.ok:
        return ProductivePreregistrationIssueResultV1(
            ok=False,
            blockers=list(validated.blockers),
            notes=notes,
            session_id=sid,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / "preregistration.json"
    payload = contract.to_dict()
    fp = compute_preregistration_fingerprint_v1(payload)
    _canonical_write_json(artifact_path, payload)

    issuance = {
        "schema": ISSUANCE_MANIFEST_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "producer_family": PRODUCER_FAMILY,
        "issuance_kind": "productive_preregistration",
        "session_id": sid,
        "preregistration_fingerprint": fp,
        "scope_digest": contract.scope_digest(),
        "confirm_token_fingerprint": fingerprint_confirm_token(confirm_token),
        "confirm_token_binding_sha256": contract.confirm_token_binding_sha256,
        "host_allowlist": list(HOST_ALLOWLIST),
        "instrument": CANONICAL_INSTRUMENT_ID,
        "venue": VENUE_OKX,
        "network_scope": NETWORK_SCOPE,
        "session_execution_scope": SESSION_EXECUTION_SCOPE,
        "planned_duration_seconds": duration,
        "earliest_start": start,
        "expires_at": end,
        "monotonic_duration_seconds": duration,
        "orders_authorized": False,
        "paper_execution_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
        "credentials_authorized": False,
        "private_endpoints_authorized": False,
        "auto_promotion_authorized": False,
        "economic_validity_mutation": False,
        "fixture_non_authoritative": False,
        "issued_at": now,
        "operator_identity": operator_identity,
        "approval_identity": approval_identity,
        "expected_repository_sha": expected_repository_sha,
        "config_identity": WALLCLOCK_CONFIG_IDENTITY,
        "code_identity": PRODUCTIVE_CODE_IDENTITY,
        "artifact_path": str(artifact_path),
    }
    issuance_path = output_dir / "issuance_manifest_preregistration.json"
    _canonical_write_json(issuance_path, issuance)

    return ProductivePreregistrationIssueResultV1(
        ok=True,
        session_id=sid,
        preregistration_fingerprint=fp,
        scope_digest=contract.scope_digest(),
        artifact_path=str(artifact_path),
        issuance_manifest_path=str(issuance_path),
        contract=contract,
        notes=notes + ["PREREGISTRATION_ISSUED"],
    )
