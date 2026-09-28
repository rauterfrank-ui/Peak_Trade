"""Immediate pre-mutation freshness for direct actual-venue POST entry.

Reuses collect_fresh_pretrade_runtime_get_v1 and bound-instrument position
truth. UNKNOWN != PASS. Real POST must not proceed without TRUSTED_PRESENT
pretrade conjunction and explicit account/position freshness tokens.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_position_truth_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_POSITIONS,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)


class CurrentProductiveActualVenuePostPreMutationFreshnessError(RuntimeError):
    """Fail-closed pre-mutation freshness violation."""


@dataclass(frozen=True)
class ActualVenuePostPreMutationFreshnessProofV1:
    account_state_fresh: bool
    position_state_fresh: bool
    full_pretrade_conjunction_pass: bool
    all_required_pre_post_gates_pass: bool
    pretrade_evidence_status: str
    position_truth: str
    reason_codes: tuple[str, ...]


def _inst_type_for_envelope_v1(envelope: FinalOrderEnvelopeV1) -> str:
    inst = str(envelope.instrument_id or "").strip()
    if inst.endswith("-SWAP"):
        return "SWAP"
    return "FUTURES"


def prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1 | None,
    pretrade_decision_id: str,
) -> ActualVenuePostPreMutationFreshnessProofV1:
    assert_envelope_unmodified_v1(envelope)
    if read_only_get_transport is None:
        raise CurrentProductiveActualVenuePostPreMutationFreshnessError(
            "PRE_MUTATION_READ_TRANSPORT_REQUIRED"
        )
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveActualVenuePostPreMutationFreshnessError(
            "MAX_POSITIONS_EFFECTIVE_MUST_REMAIN_ONE"
        )
    decision_id = str(pretrade_decision_id or "").strip()
    if not decision_id:
        raise CurrentProductiveActualVenuePostPreMutationFreshnessError(
            "PRETRADE_DECISION_ID_REQUIRED"
        )
    inst_type = _inst_type_for_envelope_v1(envelope)
    evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id=decision_id,
        instrument_id=envelope.instrument_id,
        td_mode=envelope.td_mode,
        limit_px=envelope.price,
        inst_type=inst_type,
        transport=read_only_get_transport,
        require_collection=True,
    )
    pretrade_ok = evidence.evidence_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    reasons: list[str] = list(evidence.reason_codes)
    if not pretrade_ok:
        reasons.append("FULL_PRETRADE_CONJUNCTION_NOT_TRUSTED_PRESENT")

    pos_endpoint = (
        f"{ENDPOINT_ACCOUNT_POSITIONS}?"
        f"{urlencode({'instType': inst_type, 'instId': envelope.instrument_id})}"
    )
    pos_result = read_only_get_transport.get(
        endpoint=pos_endpoint,
        auth_required=True,
        pretrade_decision_id=decision_id,
    )
    if pos_result.get_performed is not True:
        reasons.append("POSITION_GET_NOT_PERFORMED")
        return ActualVenuePostPreMutationFreshnessProofV1(
            account_state_fresh=False,
            position_state_fresh=False,
            full_pretrade_conjunction_pass=False,
            all_required_pre_post_gates_pass=False,
            pretrade_evidence_status=str(evidence.evidence_status),
            position_truth="UNKNOWN",
            reason_codes=tuple(dict.fromkeys(reasons)),
        )
    truth, eligible, _side = extract_position_truth_v1(
        pos_result.payload, native_id=envelope.instrument_id
    )
    position_fresh = pos_result.get_performed is True and truth in {
        "FLAT",
        "BOUND_INSTRUMENT_OPEN",
    }
    if truth == "FOREIGN_OPEN_POSITION_MAX_POSITIONS_1":
        position_fresh = False
        reasons.append("FOREIGN_OPEN_POSITION_MAX_POSITIONS_ONE")
    if not eligible and truth != "BOUND_INSTRUMENT_OPEN":
        position_fresh = False
        reasons.append("POSITION_TRUTH_NOT_ELIGIBLE")
    account_fresh = pretrade_ok and pos_result.get_performed is True
    all_pass = pretrade_ok and account_fresh and position_fresh
    if not all_pass:
        reasons.append("PREPOST_GATE_CONJUNCTION_FAIL_CLOSED")
    return ActualVenuePostPreMutationFreshnessProofV1(
        account_state_fresh=account_fresh,
        position_state_fresh=position_fresh,
        full_pretrade_conjunction_pass=pretrade_ok,
        all_required_pre_post_gates_pass=all_pass,
        pretrade_evidence_status=str(evidence.evidence_status),
        position_truth=str(truth),
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


__all__ = [
    "ActualVenuePostPreMutationFreshnessProofV1",
    "CurrentProductiveActualVenuePostPreMutationFreshnessError",
    "prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1",
]
