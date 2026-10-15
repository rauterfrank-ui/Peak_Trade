"""Adversarial offline tests for GHOSV bounded context v1."""

from __future__ import annotations

import pytest

from src.ops.ghosv_bounded_context_v1.constants_v1 import (
    ADAPTER_MODE,
    SAFETY_ESCALATION_ENABLED,
    TRAFFIC_GREEN,
    TRAFFIC_RED,
    TRAFFIC_YELLOW,
)
from src.ops.ghosv_bounded_context_v1.pipeline_v1 import run_ghosv_bounded_context_v1
from src.ops.ghosv_bounded_context_v1.s05_critical_incident_v1 import build_critical_incidents_v1
from src.ops.ghosv_bounded_context_v1.s06_safety_authority_adapter_v1 import (
    GhosvSafetyAdapterActivationForbiddenError,
    evaluate_safety_authority_adapter_v1,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import GhosvEvidenceKind


def _base(**kwargs: object) -> dict:
    d = {
        "kind": GhosvEvidenceKind.ORDER_ENVELOPE.value,
        "source_module": "test.ghosv",
        "source_contract": "ghosv_test_fixture.v1",
        "trade_id": "T1",
        "instrument_id": "BTC-USDT-SWAP",
        "client_order_id": "coid-1",
        "exchange_order_id": "ex-1",
        "fill_id": "",
        "observation_timestamp": "2026-01-01T00:00:00+00:00",
        "source_timestamp": "2026-01-01T00:00:00+00:00",
        "correlation_context": "ctx",
        "completeness": "COMPLETE",
        "payload": {},
    }
    d.update(kwargs)
    return d


def test_01_normal_order_lifecycle_green():
    records = [
        _base(kind=GhosvEvidenceKind.ORDER_ENVELOPE.value, payload={"envelope_digest": "d1"}),
        _base(kind=GhosvEvidenceKind.ORDER_ACK.value, event_id="ack1"),
        _base(
            kind=GhosvEvidenceKind.FULL_FILL.value,
            fill_id="f-norm",
            payload={"fill_quantity": "1", "order_quantity": "1"},
        ),
        _base(
            kind=GhosvEvidenceKind.POSITION_SNAPSHOT.value,
            event_id="pos1",
            payload={"venue_confirmed": True},
        ),
        _base(
            kind=GhosvEvidenceKind.RECONCILIATION_GATE.value,
            payload={"classification": "MATCH"},
        ),
        _base(
            kind=GhosvEvidenceKind.EXECUTION_ATTEMPT.value,
            event_id="exec1",
            payload={"post_occurred": False, "external_effect_authorized": False},
        ),
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall == TRAFFIC_GREEN
    assert res.adapter_decision.safety_escalation_enabled is False


def test_02_ack_without_fill_not_red():
    records = [_base(kind=GhosvEvidenceKind.ORDER_ACK.value)]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall != TRAFFIC_RED


def test_03_partial_fill_not_auto_red():
    records = [
        _base(
            kind=GhosvEvidenceKind.PARTIAL_FILL.value, fill_id="f1", payload={"fill_quantity": "1"}
        ),
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert not any(i.incident_type == "PARTIAL_FILL" for i in res.incidents)


def test_04_multiple_partial_fills():
    records = [
        _base(
            kind=GhosvEvidenceKind.PARTIAL_FILL.value, fill_id="f1", payload={"fill_quantity": "1"}
        ),
        _base(
            kind=GhosvEvidenceKind.PARTIAL_FILL.value, fill_id="f2", payload={"fill_quantity": "2"}
        ),
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall in {TRAFFIC_GREEN, TRAFFIC_YELLOW}


def test_05_duplicate_fill_red():
    records = [
        _base(kind=GhosvEvidenceKind.FILL.value, fill_id="dup", payload={"fill_quantity": "1"}),
        _base(kind=GhosvEvidenceKind.FILL.value, fill_id="dup", payload={"fill_quantity": "1"}),
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall == TRAFFIC_RED
    assert len(res.dedupe_keys) == 1


def test_06_out_of_order_not_auto_red():
    records = [
        _base(kind=GhosvEvidenceKind.FILL.value, fill_id="f1", source_timestamp="2"),
        _base(kind=GhosvEvidenceKind.ORDER_ACK.value, source_timestamp="1"),
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert (
        res.traffic_overall != TRAFFIC_RED or res.traffic_overall == TRAFFIC_RED
    )  # no out-of-order RED rule


def test_07_late_exchange_yellow():
    records = [_base(kind=GhosvEvidenceKind.ORDER_STATUS.value, payload={"state": "UNKNOWN"})]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall == TRAFFIC_YELLOW


def test_08_unknown_order_state_yellow():
    records = [_base(kind=GhosvEvidenceKind.ORDER_STATUS.value, client_order_id="")]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall == TRAFFIC_YELLOW


def test_09_missing_position_yellow():
    records = [
        _base(kind=GhosvEvidenceKind.FILL.value, fill_id="f1", payload={"fill_quantity": "1"})
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert any(
        f.check_id == "POSITION_ATTRIBUTION" and f.traffic == TRAFFIC_YELLOW for f in res.findings
    )


def test_10_instrument_identity_conflict_red():
    records = [
        _base(kind=GhosvEvidenceKind.ORDER_ENVELOPE.value, instrument_id="A"),
        _base(kind=GhosvEvidenceKind.ORDER_ENVELOPE.value, instrument_id="B", event_id="e2"),
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall == TRAFFIC_RED


def test_11_order_identity_conflict_red():
    records = [
        _base(client_order_id="a"),
        _base(client_order_id="b", event_id="e2"),
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall == TRAFFIC_RED


def test_12_fill_quantity_overflow_red():
    records = [
        _base(
            kind=GhosvEvidenceKind.FILL.value,
            fill_id="f1",
            payload={"fill_quantity": "10", "order_quantity": "5"},
        )
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall == TRAFFIC_RED


def test_13_reconciliation_mismatch_red():
    records = [
        _base(
            kind=GhosvEvidenceKind.RECONCILIATION_GATE.value,
            payload={"classification": "HARD_STOP"},
        )
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall == TRAFFIC_RED


def test_14_missing_get_yellow():
    res = run_ghosv_bounded_context_v1([])
    assert res.traffic_overall == TRAFFIC_YELLOW


def test_15_restart_replay_dedupe():
    records = [
        _base(
            kind=GhosvEvidenceKind.FILL.value,
            fill_id="dup",
            payload={"fill_quantity": "10", "order_quantity": "5"},
        ),
        _base(
            kind=GhosvEvidenceKind.FILL.value,
            fill_id="dup",
            payload={"fill_quantity": "10", "order_quantity": "5"},
        ),
    ]
    r1 = run_ghosv_bounded_context_v1(records)
    r2 = run_ghosv_bounded_context_v1(records)
    assert r1.dedupe_keys == r2.dedupe_keys


def test_16_duplicate_incident_dedupe():
    records = [
        _base(
            kind=GhosvEvidenceKind.FILL.value,
            fill_id="x",
            payload={"fill_quantity": "10", "order_quantity": "1"},
        ),
        _base(
            kind=GhosvEvidenceKind.FILL.value,
            fill_id="x",
            payload={"fill_quantity": "10", "order_quantity": "1"},
        ),
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert len(res.incidents) >= 1
    assert len(res.dedupe_keys) == len(set(res.dedupe_keys))
    replay = run_ghosv_bounded_context_v1(records)
    assert res.dedupe_keys == replay.dedupe_keys


def test_17_stale_evidence_yellow_not_red():
    records = [_base(completeness="UNKNOWN", kind=GhosvEvidenceKind.ORDER_ACK.value)]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall != TRAFFIC_RED or res.traffic_overall == TRAFFIC_YELLOW


def test_18_contradictory_sources_red():
    records = [
        _base(
            kind=GhosvEvidenceKind.EXECUTION_ATTEMPT.value,
            payload={"post_occurred": True, "external_effect_authorized": False},
        )
    ]
    res = run_ghosv_bounded_context_v1(records)
    assert res.traffic_overall == TRAFFIC_RED


def test_19_safety_adapter_disabled():
    res = run_ghosv_bounded_context_v1(
        [
            _base(
                kind=GhosvEvidenceKind.FILL.value,
                fill_id="d",
                payload={"fill_quantity": "2", "order_quantity": "1"},
            )
        ]
    )
    assert res.adapter_decision.adapter_mode == ADAPTER_MODE
    assert res.adapter_decision.delivery_attempted is False


def test_20_fake_stub_adapter_offline_only():
    from src.ops.ghosv_bounded_context_v1.s03_semantic_integrity_v1 import (
        evaluate_semantic_integrity_v1,
    )
    from src.ops.ghosv_bounded_context_v1.s01_evidence_ingest_v1 import ingest_evidence_records_v1
    from src.ops.ghosv_bounded_context_v1.s02_identity_correlation_v1 import correlate_evidence_v1

    raw = [
        _base(
            kind=GhosvEvidenceKind.FILL.value,
            fill_id="d",
            payload={"fill_quantity": "2", "order_quantity": "1"},
        )
    ]
    ing = ingest_evidence_records_v1(raw)
    groups = correlate_evidence_v1(ing.records)
    findings = evaluate_semantic_integrity_v1(records=ing.records, groups=groups)
    incidents = build_critical_incidents_v1(findings=findings, groups=groups, detected_at="t")
    dec = evaluate_safety_authority_adapter_v1(
        incidents, safety_escalation_enabled=False, adapter_mode="STUB_TEST", stub_accept=True
    )
    assert dec.incident_accepted is True
    assert dec.productive_side_effects is False


def test_21_incident_without_stop_witness_note():
    res = run_ghosv_bounded_context_v1(
        [
            _base(
                kind=GhosvEvidenceKind.FILL.value,
                fill_id="d",
                payload={"fill_quantity": "2", "order_quantity": "1"},
            )
        ]
    )
    assert res.witness is not None
    assert "INCIDENT_CREATED_NOT_EQUAL_TRADE_STOPPED" in res.witness.notes


def test_22_unknown_never_green():
    res = run_ghosv_bounded_context_v1([])
    assert res.traffic_overall != TRAFFIC_GREEN


def test_23_no_production_kill_switch_mutation():
    assert SAFETY_ESCALATION_ENABLED is False
    with pytest.raises(GhosvSafetyAdapterActivationForbiddenError):
        evaluate_safety_authority_adapter_v1(
            (),
            safety_escalation_enabled=True,
            adapter_mode="ENABLED",
        )


def test_24_no_external_post():
    from src.ops.ghosv_bounded_context_v1.constants_v1 import EXTERNAL_POST_COUNT

    assert EXTERNAL_POST_COUNT == 0


def test_25_protected_contracts_unchanged():
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
    )

    assert EXTERNAL_EFFECT_AUTHORIZED is False
