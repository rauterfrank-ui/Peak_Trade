"""Persisted admission seal required before productive one-shot POST join.

Reuses mandatory NEW-RISK correlation + guard atomic state and RISK-REDUCING
provenance contracts. No caller-supplied bypass flags.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
    CONTRACT_ID as MANDATORY_NEW_RISK_CONTRACT_ID,
    ProductiveVenuePostRiskClassV1,
    classify_productive_venue_post_risk_class_v1,
    load_enter_post_lifecycle_correlation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_risk_reducing_envelope_provenance_v1 import (
    RiskReducingEnvelopeProvenanceError,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    DURABLE_STATE_SENT_INITIATED,
    load_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    STATE_HALTED_UNRESOLVED,
    STATE_RECONCILIATION_PENDING,
    STATE_RESERVED_PRE_POST,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    full_core_durable_entry_state_for_guard_v1,
    load_full_core_atomic_authorization_state_v1,
)

CONTRACT_ID = "CURRENT_PRODUCTIVE_ONE_SHOT_POST_ADMISSION_SEAL_V1"
CORRELATION_FILENAME = "full_core_mandatory_new_risk_enter_post_lifecycle_correlation_v1.json"


class OneShotPostAdmissionSealError(RuntimeError):
    """Fail-closed: one-shot POST lacks persisted order-specific safety authorization."""


def _prove_no_foreign_unknown_submit_v1(
    *,
    store_root: Path | str,
    envelope: FinalOrderEnvelopeV1,
) -> None:
    durable = load_external_effect_durable_consume_v1(store_root=store_root)
    record = durable.get("record")
    if not isinstance(record, Mapping):
        return
    state = str(record.get("durable_state") or "")
    if state != DURABLE_STATE_SENT_INITIATED:
        return
    same_env = str(record.get("envelope_digest") or "") == envelope.envelope_digest
    if not same_env:
        raise OneShotPostAdmissionSealError("NO_NEW_ENTRY_WHILE_UNKNOWN_SUBMIT_IN_FLIGHT")


def _prove_new_risk_persisted_seal_v1(
    *,
    store_root: Path | str,
    envelope: FinalOrderEnvelopeV1,
) -> None:
    correlation = load_enter_post_lifecycle_correlation_v1(store_root=store_root)
    if correlation is None:
        raise OneShotPostAdmissionSealError("NEW_RISK_ADMISSION_SEAL_MISSING")
    if str(correlation.get("contract_id") or "") != MANDATORY_NEW_RISK_CONTRACT_ID:
        raise OneShotPostAdmissionSealError("NEW_RISK_ADMISSION_SEAL_CONTRACT_MISMATCH")
    for field_name, expected in (
        ("envelope_id", envelope.envelope_id),
        ("envelope_digest", envelope.envelope_digest),
        ("clordid", envelope.client_order_id),
    ):
        actual = str(correlation.get(field_name) or "")
        if actual != str(expected):
            raise OneShotPostAdmissionSealError(
                f"NEW_RISK_ADMISSION_SEAL_{field_name.upper()}_MISMATCH"
            )
    binding_digest = str(correlation.get("guard_binding_digest") or "").strip()
    consumption_key = str(correlation.get("guard_consumption_key") or "").strip()
    atomic_raw = str(correlation.get("atomic_state_dir") or "").strip()
    if not binding_digest or not consumption_key or not atomic_raw:
        raise OneShotPostAdmissionSealError("NEW_RISK_ADMISSION_SEAL_BINDING_INCOMPLETE")
    atomic_dir = Path(atomic_raw)
    guard_state = full_core_durable_entry_state_for_guard_v1(
        state_dir=atomic_dir,
        consumption_key=consumption_key,
    )
    if guard_state in {
        STATE_SUBMIT_MAY_HAVE_OCCURRED,
        STATE_RECONCILIATION_PENDING,
        STATE_HALTED_UNRESOLVED,
    }:
        raise OneShotPostAdmissionSealError(f"NO_POST_WHILE_GUARD_STATE_{guard_state}")
    if guard_state != STATE_RESERVED_PRE_POST:
        raise OneShotPostAdmissionSealError(
            f"NEW_RISK_GUARD_ATOMIC_STATE_{guard_state}_NOT_RESERVED_PRE_POST"
        )
    atomic_row = load_full_core_atomic_authorization_state_v1(
        state_dir=atomic_dir,
        consumption_key=consumption_key,
    )
    if atomic_row is None:
        raise OneShotPostAdmissionSealError("NEW_RISK_GUARD_ATOMIC_STATE_MISSING")
    stored_digest = str(getattr(atomic_row, "binding_digest", "") or "").strip()
    if stored_digest != binding_digest:
        raise OneShotPostAdmissionSealError("NEW_RISK_GUARD_BINDING_DIGEST_MISMATCH")


def prove_current_productive_one_shot_post_admission_seal_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    store_root: Path | str,
) -> ProductiveVenuePostRiskClassV1:
    """Require persisted NEW-RISK seal or authorized RISK-REDUCING provenance before POST."""
    assert_envelope_unmodified_v1(envelope)
    root = Path(store_root)
    try:
        risk = classify_productive_venue_post_risk_class_v1(envelope)
    except RiskReducingEnvelopeProvenanceError as exc:
        raise OneShotPostAdmissionSealError(str(exc)) from exc
    _prove_no_foreign_unknown_submit_v1(store_root=root, envelope=envelope)
    if risk is ProductiveVenuePostRiskClassV1.RISK_REDUCING:
        return risk
    _prove_new_risk_persisted_seal_v1(store_root=root, envelope=envelope)
    return risk


__all__ = [
    "CONTRACT_ID",
    "CORRELATION_FILENAME",
    "OneShotPostAdmissionSealError",
    "prove_current_productive_one_shot_post_admission_seal_v1",
]
