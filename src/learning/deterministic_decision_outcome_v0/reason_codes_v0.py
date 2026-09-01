"""Reason-code and hard-block taxonomy foundation v0.

Bound Blueprint tokens live in ``blueprint.ddo.*`` namespaces. Existing
repository dialects are referenced by source path only. Codes are not copied
and not normalized across dialects.
"""

from __future__ import annotations

from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

BLUEPRINT_REASON_TAXONOMY_ID: Final[str] = "blueprint.ddo.reason_v0"
BLUEPRINT_HARD_BLOCK_TAXONOMY_ID: Final[str] = "blueprint.ddo.hard_block_v0"
EXISTING_OPAQUE_TAXONOMY_ID: Final[str] = "peak_trade.existing.unnormalized_v0"

BLUEPRINT_REASON_CODES_V0: Final[tuple[str, ...]] = (
    "NO_ENTRY",
    "NO_EXIT",
    "BULL_TO_BEAR",
    "BEAR_TO_BULL",
    "STALE_BLOCK",
    "RISK_BLOCK",
    "KILL_SWITCH",
    "RECONCILIATION_BLOCK",
    "DYNAMIC_SCOPE_TRANSITION",
    "DYNAMIC_SCOPE_NON_TRANSITION",
    UNKNOWN,
)

BLUEPRINT_HARD_BLOCK_CODES_V0: Final[tuple[str, ...]] = (
    "STALE_BLOCK",
    "RISK_BLOCK",
    "KILL_SWITCH",
    "RECONCILIATION_BLOCK",
    UNKNOWN,
)

# Forensic census of existing dialects. REFERENCE_ONLY: do not import, copy, or unify.
EXISTING_SOURCE_TAXONOMY_REFS_V0: Final[tuple[dict[str, str], ...]] = (
    {
        "taxonomy_ref_id": "existing.risk.cmes.reason_codes",
        "source_path": "src/risk/cmes/reason_codes.py",
        "status": "NOT_NORMALIZED",
        "integration": "REFERENCE_ONLY",
        "codes_copied": "false",
    },
    {
        "taxonomy_ref_id": "existing.risk_layer.kill_switch.audit",
        "source_path": "src/risk_layer/kill_switch/audit.py",
        "status": "NOT_NORMALIZED",
        "integration": "REFERENCE_ONLY",
        "codes_copied": "false",
    },
    {
        "taxonomy_ref_id": "existing.trading.master_v2.canonical_trading_decision_evidence",
        "source_path": "src/trading/master_v2/canonical_trading_decision_evidence_v1.py",
        "status": "NOT_NORMALIZED",
        "integration": "REFERENCE_ONLY",
        "codes_copied": "false",
    },
    {
        "taxonomy_ref_id": "existing.trading.master_v2.safety_kernel_offline_replay",
        "source_path": "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py",
        "status": "NOT_NORMALIZED",
        "integration": "REFERENCE_ONLY",
        "codes_copied": "false",
    },
    {
        "taxonomy_ref_id": "existing.trading.master_v2.directional_assessment_hard_block",
        "source_path": "src/trading/master_v2/directional_assessment_v1.py",
        "status": "NOT_NORMALIZED",
        "integration": "REFERENCE_ONLY",
        "codes_copied": "false",
    },
    {
        "taxonomy_ref_id": "existing.ops.phase_9_2_wallclock_outcome_telemetry",
        "source_path": (
            "src/ops/phase_9_2_wallclock_outcome_telemetry_and_verifier_completeness_binding_v1/"
            "constants_v1.py"
        ),
        "status": "NOT_NORMALIZED",
        "integration": "REFERENCE_ONLY",
        "codes_copied": "false",
    },
)

_ALLOWED_EXISTING_SOURCE_PATHS: Final[frozenset[str]] = frozenset(
    item["source_path"] for item in EXISTING_SOURCE_TAXONOMY_REFS_V0
)

_REASON_CODE_FIELDS: Final[tuple[str, ...]] = (
    "taxonomy_id",
    "code",
    "source_taxonomy_ref",
)


def _require_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise DdoValidationError(f"REASON_CODE_FIELD_INVALID:{field}")
    return value


def validate_coded_ref_v0(
    payload: Mapping[str, Any], *, closed_codes: tuple[str, ...]
) -> dict[str, Any]:
    extra = set(payload.keys()) - set(_REASON_CODE_FIELDS)
    if extra:
        raise DdoValidationError(f"REASON_CODE_UNEXPECTED_FIELD:{sorted(extra)}")
    taxonomy_id = _require_str(payload.get("taxonomy_id"), "taxonomy_id")
    code = _require_str(payload.get("code"), "code")
    source_ref = payload.get("source_taxonomy_ref")
    if taxonomy_id == BLUEPRINT_REASON_TAXONOMY_ID:
        if code not in closed_codes:
            raise DdoValidationError(f"UNKNOWN_REASON_CODE:{taxonomy_id}:{code}")
        if source_ref is not None:
            raise DdoValidationError("BLUEPRINT_REASON_CODE_MUST_NOT_CARRY_SOURCE_TAXONOMY_REF")
        return {
            "taxonomy_id": taxonomy_id,
            "code": code,
            "source_taxonomy_ref": None,
        }
    if taxonomy_id == BLUEPRINT_HARD_BLOCK_TAXONOMY_ID:
        if code not in BLUEPRINT_HARD_BLOCK_CODES_V0:
            raise DdoValidationError(f"UNKNOWN_HARD_BLOCK_CODE:{code}")
        if source_ref is not None:
            raise DdoValidationError("BLUEPRINT_HARD_BLOCK_MUST_NOT_CARRY_SOURCE_TAXONOMY_REF")
        return {
            "taxonomy_id": taxonomy_id,
            "code": code,
            "source_taxonomy_ref": None,
        }
    if taxonomy_id == EXISTING_OPAQUE_TAXONOMY_ID:
        if not isinstance(source_ref, str) or source_ref not in _ALLOWED_EXISTING_SOURCE_PATHS:
            raise DdoValidationError("EXISTING_REASON_CODE_REQUIRES_BOUND_SOURCE_TAXONOMY_REF")
        return {
            "taxonomy_id": taxonomy_id,
            "code": code,
            "source_taxonomy_ref": source_ref,
        }
    raise DdoValidationError(f"UNKNOWN_REASON_TAXONOMY:{taxonomy_id}")


def validate_reason_codes_v0(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raise DdoValidationError("REASON_CODES_MUST_BE_LIST")
    return [
        validate_coded_ref_v0(item, closed_codes=BLUEPRINT_REASON_CODES_V0)
        if isinstance(item, Mapping)
        else (_raise_not_mapping("reason_codes"))
        for item in raw
    ]


def validate_hard_block_reasons_v0(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raise DdoValidationError("HARD_BLOCK_REASONS_MUST_BE_LIST")
    return [
        validate_coded_ref_v0(item, closed_codes=BLUEPRINT_HARD_BLOCK_CODES_V0)
        if isinstance(item, Mapping)
        else (_raise_not_mapping("hard_block_reasons"))
        for item in raw
    ]


def _raise_not_mapping(field: str) -> dict[str, Any]:
    raise DdoValidationError(f"{field.upper()}_ITEM_MUST_BE_OBJECT")
