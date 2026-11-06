"""Fail-closed join adjudication between Real-P4 seam materialization and F1/M9 Apply."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping

from src.governance.governed_runtime_apply_materialization_record_v1 import (
    MATERIALIZATION_AUTHORITY_ID,
    MATERIALIZATION_RECORD_SCHEMA_VERSION,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationResultV1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

JOIN_STATUS_NOT_CANONICAL: Final[str] = "REAL_P4_F1_M9_JOIN_NOT_CANONICAL"
JOIN_STATUS_FORBIDDEN_CROSS_PLANE: Final[str] = "REAL_P4_F1_M9_CROSS_PLANE_JOIN_FORBIDDEN"

SCHEMA_VERSION: Final[str] = "real_p4_to_f1_m9_apply_lineage_join/v1"


@dataclass(frozen=True, slots=True)
class RealP4ToF1M9ApplyJoinEvaluateResultV1:
    join_permitted: bool
    join_status: str
    reason_codes: tuple[str, ...]
    lineage_join_valid: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "join_permitted": self.join_permitted,
            "join_status": self.join_status,
            "lineage_join_valid": self.lineage_join_valid,
            "reason_codes": list(self.reason_codes),
        }


def evaluate_real_p4_to_f1_m9_apply_join_v1(
    *,
    materialization_record: Mapping[str, Any] | None,
    configuration: GovernedProductiveConfigurationResultV1 | None,
) -> RealP4ToF1M9ApplyJoinEvaluateResultV1:
    """CURRENT authority: Real-P4 seam record and F1/M9 per-ingress Apply are separate planes."""
    reasons: list[str] = [
        "REAL_P4_SEAM_MATERIALIZATION_PLANE_SEPARATE_FROM_F1_M9_PER_INGRESS_APPLY",
        JOIN_STATUS_NOT_CANONICAL,
    ]
    if materialization_record is None:
        reasons.append("P4_MATERIALIZATION_RECORD_MISSING")
    else:
        if materialization_record.get("schema_version") != MATERIALIZATION_RECORD_SCHEMA_VERSION:
            reasons.append("P4_MATERIALIZATION_RECORD_SCHEMA_MISMATCH")
        if (
            materialization_record.get("materialization_authority_id")
            != MATERIALIZATION_AUTHORITY_ID
        ):
            reasons.append("P4_MATERIALIZATION_AUTHORITY_MISMATCH")
        if materialization_record.get("configuration_applied") is True:
            reasons.append("P4_RECORD_CONFIGURATION_APPLIED_FORBIDDEN_FOR_JOIN_PROBE")
        p4_digest = str(materialization_record.get("p4_l6_seam_result_digest") or "")
        if not is_valid_sha256_hex(p4_digest):
            reasons.append("P4_SEAM_DIGEST_INVALID")
        if materialization_record.get("productive_target_id"):
            reasons.append("P4_RECORD_MUST_NOT_CARRY_PRODUCTIVE_TARGET")

    if configuration is not None:
        record = configuration.configuration_record
        if record is not None:
            if str(record.get("productive_target_id") or "") != PRODUCTIVE_TARGET_ID:
                reasons.append("F1_M9_PRODUCTIVE_TARGET_MISMATCH")
            config_digest = str(record.get("configuration_digest") or "")
            if materialization_record is not None:
                p4_config_ref = str(materialization_record.get("source_configuration_digest") or "")
                if p4_config_ref and config_digest and p4_config_ref != config_digest:
                    reasons.append("CROSS_PLANE_CONFIGURATION_DIGEST_MISMATCH")
        reasons.append(JOIN_STATUS_FORBIDDEN_CROSS_PLANE)

    return RealP4ToF1M9ApplyJoinEvaluateResultV1(
        join_permitted=False,
        join_status=JOIN_STATUS_NOT_CANONICAL,
        reason_codes=tuple(dict.fromkeys(reasons)),
        lineage_join_valid=False,
    )


__all__ = [
    "JOIN_STATUS_FORBIDDEN_CROSS_PLANE",
    "JOIN_STATUS_NOT_CANONICAL",
    "RealP4ToF1M9ApplyJoinEvaluateResultV1",
    "SCHEMA_VERSION",
    "evaluate_real_p4_to_f1_m9_apply_join_v1",
]
