"""Deterministic finding identities for the bounded Master V2 GHOSV."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from scripts.ops.ghosv_master_v2_bounded_context_v1.constants_v1 import (
    ALLOWED_AUTHORITY_EFFECT,
    ALLOWED_EFFECT,
    ALLOWED_EVIDENCE_STATUS,
    SCHEMA_ID,
)


def canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def finding_id_v1(
    *,
    requirement_id: str,
    finding_type: str,
    current_sha: str,
    current_tree: str,
    source_reference: str,
    contract_reference: str,
    check_id: str,
) -> str:
    payload = {
        "schema_id": SCHEMA_ID,
        "requirement_id": requirement_id,
        "finding_type": finding_type,
        "current_sha": current_sha,
        "current_tree": current_tree,
        "source_reference": source_reference,
        "contract_reference": contract_reference,
        "check_id": check_id,
    }
    return canonical_sha256(payload)


def make_finding_v1(
    *,
    requirement_id: str,
    finding_type: str,
    current_sha: str,
    current_tree: str,
    source_reference: str,
    contract_reference: str,
    check_id: str,
    evidence_status: str,
    coverage_status: str,
    uncertainty: str,
    authority_effect: str,
    safety_effect: str,
    capital_effect: str,
    boundary_classification: str,
    foreign_finding_reference: str | None,
    conflict_status: str,
    owner_go_required: bool,
) -> dict[str, Any]:
    if evidence_status not in ALLOWED_EVIDENCE_STATUS:
        raise ValueError("EVIDENCE_STATUS_REJECTED")
    if authority_effect not in ALLOWED_AUTHORITY_EFFECT:
        raise ValueError("AUTHORITY_EFFECT_REJECTED")
    if safety_effect not in ALLOWED_EFFECT or capital_effect not in ALLOWED_EFFECT:
        raise ValueError("EFFECT_REJECTED")
    return {
        "finding_id": finding_id_v1(
            requirement_id=requirement_id,
            finding_type=finding_type,
            current_sha=current_sha,
            current_tree=current_tree,
            source_reference=source_reference,
            contract_reference=contract_reference,
            check_id=check_id,
        ),
        "finding_type": finding_type,
        "domain": "MASTER_V2",
        "requirement_id": requirement_id,
        "current_sha": current_sha,
        "current_tree": current_tree,
        "source_reference": source_reference,
        "contract_reference": contract_reference,
        "evidence_status": evidence_status,
        "coverage_status": coverage_status,
        "uncertainty": uncertainty,
        "authority_effect": authority_effect,
        "safety_effect": safety_effect,
        "capital_effect": capital_effect,
        "boundary_classification": boundary_classification,
        "foreign_finding_reference": foreign_finding_reference,
        "conflict_status": conflict_status,
        "owner_go_required": owner_go_required,
    }


def sort_findings_v1(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(findings, key=lambda item: item["finding_id"])
