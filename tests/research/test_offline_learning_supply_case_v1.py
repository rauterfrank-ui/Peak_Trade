"""Boundary tests for the isolated captured-learning supply experiment."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import build_decision_event_v0
from src.learning.deterministic_decision_outcome_v0.evaluation_engine_v0 import (
    evaluate_offline_bundle_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.n_bars_bar_evidence_supplier_v1 import (
    run_offline_n_bars_horizon_pipeline_v1,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_bindings_v1 import (
    ProvenanceBindingContextV1,
    ProvenanceProducerBindingV1,
)
from src.research.offline_learning_supply_case_v1 import run_case
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _identity, _snapshot


@pytest.fixture
def request_case(tmp_path: Path):
    source = tmp_path / "original" / "capture.jsonl"
    ledger = AppendOnlyDdoLedgerV0(source)
    decision = build_decision_event_v0(_decision())
    ledger.append(decision)
    horizon = run_offline_n_bars_horizon_pipeline_v1(
        decision, _snapshot(), outcome_scalar_kind="LOG_RETURN"
    )
    outcome_ids = []
    for index, hour in enumerate((14, 15)):
        bundle = evaluate_offline_bundle_v0(
            decision,
            horizon["evaluation_observation"],
            identity=_identity(
                outcome_record_id=f"out-case-{index}",
                attribution_record_id=f"attr-case-{index}",
                counterfactual_record_id=f"cf-case-{index}",
                event_time_utc=f"2026-09-01T{hour}:00:00Z",
            ),
            provenance_binding=ProvenanceProducerBindingV1.REPLAY_HISTORICAL,
            provenance_context=ProvenanceBindingContextV1(
                decision_event_ref=decision["record_id"],
                producer_id="offline-test-fixture",
                outcome_scalar_kind="LOG_RETURN",
                evaluation_horizon="N_BARS",
            ),
            ledger=ledger,
        )
        outcome_ids.append(bundle["outcome_record"]["record_id"])
    return {
        "case_id": "test-only",
        "source_kind": "TEST_FIXTURE",
        "source_ledger": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "outcome_ids": outcome_ids,
    }


def test_real_contract_composition_preserves_unknowns_and_replay_class(request_case, tmp_path):
    source = Path(request_case["source_ledger"])
    before = source.read_bytes()
    report = run_case(request_case, tmp_path / "result")
    assert source.read_bytes() == before
    assert report["suffix_status"] == "PASS"
    assert report["end_to_end_supply_status"] == "NOT_PROVEN"
    assert report["productive_authority"] == "NONE"
    assert [result["state_version"] for result in report["results"]] == [1, 2]
    for result in report["results"]:
        assert result["provenance"]["outcome_semantic_class"] == "REPLAY_HISTORICAL"
        assert result["economic_label_before"] == result["economic_label_after"] == "UNKNOWN"
        assert "instrument_id" in result["missing_provenance_fields"]
        assert result["idempotent_replay"] is False
        assert result["intake"]["external_effect_authorized"] is False
    copied = AppendOnlyDdoLedgerV0(tmp_path / "result" / "pilot_ledger.jsonl").read_all()
    assert len(copied) == report["source_record_count"] + 2


def test_source_hash_mismatch_creates_no_output(request_case, tmp_path):
    request_case["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SOURCE_SHA256_MISMATCH"):
        run_case(request_case, tmp_path / "result")
    assert not (tmp_path / "result").exists()


def test_existing_output_is_preserved(request_case, tmp_path):
    output = tmp_path / "result"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("existing evidence")
    with pytest.raises(FileExistsError):
        run_case(request_case, output)
    assert list(output.iterdir()) == [sentinel]
    assert sentinel.read_text() == "existing evidence"


def test_source_directory_cannot_be_used_for_output(request_case):
    output = Path(request_case["source_ledger"]).parent / "nested"
    with pytest.raises(ValueError, match="OUTPUT_MUST_BE_OUTSIDE_SOURCE_DIRECTORY"):
        run_case(request_case, output)
    assert not output.exists()


@pytest.mark.parametrize("selection", ["reversed", "duplicate", "missing"])
def test_selection_failures_never_append_to_source(request_case, tmp_path, selection):
    source = Path(request_case["source_ledger"])
    before = source.read_bytes()
    if selection == "reversed":
        request_case["outcome_ids"].reverse()
    elif selection == "duplicate":
        request_case["outcome_ids"] *= 2
    else:
        request_case["outcome_ids"] = ["missing"]
    with pytest.raises((ValueError, KeyError)):
        run_case(request_case, tmp_path / "result")
    assert source.read_bytes() == before
    assert not (tmp_path / "result" / "pilot_ledger.jsonl").exists()


def test_hash_pinning_does_not_replace_ledger_integrity_validation(request_case, tmp_path):
    source = Path(request_case["source_ledger"])
    corrupted = source.read_bytes().replace(b'"sequence":1', b'"sequence":9', 1)
    assert corrupted != source.read_bytes()
    source.write_bytes(corrupted)
    request_case["source_sha256"] = hashlib.sha256(corrupted).hexdigest()
    with pytest.raises(Exception, match="SEQUENCE"):
        run_case(request_case, tmp_path / "result")
    assert source.read_bytes() == corrupted
    assert not (tmp_path / "result" / "report.json").exists()
