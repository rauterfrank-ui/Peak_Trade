"""The recurring tick keeps work identity, evidence and finite processing across retries."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from scripts.ops import run_recurrent_offline_research_v1 as campaign_ops
from scripts.ops.btc_demo_entry_learning_handoff_v1 import btc_demo_entry_learning_handoff_v1
from src.experiments.canonical_experiment_identity_v1 import CanonicalCodeProvenanceV1
from src.experiments.canonical_research_prepared_execution_v1 import read_v1
from src.experiments.offline_ddo_research_cycle_v1 import run_offline_testnet_ddo_research_cycle_v1
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from tests.learning.test_learning_current_decision_contract_realignment_v1 import (
    _resolve_enter_long_binding,
)
from tests.learning.test_offline_ddo_research_cycle_v1 import native_research_fixture
from tests.trading.master_v2 import test_double_play_entry_exit_policy_v0 as policy_inputs


def test_tick_latches_dataset_excludes_open_paper_and_skips_completed_source(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    instrument = "okx_eea:linear_perpetual:ETH:USDT:USDT:eth-usdt-swap"
    start = datetime(2026, 11, 14, 20, 0, tzinfo=timezone.utc)
    code = CanonicalCodeProvenanceV1("b" * 40, "CLEAN")
    paper, shadow, followups = (root / name for name in ("paper", "shadow", "followups"))
    for path in (paper, shadow, followups):
        path.mkdir()
    sealed = paper / "001"
    sealed.mkdir()
    (sealed / "MANIFEST.sha256").touch()
    (sealed / "paper-closeout.json").write_text('{"error":null,"status":"WINDOW_ENDED"}')
    closed_id = "simulated-accounting:" + "a" * 64
    open_id = "simulated-accounting:" + "b" * 64
    for episode, closed in ((closed_id, True), (open_id, False)):
        folder = sealed / "episodes" / episode
        folder.mkdir(parents=True)
        (folder / "exit_policy_state_v1.json").write_text(
            json.dumps({"simulated_accounting_close": {}} if closed else {})
        )
    digest = "c" * 64
    bars, cfg, request = native_research_fixture(instrument, digest)
    csv, config = root / "bars.csv", root / "config.json"
    bars.to_csv(csv)
    config.write_text(json.dumps(cfg))
    profile = request.model_dump(mode="json", exclude={"learning_evidence_digest", "times"})
    profile.update(schema_version="offline_ddo_research_profile.v1", gap_dimensions=[])
    template = root / "input.json"
    template.write_text(
        json.dumps(
            {
                "schema_version": "offline_research_input.v1",
                "instrument_id": instrument,
                "bars_csv_sha256": sha256(csv.read_bytes()).hexdigest(),
                "backtest_json_sha256": sha256(config.read_bytes()).hexdigest(),
                "profile": profile,
            }
        )
    )
    campaign = campaign_ops.ResearchCampaignV1.model_validate(
        dict(
            state=root / "state",
            paper_runs=paper,
            shadow_runs=shadow,
            shadow_follow_ups=followups,
            research_inputs={instrument: [dict(template=template, bars=csv, config=config)]},
            jobs_per_tick=1,
            history_jobs=3,
            retry_seconds=60,
        )
    )
    observed = []

    def source(workspace, item, selected):
        assert item["episode"] == closed_id
        return {
            "learning_evidence": {
                "content_hash": digest,
                "observed_at_utc": "2026-11-14T19:00:00Z",
                "outcome_evidence_provenance": {"instrument_id": instrument},
            }
        }, {}

    def research(state, cycle, **kwargs):
        observed.append(kwargs["request"].model_dump())
        if len(observed) == 1:
            return {"status": "MECHANISM_INCOMPLETE"}
        result = {
            "status": "FIRST_SEARCH_EXHAUSTED",
            "learning_evidence_digest": cycle,
            "first_artifact_id": None,
            "next_artifact_id": None,
        }
        campaign_ops.publish_v1(state / "offline-ddo-research" / cycle / "result.json", result)
        return result

    monkeypatch.setattr(campaign_ops, "_read_source", source)
    monkeypatch.setattr(campaign_ops, "run_offline_paper_ddo_research_cycle_v1", research)
    # This scheduling test replaces scientific execution with a minimal fake.
    # Complete original-owner chain admission is tested with actual engine
    # packets in test_learning_research_chain_readback_v1.
    monkeypatch.setattr(campaign_ops, "read_learning_research_chain_v1", lambda *args: {})
    tick = campaign_ops.tick_research_campaign_v1
    assert tick(campaign, code=code, now=start)["jobs"][0]["status"] == "MECHANISM_INCOMPLETE"
    job = campaign.state / "jobs" / (digest + ".json")
    original = job.read_bytes()
    assert tick(campaign, code=code, now=start + timedelta(seconds=59))["jobs"] == []
    assert tick(campaign, code=code, now=start + timedelta(minutes=1))["jobs"][0]["status"] == (
        "FIRST_SEARCH_EXHAUSTED"
    )
    assert job.read_bytes() == original
    assert observed[0] == observed[1]
    assert tick(campaign, code=code, now=start + timedelta(minutes=2))["jobs"] == []
    assert len(observed) == 2
    assert read_v1(campaign.state / "completed" / (digest + ".json"))["authority"] == "NONE"


def test_future_dataset_cannot_be_selected(tmp_path):
    root = tmp_path.resolve()
    template = root / "input.json"
    template.write_text('{"profile":{"bars_known_at":"2026-11-15T00:00:00Z"}}')
    selected = campaign_ops.ResearchInputV1(
        template=template, bars=root / "bars", config=root / "config"
    )
    campaign = campaign_ops.ResearchCampaignV1(
        state=root / "state",
        paper_runs=root,
        shadow_runs=root,
        shadow_follow_ups=root,
        research_inputs={"asset": [selected]},
        jobs_per_tick=1,
        history_jobs=1,
        retry_seconds=1,
    )
    assert (
        campaign_ops._select_input(
            campaign,
            "asset",
            {"observed_at_utc": "2026-11-14T19:00:00Z"},
            datetime(2026, 11, 14, 21, tzinfo=timezone.utc),
        )
        is None
    )


def test_campaign_history_only_uses_completed_jobs_known_at_search(tmp_path):
    workspace = campaign_ops.EvaluationReceiptArchiveV1(tmp_path.resolve())
    now = datetime(2026, 11, 14, 21, tzinfo=timezone.utc)
    for digest, clock in (("a", now - timedelta(seconds=1)), ("b", now + timedelta(seconds=1))):
        campaign_ops.publish_v1(
            workspace.safe_path_v1(Path("completed") / (digest + ".json")),
            {
                "instrument_id": "instrument",
                "strategy_id": "strategy",
                "strategy_version": "1",
                "learning_digest": digest,
                "artifacts": [digest],
                "completed_at_utc": campaign_ops._utc(clock),
            },
        )
    history = campaign_ops._history(workspace, "instrument", "strategy", "1", now)
    assert [row["learning_digest"] for row in history] == ["a"]


def test_slot_scope_rejects_crosswired_sources_and_end_boundary():
    slot = campaign_ops.ResearchSlotScopeV1(
        lane_id="LANE_3",
        surface="TESTNET",
        session_id="btc-demo-unit",
        instrument_id="canonical-btc",
        venue_native_id="BTC-USD_UM_XPERP-310328",
        starts_at="2026-11-18T14:30:00+01:00",
        ends_at="2026-11-18T16:30:00+01:00",
    )
    valid = dict(
        session_id="btc-demo-unit",
        instrument_id="canonical-btc",
        venue_native_id="BTC-USD_UM_XPERP-310328",
        decision_time="2026-11-18T13:30:00Z",
    )
    slot.require_source(**valid)
    for key, value in (
        ("session_id", "other-session"),
        ("instrument_id", "canonical-irys"),
        ("venue_native_id", "BTC-USDT-SWAP"),
        ("decision_time", "2026-11-18T15:30:00Z"),
    ):
        with pytest.raises(ValueError, match="RESEARCH_SLOT_SOURCE_SCOPE_MISMATCH"):
            slot.require_source(**{**valid, key: value})


def test_demo_decision_join_reaches_isolated_gvef_and_replays_once(tmp_path, monkeypatch):
    instrument = "okx_eea:linear_dated_future:BTC:USD:USD:btc-usd_um_xperp-310328"
    monkeypatch.setattr(policy_inputs, "_INSTRUMENT", instrument)
    capture, decision_ref, dp = _resolve_enter_long_binding()
    root = tmp_path.resolve()
    source = root / "decision-source.jsonl"
    ledger = AppendOnlyDdoLedgerV0(source)
    for row in capture.captured_records:
        ledger.append(row)
    decision = ledger.get(decision_ref)
    measurement = {
        "authority": "NONE",
        "execution_environment": "TESTNET",
        "lane_id": "LANE_3",
        "session_id": "demo-fixture",
        "episode_id": "b" * 64,
        "instrument_id": instrument,
        "venue_native_id": "BTC-USD_UM_XPERP-310328",
        "decision_id": dp.policy_decision_id,
        "decision_outcome": "ENTER_LONG",
        "config_digest": decision["config_hash"],
        "source_digest": "d" * 64,
        "envelope_created_utc": "2026-09-05T12:00:01Z",
        "confirmed_at_utc": "2026-09-05T12:00:03Z",
        "opening_fill": {"filled_quantity": "0.0001", "fees": []},
    }
    output = root / "lane3"
    before = source.read_bytes()
    with pytest.raises(ValueError, match="ORIGINAL_DOUBLE_PLAY_DECISION_MISMATCH"):
        btc_demo_entry_learning_handoff_v1(
            decision_ledger=source,
            output_root=output,
            measurement={**measurement, "instrument_id": "foreign-instrument"},
        )
    assert not output.exists()
    handoff = btc_demo_entry_learning_handoff_v1(
        decision_ledger=source,
        output_root=output,
        measurement=measurement,
    )
    assert handoff == btc_demo_entry_learning_handoff_v1(
        decision_ledger=source,
        output_root=output,
        measurement=measurement,
    )
    assert source.read_bytes() == before
    evidence = handoff["learning_evidence"]
    assert evidence["outcome_semantic_class"] == "TESTNET_VENUE_EVIDENCE"
    assert evidence["outcome_evidence_provenance"]["fill_source_type"] == "VENUE_TESTNET"
    bars, cfg, request = native_research_fixture(instrument, evidence["content_hash"])
    times = {
        key: (datetime(2026, 9, 5, 13, tzinfo=timezone.utc) + timedelta(minutes=index))
        .isoformat()
        .replace("+00:00", "Z")
        for index, key in enumerate(type(request.times).model_fields)
    }
    request = type(request).model_validate(
        {
            **request.model_dump(mode="json"),
            "observed_surface": "TESTNET",
            "gap_dimensions": [],
            "times": times,
        }
    )
    result = run_offline_testnet_ddo_research_cycle_v1(
        output,
        "demo-offline",
        handoff=handoff,
        request=request,
        bars=bars,
        cfg=cfg,
        code=CanonicalCodeProvenanceV1("b" * 40, "CLEAN"),
    )
    assert result["status"] == "MECHANISM_PASS", result
    assert result["evaluation"]["economic_status"] == "BLOCKED"
