"""F5-SURV / F5-CAP per-token shadow calibration test-entry registry (Owner D2/D3).

No optimizable envelope; no shared optimizer surface. One identity per token.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    STAGE2_TOKENS,
)

SCHEMA_VERSION: Final[str] = "canonical_f5_shadow_per_token_calibration_test_entry_v1"
OWNER_DECISION_SURV: Final[str] = "D2"
OWNER_DECISION_CAP: Final[str] = "D3"
MODE: Final[str] = "SHADOW_CALIBRATION_ONLY"
OPTIMIZER_ENVELOPE_AUTHORIZED: Final[bool] = False
PRODUCTIVE_EFFECT: Final[str] = "NONE"


class ShadowCalibrationTestEntryGateV1(str, Enum):
    SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1 = "SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1"
    SHADOW_EVIDENCE_PACK_VALIDATION_V1 = "SHADOW_EVIDENCE_PACK_VALIDATION_V1"


@dataclass(frozen=True)
class ShadowPerTokenCalibrationEntryV1:
    owner_value_token: str
    family_subfamily: str
    owner_decision_id: str
    test_entry_gate: ShadowCalibrationTestEntryGateV1
    optimizer_envelope_authorized: bool
    shared_optimizer_envelope_forbidden: bool
    productive_threshold_mutation_forbidden: bool
    calibration_protocol_ref: str
    campaign_manifest_ref: str


_SURVIVAL_TOKENS: Final[tuple[str, ...]] = tuple(
    t for t in STAGE2_TOKENS if t.startswith("OWNER_VALUE_SURVIVAL_LIMIT_")
)
_CAPITAL_TOKENS: Final[tuple[str, ...]] = tuple(
    t for t in STAGE2_TOKENS if t.startswith("OWNER_VALUE_CAPITAL_SLOT_")
)

_CALIBRATION_PROTOCOL = "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md"
_CAMPAIGN_MANIFEST = (
    "docs/ops/PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_CAMPAIGN_MANIFEST_V1.json"
)


def _entry(token: str, *, subfamily: str, decision: str) -> ShadowPerTokenCalibrationEntryV1:
    return ShadowPerTokenCalibrationEntryV1(
        owner_value_token=token,
        family_subfamily=subfamily,
        owner_decision_id=decision,
        test_entry_gate=ShadowCalibrationTestEntryGateV1.SHADOW_PER_TOKEN_THRESHOLD_SENSITIVITY_V1,
        optimizer_envelope_authorized=False,
        shared_optimizer_envelope_forbidden=True,
        productive_threshold_mutation_forbidden=True,
        calibration_protocol_ref=_CALIBRATION_PROTOCOL,
        campaign_manifest_ref=_CAMPAIGN_MANIFEST,
    )


def shadow_per_token_calibration_entries_v1() -> tuple[ShadowPerTokenCalibrationEntryV1, ...]:
    surv = [_entry(t, subfamily="F5-SURV", decision=OWNER_DECISION_SURV) for t in _SURVIVAL_TOKENS]
    cap = [_entry(t, subfamily="F5-CAP", decision=OWNER_DECISION_CAP) for t in _CAPITAL_TOKENS]
    return tuple(surv + cap)


def build_shadow_calibration_registry_v1() -> Mapping[str, Any]:
    entries = shadow_per_token_calibration_entries_v1()
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "mode": MODE,
            "optimizer_envelope_authorized": OPTIMIZER_ENVELOPE_AUTHORIZED,
            "productive_effect": PRODUCTIVE_EFFECT,
            "survival_token_count": len(_SURVIVAL_TOKENS),
            "capital_token_count": len(_CAPITAL_TOKENS),
            "entries": [
                {
                    "owner_value_token": e.owner_value_token,
                    "family_subfamily": e.family_subfamily,
                    "owner_decision_id": e.owner_decision_id,
                    "test_entry_gate": e.test_entry_gate.value,
                    "optimizer_envelope_authorized": e.optimizer_envelope_authorized,
                    "shared_optimizer_envelope_forbidden": e.shared_optimizer_envelope_forbidden,
                    "productive_threshold_mutation_forbidden": (
                        e.productive_threshold_mutation_forbidden
                    ),
                    "calibration_protocol_ref": e.calibration_protocol_ref,
                    "campaign_manifest_ref": e.campaign_manifest_ref,
                }
                for e in entries
            ],
        }
    )


def assert_no_shared_surv_cap_optimizer_envelope_v1(*, surface_id: str) -> None:
    forbidden_markers = ("F5_SURV_CAP", "SURVIVAL_CAPITAL_COMBINED", "PURE_STACK_SAFETY_OPTIMIZER")
    upper = surface_id.upper()
    for marker in forbidden_markers:
        if marker in upper:
            raise ValueError(f"shared_f5_surv_cap_optimizer_forbidden:{surface_id}")
