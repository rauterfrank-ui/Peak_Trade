"""Offline delayed G12 conjunction contract tests. No network. No submit."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.constants_v1 import (
    CANONICAL_SSOT_LIVE_FLATTEN_PROVABILITY_PROVEN,
    CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN,
    DELAYED_ZERO_DOES_NOT_IMPLY_LIVE_FLATTEN_PROVEN,
    EMPTY_DATA_IS_ZERO,
    FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL,
    G12_STATUS,
    POSID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS,
    TARGET_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.contract_v1 import (
    DelayedG12ConjunctionContractError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.evaluate_v1 import (
    evaluate_delayed_g12_conjunction_v1,
)
from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.types_v1 import (
    DelayedG12ConjunctionInputV1,
    FlattenLineageSlotV1,
    ObservationSlotV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_action_proof_contract_v1 import (
    P7_3_EMPTY_DATA_IS_ZERO,
    evaluate_canary_flatten_post_action_proof_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_ZERO_PROVEN,
    classify_target_position_state_v1,
)

TARGET = TARGET_INSTRUMENT_ID
OTHER = "BTC-USD_UM_XPERP-999999"
POS_ID = "3891385768441942017"
CL_ORD_ID = "ptokxeprod508b7b41508b7b4101"
PRE_ID = "pre-identity-aaa"
IMMEDIATE_ID = "immediate-post-identity-bbb"
DELAYED_ID = "delayed-zero-identity-ccc"
PENDING_ID = "pending-identity-ddd"
RELATED_ID = "related-identity-eee"


def _envelope(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _slot(
    *,
    endpoint: str,
    identity: str,
    request_time_utc: str,
    payload: Mapping[str, Any],
    query: Mapping[str, str] | None = None,
    http_status: int = 200,
) -> ObservationSlotV1:
    return ObservationSlotV1(
        endpoint=endpoint,
        observation_identity=identity,
        request_time_utc=request_time_utc,
        payload=payload,
        query=dict(query) if query else None,
        http_status=http_status,
        venue_code="0",
    )


def _lineage(**overrides: Any) -> FlattenLineageSlotV1:
    payload: dict[str, Any] = {
        "authorized": True,
        "reduce_only": True,
        "ord_type": "limit",
        "side": "sell",
        "sz": "1",
        "px": "0.7675",
        "cl_ord_id": CL_ORD_ID,
        "instrument_id": TARGET,
        "venue_accepted": True,
        "submit_time_utc": "2026-09-04T06:18:16Z",
        "submit_http_status": 200,
        "pre_observation": _slot(
            endpoint="/api/v5/account/positions",
            identity=PRE_ID,
            request_time_utc="2026-09-04T06:18:15Z",
            payload=_envelope({"instId": TARGET, "pos": "1", "posId": POS_ID}),
        ),
        "fill_cl_ord_id": CL_ORD_ID,
        "fill_instrument_id": TARGET,
        "fill_side": "sell",
        "fill_sz": "1",
        "fill_px": "0.7675",
        "fill_time_utc": "2026-09-04T06:19:00Z",
        "immediate_post_action_identity": IMMEDIATE_ID,
        "proven_pos_id": POS_ID,
    }
    payload.update(overrides)
    return FlattenLineageSlotV1(**payload)


def _delayed(**overrides: Any) -> ObservationSlotV1:
    payload: dict[str, Any] = {
        "endpoint": f"/api/v5/account/positions?posId={POS_ID}",
        "identity": DELAYED_ID,
        "request_time_utc": "2026-09-04T11:01:48Z",
        "payload": _envelope({"instId": TARGET, "pos": "0", "posId": POS_ID, "posSide": "net"}),
        "query": {"posId": POS_ID},
    }
    payload.update(overrides)
    return _slot(**payload)


def _pending(**overrides: Any) -> ObservationSlotV1:
    payload: dict[str, Any] = {
        "endpoint": "/api/v5/trade/orders-pending",
        "identity": PENDING_ID,
        "request_time_utc": "2026-09-04T11:02:00Z",
        "payload": _envelope(),
        "query": {},
    }
    payload.update(overrides)
    return _slot(**payload)


def _related(**overrides: Any) -> ObservationSlotV1:
    payload: dict[str, Any] = {
        "endpoint": "/api/v5/account/positions",
        "identity": RELATED_ID,
        "request_time_utc": "2026-09-04T11:02:01Z",
        "payload": _envelope(),
        "query": {},
    }
    payload.update(overrides)
    return _slot(**payload)


def _complete(**overrides: Any) -> DelayedG12ConjunctionInputV1:
    payload: dict[str, Any] = {
        "instrument_id": TARGET,
        "flatten_lineage": _lineage(),
        "delayed_target_zero": _delayed(),
        "pending_orders": _pending(),
        "related_positions": _related(),
        "forensic_local_treated_as_canonical": False,
    }
    payload.update(overrides)
    return DelayedG12ConjunctionInputV1(**payload)


def _status(verdict: Any, proposition: str) -> str:
    mapping = {item.proposition: item.status for item in verdict.conjuncts}
    return mapping[proposition]


def test_contract_invariants_remain_fail_closed() -> None:
    assert_contract_invariants_v1()
    assert EMPTY_DATA_IS_ZERO is False
    assert DELAYED_ZERO_DOES_NOT_IMPLY_LIVE_FLATTEN_PROVEN is True
    assert POSID_FILTERED_ENVELOPE_DOES_NOT_PROVE_RELATED_COMPLETENESS is True
    assert FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL is True
    assert G12_STATUS == "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN"
    assert CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN is False
    assert CANONICAL_SSOT_LIVE_FLATTEN_PROVABILITY_PROVEN is False


def test_positive_full_conjunction_does_not_rewrite_canonical_ssot() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(_complete())
    assert verdict.full_conjunction_proven is True
    assert verdict.live_flatten_provability_proven is True
    assert verdict.delayed_explicit_target_zero is True
    assert verdict.canonical_ssot_g12_status == G12_STATUS
    assert verdict.network_effect == "none"
    assert verdict.order_effect == "none"
    assert len(verdict.provenance_sha256) == 64
    for item in verdict.conjuncts:
        assert item.status == "PASS"


def test_delayed_zero_alone_cannot_close_g12() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            flatten_lineage=None,
            pending_orders=None,
            related_positions=None,
        )
    )
    assert verdict.delayed_explicit_target_zero is True
    assert verdict.full_conjunction_proven is False
    assert verdict.live_flatten_provability_proven is False
    assert _status(verdict, "P5_DELAYED_TARGET_ZERO") == "PASS"
    assert _status(verdict, "P7_PENDING_EMPTY") == "NOT_PROVEN"
    assert _status(verdict, "P9_NO_UNEXPECTED_RELATED_NONZERO") == "NOT_PROVEN"


def test_fill_only_cannot_close_g12() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(delayed_target_zero=None, pending_orders=None, related_positions=None)
    )
    assert _status(verdict, "P3_ORDER_FILLED") == "PASS"
    assert _status(verdict, "P5_DELAYED_TARGET_ZERO") == "NOT_PROVEN"
    assert verdict.full_conjunction_proven is False
    assert verdict.live_flatten_provability_proven is False


def test_empty_delayed_data_is_not_zero() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(delayed_target_zero=_delayed(payload=_envelope()))
    )
    assert _status(verdict, "P5_DELAYED_TARGET_ZERO") == "FAIL"
    assert "EMPTY_DATA_IS_NOT_ZERO" in _reason(verdict, "P5_DELAYED_TARGET_ZERO")
    assert verdict.delayed_explicit_target_zero is False
    assert verdict.full_conjunction_proven is False


def _reason(verdict: Any, proposition: str) -> str:
    mapping = {item.proposition: item.reason for item in verdict.conjuncts}
    return mapping[proposition]


def test_absent_target_row_is_not_zero() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            delayed_target_zero=_delayed(
                payload=_envelope({"instId": OTHER, "pos": "0", "posId": "1"})
            )
        )
    )
    assert _status(verdict, "P5_DELAYED_TARGET_ZERO") == "FAIL"
    classified = classify_target_position_state_v1(
        positions_payload=_envelope({"instId": OTHER, "pos": "0", "posId": "1"}),
        instrument_id=TARGET,
    )
    assert classified.state == TARGET_POSITION_NOT_OBSERVED


def test_ambiguous_posid_rows_fail() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            delayed_target_zero=_delayed(
                payload=_envelope(
                    {"instId": TARGET, "pos": "0", "posId": POS_ID},
                    {"instId": TARGET, "pos": "0", "posId": POS_ID},
                )
            )
        )
    )
    assert _status(verdict, "P5_DELAYED_TARGET_ZERO") == "FAIL"
    assert "AMBIGUOUS" in _reason(verdict, "P5_DELAYED_TARGET_ZERO") or "UNIQUE" in _reason(
        verdict, "P5_DELAYED_TARGET_ZERO"
    )


def test_wrong_posid_fails_lineage() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            delayed_target_zero=_delayed(
                endpoint="/api/v5/account/positions?posId=1",
                query={"posId": "1"},
                payload=_envelope({"instId": TARGET, "pos": "0", "posId": "1"}),
            )
        )
    )
    assert _status(verdict, "P5_DELAYED_TARGET_ZERO") == "FAIL"
    assert _status(verdict, "P6_CAUSAL_LINEAGE") == "FAIL"


def test_wrong_clordid_fill_fails() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(flatten_lineage=_lineage(fill_cl_ord_id="other-clordid"))
    )
    assert _status(verdict, "P3_ORDER_FILLED") == "FAIL"
    assert verdict.full_conjunction_proven is False


def test_pending_nonempty_fails() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            pending_orders=_pending(payload=_envelope({"instId": TARGET, "clOrdId": CL_ORD_ID}))
        )
    )
    assert _status(verdict, "P7_PENDING_EMPTY") == "FAIL"
    assert _reason(verdict, "P7_PENDING_EMPTY") == "PENDING_NOT_EMPTY"


def test_stale_pending_before_delayed_zero_fails() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(pending_orders=_pending(request_time_utc="2026-09-04T06:19:54Z"))
    )
    assert _status(verdict, "P7_PENDING_EMPTY") == "FAIL"
    assert "STALE" in _reason(verdict, "P7_PENDING_EMPTY")


def test_related_nonzero_fails() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            related_positions=_related(
                payload=_envelope({"instId": OTHER, "pos": "2"}),
            )
        )
    )
    assert _status(verdict, "P9_NO_UNEXPECTED_RELATED_NONZERO") == "FAIL"
    assert _reason(verdict, "P9_NO_UNEXPECTED_RELATED_NONZERO") == (
        "UNEXPECTED_RELATED_INSTRUMENT_POSITION"
    )


def test_posid_filtered_related_surface_cannot_prove_p9() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            related_positions=_related(
                endpoint=f"/api/v5/account/positions?posId={POS_ID}",
                query={"posId": POS_ID},
                payload=_envelope({"instId": TARGET, "pos": "0", "posId": POS_ID}),
            )
        )
    )
    assert _status(verdict, "P9_NO_UNEXPECTED_RELATED_NONZERO") == "FAIL"
    assert _reason(verdict, "P9_NO_UNEXPECTED_RELATED_NONZERO") == (
        "POSID_FILTERED_ENVELOPE_CANNOT_PROVE_RELATED"
    )


def test_instid_filtered_related_surface_cannot_prove_p9() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            related_positions=_related(
                endpoint=f"/api/v5/account/positions?instId={TARGET}",
                query={"instId": TARGET},
                payload=_envelope(),
            )
        )
    )
    assert _status(verdict, "P9_NO_UNEXPECTED_RELATED_NONZERO") == "FAIL"
    assert _reason(verdict, "P9_NO_UNEXPECTED_RELATED_NONZERO") == (
        "INSTID_FILTERED_ENVELOPE_CANNOT_PROVE_RELATED"
    )


def test_flip_risk_nonzero_opposite_post_fails() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            delayed_target_zero=_delayed(
                payload=_envelope({"instId": TARGET, "pos": "-1", "posId": POS_ID})
            )
        )
    )
    assert _status(verdict, "P5_DELAYED_TARGET_ZERO") == "FAIL"
    assert _status(verdict, "P8_NO_FLIP") == "NOT_PROVEN"


def test_temporal_inversion_fails() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(delayed_target_zero=_delayed(request_time_utc="2026-09-04T06:18:10Z"))
    )
    assert _status(verdict, "P10_TEMPORAL_ORDER") == "FAIL"
    assert "TEMPORAL_INVERSION" in _reason(verdict, "P10_TEMPORAL_ORDER")


def test_identity_equality_with_immediate_post_readback_fails_p6() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(delayed_target_zero=_delayed(identity=IMMEDIATE_ID))
    )
    assert _status(verdict, "P6_CAUSAL_LINEAGE") == "FAIL"
    assert _reason(verdict, "P6_CAUSAL_LINEAGE") == (
        "DELAYED_IDENTITY_EQUALS_IMMEDIATE_POST_READBACK"
    )


def test_wrong_instrument_binding_rejected() -> None:
    with pytest.raises(DelayedG12ConjunctionContractError, match="INSTRUMENT_BINDING_MISMATCH"):
        evaluate_delayed_g12_conjunction_v1(_complete(instrument_id=OTHER))


def test_forensic_local_promotion_rejected() -> None:
    with pytest.raises(DelayedG12ConjunctionContractError, match="FORENSIC_LOCAL_PROMOTED"):
        evaluate_delayed_g12_conjunction_v1(_complete(forensic_local_treated_as_canonical=True))


def test_incomplete_evidence_is_not_proven() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        DelayedG12ConjunctionInputV1(
            instrument_id=TARGET,
            flatten_lineage=None,
            delayed_target_zero=None,
            pending_orders=None,
            related_positions=None,
        )
    )
    assert verdict.full_conjunction_proven is False
    assert all(item.status == "NOT_PROVEN" for item in verdict.conjuncts)


def test_case_c_empty_positions_remain_not_zero_on_existing_classifier() -> None:
    classified = classify_target_position_state_v1(
        positions_payload=_envelope(),
        instrument_id=TARGET,
    )
    assert classified.state == TARGET_POSITION_NOT_OBSERVED
    assert P7_3_EMPTY_DATA_IS_ZERO is False
    same_session = evaluate_canary_flatten_post_action_proof_contract_v1(
        pre_positions_payload=_envelope({"instId": TARGET, "pos": "1"}),
        post_positions_payload=_envelope(),
        post_pending_orders_payload=_envelope(),
        instrument_id=TARGET,
    )
    assert same_session.offline_contract_satisfied is False
    assert same_session.post_target_observed is False
    assert same_session.live_flatten_provability == "UNPROVEN"


def test_existing_explicit_zero_row_still_classifies_as_zero() -> None:
    classified = classify_target_position_state_v1(
        positions_payload=_envelope({"instId": TARGET, "pos": "0", "posId": POS_ID}),
        instrument_id=TARGET,
    )
    assert classified.state == TARGET_POSITION_ZERO_PROVEN


def test_delayed_zero_does_not_imply_pending_or_related() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(pending_orders=None, related_positions=None)
    )
    assert _status(verdict, "P5_DELAYED_TARGET_ZERO") == "PASS"
    assert _status(verdict, "P7_PENDING_EMPTY") == "NOT_PROVEN"
    assert _status(verdict, "P9_NO_UNEXPECTED_RELATED_NONZERO") == "NOT_PROVEN"
    assert verdict.live_flatten_provability_proven is False


def test_malformed_numeric_delayed_position_fails() -> None:
    verdict = evaluate_delayed_g12_conjunction_v1(
        _complete(
            delayed_target_zero=_delayed(
                payload=_envelope({"instId": TARGET, "pos": "not-a-number", "posId": POS_ID})
            )
        )
    )
    assert _status(verdict, "P5_DELAYED_TARGET_ZERO") == "FAIL"
    assert verdict.delayed_explicit_target_zero is False
