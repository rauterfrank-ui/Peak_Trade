"""Exercise the composed learning-to-native-research path with actual engine runs."""

from dataclasses import asdict
import json
import math

import pytest

from src.experiments.canonical_experiment_identity_v1 import CanonicalCodeProvenanceV1
from src.experiments.canonical_native_research_measurements_v1 import (
    native_research_input_hashes_v1,
)
from src.experiments.canonical_research_prepared_execution_v1 import read_v1
from src.experiments.offline_ddo_research_cycle_v1 import (
    OfflineDdoResearchRequestV1,
    ResearchIdentitySourcesV1,
    run_offline_ddo_research_cycle_v1,
)
from src.learning.deterministic_decision_outcome_v0 import (
    offline_learning_follow_up_v1 as follow_up,
)
from tests.backtest.test_parameter_sensitivity_split_observation_v1 import _inputs
from tests.evaluation.golden_vectors.runner_fixtures_v1 import protected_digests
from tests.experiments.test_canonical_advanced_search_v1 import _identity_request
from tests.learning.test_offline_ddo_learning_follow_up_v1 import (
    SCOPE,
    _capture,
    _hold_input,
    _request,
    _source,
    _time,
)
from tests.trading.master_v2 import test_double_play_entry_exit_policy_v0 as policy_inputs


def test_ddo_evidence_drives_archived_native_continuation_and_gvef(tmp_path, monkeypatch):
    instrument = "okx_eea:linear_perpetual:ETH:USDT:USDT:eth-usdt-swap"
    monkeypatch.setitem(SCOPE, "instrument_id", instrument)
    monkeypatch.setattr(policy_inputs, "_INSTRUMENT", instrument)
    root = tmp_path.resolve()
    ledger = follow_up.offline_learning_ledger_path_v1(root, SCOPE["account_scope"])
    initial_ref = _capture(ledger, _hold_input(), event_time=_time(12))
    plan = follow_up.prepare_offline_learning_follow_up_v1(
        root, "first", _request(initial_ref, at=_time(12, 5))
    )
    plan_digest = plan["plan_digest"]
    completion = follow_up.complete_offline_learning_follow_up_v1(
        root, "first", plan_digest=plan_digest, source=_source(initial_ref, 13, 100, 110)
    )
    learning = follow_up.export_completed_offline_learning_evidence_v1(
        root, "first", plan_digest=plan_digest
    )
    bars, cfg = _inputs()
    prices = [
        105 + 4.1 * math.sin(i / 13 + 0.23) + 0.013 * i + 0.15 * math.sin(i / 3)
        for i in range(len(bars))
    ]
    for name, shift in {
        "open": 0,
        "close": 0,
        "mark_price": 0,
        "index_price": 0,
        "high": 0.5,
        "low": -0.5,
        "best_bid": -0.05,
        "best_ask": 0.05,
    }.items():
        bars[name] = [price + shift for price in prices]
    raw = {
        "schema_version": "offline_ddo_research_request.v1",
        "learning_evidence_digest": learning["content_hash"],
        "instrument_id": SCOPE["instrument_id"],
        "strategy_id": "ma_crossover",
        "strategy_version": "v1",
        **native_research_input_hashes_v1(bars, cfg),
        "bars_known_at": "2026-07-03T00:01:00Z",
        "evidence_source_class": "TEST_ONLY_SYNTHETIC",
        "identity_sources": {
            key: value
            for key, value in asdict(_identity_request()).items()
            if key in ResearchIdentitySourcesV1.model_fields
        },
        "search_space_id": "ddo-native-offline",
        "parent_hypothesis_id": "hyp.ma-crossover.v1",
        "hypothesis_kind": "trend_following",
        "regime": "high_vol",
        "seed": 55,
        "first_axes": {"fast_window": [10], "slow_window": [100]},
        "next_axes": {"fast_window": [10], "slow_window": [75, 100, 125]},
        "search_space_cardinality_limit": 8,
        "market_universe": ["TEST_ONLY_SYNTHETIC"],
        "gap_dimensions": [
            {"name": "fee", "expected": 0.01, "observed": 0.01, "threshold": 0.005, "unit": "ratio"}
        ],
        "observed_surface": "SHADOW",
        "threshold_policy_digest": "a" * 64,
        "protected_digest_baseline": protected_digests(),
        "times": {
            "baseline_search": _time(16),
            "baseline_measurement": _time(16, 1),
            "first_search": _time(16, 2),
            "first_measurement": _time(16, 3),
            "meta": _time(16, 4),
            "next_search": _time(16, 5),
            "next_measurement": _time(16, 6),
            "evaluation": _time(16, 7),
        },
    }
    request = OfflineDdoResearchRequestV1.model_validate(raw)

    def run(value=request, *, source_bars=bars):
        return run_offline_ddo_research_cycle_v1(
            root,
            "first",
            plan_digest=plan_digest,
            request=value,
            bars=source_bars,
            cfg=cfg,
            code=CanonicalCodeProvenanceV1("b" * 40, "CLEAN"),
        )

    with pytest.raises(ValueError, match="LEARNING_BINDING_MISMATCH"):
        run(request.model_copy(update={"learning_evidence_digest": "0" * 64}))
    with pytest.raises(ValueError, match="INPUT_DIGEST_MISMATCH"):
        run(source_bars=bars.iloc[:-1])
    with pytest.raises(ValueError, match="DATASET_TIME_MISMATCH"):
        run(request.model_copy(update={"bars_known_at": "2026-07-02T23:30:00Z"}))
    directory = root / "offline-ddo-research" / "first"
    assert not directory.exists()

    before = ledger.read_bytes()
    result = run()
    assert result["status"] == "MECHANISM_PASS", result["evaluation"]
    assert result["evaluation"]["economic_status"] == "BLOCKED"
    assert result["authority"] == "NONE"
    binding = read_v1(directory / "request.json")
    assert (
        binding["optimization_admission"]["source_learning_state_record_ref"]
        == completion["learning_state_record_ref"]
    )
    first, next_id = result["first_artifact_id"], result["next_artifact_id"]
    assert first != next_id
    next_search = result["next_search"]
    assert set(next_search["input_lineage"]["archived_experiment_artifacts"].values()) == {first}
    already_measured = next(
        row for row in next_search["candidates"] if row["status"] == "ALREADY_MEASURED"
    )
    assert already_measured["parameter_region"]["slow_window"] == 100
    proposed = next(row for row in next_search["candidates"] if row["status"] == "PROPOSED")
    assert proposed["parameter_region"]["slow_window"] in (75, 125)
    meta = result["meta_feedback"]["meta_input_binding"]["meta_learning_record"]
    assert meta["research_proposals"] == []
    for artifact_id in (first, next_id):
        packet = json.loads((directory / "native-archive" / f"{artifact_id}.json").read_bytes())
        assert (
            packet["measurement_receipt"]["source_hashes"]["dataset_sha256"]
            == request.dataset_sha256
        )
        assert packet["measurement_receipt"]["engine_invocations"] == 4

    def unexpected_measurement(*args, **kwargs):
        pytest.fail("reopening the cycle must not remeasure")

    monkeypatch.setattr(
        "src.experiments.offline_ddo_research_cycle_v1.measure_native_research_champion_v1",
        unexpected_measurement,
    )
    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.measure_native_research_candidate_v1",
        unexpected_measurement,
    )
    assert run() == result
    assert ledger.read_bytes() == before
    with pytest.raises(ValueError, match="IMMUTABLE_CONFLICT"):
        run(request.model_copy(update={"seed": 56}))
