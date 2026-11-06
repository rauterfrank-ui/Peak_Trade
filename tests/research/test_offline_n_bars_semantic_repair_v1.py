"""Counterexamples for the isolated source/time repair candidate."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import build_decision_event_v0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_evidence_record_v1 import (
    build_learning_evidence_record_v1,
)
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_v1 import (
    build_outcome_evidence_provenance_v1,
)
from src.learning.deterministic_decision_outcome_v0.optimization_provenance_eligibility_v1 import (
    assert_optimization_pool_compatible_v1,
)
from src.research.offline_n_bars_semantic_repair_v1 import (
    OBSERVED_USE,
    RECORDED,
    SYNTHETIC,
    SYNTHETIC_USE,
    canonical,
    digest_bytes,
    inspect_source,
    require_consumer_origin,
    run_candidate,
)
from tests.learning.test_ddo_o4_n_bars_productive_chain_v1 import _decision, _snapshot


@pytest.fixture
def case(tmp_path):
    snapshot = _snapshot()
    instrument = snapshot["o4_bars"][0]["canonical_instrument_id"]
    decision = dict(
        build_decision_event_v0(
            _decision(
                selected_instrument_ref=instrument,
                cycle_id="offline-clock-cycle-1",
                authority_owner="NONE_OFFLINE_TEST_FIXTURE",
            )
        )
    )
    source = {
        "source_kind": SYNTHETIC,
        "clock_domain": "SIMULATED_UTC",
        "source_epoch": "fixture-epoch-1",
        "canonical_instrument_id": instrument,
        "venue_instrument_id": "ETH-USD-SWAP",
        "venue": "okx_eea",
        "price_unit": "USD per ETH (constructed test values)",
        "price_basis": "EXPLICIT_BAR_CLOSE",
        "bar_receipts": [
            {"source_kind": SYNTHETIC, "available_at_utc": close, "bar": bar}
            for close, bar in zip(
                ("2026-09-01T13:00:00Z", "2026-09-01T14:00:00Z"), snapshot["o4_bars"]
            )
        ],
    }
    request = {
        "decision": decision,
        "requested_use": SYNTHETIC_USE,
        "horizon_start_time_utc": snapshot["horizon_start_time_utc"],
        "n_bars": 2,
        "interval": "PT1H",
    }
    original = tmp_path / "input"
    original.mkdir()
    path = original / "declared-source.json"
    path.write_bytes(canonical(source))
    return request, source, path


def _run(case, output, as_of="2026-09-01T14:00:00Z"):
    request, _, path = case
    return run_candidate(
        request,
        source_path=path,
        source_sha256=digest_bytes(path.read_bytes()),
        as_of_utc=as_of,
        output=output,
    )


@pytest.mark.parametrize(
    "as_of,count",
    [("2026-09-01T12:00:00Z", 0), ("2026-09-01T13:00:00Z", 1), ("2026-09-01T13:59:59Z", 1)],
)
def test_no_outcome_or_state_before_horizon_is_available(case, tmp_path, as_of, count):
    output = tmp_path / "result"
    report = _run(case, output, as_of)
    assert report["status"] == "WAITING_FOR_COMPLETE_AVAILABLE_HORIZON"
    assert report["bars_available"] == count
    assert report["measurement_created"] is False
    assert not output.exists()


def test_generated_prices_keep_synthetic_origin_through_actual_consumer(case, tmp_path):
    request, source, path = case
    before = path.read_bytes()
    output = tmp_path / "result"
    report = _run(case, output)
    assert report["intake_status"] == "ACCEPTED_OFFLINE_RESEARCH_INPUT"
    assert report["market_observation_source"] == SYNTHETIC
    assert report["outcome_semantic_class"] == "INTERNAL_SIMULATED_OUTCOME"
    assert report["productive_truth_claim"] is False
    assert report["provenance_preserved"] is True
    assert report["bar_times_preserved"] is True
    assert report["economic_score_label"] == "UNKNOWN"
    measurement = json.loads((output / "measurement.json").read_text())
    assert measurement["start_price"] == 100
    assert measurement["end_price"] == 110
    require_consumer_origin(
        json.loads((output / "learning_evidence.json").read_text()),
        source=source,
        lineage=report["source_lineage_digest"],
        requested_use=request["requested_use"],
        expected_measurement=measurement,
    )
    assert path.read_bytes() == before


def test_generated_source_cannot_be_requested_as_observed_research(case, tmp_path):
    case[0]["requested_use"] = OBSERVED_USE
    with pytest.raises(ValueError, match="SOURCE_KIND_USE_MISMATCH"):
        _run(case, tmp_path / "result")
    assert not (tmp_path / "result").exists()


@pytest.mark.parametrize(
    "change,reason",
    [
        ("early_receipt", "BAR_AVAILABLE_BEFORE_OBSERVATION_OR_CLOSE"),
        ("changed_instrument", "BAR_IDENTITY_MISMATCH"),
        ("changed_observation_instrument", "BAR_IDENTITY_MISMATCH"),
        ("wrong_interval", "ORIGINAL_BAR_INTERVAL_MISMATCH"),
        ("duplicate", "DUPLICATE_OR_CONFLICTING_BAR"),
        ("mixed_origin", "MIXED_SOURCE_ORIGIN"),
        ("seed_marker", "KNOWN_RETIMED_SEED_NOT_ORIGINAL_BAR_EVIDENCE"),
        ("not_final", "FINALIZED_COMPLETE_BAR_REQUIRED"),
    ],
)
def test_corrupt_source_contracts_do_not_mint_evidence(case, tmp_path, change, reason):
    request, source, path = case
    first = source["bar_receipts"][0]
    if change == "early_receipt":
        first["available_at_utc"] = "2026-09-01T12:00:00Z"
    elif change == "changed_instrument":
        first["bar"]["canonical_instrument_id"] = "FOREIGN"
    elif change == "changed_observation_instrument":
        first["bar"]["last_observation_identity"]["venue_instrument_id"] = "FOREIGN"
    elif change == "wrong_interval":
        first["bar"]["interval"] = "PT1M"
    elif change == "duplicate":
        source["bar_receipts"].append(copy.deepcopy(first))
    elif change == "mixed_origin":
        first["source_kind"] = RECORDED
    elif change == "seed_marker":
        first["bar"]["config_digest"] = "ddo-handoff-o4-seed-v1"
    elif change == "not_final":
        first["bar"]["finalization_state"] = "IN_PROGRESS_BAR"
    path.write_bytes(canonical(source))
    with pytest.raises(ValueError, match=reason):
        _run(case, tmp_path / "result")
    assert not (tmp_path / "result").exists()


def test_missing_bar_and_delayed_receipt_remain_pending(case, tmp_path):
    request, source, path = case
    source["bar_receipts"][1]["available_at_utc"] = "2026-09-01T14:01:00Z"
    path.write_bytes(canonical(source))
    assert _run(case, tmp_path / "pending")["status"] == "WAITING_FOR_COMPLETE_AVAILABLE_HORIZON"
    assert (
        _run(case, tmp_path / "done", "2026-09-01T14:01:00Z")["status"]
        == "COMPLETED_OFFLINE_CANDIDATE"
    )
    source["bar_receipts"].pop()
    assert (
        inspect_source(request, source, as_of_utc="2026-09-02T00:00:00Z")["status"]
        == "WAITING_FOR_COMPLETE_AVAILABLE_HORIZON"
    )


def test_consumer_refuses_relabelled_or_rerouted_synthetic_evidence(case, tmp_path):
    _, source, _ = case
    output = tmp_path / "result"
    report = _run(case, output)
    evidence = json.loads((output / "learning_evidence.json").read_text())
    measurement = json.loads((output / "measurement.json").read_text())
    with pytest.raises(ValueError, match="SYNTHETIC_EVIDENCE_NOT_OBSERVED_RESEARCH"):
        require_consumer_origin(
            evidence,
            source=source,
            lineage=report["source_lineage_digest"],
            requested_use=OBSERVED_USE,
            expected_measurement=measurement,
        )
    evidence["outcome_evidence_provenance"]["market_observation_source"] = "PUBLIC_MD"
    with pytest.raises(ValueError, match="CONSUMER_ORIGIN_CHANGED"):
        require_consumer_origin(
            evidence,
            source=source,
            lineage=report["source_lineage_digest"],
            requested_use=SYNTHETIC_USE,
            expected_measurement=measurement,
        )


@pytest.mark.parametrize(
    "field,reason",
    [
        ("lineage", "CONSUMER_SOURCE_LINEAGE_CHANGED"),
        ("measurement", "CONSUMER_MEASUREMENT_REF_CHANGED"),
        ("instrument", "CONSUMER_INSTRUMENT_CHANGED"),
        ("time", "CONSUMER_EVALUATION_TIME_CHANGED"),
        ("class", "CONSUMER_SEMANTIC_CLASS_CHANGED"),
        ("pool", "CONSUMER_POOL_CHANGED"),
    ],
)
def test_consumer_checks_source_bindings_beyond_synthetic_label(case, tmp_path, field, reason):
    _, source, _ = case
    output = tmp_path / "result"
    report = _run(case, output)
    evidence = json.loads((output / "learning_evidence.json").read_text())
    measurement = json.loads((output / "measurement.json").read_text())
    if field == "lineage":
        evidence["outcome_evidence_provenance"]["lineage_digest"] = "0" * 64
    elif field == "measurement":
        evidence["actual_outcome_ref"] = "ddo.outcome.measure.foreign"
    elif field == "instrument":
        evidence["outcome_evidence_provenance"]["instrument_id"] = "FOREIGN"
    elif field == "time":
        evidence["outcome_evidence_provenance"]["evaluation_timestamp_utc"] = "2026-09-01T15:00:00Z"
    elif field == "class":
        evidence["outcome_semantic_class"] = "OBSERVED_PRODUCTIVE_PRE_EXTERNAL"
    elif field == "pool":
        evidence["evidence_pool_class"] = "OBSERVED_PRODUCTIVE_PRE_EXTERNAL"
    with pytest.raises(ValueError, match=reason):
        require_consumer_origin(
            evidence,
            source=source,
            lineage=report["source_lineage_digest"],
            requested_use=SYNTHETIC_USE,
            expected_measurement=measurement,
        )


def test_recorded_replay_stays_nonproductive_and_separate_from_synthetic(case, tmp_path):
    _, source, path = case
    synthetic_dir = tmp_path / "synthetic"
    _run(case, synthetic_dir)
    source["source_kind"], source["clock_domain"] = RECORDED, "CAPTURE_UTC"
    for receipt in source["bar_receipts"]:
        receipt["source_kind"] = RECORDED
    path.write_bytes(canonical(source))
    case[0]["requested_use"] = OBSERVED_USE
    replay_dir = tmp_path / "replay"
    report = _run(case, replay_dir)
    assert report["outcome_semantic_class"] == "REPLAY_HISTORICAL"
    # This is a constructed receipt fixture exercising the recorded-input branch.
    assert report["real_market_origin_independently_proven"] is False
    with pytest.raises(DdoValidationError, match="INCOMPATIBLE_EVIDENCE_CLASSES"):
        assert_optimization_pool_compatible_v1(
            json.loads((synthetic_dir / "learning_evidence.json").read_text()),
            json.loads((replay_dir / "learning_evidence.json").read_text()),
        )


def test_rehashed_wrong_origin_passes_old_intake_but_fails_source_bound_consumer(case, tmp_path):
    _, source, _ = case
    output = tmp_path / "result"
    report = _run(case, output)
    evidence = json.loads((output / "learning_evidence.json").read_text())
    evidence.pop("content_hash")
    prov = evidence["outcome_evidence_provenance"]
    prov.pop("provenance_digest")
    prov["market_observation_source"] = "PUBLIC_MD"
    prov = dict(build_outcome_evidence_provenance_v1(prov))
    evidence["outcome_evidence_provenance"] = prov
    evidence["outcome_evidence_provenance_digest"] = prov["provenance_digest"]
    rehashed = dict(build_learning_evidence_record_v1(evidence))
    ack = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=rehashed)
    )
    assert ack["status"] == "ACCEPTED_OFFLINE_RESEARCH_INPUT"
    with pytest.raises(ValueError, match="CONSUMER_ORIGIN_CHANGED"):
        require_consumer_origin(
            rehashed,
            source=source,
            lineage=report["source_lineage_digest"],
            requested_use=SYNTHETIC_USE,
            expected_measurement=json.loads((output / "measurement.json").read_text()),
        )


def test_input_hash_and_output_exclusivity(case, tmp_path):
    request, _, path = case
    with pytest.raises(ValueError, match="SOURCE_SHA256_MISMATCH"):
        run_candidate(
            request,
            source_path=path,
            source_sha256="0" * 64,
            as_of_utc="2026-09-01T14:00:00Z",
            output=tmp_path / "invalid",
        )
    assert not (tmp_path / "invalid").exists()
    output = tmp_path / "result"
    _run(case, output)
    before = (output / "candidate_ledger.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        _run(case, output)
    assert (output / "candidate_ledger.jsonl").read_bytes() == before
