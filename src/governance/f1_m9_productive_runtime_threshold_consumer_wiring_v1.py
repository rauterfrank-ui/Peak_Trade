"""F1/M9 productive runtime threshold consumer wiring v1.

Mechanical composition: governed seam transport → presence gate → bounded MV2 enforcement
→ existing Double Play alpha boundary. No new threshold authority, enforcement engine,
or orchestrator owner.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.authorized_productive_parameter_seam_v1 import verify_seam_record_digest_v1
from src.governance.f1_m9_bounded_threshold_enforcement_mv2_consumer_v1 import (
    apply_bounded_enforcement_to_double_play_alpha_v1,
    evaluate_bounded_threshold_enforcement_at_mv2_consumer_v1,
    threshold_enforcement_authorized_v1,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    STATUS_TRANSPORT_READY,
    resolve_governed_runtime_seam_for_presence_gate_v1,
)
from src.governance.real_p4_to_f1_m9_apply_lineage_join_v1 import JOIN_STATUS_NOT_CANONICAL
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    derive_presence_status_for_age_policy_v1,
)
from src.trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    DoublePlayTypedVolatilityPresenceGateResultV1,
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
)
from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    CanonicalMarketContextBindingOutcome,
    CanonicalMarketContextEligibilityV1,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    VolatilityRestartStatusV1,
    VolatilityReuseStatusV1,
)

SCHEMA_VERSION: Final[str] = "f1_m9_productive_runtime_threshold_consumer_wiring/v1"
WORKPACKAGE_ID: Final[str] = (
    "GOVERNED_F1_M9_PRODUCTIVE_RUNTIME_THRESHOLD_CONSUMER_WIRING_REAL_MECHANICAL_CONTINUATION_V1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/"
    "GOVERNED_F1_M9_PRODUCTIVE_RUNTIME_THRESHOLD_CONSUMER_WIRING_REAL_MECHANICAL_CONTINUATION_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1_decision_v1.json"
)
OWNER_WP_DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "governed_f1_m9_productive_runtime_threshold_consumer_wiring_wp_v1_owner_decision_v1.json"
)

RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS: Final[int] = 600
REAL_P4_TO_F1_M9_JOIN_STATUS: Final[str] = JOIN_STATUS_NOT_CANONICAL
CONTINUOUS_RUN_AUTHORIZED: Final[bool] = False
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False

FORBIDDEN_UNGOVERNED_NUMERIC_DEFAULTS: Final[tuple[int, ...]] = (25, 100, 500, 10000)

STATUS_WIRED: Final[str] = "THRESHOLD_RUNTIME_CONSUMER_WIRED"
STATUS_DENIED: Final[str] = "THRESHOLD_RUNTIME_CONSUMER_DENIED_FAIL_CLOSED"

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class F1M9ProductiveRuntimeThresholdConsumerPathResultV1:
    wiring_status: str
    reason_codes: tuple[str, ...]
    transport_ready: bool
    presence_gate: DoublePlayTypedVolatilityPresenceGateResultV1 | None
    threshold_numeric_max_age_seconds: float | None
    seam_digest: str | None
    owner_threshold_record_digest: str | None
    configuration_runtime_applied: bool
    enforcement_applied: bool
    alpha_scope_entry_authority_allowed: bool
    productive_runtime_admission: bool
    productive_activation_authorized: bool
    real_p4_to_f1_m9_join_status: str
    external_effect_authorized: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "alpha_scope_entry_authority_allowed": self.alpha_scope_entry_authority_allowed,
            "configuration_runtime_applied": self.configuration_runtime_applied,
            "enforcement_applied": self.enforcement_applied,
            "external_effect_authorized": self.external_effect_authorized,
            "owner_threshold_record_digest": self.owner_threshold_record_digest,
            "presence_gate": (
                self.presence_gate.to_dict() if self.presence_gate is not None else None
            ),
            "productive_activation_authorized": self.productive_activation_authorized,
            "productive_runtime_admission": self.productive_runtime_admission,
            "real_p4_to_f1_m9_join_status": self.real_p4_to_f1_m9_join_status,
            "reason_codes": list(self.reason_codes),
            "seam_digest": self.seam_digest,
            "threshold_numeric_max_age_seconds": self.threshold_numeric_max_age_seconds,
            "transport_ready": self.transport_ready,
            "wiring_status": self.wiring_status,
        }


def load_consumer_wiring_decision_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _REPO_ROOT
    path = root / DECISION_CONFIG
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def consumer_wiring_authorized_v1(*, repo_root: Path | None = None) -> bool:
    decision = load_consumer_wiring_decision_v1(repo_root=repo_root)
    return (
        decision.get("owner_go") is True
        and decision.get("threshold_runtime_consumer_wiring_authorized") is True
        and decision.get("productive_activation_authorized") is False
    )


def _deny(
    reasons: list[str],
    *,
    presence_gate: DoublePlayTypedVolatilityPresenceGateResultV1 | None = None,
) -> F1M9ProductiveRuntimeThresholdConsumerPathResultV1:
    return F1M9ProductiveRuntimeThresholdConsumerPathResultV1(
        wiring_status=STATUS_DENIED,
        reason_codes=tuple(dict.fromkeys(reasons)),
        transport_ready=False,
        presence_gate=presence_gate,
        threshold_numeric_max_age_seconds=None,
        seam_digest=None,
        owner_threshold_record_digest=None,
        configuration_runtime_applied=False,
        enforcement_applied=False,
        alpha_scope_entry_authority_allowed=False,
        productive_runtime_admission=False,
        productive_activation_authorized=False,
        real_p4_to_f1_m9_join_status=REAL_P4_TO_F1_M9_JOIN_STATUS,
        external_effect_authorized=EXTERNAL_EFFECT_AUTHORIZED,
    )


def _forbidden_numeric_default(value: Any) -> bool:
    try:
        numeric = int(float(value))
    except (TypeError, ValueError):
        return False
    return numeric in FORBIDDEN_UNGOVERNED_NUMERIC_DEFAULTS


def evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
    *,
    market_context: CanonicalMarketContextV1,
    eligibility: CanonicalMarketContextEligibilityV1 | None = None,
    binding_outcome: CanonicalMarketContextBindingOutcome = (
        CanonicalMarketContextBindingOutcome.ACCEPTED
    ),
    reuse_status: VolatilityReuseStatusV1 = VolatilityReuseStatusV1.NOT_APPLICABLE,
    restart_status: VolatilityRestartStatusV1 = VolatilityRestartStatusV1.NOT_APPLICABLE,
    governed_seam_record: Mapping[str, Any] | None = None,
    require_governed_seam: bool = False,
    runtime_surface: str | None = None,
    repo_root: Path | None = None,
) -> F1M9ProductiveRuntimeThresholdConsumerPathResultV1:
    """Wire ratified/applied F1/M9 threshold through transport, gate, and bounded enforcement."""
    root = repo_root or _REPO_ROOT
    reasons: list[str] = []

    if require_governed_seam and not consumer_wiring_authorized_v1(repo_root=root):
        return _deny(["CONSUMER_WIRING_NOT_AUTHORIZED"])

    runtime_admission_granted = False
    activation_authorized = False
    if require_governed_seam:
        from src.governance.current_productive_activation_policy_v1 import (
            evaluate_productive_runtime_admission_v1,
        )

        if not runtime_surface:
            return _deny(["PRODUCTIVE_RUNTIME_SURFACE_REQUIRED"])
        admission = evaluate_productive_runtime_admission_v1(
            runtime_surface=runtime_surface,
            repo_root=root,
        )
        if not admission.runtime_admission_granted:
            return _deny(list(admission.reason_codes) or ["PRODUCTIVE_RUNTIME_ADMISSION_DENIED"])
        runtime_admission_granted = True
        activation_authorized = admission.productive_activation_authorized

    transport = resolve_governed_runtime_seam_for_presence_gate_v1(governed_seam_record)
    transport_ready = transport.transport_status == STATUS_TRANSPORT_READY

    if require_governed_seam:
        if governed_seam_record is None:
            return _deny(["GOVERNED_SEAM_RECORD_REQUIRED"])
        if not transport_ready or transport.seam_for_consumer is None:
            return _deny(list(transport.reason_codes) or ["RUNTIME_SEAM_TRANSPORT_DENIED"])

    seam_for_gate = transport.seam_for_consumer
    presence_gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        market_context,
        binding_outcome=binding_outcome,
        eligibility=eligibility,
        reuse_status=reuse_status,
        restart_status=restart_status,
        authorized_productive_parameter_seam=seam_for_gate,
    )

    if require_governed_seam and seam_for_gate is None:
        return _deny(["PRESENCE_GATE_GOVERNED_SEAM_MISSING"], presence_gate=presence_gate)

    seam_record = dict(seam_for_gate) if seam_for_gate is not None else None
    threshold_seconds: float | None = None
    seam_digest: str | None = None
    owner_threshold_digest: str | None = None
    runtime_applied = False

    if seam_record is not None:
        if not verify_seam_record_digest_v1(seam_record):
            return _deny(["SEAM_DIGEST_INVALID"], presence_gate=presence_gate)
        seam_digest = str(seam_record.get("seam_digest") or "")
        owner_threshold_digest = str(seam_record.get("threshold_value_authorization_digest") or "")
        runtime_applied = seam_record.get("runtime_applied") is True
        numeric = seam_record.get("numeric_max_age_seconds")
        if _forbidden_numeric_default(numeric):
            return _deny(["FORBIDDEN_UNGOVERNED_NUMERIC_DEFAULT"], presence_gate=presence_gate)
        if require_governed_seam:
            if not runtime_applied:
                return _deny(
                    ["CONFIGURATION_RUNTIME_APPLIED_REQUIRED"], presence_gate=presence_gate
                )
            if float(numeric) != float(RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS):
                return _deny(["RATIFIED_THRESHOLD_VALUE_MISMATCH"], presence_gate=presence_gate)
        try:
            threshold_seconds = float(numeric)
        except (TypeError, ValueError):
            return _deny(["NUMERIC_MAX_AGE_INVALID"], presence_gate=presence_gate)

    presence_for_enforcement = derive_presence_status_for_age_policy_v1(
        typed_estimate_present=presence_gate.typed_estimate_present,
        typed_validation_ok=presence_gate.typed_validation_ok,
    )
    enforcement = evaluate_bounded_threshold_enforcement_at_mv2_consumer_v1(
        seam_record=seam_record,
        estimate=market_context.canonical_volatility_estimate,
        reference_market_event_time=market_context.market_event_time,
        presence_status=presence_for_enforcement,
        reuse_status=reuse_status,
        restart_status=restart_status,
        clock_trust_status=market_context.clock_trust_status,
        data_integrity_status=market_context.data_integrity_status,
        repo_root=root,
    )

    if require_governed_seam and not threshold_enforcement_authorized_v1(repo_root=root):
        return _deny(["THRESHOLD_ENFORCEMENT_NOT_AUTHORIZED"], presence_gate=presence_gate)

    alpha_allowed, alpha_reasons = apply_bounded_enforcement_to_double_play_alpha_v1(
        baseline_alpha_allowed=presence_gate.alpha_scope_entry_authority_allowed,
        enforcement=enforcement,
    )
    reasons.extend(alpha_reasons)
    if transport_ready:
        reasons.append("PRESENCE_GATE_TRANSPORT_READY")
    if enforcement.enforcement_applied:
        reasons.append("BOUNDED_THRESHOLD_ENFORCEMENT_APPLIED")

    if require_governed_seam:
        wiring_status = (
            STATUS_WIRED
            if transport_ready and seam_record is not None and enforcement.enforcement_applied
            else STATUS_DENIED
        )
    else:
        wiring_status = STATUS_WIRED if presence_gate is not None else STATUS_DENIED
    return F1M9ProductiveRuntimeThresholdConsumerPathResultV1(
        wiring_status=wiring_status,
        reason_codes=tuple(dict.fromkeys(reasons)),
        transport_ready=transport_ready,
        presence_gate=presence_gate,
        threshold_numeric_max_age_seconds=threshold_seconds,
        seam_digest=seam_digest,
        owner_threshold_record_digest=owner_threshold_digest or None,
        configuration_runtime_applied=runtime_applied,
        enforcement_applied=enforcement.enforcement_applied,
        alpha_scope_entry_authority_allowed=alpha_allowed,
        productive_runtime_admission=runtime_admission_granted,
        productive_activation_authorized=activation_authorized,
        real_p4_to_f1_m9_join_status=REAL_P4_TO_F1_M9_JOIN_STATUS,
        external_effect_authorized=EXTERNAL_EFFECT_AUTHORIZED,
    )


__all__ = [
    "CONTINUOUS_RUN_AUTHORIZED",
    "DECISION_CONFIG",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "FORBIDDEN_UNGOVERNED_NUMERIC_DEFAULTS",
    "F1M9ProductiveRuntimeThresholdConsumerPathResultV1",
    "NORMATIVE_SPEC",
    "OWNER_WP_DECISION_CONFIG",
    "RATIFIED_THRESHOLD_NUMERIC_MAX_AGE_SECONDS",
    "REAL_P4_TO_F1_M9_JOIN_STATUS",
    "SCHEMA_VERSION",
    "STATUS_DENIED",
    "STATUS_WIRED",
    "WORKPACKAGE_ID",
    "consumer_wiring_authorized_v1",
    "evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1",
    "load_consumer_wiring_decision_v1",
]
