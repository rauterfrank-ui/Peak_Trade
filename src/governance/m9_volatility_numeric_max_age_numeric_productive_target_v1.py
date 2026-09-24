"""M9 numeric productive target contract v1 (Owner-ratified target class only).

Registers exactly one productive target identity for governed numeric max-age
semantics. Target registration does not authorize apply, threshold values, or
enforcement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.m9_volatility_numeric_max_age_ratified_threshold_capability_v1 import (
    CAPABILITY_ID as RATIFIED_THRESHOLD_CAPABILITY_ID,
    CAPABILITY_VERSION as RATIFIED_THRESHOLD_CAPABILITY_VERSION,
    ThresholdValueAuthorizationStatusV1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "m9_volatility_numeric_max_age_numeric_productive_target/v1"
DOMAIN: Final[str] = "peak_trade.governance.m9_numeric_productive_target.v1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/M9_VOLATILITY_NUMERIC_MAX_AGE_NUMERIC_PRODUCTIVE_TARGET_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1_decision_v1.json"
)

PRODUCTIVE_TARGET_ID: Final[str] = (
    "peak_trade.governance.productive_target.m9_volatility_numeric_max_age_seconds/v1"
)
PRODUCTIVE_TARGET_VERSION: Final[str] = SCHEMA_VERSION
PRODUCTIVE_TARGET_OWNER: Final[str] = (
    "src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1"
)

OPTIMIZATION_SURFACE_ID: Final[str] = "VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1"
SOURCE_CANDIDATE_PARAMETER: Final[str] = "max_age_seconds"
TARGET_POLICY_PARAMETER: Final[str] = "numeric_max_age_seconds"
TARGET_UNIT: Final[str] = "SECONDS"

POLICY_CAPABILITY_ID: Final[str] = (
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_POLICY_CONTRACT_AND_NON_ENFORCING_TELEMETRY_V1"
)
POLICY_CONSUMER_MODULE: Final[str] = (
    "trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1"
)
POLICY_EVALUATOR_SYMBOL: Final[str] = "evaluate_canonical_volatility_estimate_age_policy_v1"

TARGET_REGISTRATION_IMPLIES_PRODUCTIVE_APPLY: Final[bool] = False
TARGET_REGISTRATION_IMPLIES_THRESHOLD_VALUE: Final[bool] = False
TARGET_REGISTRATION_IMPLIES_ENFORCEMENT: Final[bool] = False

_REPO_ROOT = Path(__file__).resolve().parents[2]


class ProductiveTargetContractError(ValueError):
    """Fail-closed productive target contract error."""


class ProductiveApplyAuthorizationStatusV1(str, Enum):
    NONE = "NONE"
    AUTHORIZED = "AUTHORIZED"


@dataclass(frozen=True)
class ProductiveNumericMaxAgePolicyAdmissionV1:
    """Admission bundle for policy seam (M10 authorization is a future edge)."""

    productive_target_id: str
    productive_target_version: str
    ratified_threshold_capability_id: str
    ratified_threshold_capability_version: str
    threshold_value_authorization_status: str
    threshold_value_authorization_digest: str | None
    threshold_numeric_max_age_seconds: float | None
    productive_apply_authorization_status: str
    productive_apply_authorization_digest: str | None
    optimization_ingress_digest: str | None = None
    optimization_candidate_ref: str | None = None
    governance_review_admission_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "governance_review_admission_status": self.governance_review_admission_status,
            "optimization_candidate_ref": self.optimization_candidate_ref,
            "optimization_ingress_digest": self.optimization_ingress_digest,
            "productive_apply_authorization_digest": self.productive_apply_authorization_digest,
            "productive_apply_authorization_status": self.productive_apply_authorization_status,
            "productive_target_id": self.productive_target_id,
            "productive_target_version": self.productive_target_version,
            "ratified_threshold_capability_id": self.ratified_threshold_capability_id,
            "ratified_threshold_capability_version": self.ratified_threshold_capability_version,
            "threshold_numeric_max_age_seconds": self.threshold_numeric_max_age_seconds,
            "threshold_value_authorization_digest": self.threshold_value_authorization_digest,
            "threshold_value_authorization_status": self.threshold_value_authorization_status,
        }


def load_owner_decision_v1() -> MappingProxyType[str, Any]:
    path = _REPO_ROOT / DECISION_CONFIG
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ProductiveTargetContractError("DECISION_CONFIG_NOT_MAPPING")
    if payload.get("productive_target_id") != PRODUCTIVE_TARGET_ID:
        raise ProductiveTargetContractError("DECISION_PRODUCTIVE_TARGET_ID_MISMATCH")
    if payload.get("owner_decision") != "NUMERIC_PRODUCTIVE_PARAMETER":
        raise ProductiveTargetContractError("DECISION_OWNER_CHOICE_MISMATCH")
    if payload.get("authorized_productive_target_count") != 1:
        raise ProductiveTargetContractError("DECISION_TARGET_COUNT_NOT_EXACTLY_ONE")
    return MappingProxyType(payload)


def authorized_productive_target_ids_v1() -> frozenset[str]:
    decision = load_owner_decision_v1()
    if decision.get("zero_authorized_productive_targets") is True:
        return frozenset()
    target_id = str(decision.get("productive_target_id") or "")
    if not target_id:
        raise ProductiveTargetContractError("PRODUCTIVE_TARGET_ID_MISSING")
    return frozenset({target_id})


def zero_authorized_productive_targets_v1() -> bool:
    return len(authorized_productive_target_ids_v1()) == 0


def build_productive_target_registry_snapshot_v1() -> MappingProxyType[str, Any]:
    decision = load_owner_decision_v1()
    targets = tuple(sorted(authorized_productive_target_ids_v1()))
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": DOMAIN,
        "authorized_productive_target_ids": targets,
        "authorized_productive_target_count": len(targets),
        "zero_authorized_productive_targets": zero_authorized_productive_targets_v1(),
        "owner_decision_config": DECISION_CONFIG,
        "owner_decision_config_digest": compute_content_sha256(dict(decision)),
        "target_registration_implies_productive_apply": (
            TARGET_REGISTRATION_IMPLIES_PRODUCTIVE_APPLY
        ),
        "universe_membership_implies_target_authorization": False,
    }
    body["registry_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "registry_digest"}
    )
    return MappingProxyType(body)


def build_productive_target_contract_v1() -> MappingProxyType[str, Any]:
    decision = load_owner_decision_v1()
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": DOMAIN,
        "productive_target_id": PRODUCTIVE_TARGET_ID,
        "productive_target_version": PRODUCTIVE_TARGET_VERSION,
        "productive_target_owner": PRODUCTIVE_TARGET_OWNER,
        "owner_decision": decision.get("owner_decision"),
        "optimization_surface_id": OPTIMIZATION_SURFACE_ID,
        "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
        "target_policy_parameter": TARGET_POLICY_PARAMETER,
        "target_unit": TARGET_UNIT,
        "policy_capability_id": POLICY_CAPABILITY_ID,
        "policy_consumer_module": POLICY_CONSUMER_MODULE,
        "policy_evaluator_symbol": POLICY_EVALUATOR_SYMBOL,
        "ratified_threshold_capability_id": RATIFIED_THRESHOLD_CAPABILITY_ID,
        "ratified_threshold_capability_version": RATIFIED_THRESHOLD_CAPABILITY_VERSION,
        "normative_spec": NORMATIVE_SPEC,
        "decision_config": DECISION_CONFIG,
    }
    body["contract_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "contract_digest"}
    )
    return MappingProxyType(body)


def validate_productive_target_id_v1(productive_target_id: str) -> tuple[bool, str]:
    normalized = productive_target_id.strip()
    if not normalized:
        return False, "PRODUCTIVE_TARGET_ID_EMPTY"
    if normalized not in authorized_productive_target_ids_v1():
        return False, "PRODUCTIVE_TARGET_ID_NOT_AUTHORIZED"
    return True, "PRODUCTIVE_TARGET_ID_OK"


def build_policy_admission_from_authorized_seam_record_v1(
    seam_record: Mapping[str, Any] | None,
) -> ProductiveNumericMaxAgePolicyAdmissionV1 | None:
    """Build admission only from seam fields produced by valid F1/M9 threshold authority."""
    if seam_record is None:
        return None
    if (
        seam_record.get("threshold_value_authorization_status")
        != ThresholdValueAuthorizationStatusV1.AUTHORIZED.value
    ):
        return None
    digest = seam_record.get("threshold_value_authorization_digest")
    if not isinstance(digest, str) or not is_valid_sha256_hex(digest):
        return None
    numeric = seam_record.get("threshold_numeric_max_age_seconds")
    if numeric is None:
        numeric = seam_record.get("numeric_max_age_seconds")
    if not isinstance(numeric, (int, float)) or isinstance(numeric, bool):
        return None
    apply_digest = seam_record.get("productive_apply_authorization_digest")
    if not isinstance(apply_digest, str) or not is_valid_sha256_hex(apply_digest):
        return None
    return ProductiveNumericMaxAgePolicyAdmissionV1(
        productive_target_id=str(seam_record.get("productive_target_id") or ""),
        productive_target_version=str(seam_record.get("productive_target_version") or ""),
        ratified_threshold_capability_id=str(
            seam_record.get("threshold_capability_id") or RATIFIED_THRESHOLD_CAPABILITY_ID
        ),
        ratified_threshold_capability_version=str(
            seam_record.get("threshold_capability_version") or RATIFIED_THRESHOLD_CAPABILITY_VERSION
        ),
        threshold_value_authorization_status=ThresholdValueAuthorizationStatusV1.AUTHORIZED.value,
        threshold_value_authorization_digest=digest,
        threshold_numeric_max_age_seconds=float(numeric),
        productive_apply_authorization_status=ProductiveApplyAuthorizationStatusV1.AUTHORIZED.value,
        productive_apply_authorization_digest=apply_digest,
    )


def validate_policy_admission_request_v1(
    admission: ProductiveNumericMaxAgePolicyAdmissionV1 | None,
) -> tuple[bool, tuple[str, ...]]:
    if admission is None:
        return False, ("ADMISSION_MISSING",)
    reasons: list[str] = []
    if admission.optimization_ingress_digest:
        reasons.append("OPTIMIZATION_INGRESS_DIGEST_FORBIDDEN")
    if admission.optimization_candidate_ref:
        reasons.append("OPTIMIZATION_CANDIDATE_REF_FORBIDDEN")
    if admission.governance_review_admission_status == "ADMITTED_FOR_GOVERNANCE_REVIEW":
        reasons.append("GOVERNANCE_REVIEW_ADMISSION_NOT_PRODUCTIVE_AUTHORIZATION")
    ok, target_reason = validate_productive_target_id_v1(admission.productive_target_id)
    if not ok:
        reasons.append(target_reason)
    if admission.productive_target_version != PRODUCTIVE_TARGET_VERSION:
        reasons.append("PRODUCTIVE_TARGET_VERSION_MISMATCH")
    if admission.ratified_threshold_capability_id != RATIFIED_THRESHOLD_CAPABILITY_ID:
        reasons.append("RATIFIED_THRESHOLD_CAPABILITY_ID_MISMATCH")
    if admission.ratified_threshold_capability_version != RATIFIED_THRESHOLD_CAPABILITY_VERSION:
        reasons.append("RATIFIED_THRESHOLD_CAPABILITY_VERSION_MISMATCH")
    if admission.productive_apply_authorization_status != (
        ProductiveApplyAuthorizationStatusV1.AUTHORIZED.value
    ):
        reasons.append("PRODUCTIVE_APPLY_AUTHORIZATION_REQUIRED")
    if not admission.productive_apply_authorization_digest or not is_valid_sha256_hex(
        admission.productive_apply_authorization_digest
    ):
        reasons.append("PRODUCTIVE_APPLY_AUTHORIZATION_DIGEST_INVALID")
    if admission.threshold_value_authorization_status != "AUTHORIZED":
        reasons.append("THRESHOLD_VALUE_AUTHORIZATION_REQUIRED")
    if not admission.threshold_value_authorization_digest or not is_valid_sha256_hex(
        admission.threshold_value_authorization_digest
    ):
        reasons.append("THRESHOLD_VALUE_AUTHORIZATION_DIGEST_INVALID")
    if admission.threshold_numeric_max_age_seconds is None:
        reasons.append("THRESHOLD_NUMERIC_VALUE_MISSING")
    if reasons:
        return False, tuple(reasons)
    return True, ("ADMISSION_REQUEST_VALID",)


def direct_productive_write_possible_v1() -> bool:
    return False
