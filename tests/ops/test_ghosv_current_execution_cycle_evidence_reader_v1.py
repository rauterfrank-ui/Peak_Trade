"""Offline tests: governed-cycle ledger/transitions + optional G004 → GHOSV."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    LEDGER_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persisted_reconciliation_disposition_v1 import (
    CONTRACT_ID as G004_CONTRACT_ID,
    DISPOSITION_FILENAME,
    attempt_digest_v1,
)
from src.ops.ghosv_bounded_context_v1.current_execution_cycle_evidence_reader_v1 import (
    GOVERNED_CYCLE_POST_WITNESS_CONTRACT,
    GovernedCycleEvidenceOptionsV1,
    load_g004_disposition_evidence_v1,
    load_governed_cycle_evidence_dir_v1,
    load_governed_cycle_transitions_evidence_v1,
    parse_post_count_field_v1,
)
from src.ops.ghosv_bounded_context_v1.current_execution_evidence_reader_v1 import (
    CurrentExecutionEvidenceSourcesV1,
    read_current_execution_evidence_v1,
)
from src.ops.ghosv_bounded_context_v1.s01_evidence_ingest_v1 import GhosvEvidenceIngestError
from src.ops.ghosv_bounded_context_v1.types_v1 import GhosvCompleteness, GhosvEvidenceKind

REPO = Path(__file__).resolve().parents[2]
RUNTIME_CYCLE_FIXTURE = (
    REPO
    / "runtime/current_productive/natural_evidence_accumulation_v1/runs/20261012T111235Z/cycles/6866554fd9b7708ba5c049f302f3fa4a8d11237453992759bbb4a5273929cf6f/s5"
)


def _write_cycle_dir(
    tmp_path: Path,
    *,
    ledger: dict,
    transitions: list[dict] | None = None,
    malformed_tail: str | None = None,
) -> Path:
    root = tmp_path / "cycle"
    root.mkdir(parents=True)
    (root / LEDGER_FILENAME).write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    if transitions is not None or malformed_tail is not None:
        lines: list[str] = []
        if transitions:
            lines.extend(json.dumps(row, sort_keys=True) for row in transitions)
        if malformed_tail is not None:
            lines.append(malformed_tail)
        (root / "transitions.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


def _base_ledger(**extra: object) -> dict:
    payload = {
        "state": "COMPLETED",
        "binding_digest": "digest-a",
        "cycle_owner_go": "OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_V1",
        "native_id": "BTC-USDT-SWAP",
        "POST_COUNT": "0",
        "PERMIT_CREATED": "false",
    }
    payload.update(extra)
    return payload


def test_valid_ledger_and_transitions_fixture():
    if not RUNTIME_CYCLE_FIXTURE.is_dir():
        pytest.skip("runtime cycle fixture absent")
    records = load_governed_cycle_evidence_dir_v1(
        RUNTIME_CYCLE_FIXTURE,
        trade_id="runtime-cycle",
    )
    kinds = {r.kind for r in records}
    assert GhosvEvidenceKind.RUNTIME_OBSERVATION.value in kinds
    assert GhosvEvidenceKind.EXECUTION_ATTEMPT.value in kinds
    post_witness = [r for r in records if r.source_contract == GOVERNED_CYCLE_POST_WITNESS_CONTRACT]
    assert post_witness
    assert post_witness[0].payload.get("pre_external_witness") is False
    assert post_witness[0].payload.get("post_submission_witness") is True


def test_explicit_post_count_zero(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(POST_COUNT="0"),
        transitions=[_base_ledger(state="IN_PROGRESS"), _base_ledger(state="COMPLETED")],
    )
    records = load_governed_cycle_evidence_dir_v1(root, trade_id="t0")
    witness = next(
        r
        for r in records
        if r.kind == GhosvEvidenceKind.EXECUTION_ATTEMPT.value
        and r.source_contract == GOVERNED_CYCLE_POST_WITNESS_CONTRACT
        and r.payload.get("transition_index") is None
    )
    assert witness.payload.get("post_count_known") is True
    assert witness.payload.get("post_occurred") is False
    assert witness.payload.get("post_count") == 0


def test_missing_post_count_unknown(tmp_path: Path):
    ledger = _base_ledger()
    del ledger["POST_COUNT"]
    root = _write_cycle_dir(tmp_path, ledger=ledger)
    records = load_governed_cycle_evidence_dir_v1(root, trade_id="t-missing")
    witness = next(
        r
        for r in records
        if r.kind == GhosvEvidenceKind.EXECUTION_ATTEMPT.value
        and r.source_contract == GOVERNED_CYCLE_POST_WITNESS_CONTRACT
    )
    assert witness.payload.get("post_count_known") is False
    assert witness.completeness == GhosvCompleteness.UNKNOWN.value


def test_malformed_post_count_unknown(tmp_path: Path):
    root = _write_cycle_dir(tmp_path, ledger=_base_ledger(POST_COUNT="not-int"))
    records = load_governed_cycle_evidence_dir_v1(root, trade_id="t-bad")
    witness = next(
        r
        for r in records
        if r.kind == GhosvEvidenceKind.EXECUTION_ATTEMPT.value
        and r.source_contract == GOVERNED_CYCLE_POST_WITNESS_CONTRACT
    )
    assert witness.payload.get("post_count_known") is False
    assert witness.completeness == GhosvCompleteness.UNKNOWN.value


def test_conflicting_post_count_unknown(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(POST_COUNT="0"),
        transitions=[
            _base_ledger(state="IN_PROGRESS", POST_COUNT="0"),
            _base_ledger(state="COMPLETED", POST_COUNT="1"),
        ],
    )
    records = load_governed_cycle_evidence_dir_v1(root, trade_id="t-conflict")
    assert any(r.payload.get("post_count_conflict") for r in records)
    witnesses = [
        r
        for r in records
        if r.kind == GhosvEvidenceKind.EXECUTION_ATTEMPT.value
        and r.source_contract == GOVERNED_CYCLE_POST_WITNESS_CONTRACT
    ]
    assert all(w.completeness == GhosvCompleteness.UNKNOWN.value for w in witnesses)


def test_local_cancelled_stop_not_venue_cancel(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(state="CANCELLED_STOP", reason_code="CANCELLED"),
    )
    records = load_governed_cycle_evidence_dir_v1(root, trade_id="t-cancel")
    obs = next(r for r in records if r.kind == GhosvEvidenceKind.RUNTIME_OBSERVATION.value)
    assert obs.payload.get("local_orchestrator_stop") is True
    assert obs.payload.get("venue_cancel_witness") is False


def test_truncated_jsonl_unknown(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(),
        transitions=[],
        malformed_tail='{"state": "IN_PROGRESS",',
    )
    records = load_governed_cycle_transitions_evidence_v1(
        root / "transitions.jsonl",
        trade_id="t-trunc",
        ledger_path=root / LEDGER_FILENAME,
    )
    assert any(r.payload.get("truncated_jsonl") for r in records)


def test_duplicate_transition_flagged(tmp_path: Path):
    row = _base_ledger(state="IN_PROGRESS")
    root = _write_cycle_dir(tmp_path, ledger=_base_ledger(), transitions=[row, dict(row)])
    records = load_governed_cycle_evidence_dir_v1(root, trade_id="t-dup")
    assert any(r.payload.get("duplicate_adjacent_transition") for r in records)


def test_out_of_order_transition_flagged(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(state="COMPLETED"),
        transitions=[
            _base_ledger(state="COMPLETED"),
            _base_ledger(state="IN_PROGRESS"),
        ],
    )
    records = load_governed_cycle_evidence_dir_v1(root, trade_id="t-order")
    assert any(r.payload.get("sequence_anomaly") for r in records)


def test_conflicting_run_cycle_native_id(tmp_path: Path):
    root = _write_cycle_dir(
        tmp_path,
        ledger=_base_ledger(native_id="BTC-USDT-SWAP"),
        transitions=[_base_ledger(state="IN_PROGRESS", native_id="ETH-USDT-SWAP")],
    )
    with pytest.raises(GhosvEvidenceIngestError, match="CROSS_CONTAMINATION"):
        load_governed_cycle_evidence_dir_v1(root, trade_id="t-xinst")


def test_valid_g004_disposition(tmp_path: Path):
    store = tmp_path / "post_store"
    store.mkdir()
    submit = "submit-a"
    digest = "env-digest-a"
    record = {
        "contract_id": G004_CONTRACT_ID,
        "submit_attempt_id": submit,
        "clordid": "cl-a",
        "envelope_digest": digest,
        "attempt_digest": attempt_digest_v1(submit_attempt_id=submit, envelope_digest=digest),
        "native_id": "BTC-USDT-SWAP",
        "reconciliation_outcome": "CONFIRMED_FILLED",
        "typed_post_submit_outcome": "ACKNOWLEDGED",
        "local_submit_outcome": "TRANSPORT_ACK",
        "ack_is_not_fill": True,
        "persisted_at_utc": "2026-01-01T00:00:00.000000Z",
        "venue_ord_id": "ord-1",
    }
    (store / DISPOSITION_FILENAME).write_text(json.dumps(record), encoding="utf-8")
    records = load_g004_disposition_evidence_v1(store, trade_id="g4")
    kinds = {r.kind for r in records}
    assert GhosvEvidenceKind.RECONCILIATION_GATE.value in kinds
    assert GhosvEvidenceKind.ORDER_STATUS.value in kinds
    assert GhosvEvidenceKind.ORDER_ACK.value in kinds
    assert GhosvEvidenceKind.FULL_FILL.value not in kinds
    assert GhosvEvidenceKind.PARTIAL_FILL.value not in kinds
    ack = next(r for r in records if r.kind == GhosvEvidenceKind.ORDER_ACK.value)
    assert ack.payload.get("treated_as_fill") is False


def test_missing_optional_g004_empty():
    records = load_g004_disposition_evidence_v1(
        Path("/nonexistent/path/should/not/exist"),
        trade_id="no-g4",
    )
    assert records == ()


def test_ambiguous_g004_attempt_digest(tmp_path: Path):
    store = tmp_path / "post_store"
    store.mkdir()
    record = {
        "contract_id": G004_CONTRACT_ID,
        "submit_attempt_id": "sa",
        "clordid": "cl",
        "envelope_digest": "ed",
        "attempt_digest": "wrong",
        "native_id": "BTC-USDT-SWAP",
        "reconciliation_outcome": "CONFIRMED_OPEN",
        "typed_post_submit_outcome": "ACKNOWLEDGED",
        "local_submit_outcome": "TRANSPORT_ACK",
        "ack_is_not_fill": True,
    }
    (store / DISPOSITION_FILENAME).write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(GhosvEvidenceIngestError, match="G004_ATTEMPT_DIGEST"):
        load_g004_disposition_evidence_v1(store, trade_id="bad-g4")


def test_g004_reconciliation_not_promoted_to_fill(tmp_path: Path):
    store = tmp_path / "post_store"
    store.mkdir()
    submit = "submit-fill"
    digest = "env-d"
    record = {
        "contract_id": G004_CONTRACT_ID,
        "submit_attempt_id": submit,
        "clordid": "cl-fill",
        "envelope_digest": digest,
        "attempt_digest": attempt_digest_v1(submit_attempt_id=submit, envelope_digest=digest),
        "native_id": "BTC-USDT-SWAP",
        "reconciliation_outcome": "CONFIRMED_FILLED",
        "typed_post_submit_outcome": "ACKNOWLEDGED",
        "local_submit_outcome": "TRANSPORT_ACK",
        "ack_is_not_fill": True,
    }
    (store / DISPOSITION_FILENAME).write_text(json.dumps(record), encoding="utf-8")
    records = load_g004_disposition_evidence_v1(store, trade_id="fill-witness")
    status = next(r for r in records if r.kind == GhosvEvidenceKind.ORDER_STATUS.value)
    assert status.payload.get("not_a_fill_event") is True


def test_cross_order_isolation_via_expected_clordid(tmp_path: Path):
    store = tmp_path / "post_store"
    store.mkdir()
    submit = "submit-x"
    digest = "env-x"
    record = {
        "contract_id": G004_CONTRACT_ID,
        "submit_attempt_id": submit,
        "clordid": "cl-actual",
        "envelope_digest": digest,
        "attempt_digest": attempt_digest_v1(submit_attempt_id=submit, envelope_digest=digest),
        "native_id": "BTC-USDT-SWAP",
        "reconciliation_outcome": "CONFIRMED_OPEN",
        "typed_post_submit_outcome": "ACKNOWLEDGED",
        "local_submit_outcome": "TRANSPORT_ACK",
        "ack_is_not_fill": True,
    }
    (store / DISPOSITION_FILENAME).write_text(json.dumps(record), encoding="utf-8")
    opts = GovernedCycleEvidenceOptionsV1(g004_expected_clordid="cl-other")
    with pytest.raises(GhosvEvidenceIngestError, match="G004_CLORDID_MISMATCH"):
        load_g004_disposition_evidence_v1(store, trade_id="xord", options=opts)


def test_restart_replay_consistent_post_count_parse():
    _, known = parse_post_count_field_v1({"POST_COUNT": "0"})
    assert known is True
    _, known2 = parse_post_count_field_v1({"POST_COUNT": 0})
    assert known2 is True


def test_integrated_reader_sources(tmp_path: Path):
    cycle = _write_cycle_dir(tmp_path, ledger=_base_ledger())
    store = tmp_path / "post_store"
    store.mkdir()
    submit = "submit-int"
    digest = "env-int"
    (store / DISPOSITION_FILENAME).write_text(
        json.dumps(
            {
                "contract_id": G004_CONTRACT_ID,
                "submit_attempt_id": submit,
                "clordid": "cl-int",
                "envelope_digest": digest,
                "attempt_digest": attempt_digest_v1(
                    submit_attempt_id=submit, envelope_digest=digest
                ),
                "native_id": "BTC-USDT-SWAP",
                "reconciliation_outcome": "CONFIRMED_OPEN",
                "typed_post_submit_outcome": "ACKNOWLEDGED",
                "local_submit_outcome": "TRANSPORT_ACK",
                "ack_is_not_fill": True,
            }
        ),
        encoding="utf-8",
    )
    records = read_current_execution_evidence_v1(
        CurrentExecutionEvidenceSourcesV1(
            trade_id="integrated",
            governed_cycle_evidence_dir=cycle,
            g004_post_attempt_store_root=store,
        )
    )
    assert len(records) >= 4
