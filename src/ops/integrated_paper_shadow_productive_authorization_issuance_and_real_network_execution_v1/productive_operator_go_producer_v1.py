"""Productive Operator-GO + authorization_artifact_v2 issuance (single-use)."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_artifact_v2 import (
    AuthorizationArtifactV2,
    parse_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_writer_v2 import (
    build_authorization_artifact_dict_v2,
    new_authorization_id_v2,
    write_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZED_NETWORK_SCOPE,
    AUTHORIZED_VENUE,
    CANONICAL_RUNBOOK_SHA256,
    MANDATORY_SAFETY_BOUNDARIES,
    REQUIRED_SESSION_DURATION_SECONDS,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.constants_v1 import (  # noqa: E501
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
    ISSUANCE_MANIFEST_SCHEMA,
    NETWORK_SCOPE,
    PRODUCER_FAMILY,
    PRODUCTIVE_CODE_IDENTITY,
    SCHEMA_VERSION,
    SESSION_EXECUTION_SCOPE,
    WALLCLOCK_CONFIG_IDENTITY,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
    fingerprint_confirm_token,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    CAPABILITY_ID as GO_CAPABILITY_ID,
    OPERATOR_GO_SCHEMA_VERSION,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    OperatorGoContractV1,
    parse_operator_go_contract_v1,
    validate_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    SessionPreregistrationContractV1,
    validate_preregistration_contract_v1,
)


class ProductiveOperatorGoError(ValueError):
    """Fail-closed productive Operator-GO issuance error."""


@dataclass
class ProductiveAuthorizationIssueResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    go_id: str = ""
    authorization_id: str = ""
    authorization_fingerprint: str = ""
    operator_go_path: str = ""
    authorization_artifact_path: str = ""
    issuance_manifest_path: str = ""
    go: Optional[OperatorGoContractV1] = None
    artifact: Optional[AuthorizationArtifactV2] = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "go_id": self.go_id,
            "authorization_id": self.authorization_id,
            "authorization_fingerprint": self.authorization_fingerprint,
            "operator_go_path": self.operator_go_path,
            "authorization_artifact_path": self.authorization_artifact_path,
            "issuance_manifest_path": self.issuance_manifest_path,
            "notes": list(self.notes),
            "fixture_non_authoritative": False,
            "schema_version": SCHEMA_VERSION,
            "producer_family": PRODUCER_FAMILY,
            "paper_shadow_observation_authorized": bool(self.ok),
            "session_executed": False,
            "network_used": False,
            "canonical_authorization_schema": AUTHORIZATION_SCHEMA,
            "productive_authorization_issuance_v2_only": True,
        }


def _canonical_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    assert_no_plaintext_token_fields(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _fingerprint(payload: Mapping[str, Any]) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_productive_operator_go_dict_v1(
    *,
    prereg: SessionPreregistrationContractV1,
    now_unix: float,
    go_id: Optional[str] = None,
) -> dict[str, Any]:
    gid = go_id or f"go_pso_wallclock_prod_{secrets.token_hex(12)}"
    return {
        "schema_version": OPERATOR_GO_SCHEMA_VERSION,
        "capability_id": GO_CAPABILITY_ID,
        "go_id": gid,
        "session_id": prereg.session_id,
        "venue": prereg.venue,
        "market_type": prereg.market_type,
        "instrument_allowlist": list(prereg.instrument_allowlist),
        "strategy_portfolio_id": prereg.strategy_portfolio_id,
        "planned_duration_seconds": prereg.planned_duration_seconds,
        "observation_mode": prereg.observation_mode,
        "orders_authorized": False,
        "broker_writes_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
        "auto_promotion_authorized": False,
        "network_authorized": True,
        "credentials_authorized": False,
        "session_execution_authorized": True,
        "network_scope": NETWORK_SCOPE,
        "session_execution_scope": SESSION_EXECUTION_SCOPE,
        "paper_execution_authorized": False,
        "enabled": True,
        "armed": True,
        "arming_state": "armed",
        "issued_at": float(now_unix),
        "not_before": float(prereg.earliest_start),
        "expires_at": float(prereg.expires_at),
        "single_use": True,
        "consumed": False,
        "revoked": False,
        "revocation_state": "none",
        "confirm_token_binding_sha256": prereg.confirm_token_binding_sha256,
        "confirm_token_hash_reference": prereg.confirm_token_hash_reference,
        "expected_repository_sha": prereg.expected_repository_sha,
        "config_identity": prereg.config_identity,
        "code_identity": prereg.code_identity,
        "operator_identity": prereg.operator_identity,
        "approval_identity": prereg.approval_identity,
        "scope_digest": prereg.scope_digest(),
        "fixture_non_authoritative": False,
        "notes": [
            "PRODUCTIVE_OPERATOR_GO",
            "NOT_A_FIXTURE",
            "AUTHORIZATION_IS_NOT_EXECUTION",
            f"HOST={CANONICAL_HOST}",
            f"INSTRUMENT={CANONICAL_INSTRUMENT_ID}",
            "SCOPED_WALLCLOCK_MD_OBSERVE_ONLY",
            "AUTHORIZATION_ARTIFACT_V2_ONLY",
        ],
    }


def issue_productive_authorization_v1(
    *,
    prereg: SessionPreregistrationContractV1,
    confirm_token: str,
    output_dir: Path,
    now_unix: Optional[float] = None,
    authorization_id: Optional[str] = None,
    previously_seen_fingerprints: frozenset[str] | None = None,
    known_authorization_ids: frozenset[str] | None = None,
    runbook_sha256: str = CANONICAL_RUNBOOK_SHA256,
    venue: Optional[str] = None,
    network_scope: Optional[str] = None,
) -> ProductiveAuthorizationIssueResultV1:
    notes = [
        "PRODUCTIVE_OPERATOR_GO_ISSUANCE",
        "SINGLE_USE_AUTHORIZATION",
        "FIXTURE_NON_AUTHORITATIVE=false",
        "PRODUCTIVE_AUTHORIZATION_ISSUANCE_V2_ONLY",
        f"CANONICAL_SCHEMA={AUTHORIZATION_SCHEMA}",
    ]
    now = float(time.time() if now_unix is None else now_unix)
    blockers: list[str] = []

    if prereg.fixture_non_authoritative:
        blockers.append("FIXTURE_PREREG_FORBIDDEN_FOR_PRODUCTIVE_ISSUANCE")
    pr = validate_preregistration_contract_v1(
        prereg, now_unix=now, expected_repository_sha=prereg.expected_repository_sha
    )
    blockers.extend(pr.blockers)

    # Venue must be explicit and match AUTHORIZED_VENUE — no silent default.
    venue_value = venue if venue is not None else prereg.venue
    if venue_value is None or venue_value == "":
        blockers.append("VENUE_MISSING")
    elif venue_value != AUTHORIZED_VENUE:
        blockers.append(f"VENUE_REJECTED:{venue_value}")
    network_value = network_scope if network_scope is not None else AUTHORIZED_NETWORK_SCOPE
    if network_value != AUTHORIZED_NETWORK_SCOPE:
        blockers.append(f"NETWORK_SCOPE_REJECTED:{network_value}")

    go_raw = build_productive_operator_go_dict_v1(prereg=prereg, now_unix=now)
    go = parse_operator_go_contract_v1(go_raw)
    gr = validate_operator_go_contract_v1(
        go, prereg=prereg, now_unix=now, expected_repository_sha=prereg.expected_repository_sha
    )
    blockers.extend(gr.blockers)

    auth_id = authorization_id or new_authorization_id_v2()
    if known_authorization_ids and auth_id in known_authorization_ids:
        blockers.append("DUPLICATE_AUTHORIZATION_ID")
    if previously_seen_fingerprints:
        fp = fingerprint_confirm_token(confirm_token)
        if fp in previously_seen_fingerprints:
            blockers.append("CONFIRM_TOKEN_REPLAY")

    if blockers:
        return ProductiveAuthorizationIssueResultV1(
            ok=False, blockers=sorted(set(blockers)), notes=notes
        )

    config_digests = {
        "wallclock_config_identity": hashlib.sha256(
            (go.config_identity or WALLCLOCK_CONFIG_IDENTITY).encode("utf-8")
        ).hexdigest(),
        "productive_code_identity": hashlib.sha256(
            PRODUCTIVE_CODE_IDENTITY.encode("utf-8")
        ).hexdigest(),
    }
    payload = build_authorization_artifact_dict_v2(
        authorization_id=auth_id,
        preregistration_id=prereg.session_id,
        preregistration_digest=prereg.scope_digest(),
        repository_sha=prereg.expected_repository_sha,
        runbook_sha256=runbook_sha256,
        session_duration_seconds=REQUIRED_SESSION_DURATION_SECONDS,
        config_digests=config_digests,
        safety_boundaries=dict(MANDATORY_SAFETY_BOUNDARIES),
        confirm_token=confirm_token,
        confirm_token_binding_sha256=prereg.confirm_token_binding_sha256,
        capability=TARGET_RUNTIME_CAPABILITY,
        created_at=now,
        expires_at=float(prereg.expires_at),
        venue=venue_value,
        network_scope=network_value,
        notes=[
            "PRODUCTIVE_AUTHORIZATION_ARTIFACT_V2",
            "NOT_A_FIXTURE",
            "NO_LEGACY_V1",
        ],
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    go_path = output_dir / "operator_go.json"
    art_path = output_dir / "authorization_artifact.json"
    written = write_authorization_artifact_v2(output_path=art_path, artifact_dict=payload)
    if not written.ok or written.artifact is None:
        return ProductiveAuthorizationIssueResultV1(
            ok=False,
            blockers=list(written.blockers) or ["AUTHORIZATION_V2_WRITE_FAILED"],
            notes=notes,
        )
    artifact = written.artifact
    go_payload = go.to_dict()
    _canonical_write_json(go_path, go_payload)
    art_payload = artifact.to_dict()
    auth_fp = _fingerprint(art_payload)

    issuance = {
        "schema": ISSUANCE_MANIFEST_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "producer_family": PRODUCER_FAMILY,
        "issuance_kind": "productive_authorization",
        "canonical_authorization_schema": AUTHORIZATION_SCHEMA,
        "session_id": prereg.session_id,
        "go_id": go.go_id,
        "authorization_id": artifact.authorization_id,
        "authorization_fingerprint": auth_fp,
        "preregistration_scope_digest": prereg.scope_digest(),
        "confirm_token_fingerprint": fingerprint_confirm_token(confirm_token),
        "confirm_token_binding_sha256": go.confirm_token_binding_sha256,
        "config_identity": go.config_identity or WALLCLOCK_CONFIG_IDENTITY,
        "code_identity": PRODUCTIVE_CODE_IDENTITY,
        "expected_repository_sha": go.expected_repository_sha,
        "runbook_sha256": runbook_sha256,
        "venue": artifact.venue,
        "network_scope": artifact.network_scope,
        "instrument": CANONICAL_INSTRUMENT_ID,
        "host": CANONICAL_HOST,
        "session_execution_scope": SESSION_EXECUTION_SCOPE,
        "earliest_start": prereg.earliest_start,
        "expires_at": prereg.expires_at,
        "planned_duration_seconds": prereg.planned_duration_seconds,
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
        "operator_go_path": str(go_path),
        "authorization_artifact_path": str(art_path),
    }
    issuance_path = output_dir / "issuance_manifest_authorization.json"
    _canonical_write_json(issuance_path, issuance)

    return ProductiveAuthorizationIssueResultV1(
        ok=True,
        go_id=go.go_id,
        authorization_id=artifact.authorization_id,
        authorization_fingerprint=auth_fp,
        operator_go_path=str(go_path),
        authorization_artifact_path=str(art_path),
        issuance_manifest_path=str(issuance_path),
        go=go,
        artifact=parse_authorization_artifact_v2(art_payload),
        notes=notes + ["PRODUCTIVE_AUTHORIZATION_ISSUED_V2"],
    )
