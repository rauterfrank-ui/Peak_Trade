"""Mandatory lifecycle admission for productive NEW-RISK Enter venue POST.

Fail-closed gate for `perform_real_venue_post=True` entry orders (non-reduce-only).
Risk-reducing envelopes require authorized CURRENT provenance (not caller-only reduce_only).

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    FullCoreCapitalGuardConfigV1,
    load_full_core_capital_guard_config_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pilot_capital_guard_post_bind_v1 import (
    OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    DURABLE_STATE_SENT_INITIATED,
    load_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_risk_reducing_envelope_provenance_v1 import (
    RiskReducingEnvelopeProvenanceError,
    verify_authorized_risk_reducing_envelope_provenance_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
    STATE_HALTED_UNRESOLVED,
    STATE_RECONCILIATION_PENDING,
    STATE_RESERVED_PRE_POST,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    full_core_durable_entry_state_for_guard_v1,
)

CONTRACT_ID = "CURRENT_PRODUCTIVE_MANDATORY_NEW_RISK_ENTER_POST_ADMISSION_V1"
CORRELATION_FILENAME = "full_core_mandatory_new_risk_enter_post_lifecycle_correlation_v1.json"
GUARD_ATOMIC_SUBDIR = "full_core_enter_post_guard_atomic_v1"


class ProductiveVenuePostRiskClassV1(str, Enum):
    NEW_RISK_ENTER = "NEW_RISK_ENTER"
    RISK_REDUCING = "RISK_REDUCING"


class MandatoryNewRiskEnterPostAdmissionError(RuntimeError):
    """Fail-closed NEW-RISK Enter POST admission violation."""


@dataclass(frozen=True)
class MandatoryNewRiskEnterPostAdmissionContextV1:
    risk_class: ProductiveVenuePostRiskClassV1
    pilot_capital_guard_bind_go: str
    native_instrument_id: str
    guard_config: FullCoreCapitalGuardConfigV1
    atomic_state_dir: Path
    private_get_go: str


def classify_productive_venue_post_risk_class_v1(
    envelope: FinalOrderEnvelopeV1,
) -> ProductiveVenuePostRiskClassV1:
    """Classify venue POST risk; reduce_only alone is never sufficient."""
    assert_envelope_unmodified_v1(envelope)
    if envelope.reduce_only is True:
        verify_authorized_risk_reducing_envelope_provenance_v1(envelope)
        return ProductiveVenuePostRiskClassV1.RISK_REDUCING
    return ProductiveVenuePostRiskClassV1.NEW_RISK_ENTER


def default_guard_atomic_state_dir_for_store_v1(*, store_root: Path | str) -> Path:
    return Path(store_root) / GUARD_ATOMIC_SUBDIR


def correlation_path_v1(*, store_root: Path | str) -> Path:
    return Path(store_root) / CORRELATION_FILENAME


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = json.dumps(payload, sort_keys=True).lower()
    for token in ("secret", "passphrase", "api_key", "apikey", "private_key"):
        if token in blob:
            raise MandatoryNewRiskEnterPostAdmissionError(f"SECRET_TOKEN_PRESENT:{token}")


def load_enter_post_lifecycle_correlation_v1(
    *, store_root: Path | str
) -> dict[str, Any] | None:
    path = correlation_path_v1(store_root=store_root)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MandatoryNewRiskEnterPostAdmissionError("CORRELATION_MALFORMED")
    return payload


def persist_enter_post_lifecycle_correlation_v1(
    *,
    store_root: Path | str,
    envelope: FinalOrderEnvelopeV1,
    authorization_binding: FullCoreAuthorizationBindingV1,
    pretrade_decision_id: str,
    submit_attempt_id: str,
    atomic_state_dir: Path | str,
) -> None:
    assert_envelope_unmodified_v1(envelope)
    record = {
        "contract_id": CONTRACT_ID,
        "envelope_id": envelope.envelope_id,
        "envelope_digest": envelope.envelope_digest,
        "clordid": envelope.client_order_id,
        "native_id": authorization_binding.native_id,
        "account_scope": authorization_binding.account_scope,
        "pretrade_decision_id": pretrade_decision_id,
        "submit_attempt_id": submit_attempt_id,
        "guard_consumption_key": authorization_binding.consumption_key(),
        "guard_binding_digest": authorization_binding.to_canary_atomic_binding_v1().binding_digest(),
        "atomic_state_dir": str(atomic_state_dir),
    }
    _assert_no_secrets(record)
    path = correlation_path_v1(store_root=store_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def prove_new_risk_enter_post_store_admission_clear_v1(
    *,
    store_root: Path | str,
    envelope: FinalOrderEnvelopeV1,
    atomic_state_dir: Path | str | None = None,
) -> None:
    """Fail-closed if permit or guard state forbids a new entry POST."""
    assert_envelope_unmodified_v1(envelope)
    durable = load_external_effect_durable_consume_v1(store_root=store_root)
    record = durable.get("record")
    if isinstance(record, Mapping):
        state = str(record.get("durable_state") or "")
        if state == DURABLE_STATE_SENT_INITIATED:
            same_env = str(record.get("envelope_digest") or "") == envelope.envelope_digest
            if not same_env:
                raise MandatoryNewRiskEnterPostAdmissionError(
                    "NO_NEW_ENTRY_WHILE_UNKNOWN_SUBMIT_IN_FLIGHT"
                )
            raise MandatoryNewRiskEnterPostAdmissionError(
                "NO_NEW_ENTRY_WHILE_UNKNOWN_SUBMIT_SAME_ENVELOPE"
            )
    correlation = load_enter_post_lifecycle_correlation_v1(store_root=store_root)
    if correlation is not None:
        prior_digest = str(correlation.get("envelope_digest") or "")
        if prior_digest and prior_digest != envelope.envelope_digest:
            raise MandatoryNewRiskEnterPostAdmissionError(
                "LIFECYCLE_CORRELATION_ENVELOPE_MISMATCH"
            )
    atomic_dir = Path(atomic_state_dir) if atomic_state_dir is not None else None
    if atomic_dir is None and correlation is not None:
        raw = str(correlation.get("atomic_state_dir") or "").strip()
        if raw:
            atomic_dir = Path(raw)
    if atomic_dir is not None and correlation is not None:
        key = str(correlation.get("guard_consumption_key") or "")
        if key:
            guard_state = full_core_durable_entry_state_for_guard_v1(
                state_dir=atomic_dir,
                consumption_key=key,
            )
            if guard_state in {
                STATE_RESERVED_PRE_POST,
                STATE_SUBMIT_MAY_HAVE_OCCURRED,
                STATE_RECONCILIATION_PENDING,
                STATE_HALTED_UNRESOLVED,
            }:
                raise MandatoryNewRiskEnterPostAdmissionError(
                    f"NO_NEW_ENTRY_WHILE_GUARD_STATE_{guard_state}"
                )


def resolve_mandatory_new_risk_enter_post_admission_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    store_root: Path | str,
    pilot_capital_guard_bind_go: str | None,
    pilot_capital_guard_config: FullCoreCapitalGuardConfigV1 | None,
    pilot_native_instrument_id: str | None,
    pilot_atomic_state_dir: Path | None,
    pilot_dw_private_get_go: str,
    read_only_get_transport_present: bool,
) -> MandatoryNewRiskEnterPostAdmissionContextV1 | None:
    risk = classify_productive_venue_post_risk_class_v1(envelope)
    if risk is ProductiveVenuePostRiskClassV1.RISK_REDUCING:
        return None

    pilot_go = str(pilot_capital_guard_bind_go or "").strip()
    if pilot_go != OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1:
        raise MandatoryNewRiskEnterPostAdmissionError(
            "NEW_RISK_POST_MANDATORY_PILOT_CAPITAL_GUARD_BIND_GO_REQUIRED"
        )
    if not read_only_get_transport_present:
        raise MandatoryNewRiskEnterPostAdmissionError(
            "NEW_RISK_POST_MANDATORY_READ_TRANSPORT_REQUIRED"
        )
    native = str(pilot_native_instrument_id or "").strip()
    if not native:
        raise MandatoryNewRiskEnterPostAdmissionError(
            "NEW_RISK_POST_MANDATORY_NATIVE_INSTRUMENT_ID_REQUIRED"
        )
    cfg = pilot_capital_guard_config or load_full_core_capital_guard_config_v1()
    if cfg.full_core_guard_join_enabled is not True:
        raise MandatoryNewRiskEnterPostAdmissionError("NEW_RISK_POST_GUARD_JOIN_DISABLED")
    if cfg.owner_caps_ratified is not True:
        raise MandatoryNewRiskEnterPostAdmissionError("NEW_RISK_POST_OWNER_CAPS_UNRATIFIED")
    atomic_dir = (
        pilot_atomic_state_dir
        if pilot_atomic_state_dir is not None
        else default_guard_atomic_state_dir_for_store_v1(store_root=store_root)
    )
    prove_new_risk_enter_post_store_admission_clear_v1(
        store_root=store_root,
        envelope=envelope,
        atomic_state_dir=atomic_dir,
    )
    private_go = str(pilot_dw_private_get_go or "").strip()
    if private_go != "GRANTED_SCOPED_READ_ONLY":
        raise MandatoryNewRiskEnterPostAdmissionError("NEW_RISK_POST_DW_PRIVATE_GET_GO_INVALID")
    return MandatoryNewRiskEnterPostAdmissionContextV1(
        risk_class=risk,
        pilot_capital_guard_bind_go=pilot_go,
        native_instrument_id=native,
        guard_config=cfg,
        atomic_state_dir=atomic_dir,
        private_get_go=private_go,
    )


__all__ = [
    "RiskReducingEnvelopeProvenanceError",
    "CONTRACT_ID",
    "CORRELATION_FILENAME",
    "GUARD_ATOMIC_SUBDIR",
    "MandatoryNewRiskEnterPostAdmissionContextV1",
    "MandatoryNewRiskEnterPostAdmissionError",
    "ProductiveVenuePostRiskClassV1",
    "classify_productive_venue_post_risk_class_v1",
    "correlation_path_v1",
    "default_guard_atomic_state_dir_for_store_v1",
    "load_enter_post_lifecycle_correlation_v1",
    "persist_enter_post_lifecycle_correlation_v1",
    "prove_new_risk_enter_post_store_admission_clear_v1",
    "resolve_mandatory_new_risk_enter_post_admission_v1",
]
