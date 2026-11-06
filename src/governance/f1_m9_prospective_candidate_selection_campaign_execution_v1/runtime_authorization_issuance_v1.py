"""Issuance owner for fresh F1/M9 prospective campaign runtime authorization records."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.constants_v1 import (
    CAMPAIGN_ID,
    DURABLE_CAMPAIGN_ROOT_REL,
    PREREGISTRATION_DIGEST,
    PREREGISTRATION_ID,
    REAL_MD_SUPPLIER_ID,
    RUNTIME_AUTHORIZATION_SCHEMA_VERSION,
    SELECTION_POLICY_DIGEST,
    SELECTION_POLICY_ID,
    SELECTION_RULE_ID,
    SOURCE_PARAMETER_ID,
    SURFACE_ID,
    TARGET_PARAMETER_ID,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.durable_paths_v1 import (
    resolve_f1_m9_prospective_campaign_durable_paths_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
    authorization_body_for_digest,
    compute_runtime_authorization_digest,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.session_work_units_v1 import (
    resolve_preregistered_session_work_units_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

ISSUANCE_SCHEMA_VERSION: str = "f1_m9_prospective_campaign_runtime_authorization_issuance/v1"
ISSUANCE_OWNER_ID: str = "f1_m9_prospective_campaign_runtime_authorization_issuance_v1"

AUTHORIZED_CAPABILITIES_V1: tuple[str, ...] = (
    "PUBLIC_REAL_MARKET_DATA_READ",
    "CAMPAIGN_SCOPED_DURABLE_EVIDENCE_WRITE",
    "PREREGISTERED_SESSION_WORK_UNIT_EXECUTION",
    "EVIDENCE_SEALING_INTEGRITY_COMPLETENESS",
    "OOS_ROBUSTNESS_ECONOMIC_EVALUATION",
    "DETERMINISTIC_REPLAY",
    "RESEARCH_CANDIDATE_SELECTION",
)

FORBIDDEN_CAPABILITIES_V1: tuple[str, ...] = (
    "PRIVATE_EXCHANGE_API",
    "CREDENTIAL_ACCESS",
    "ORDER_SUBMISSION",
    "ACCOUNT_POSITION_MUTATION",
    "PRODUCTIVE_PARAMETER_APPLY",
    "PRODUCTIVE_CONFIG_MUTATION",
    "PROMOTION",
    "TRADING_AUTHORITY",
)


class RuntimeAuthorizationIssuanceError(ValueError):
    """Fail-closed issuance validation error."""


def is_valid_bound_origin_main_sha_v1(value: str) -> bool:
    return is_valid_sha256_hex(value) or bool(_GIT_SHA_RE.match(value))


def _work_unit_ids(*, repo_root: Path) -> tuple[str, ...]:
    units = resolve_preregistered_session_work_units_v1(repo_root=repo_root)
    return tuple(str(u["session_id"]) for u in units)


def issue_f1_m9_prospective_campaign_runtime_authorization_v1(
    *,
    authorization_id: str,
    bound_origin_main_sha: str,
    execution_idempotency_key: str,
    owner_identity: str,
    decision_identity: str,
    earliest_valid_utc: datetime,
    expires_at_utc: datetime,
    repo_root: Path | None = None,
    allow_issuance: bool = False,
) -> dict[str, Any]:
    if not allow_issuance:
        raise RuntimeAuthorizationIssuanceError("RUNTIME_AUTHORIZATION_ISSUANCE_NOT_ENABLED")
    if not is_valid_bound_origin_main_sha_v1(bound_origin_main_sha):
        raise RuntimeAuthorizationIssuanceError("BOUND_ORIGIN_MAIN_SHA_INVALID")
    root = repo_root or Path(__file__).resolve().parents[3]
    durable = resolve_f1_m9_prospective_campaign_durable_paths_v1(repo_root=root)
    work_units = _work_unit_ids(repo_root=root)
    body: dict[str, Any] = {
        "schema_version": RUNTIME_AUTHORIZATION_SCHEMA_VERSION,
        "issuance_schema_version": ISSUANCE_SCHEMA_VERSION,
        "issuance_owner_id": ISSUANCE_OWNER_ID,
        "authorization_id": authorization_id,
        "campaign_id": CAMPAIGN_ID,
        "preregistration_id": PREREGISTRATION_ID,
        "preregistration_digest": PREREGISTRATION_DIGEST,
        "selection_policy_id": SELECTION_POLICY_ID,
        "selection_policy_digest": SELECTION_POLICY_DIGEST,
        "selection_rule_id": SELECTION_RULE_ID,
        "surface_id": SURFACE_ID,
        "parameter_id": TARGET_PARAMETER_ID,
        "source_parameter_id": SOURCE_PARAMETER_ID,
        "bound_origin_main_sha": bound_origin_main_sha,
        "real_md_supplier_id": REAL_MD_SUPPLIER_ID,
        "durable_campaign_root_rel": DURABLE_CAMPAIGN_ROOT_REL,
        "durable_campaign_root_abs": str(durable.campaign_root),
        "authorized_work_unit_ids": list(work_units),
        "authorized_capabilities": list(AUTHORIZED_CAPABILITIES_V1),
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES_V1),
        "campaign_execution_authorized": True,
        "public_market_data_read_authorized": True,
        "durable_evidence_write_authorized": True,
        "authorized_data_source": "REAL_PUBLIC_MARKET_DATA",
        "authorized_public_md_venue": "OKX_EEA",
        "authorized_public_md_host": "https://eea.okx.com",
        "earliest_valid_utc": earliest_valid_utc.isoformat().replace("+00:00", "Z"),
        "expires_at_utc": expires_at_utc.isoformat().replace("+00:00", "Z"),
        "owner_identity": owner_identity,
        "decision_identity": decision_identity,
        "execution_idempotency_key": execution_idempotency_key,
    }
    issuance_body = {k: v for k, v in body.items() if k != "authorization_digest"}
    body["issuance_record_digest"] = compute_content_sha256(issuance_body)
    body["authorization_digest"] = compute_runtime_authorization_digest(body)
    return body


def verify_issued_runtime_authorization_bindings_v1(
    payload: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
    expected_bound_origin_main_sha: str | None = None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    root = repo_root or Path(__file__).resolve().parents[3]
    if str(payload.get("issuance_schema_version") or "") != ISSUANCE_SCHEMA_VERSION:
        reasons.append("ISSUANCE_SCHEMA_MISMATCH")
    if str(payload.get("issuance_owner_id") or "") != ISSUANCE_OWNER_ID:
        reasons.append("ISSUANCE_OWNER_MISMATCH")
    stored_issuance = str(payload.get("issuance_record_digest") or "")
    if not is_valid_sha256_hex(stored_issuance):
        reasons.append("ISSUANCE_RECORD_DIGEST_INVALID")
    else:
        body = {k: v for k, v in payload.items() if k not in ("authorization_digest",)}
        check = {k: v for k, v in body.items() if k != "issuance_record_digest"}
        if compute_content_sha256(check) != stored_issuance:
            reasons.append("ISSUANCE_RECORD_DIGEST_MISMATCH")
    if str(payload.get("campaign_id") or "") != CAMPAIGN_ID:
        reasons.append("CAMPAIGN_ID_MISMATCH")
    if str(payload.get("real_md_supplier_id") or "") != REAL_MD_SUPPLIER_ID:
        reasons.append("REAL_MD_SUPPLIER_BINDING_MISMATCH")
    durable = resolve_f1_m9_prospective_campaign_durable_paths_v1(repo_root=root)
    if str(payload.get("durable_campaign_root_abs") or "") != str(durable.campaign_root):
        reasons.append("DURABLE_CAMPAIGN_ROOT_MISMATCH")
    expected_units = _work_unit_ids(repo_root=root)
    authorized_units = tuple(str(x) for x in (payload.get("authorized_work_unit_ids") or []))
    if authorized_units != expected_units:
        reasons.append("AUTHORIZED_WORK_UNIT_MISMATCH")
    caps = set(payload.get("authorized_capabilities") or [])
    if not all(c in caps for c in AUTHORIZED_CAPABILITIES_V1):
        reasons.append("AUTHORIZED_CAPABILITIES_INCOMPLETE")
    forbidden = set(payload.get("forbidden_capabilities") or [])
    if caps.intersection(set(FORBIDDEN_CAPABILITIES_V1)):
        reasons.append("FORBIDDEN_CAPABILITY_PRESENT_IN_AUTHORIZED")
    if set(FORBIDDEN_CAPABILITIES_V1) - forbidden:
        reasons.append("FORBIDDEN_CAPABILITIES_DECLARATION_INCOMPLETE")
    bound_sha = str(payload.get("bound_origin_main_sha") or "")
    if expected_bound_origin_main_sha and bound_sha != expected_bound_origin_main_sha:
        reasons.append("BOUND_ORIGIN_MAIN_SHA_MISMATCH")
    auth_body = authorization_body_for_digest(payload)
    if compute_runtime_authorization_digest(payload) != str(payload.get("authorization_digest")):
        reasons.append("AUTHORIZATION_DIGEST_MISMATCH")
    return tuple(reasons)


__all__ = [
    "AUTHORIZED_CAPABILITIES_V1",
    "FORBIDDEN_CAPABILITIES_V1",
    "ISSUANCE_OWNER_ID",
    "ISSUANCE_SCHEMA_VERSION",
    "RuntimeAuthorizationIssuanceError",
    "is_valid_bound_origin_main_sha_v1",
    "issue_f1_m9_prospective_campaign_runtime_authorization_v1",
    "verify_issued_runtime_authorization_bindings_v1",
]
