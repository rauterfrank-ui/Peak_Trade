"""The hourly MA input and the I17 decision epoch have separate clocks."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from dataclasses import replace
from math import ceil

import pandas as pd
import pytest

from scripts.ops import run_i17_candidate_comparison_v1 as comparison
from scripts.ops.run_i17_candidate_comparison_v1 import _compare, _strategy_binding
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
    EvaluationReceiptArchiveV1,
)
from src.experiments.canonical_research_prepared_execution_v1 import digest_v1
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.candidate_observation_v1 import (
    I17CandidateHostObservationV1,
    candidate_plan_component_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
    WallclockRuntimeConfigV1,
    WallclockSessionRuntimeV1,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_preregistration_producer_v1 import (
    build_productive_preregistration_dict_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2 import (
    hardening_cycle_bridge_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    I17OfflineCandidateInputV2,
    run_hardened_bridge_cycle_v2,
)
from src.strategies.registry import build_registry_snapshot
from src.strategies.suitability_registry_adapter_v1 import build_suitability_registry_from_snapshot
from tests.ops.test_integrated_paper_shadow_observation_wallclock_session_execution_v1 import (
    FakeClock,
    NOW,
    REPO_ROOT,
    SHA,
    _fake_ticker_fetcher,
    _load_wallclock_go,
    _load_wallclock_prereg,
    _material,
    _write_v2_auth,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    InstrumentObservationKeyV1,
    ObservationCandidateV1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)


def _pair_and_candles():
    profiles = {}
    for role, slow, digest in (("reference", 30, "a"), ("candidate", 40, "b")):
        params = {"fast_window": 10, "slow_window": slow}
        profiles[role] = {
            "packet": digest * 64,
            "parameters": params,
            "config": {
                "economic_evaluation_v1": {
                    "strategy_id": "ma_crossover",
                    "strategy_version": "v1",
                    "strategy_params": params,
                }
            },
        }
    plan = {
        "instrument_id": CANONICAL_INSTRUMENT_ID,
        "strategy_id": "ma_crossover",
        "strategy_version": "v1",
        "profiles": profiles,
    }
    times = pd.date_range(end="2026-11-14T19:00:00Z", periods=70, freq="h")
    closes = [1800.0 + item for item in range(len(times))]
    bars = pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes, "volume": 1.0}, index=times
    )
    return plan, bars


def test_same_final_hour_prefix_binds_two_real_i17_epochs():
    plan, bars = _pair_and_candles()
    rows = []
    for sequence, time in enumerate(("2026-11-14T17:59:59+00:00", "2026-11-14T18:00:01+00:00"), 1):
        now = datetime.fromisoformat(time).timestamp()
        rows.append(
            (
                now,
                {
                    "sequence": sequence,
                    "event_ts_unix": now - 0.1,
                    "receive_ts_unix": now - 0.02,
                    "mid_price": 1800.0 + sequence,
                },
                f"original-{sequence}",
            )
        )
    now, repeated, decision_id = rows[-1]
    rows.append(
        (now + 1.0, dict(repeated, sequence=3, receive_ts_unix=now + 0.1), decision_id + "-repeat")
    )
    cycles = _compare(plan, rows, bars, identifier="1" * 64)
    assert [cycle["last_candle_close_utc"] for cycle in cycles] == [
        "2026-11-14T17:00:00+00:00",
        "2026-11-14T18:00:00+00:00",
        "2026-11-14T18:00:00+00:00",
    ]
    for epoch, cycle in enumerate(cycles, 1):
        for role, arm in cycle["arms"].items():
            material = arm["material"]
            assert material["trading_epoch"] == epoch
            assert arm["market_observation_epoch"] == min(epoch, 2)
            assert arm["market_observation_classification"] == (
                "distinct" if epoch < 3 else "transport_only_duplicate"
            )
            assert material["instrument_id"] == CANONICAL_INSTRUMENT_ID
            assert arm["artifact_digest"] == plan["profiles"][role]["packet"]
            prefix = bars.loc[: cycle["last_candle_close_utc"]]
            binding = _strategy_binding(plan, plan["profiles"][role], prefix)
            assert material["strategy_signal_digest"] == binding.provenance.strategy_signal_digest
            assert material["cycle_signal_value"] == int(binding.signals.iloc[-1])


def _capture_last(bars, requested_at, received_at):
    query = comparison._last_query(
        CANONICAL_INSTRUMENT_ID, datetime.fromisoformat(requested_at).timestamp()
    )
    rows = [
        [
            str(int((time - comparison.HOUR).timestamp()) * 1000),
            *[str(row[field]) for field in ("open", "high", "low", "close")],
            "1",
            str(row["volume"]),
            "1",
            "1",
        ]
        for time, row in bars.iterrows()
    ]
    raw = json.dumps({"code": "0", "data": rows}).encode()
    return {
        "host": comparison.PUBLIC_HTTP_HOST,
        "endpoint": comparison.LAST_ENDPOINT,
        "query": query,
        "requested_at_utc": requested_at,
        "received_at_utc": received_at,
        "raw_sha256": sha256(raw).hexdigest(),
        "raw_hex": raw.hex(),
    }


def _decision_time_inputs():
    plan, bars = _pair_and_candles()
    plan.update(
        schema_version=comparison.PLAN_SCHEMA,
        authority="NONE",
        mode="PROSPECTIVE_PUBLIC_DATA_OFFLINE_REPLAY",
        candidate_known_at_utc="2026-11-14T16:10:00+00:00",
        parent_data_known_at_utc="2026-11-14T16:00:00+00:00",
        registered_at_utc="2026-11-14T16:55:00+00:00",
        start_utc="2026-11-14T17:00:00+00:00",
        end_utc="2026-11-14T19:00:00+00:00",
    )
    bars = bars.iloc[:-1].copy()
    prices = [1900.0 - n for n in range(len(bars))]
    prices[-1] += 175.0  # Crosses MA 30, stays under MA 40.
    for field in ("open", "high", "low", "close"):
        bars[field] = prices
    rows = []
    for index, second in enumerate(("17:59:59", "18:00:01", "18:00:03"), 1):
        decided = datetime.fromisoformat(f"2026-11-14T{second}+00:00").timestamp()
        rows.append(
            (
                decided,
                {
                    "sequence": index,
                    "event_ts_unix": decided - 0.1,
                    "receive_ts_unix": decided - 0.02,
                    "mid_price": 1800.0 + index,
                },
                f"decision-{index}",
            )
        )
    archive = {
        "schema_version": comparison.DECISION_TIME_LAST_SCHEMA,
        "plan_digest": digest_v1(plan),
        "original_i17_manifest_sha256": "1" * 64,
        "captures": [
            _capture_last(bars.iloc[:-1], "2026-11-14T17:00:05+00:00", "2026-11-14T17:00:06+00:00"),
            _capture_last(bars.iloc[1:], "2026-11-14T18:00:02+00:00", "2026-11-14T18:00:03+00:00"),
        ],
    }
    return plan, rows, archive


def test_i17_preflight_uses_new_hour_only_after_receive_and_replays_same_proof(
    tmp_path, monkeypatch
):
    plan, rows, archive = _decision_time_inputs()
    monkeypatch.setattr(
        comparison, "_read_i17", lambda *_: (archive["original_i17_manifest_sha256"], rows)
    )
    received_material = []
    run_replay = hardening_cycle_bridge_v2.run_integrated_offline_trading_logic_replay_v1

    def record_replay(inputs):
        received_material.append(inputs.strategy_suitability_agreement_material)
        return run_replay(inputs)

    monkeypatch.setattr(
        hardening_cycle_bridge_v2, "run_integrated_offline_trading_logic_replay_v1", record_replay
    )
    workspace = EvaluationReceiptArchiveV1(tmp_path / "preflight")
    args = dict(
        plan=plan,
        evidence_root=tmp_path / "i17",
        code_sha="2" * 40,
        decision_time_archive=archive,
    )
    result = comparison.compare_v1(workspace, **args)
    assert result["scope"] == "I17_DECISION_TIME_OFFLINE_PREFLIGHT"
    assert result["authority"] == "NONE"
    assert result["different_strategy_states"] == 1
    first, before_receive, on_receive = result["cycles"]
    assert first["last_candle_close_utc"] == before_receive["last_candle_close_utc"]
    for cycle, capture in zip(result["cycles"], (0, 0, 1), strict=True):
        source = archive["captures"][capture]
        assert cycle["last_candle_input"] == {
            "received_at_utc": source["received_at_utc"],
            "source_capture_digest": digest_v1(source),
        }
    assert before_receive["last_candle_close_utc"] == "2026-11-14T17:00:00+00:00"
    assert on_receive["last_candle_close_utc"] == "2026-11-14T18:00:00+00:00"
    for role, expected_states in (("reference", (0, 0, 1)), ("candidate", (0, 0, 0))):
        arm_rows = [cycle["arms"][role] for cycle in result["cycles"]]
        assert all(arm["artifact_digest"] == plan["profiles"][role]["packet"] for arm in arm_rows)
        assert tuple(arm["material"]["cycle_signal_value"] for arm in arm_rows) == expected_states
        assert [arm["material"]["trading_epoch"] for arm in arm_rows] == [1, 2, 3]
    assert (
        on_receive["arms"]["reference"]["material"]["strategy_params_digest"]
        != on_receive["arms"]["candidate"]["material"]["strategy_params_digest"]
    )
    assert [material.cycle_signal_value for material in received_material] == [0, 0, 0, 0, 1, 0]
    assert [material.material_digest for material in received_material] == [
        cycle["arms"][role]["material"]["material_digest"]
        for cycle in result["cycles"]
        for role in ("reference", "candidate")
    ]
    assert comparison.compare_v1(workspace, **args, verify=True) == result


def test_i17_preflight_rejects_missing_available_input_before_first_decision():
    plan, rows, archive = _decision_time_inputs()
    archive["captures"].pop(0)
    snapshots = comparison._decision_time_last_snapshots(
        plan, rows, archive, manifest_sha=archive["original_i17_manifest_sha256"]
    )
    with pytest.raises(ValueError, match="I17_DECISION_TIME_LAST_NOT_YET_AVAILABLE"):
        _compare(plan, rows, None, identifier="1" * 64, decision_time_last=snapshots)


def test_i17_preflight_requires_profiles_bound_before_the_observed_window():
    plan, rows, archive = _decision_time_inputs()
    plan["registered_at_utc"] = plan["start_utc"]
    archive["plan_digest"] = digest_v1(plan)
    with pytest.raises(ValueError, match="I17_DECISION_TIME_WINDOW_OR_PLAN_MISMATCH"):
        comparison._decision_time_last_snapshots(
            plan, rows, archive, manifest_sha=archive["original_i17_manifest_sha256"]
        )


def test_i17_preflight_rejects_revised_finalized_warmup():
    plan, rows, archive = _decision_time_inputs()
    latest = archive["captures"][-1]
    payload = json.loads(bytes.fromhex(latest["raw_hex"]))
    payload["data"][0][1:5] = ["2000.0"] * 4
    raw = json.dumps(payload).encode()
    latest.update(raw_hex=raw.hex(), raw_sha256=sha256(raw).hexdigest())
    with pytest.raises(ValueError, match="I17_DECISION_TIME_LAST_PREFIX_CHANGED"):
        comparison._decision_time_last_snapshots(
            plan, rows, archive, manifest_sha=archive["original_i17_manifest_sha256"]
        )


def test_i17_last_capture_preserves_transport_time_and_binds_the_sealed_scope(
    tmp_path, monkeypatch
):
    plan, rows, source = _decision_time_inputs()
    evidence_root = tmp_path / "i17"
    evidence_root.mkdir()
    prereg = build_productive_preregistration_dict_v1(
        session_id="i17-capture-fixture",
        expected_repository_sha="2" * 40,
        planned_duration_seconds=7200,
        earliest_start=datetime.fromisoformat(plan["start_utc"]).timestamp(),
        expires_at=datetime.fromisoformat(plan["end_utc"]).timestamp(),
        evidence_root=str(evidence_root),
        operator_identity="fixture-operator",
        approval_identity="fixture-approval",
        confirm_token="synthetic-token",
    )
    scope = comparison.parse_preregistration_contract_v1(prereg).scope_digest()
    files = {"prereg.json": json.dumps(prereg).encode(), "scope_digest.txt": scope.encode()}
    for name, raw in files.items():
        (evidence_root / name).write_bytes(raw)
    manifest = "".join(
        f"{sha256(raw).hexdigest()}  {name}\n" for name, raw in files.items()
    ).encode()
    (evidence_root / "evidence_manifest.sha256").write_bytes(manifest)
    manifest_sha = sha256(manifest).hexdigest()
    monkeypatch.setattr(comparison, "_read_i17", lambda *_: (manifest_sha, rows))

    journal = EvaluationReceiptArchiveV1(tmp_path / "journal")
    calls = []
    for saved in source["captures"]:
        now = datetime.fromisoformat(saved["requested_at_utc"])

        def fetch(path, query):
            nonlocal now
            assert path == comparison.LAST_ENDPOINT
            assert query == saved["query"]
            calls.append(query["after"])
            now = datetime.fromisoformat(saved["received_at_utc"])
            return bytes.fromhex(saved["raw_hex"])

        args = dict(plan=plan, scope_digest=scope, fetch=fetch, clock=lambda: now)
        assert comparison.capture_decision_time_last_v1(journal, **args) == saved
        assert comparison.capture_decision_time_last_v1(journal, **args) == saved

    assert len(calls) == 2
    result = comparison.seal_decision_time_last_v1(journal, plan=plan, evidence_root=evidence_root)
    assert (
        comparison.seal_decision_time_last_v1(journal, plan=plan, evidence_root=evidence_root)
        == result
    )
    archive = comparison.read_v1(result)
    assert archive["original_i17_scope_digest"] == scope
    assert archive["original_i17_manifest_sha256"] == manifest_sha
    assert archive["plan_digest"] == digest_v1(plan)
    assert archive["captures"] == source["captures"]

    workspace = EvaluationReceiptArchiveV1(tmp_path / "comparison")
    preflight_args = dict(plan=plan, evidence_root=evidence_root, code_sha="2" * 40)
    wrong_scope = {**archive, "original_i17_scope_digest": "b" * 64}
    with pytest.raises(ValueError, match="I17_DECISION_TIME_ORIGINAL_SCOPE_MISMATCH"):
        comparison.compare_v1(workspace, **preflight_args, decision_time_archive=wrong_scope)
    assert not (workspace.root / "result.json").exists()
    proof = comparison.compare_v1(workspace, **preflight_args, decision_time_archive=archive)
    assert proof["original_i17_scope_digest"] == scope
    assert proof["different_strategy_states"] == 1


def test_i17_last_capture_rejects_receipt_after_the_planned_window(tmp_path):
    plan, _, source = _decision_time_inputs()
    now = datetime.fromisoformat(source["captures"][-1]["requested_at_utc"])
    journal = EvaluationReceiptArchiveV1(tmp_path / "journal")

    def fetch(*_):
        nonlocal now
        now = datetime.fromisoformat(plan["end_utc"])
        return bytes.fromhex(source["captures"][-1]["raw_hex"])

    with pytest.raises(ValueError, match="I17_DECISION_TIME_CAPTURE_CLOCK_INVALID"):
        comparison.capture_decision_time_last_v1(
            journal, plan=plan, scope_digest="a" * 64, fetch=fetch, clock=lambda: now
        )
    assert not list(journal.root.rglob("*.json"))


@pytest.mark.parametrize("case", ("compared", "wrong_plan", "no_initial_last"))
def test_i17_host_binds_both_profiles_to_one_observation_in_the_real_cycle(
    tmp_path, monkeypatch, case
):
    monkeypatch.delenv("PEAK_TRADE_O7_LIVE_OHLCV_BRIDGE_ENABLED", raising=False)
    plan, bars = _pair_and_candles()
    boundary = ceil(NOW / 3600) * 3600

    def utc(at):
        return datetime.fromtimestamp(at, timezone.utc)

    plan.update(
        schema_version=comparison.PLAN_SCHEMA,
        authority="NONE",
        mode="PROSPECTIVE_PUBLIC_DATA_OFFLINE_REPLAY",
        candidate_known_at_utc=utc(boundary - 4000).isoformat(),
        parent_data_known_at_utc=utc(boundary - 4100).isoformat(),
        registered_at_utc=utc(boundary - 3900).isoformat(),
        start_utc=utc(boundary - 3600).isoformat(),
        end_utc=utc(boundary + 3600).isoformat(),
    )
    prices = [1900.0 - n for n in range(len(bars))]
    prices[-1] += 175.0
    for field in ("open", "high", "low", "close"):
        bars[field] = prices
    bars.index = pd.date_range(end=utc(boundary), periods=len(bars), freq="h")
    journal = EvaluationReceiptArchiveV1(tmp_path / "last-journal")
    anchor = _load_wallclock_prereg()
    component = candidate_plan_component_v1(plan)
    if case == "wrong_plan":
        component = candidate_plan_component_v1({**plan, "case": case})
    prereg = replace(
        anchor, strategy_component_identities=(*anchor.strategy_component_identities, component)
    )
    go = replace(_load_wallclock_go(), scope_digest=prereg.scope_digest())
    token = _material()
    artifact = _write_v2_auth(tmp_path, prereg=prereg, token=token)

    def publish_last(frame, clock):
        expected = _capture_last(
            frame, utc(clock.time()).isoformat(), utc(clock.time() + 0.0625).isoformat()
        )

        def fetch_last(path, query):
            assert path == comparison.LAST_ENDPOINT and query == expected["query"]
            clock.sleep(0.0625)
            return bytes.fromhex(expected["raw_hex"])

        return comparison.capture_decision_time_last_v1(
            journal,
            plan=plan,
            scope_digest=prereg.scope_digest(),
            fetch=fetch_last,
            clock=lambda: utc(clock.time()),
        )

    first = None
    if case == "compared":
        first = publish_last(bars.iloc[:-1], FakeClock(wall=boundary - 1))
    latest = []
    clock = FakeClock(wall=boundary + 0.125)
    polls = 0

    def fetch_market(url, *args):
        nonlocal polls
        assert comparison.LAST_ENDPOINT not in url
        if "/market/ticker?" in url:
            polls += 1
            if polls == 2:
                latest.append(publish_last(bars.iloc[1:], clock))
        return _fake_ticker_fetcher(str(3500 + polls), clock=clock)(url, *args)

    root = tmp_path / "host"
    transport = EeaPublicMdTransportV1(fetcher=fetch_market, sleep=clock.sleep, environ={})
    runtime = WallclockSessionRuntimeV1(
        evidence_root=root,
        transport=transport,
        config=WallclockRuntimeConfigV1(
            max_cycles=3, poll_interval_seconds=0.25, min_quality_window_seconds=0
        ),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
        candidate_observation=I17CandidateHostObservationV1(plan=plan, journal=journal),
    )
    result = runtime.run(
        prereg=prereg,
        go=go,
        confirm_token=token,
        artifact_path=artifact,
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fp.ledger",
    )
    if case == "wrong_plan":
        assert result.blockers == ["I17_CANDIDATE_HOST_PREREGISTRATION_MISMATCH"]
        assert not result.consumed and not result.network_opened and transport.fetch_count == 0
        assert not root.exists()
        return
    assert result.consumed and not result.orders_submitted
    assert verify_wallclock_evidence_bundle_v1(evidence_root=root).verified
    assert len(latest) == 1
    cycles = [
        json.loads(line) for line in (root / "bridge_cycle_ledger.jsonl").read_text().splitlines()
    ]
    assert len(cycles) == 3
    pairs = [cycle["i17_candidate_comparison"] for cycle in cycles]
    assert [pair["parent_decision_id"] for pair in pairs] == [row["decision_id"] for row in cycles]
    assert {pair["plan_digest"] for pair in pairs} == {digest_v1(plan)}
    assert {pair["original_i17_scope_digest"] for pair in pairs} == {prereg.scope_digest()}
    if case == "no_initial_last":
        assert {pair["status"] for pair in pairs} == {"FAILED"}
        assert {pair["reason"] for pair in pairs} == {"I17_DECISION_TIME_LAST_NOT_YET_AVAILABLE"}
        return
    assert {pair["status"] for pair in pairs} == {"COMPARED"}
    assert [pair["last_candle_close_utc"] for pair in pairs] == [
        utc(boundary - 3600).isoformat(),
        utc(boundary).isoformat(),
        utc(boundary).isoformat(),
    ]
    assert [pair["last_candle_input"]["source_capture_digest"] for pair in pairs] == [
        digest_v1(first),
        digest_v1(latest[0]),
        digest_v1(latest[0]),
    ]
    assert [pair["mark_sequence"] for pair in pairs] == [
        row["shadow_decision_timing"]["market_sequence"] for row in cycles
    ]
    for cycle, pair in zip(cycles, pairs, strict=True):
        timing = cycle["shadow_decision_timing"]
        assert pair["mark_event_ts_unix"] == timing["mark_event_ts_unix"]
        assert pair["mark_receive_ts_unix"] == timing["mark_receive_ts_unix"]
        assert (
            pair["last_candle_close_utc"]
            <= pair["last_candle_input"]["received_at_utc"]
            <= pair["decision_time_utc"]
        )
        assert (
            pair["arms"]["reference"]["market_observation_epoch"]
            == (pair["arms"]["candidate"]["market_observation_epoch"])
        )
    for role, expected in (("reference", [0, 1, 1]), ("candidate", [0, 0, 0])):
        values = [pair["arms"][role]["material"] for pair in pairs]
        assert [value["cycle_signal_value"] for value in values] == expected
        assert [value["trading_epoch"] for value in values] == [1, 2, 3]


def test_candidate_bridge_rejects_state_persistence_before_cycle(tmp_path):
    plan, bars = _pair_and_candles()
    binding = _strategy_binding(plan, plan["profiles"]["reference"], bars)
    material = normalize_strategy_signal_to_suitability_agreement_material_v1(
        binding, instrument_id=CANONICAL_INSTRUMENT_ID, trading_epoch=1, signal_index=len(bars) - 1
    )
    registry = build_suitability_registry_from_snapshot(build_registry_snapshot())
    entry = next(item for item in registry.entries if item.strategy_id == "ma_crossover")
    tick_time = datetime(2026, 11, 14, tzinfo=timezone.utc).timestamp()
    instrument_key = InstrumentObservationKeyV1(
        "okx", CANONICAL_INSTRUMENT_ID, CANONICAL_INSTRUMENT_ID
    )
    accepted = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=instrument_key),
        ObservationCandidateV1(
            "okx", CANONICAL_INSTRUMENT_ID, CANONICAL_INSTRUMENT_ID, tick_time, 1800.0
        ),
    )
    state = HardenedBridgeSessionStateV2(instrument_id=CANONICAL_INSTRUMENT_ID)
    state.decision_config_state_root = str(tmp_path / "runtime")
    with pytest.raises(ValueError, match="I17_CANDIDATE_REQUIRES_ISOLATED_OFFLINE_CYCLE"):
        run_hardened_bridge_cycle_v2(
            state,
            mid_price=1800.0,
            event_ts_unix=tick_time,
            session_id="candidate-test",
            offline_candidate=I17OfflineCandidateInputV2("a" * 64, entry, material, accepted),
        )
    assert state.cycle_index == 0
    assert not (tmp_path / "runtime").exists()
