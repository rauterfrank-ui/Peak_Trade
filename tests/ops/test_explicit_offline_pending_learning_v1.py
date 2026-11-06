"""Actual captured Core -> retained Pending -> original supplier -> numeric MI."""

from dataclasses import replace
from datetime import datetime
import json
import math
from pathlib import Path

import pytest

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    DdoCaptureBindingV0,
    SEAM_DOUBLE_PLAY_ENTRY_EXIT,
    observe_producer_result_v0,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
    mint_forecast_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_context_v1 import (
    pending_decision_context_from_invocation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.offline_v1 import (
    create_explicit_offline_pending_v1,
    advance_explicit_offline_pending_v1,
    read_explicit_offline_pending_v1,
    offline_return_target_v1,
    OfflineOutcomeError,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.artifact_matrix_v1 import (
    purge_lane_local_artifacts_for_release_v1,
)
from tests.ops.test_pending_exact_decision_context_v1 import _invocation
from tests.ops.test_bounded_offline_all_purpose_consumers_v1 import _profiles


def _case(tmp_path, *, mark=1234.5, source_class="SYNTHETIC_OFFLINE"):
    invocation = _invocation()  # original DP policy result, no caller-made Decision label
    invocation.cycle_result.replay.intermediate.market_context.mark_price = mark
    context = pending_decision_context_from_invocation_v1(invocation)
    lane = tmp_path / "lane"
    ledger_path = lane / "ddo_learning_capture_v1.jsonl"
    binding = DdoCaptureBindingV0(
        enabled=True, ledger_path=ledger_path, capture_scope_config_hash="a" * 64
    )
    observed = observe_producer_result_v0(
        binding,
        seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=invocation.cycle_result.replay.intermediate.entry_exit_decision,
        event_time_utc="2026-11-04T10:00:00Z",
        correlation_id="ddo.corr.e3",
        cycle_id=context.cycle_id,
        repository_sha="1814ca5b24d1d3ab537683e340b3ab045ea51e62",
    )
    assert observed["ok"]
    records = AppendOnlyDdoLedgerV0(ledger_path).read_all()
    observation = next(
        r for r in records if r["schema_name"] == "double_play_entry_exit_observation"
    )
    dpo = {
        k: str(v).lower() if isinstance(v, bool) else str(v)
        for k, v in observation["producer_canonical_payload"].items()
    }
    dpo.update(
        dpo_ref=observation["record_id"],
        decision_event_ref=observation["decision_event_ref"],
        cycle_id=context.cycle_id,
    )
    target = offline_return_target_v1(context=context, n_bars=2, venue="okx")
    end = datetime.fromisoformat(
        target["return_end_close_time_utc"].replace("Z", "+00:00")
    ).timestamp()
    asof = end + 3602
    source = _profiles(
        tmp_path / "facts",
        canonical=context.instrument_id,
        native=context.native_id,
        now_ms=round(asof * 1000),
        last_ms=round((asof - 2) * 1000),
    )["OUTCOME"]
    forecast = mint_forecast_evidence_v1(
        information_set_ref="info.e3.explicit.synthetic",
        forecast_created_at_utc="2026-11-04T10:00:01Z",
        outcome_horizon_end_utc=target["return_end_close_time_utc"],
        n_bars=2,
        bar_spec_ref=target["bar_spec_ref"],
        forecast_kind="RETURN_DISTRIBUTION_SUMMARY",
        probabilistic_payload={"mean_return": 0.02, "std_return": 0.1},
        market_state_refs=["market.e3.synthetic"],
        forecast_model_ref="model.e3.synthetic",
        support_disposition="SUFFICIENT_EVIDENCE",
        provenance={"source_class": source_class, "measured_return_target_v1": target},
        selected_instrument_ref=target["instrument_ref"],
        decision_event_ref=dpo["decision_event_ref"],
    )
    args = dict(
        retention_root=tmp_path / "retained",
        source_lane_root=lane,
        source_ledger=ledger_path,
        context=context,
        dpo=dpo,
        source=source,
        source_class=source_class,
        forecast=forecast,
        account_identity="offline-test-account",
        venue="okx",
        n_bars=2,
        expires_at_unix=asof + 7200,
        retry_interval_seconds=1,
        max_attempts=10,
        max_retained_jobs=10,
        retained_bytes_backpressure_threshold=10000000,
    )
    return args, asof


def test_retained_actual_core_to_numeric_consumer_survives_lane_release_and_replay(tmp_path):
    args, asof = _case(tmp_path)
    raw = args["source_ledger"].read_bytes()
    root = create_explicit_offline_pending_v1(**args)
    assert create_explicit_offline_pending_v1(**args) == root
    assert read_explicit_offline_pending_v1(root)["attempts"] == 0
    missing = advance_explicit_offline_pending_v1(
        root=root, as_of_unix=args["context"].decision_timestamp_unix, source=None
    )
    assert missing["stage"] == "WAITING_SOURCE" and missing["independent_sample_count"] == 0
    purge_lane_local_artifacts_for_release_v1(args["source_lane_root"])
    assert not args["source_ledger"].exists()
    archives = list(tmp_path.glob(".peaktrade_lane_retention_v1/*/*/retention_ack_v1.json"))
    assert len(archives) == 1
    assert (
        archives[0].parent / "released_originals/ddo_learning_capture_v1.jsonl"
    ).read_bytes() == raw
    assert (root / "decision_source.jsonl").read_bytes() == raw
    done = advance_explicit_offline_pending_v1(root=root, as_of_unix=asof, source=args["source"])
    assert done["stage"] == "INGESTED" and done["independent_sample_count"] == 1
    assert done["numeric_readback"]["realized_return"] == math.log(120 / 110)
    assert done["numeric_readback"]["error"] == math.log(120 / 110) - 0.02
    before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert advance_explicit_offline_pending_v1(root=root, as_of_unix=asof + 1, source=None) == done
    assert before == {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert len(list((args["retention_root"] / "jobs_v1").iterdir())) == 1
    records = AppendOnlyDdoLedgerV0(root / "LANE_1/ddo_learning_capture_v1.jsonl").read_all()
    outcome = next(r for r in records if r["schema_name"] == "outcome_record")
    assert (
        outcome["outcome_evidence_provenance"]["market_observation_source"] == "SYNTHETIC_OFFLINE"
    )
    assert (
        outcome["outcome_evidence_provenance"]["outcome_semantic_class"]
        == "INTERNAL_SIMULATED_OUTCOME"
    )
    assert outcome["evaluation_horizon"] == "N_BARS"


def test_waiting_before_future_bars_does_not_measure_zero(tmp_path):
    args, asof = _case(tmp_path)
    root = create_explicit_offline_pending_v1(**args)
    early = args["context"].decision_timestamp_unix + 2
    result = advance_explicit_offline_pending_v1(
        root=root, as_of_unix=early, source=args["source"].at_v1(round(early * 1000))
    )
    assert result["stage"] == "WAITING_HORIZON"
    assert not (root / "offline_measurement_v1.json").exists()
    assert (
        advance_explicit_offline_pending_v1(root=root, as_of_unix=asof, source=args["source"])[
            "stage"
        ]
        == "INGESTED"
    )


@pytest.mark.parametrize("kind", ["expired", "retry", "foreign_source", "max_jobs", "max_bytes"])
def test_deadline_budget_and_backpressure_preserve_pins(tmp_path, kind):
    args, asof = _case(tmp_path)
    if kind == "max_bytes":
        with pytest.raises(OfflineOutcomeError, match="BACKPRESSURE"):
            create_explicit_offline_pending_v1(
                **{**args, "retained_bytes_backpressure_threshold": 1}
            )
        assert args["source_ledger"].is_file()
        return
    root = create_explicit_offline_pending_v1(**args)
    capsule = (root / "capsule_v1.json").read_bytes()
    if kind == "expired":
        out = advance_explicit_offline_pending_v1(
            root=root, as_of_unix=args["expires_at_unix"] + 1, source=None
        )
        assert out["stage"] == "EXPIRED"
    elif kind == "retry":
        for i in range(10):
            out = advance_explicit_offline_pending_v1(root=root, as_of_unix=asof + i, source=None)
        assert out["stage"] == "WAITING_SOURCE"
        out = advance_explicit_offline_pending_v1(root=root, as_of_unix=asof + 10, source=None)
        assert out["stage"] == "RETRY_BUDGET_EXHAUSTED" and out["attempts"] == 10
    elif kind == "foreign_source":
        source = replace(args["source"], store_root=str((tmp_path / "foreign").resolve()))
        assert (
            advance_explicit_offline_pending_v1(root=root, as_of_unix=asof, source=source)["stage"]
            == "QUARANTINED"
        )
    else:
        with pytest.raises(OfflineOutcomeError, match="BACKPRESSURE"):
            create_explicit_offline_pending_v1(
                **{**args, "account_identity": "another-account", "max_retained_jobs": 1}
            )
    assert (root / "capsule_v1.json").read_bytes() == capsule
    assert not (root / "consumer_ack_v1.json").exists()


@pytest.mark.parametrize(
    "boundary", ["measurement", "evaluation", "learning", "optimization", "mi", "ack", "closed"]
)
def test_interruption_after_actual_owner_write_resumes_without_extra_sample(
    tmp_path, monkeypatch, boundary
):
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import (
        offline_v1 as runtime,
    )

    args, asof = _case(tmp_path)
    root = create_explicit_offline_pending_v1(**args)
    hit = []
    function = {
        "evaluation": "persist_evaluation_bundle_v0",
        "learning": "ingest_evaluation_bundle_into_learning_state_v1",
        "mi": "calibrate_explicit_measured_return_v1",
        "closed": "persist_record_v1",
    }.get(boundary, "immutable_json_v1")
    actual = getattr(runtime, function)

    def interrupted(*a, **kw):
        result = actual(*a, **kw)
        target = (
            boundary in {"evaluation", "learning", "mi"}
            or boundary == "closed"
            and kw.get("event_type") == "CLOSED"
            or boundary == "measurement"
            and a[0].name == "offline_measurement_v1.json"
            or boundary == "optimization"
            and a[0].name == "optimization_input_v1.json"
            or boundary == "ack"
            and a[0].name == "consumer_ack_v1.json"
        )
        if target and not hit:
            hit.append(True)
            raise RuntimeError("simulated process death after durable owner write")
        return result

    monkeypatch.setattr(runtime, function, interrupted)
    with pytest.raises(RuntimeError, match="process death"):
        advance_explicit_offline_pending_v1(root=root, as_of_unix=asof, source=args["source"])
    assert hit
    if boundary != "closed":
        assert read_explicit_offline_pending_v1(root)["independent_sample_count"] == 0
    monkeypatch.setattr(runtime, function, actual)
    # Measured obligations recover after the acquisition deadline; no new data
    # or new retry is substituted for the retained original measurement.
    result = advance_explicit_offline_pending_v1(
        root=root, as_of_unix=args["expires_at_unix"] + 1, source=None
    )
    assert result["stage"] == "INGESTED" and result["attempts"] == 1
    ledger = AppendOnlyDdoLedgerV0(root / "LANE_1/ddo_learning_capture_v1.jsonl")
    assert len([r for r in ledger.read_all() if r["schema_name"] == "outcome_record"]) == 1
    assert len([r for r in ledger.read_all() if r["schema_name"] == "learning_state_record"]) == 1
    assert (
        len(list((root / "mi_consumer").glob("*/mi_offline_durable_evidence_record_v1.json"))) == 1
    )


def test_fresh_process_reloads_due_obligation_and_actual_numbers(tmp_path):
    import subprocess
    from dataclasses import asdict

    args, asof = _case(tmp_path)
    root = create_explicit_offline_pending_v1(**args)
    payload = tmp_path / "restart.json"
    payload.write_text(
        json.dumps({"root": str(root), "asof": asof, "source": asdict(args["source"])})
    )
    script = """
import json,sys
from pathlib import Path
from src.ops.economic_md_input_producer_v1.purpose_admission_v1 import PublicFactPurposePolicyV1
from src.ops.economic_md_input_producer_v1.purpose_consumers_v1 import PurposeBoundPublicFactSourceV1
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.offline_v1 import advance_explicit_offline_pending_v1,read_explicit_offline_pending_v1
p=json.loads(Path(sys.argv[1]).read_text()); s=p['source']; policy=s['policy']
for k in ('allowed_sources','maximum_ages_seconds'):policy[k]=tuple(tuple(r) for r in policy[k])
policy['finalized_kinds']=tuple(policy['finalized_kinds']);s['policy']=PublicFactPurposePolicyV1(**policy)
if sys.argv[2]=='advance':advance_explicit_offline_pending_v1(root=Path(p['root']),as_of_unix=p['asof'],source=PurposeBoundPublicFactSourceV1(**s))
print('RESULT='+json.dumps(read_explicit_offline_pending_v1(Path(p['root']))))
"""
    outputs = []
    repo = Path(__file__).resolve().parents[2]
    for mode in ("read", "advance", "read"):
        run = subprocess.run(
            [str(repo / "scripts/pt"), "-c", script, str(payload), mode],
            cwd=repo,
            text=True,
            capture_output=True,
        )
        assert run.returncode == 0, run.stdout + run.stderr
        outputs.append(
            json.loads(next(l[7:] for l in run.stdout.splitlines() if l.startswith("RESULT=")))
        )
    assert outputs[0]["stage"] == "WAITING_HORIZON"
    assert outputs[1] == outputs[2]
    assert outputs[2]["numeric_readback"]["realized_return"] == math.log(120 / 110)


@pytest.mark.parametrize(
    "mutation",
    ["ack", "numeric", "missing_numeric", "source", "capsule", "working_ledger", "optimization"],
)
def test_readback_rejects_stale_ack_and_changed_actual_consumer(tmp_path, mutation):
    args, asof = _case(tmp_path)
    root = create_explicit_offline_pending_v1(**args)
    advance_explicit_offline_pending_v1(root=root, as_of_unix=asof, source=args["source"])
    if mutation in {"numeric", "missing_numeric"}:
        path = next((root / "mi_consumer").glob("*/mi_offline_durable_evidence_record_v1.json"))
        if mutation == "missing_numeric":
            path.rename(path.with_suffix(".retained-original"))
            data = None
        else:
            data = json.loads(path.read_text())
            data["calibration_evidence"]["calibration_result"]["realized_return"] += 1
    else:
        path = (
            root
            / {
                "ack": "consumer_ack_v1.json",
                "source": "decision_source.jsonl",
                "capsule": "capsule_v1.json",
                "working_ledger": "LANE_1/ddo_learning_capture_v1.jsonl",
                "optimization": "optimization_input_v1.json",
            }[mutation]
        )
        if mutation in {"source", "working_ledger"}:
            path.write_bytes(b" " + path.read_bytes())
            data = None
        else:
            data = json.loads(path.read_text())
            data["tampered"] = True
    if data is not None:
        path.write_text(json.dumps(data))
    with pytest.raises((ValueError, KeyError, FileNotFoundError)):
        read_explicit_offline_pending_v1(root)


def test_stale_missing_expired_and_storage_pressure_are_different(tmp_path):
    args, asof = _case(tmp_path)
    root = create_explicit_offline_pending_v1(**args)
    t = asof + 301  # captured facts exceed the explicitly pinned capture age (300s)
    stale = advance_explicit_offline_pending_v1(
        root=root, as_of_unix=t, source=args["source"].at_v1(round(t * 1000))
    )
    assert stale["stage"] == "WAITING_STALE_SOURCE"
    # Capacity pressure does not delete existing pins or fabricate an outcome.
    padding = args["retention_root"] / "retained-unrelated.bin"
    padding.write_bytes(b"x" * args["retained_bytes_backpressure_threshold"])
    pressured = advance_explicit_offline_pending_v1(root=root, as_of_unix=t + 1, source=None)
    assert pressured["stage"] == "STORAGE_BACKPRESSURE" and pressured["attempts"] == 1
    assert (root / "capsule_v1.json").is_file() and not (root / "consumer_ack_v1.json").exists()
    expired = advance_explicit_offline_pending_v1(
        root=root, as_of_unix=args["expires_at_unix"] + 1, source=None
    )
    assert expired["stage"] == "EXPIRED"
    assert padding.stat().st_size == args["retained_bytes_backpressure_threshold"]


def test_market_return_forecast_error_and_accounting_pnl_remain_distinct(tmp_path):
    from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
        build_simulated_fill_v1,
    )
    from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
        ProductiveFuturesAccountingSessionV1,
    )
    from tests.ops.test_simulated_accounting_entry_source_v1 import _contract

    numbers = []
    pnl = []
    for i, (mark, fee) in enumerate(((100, 0), (105, 10))):
        args, asof = _case(tmp_path / str(i), mark=mark)
        root = create_explicit_offline_pending_v1(**args)
        done = advance_explicit_offline_pending_v1(
            root=root, as_of_unix=asof, source=args["source"]
        )
        numbers.append(done["numeric_readback"])
        session = ProductiveFuturesAccountingSessionV1(
            contract=_contract(args["context"].native_id, contract_size="1", min_qty="0.1")
        )
        for j, (side, price) in enumerate((("BUY", mark), ("SELL", 120))):
            fill = build_simulated_fill_v1(
                fill_id=str(j),
                instrument_id=session.contract.symbol,
                side=side,
                quantity="1",
                mark_price=price,
                contract=session.contract,
                fee_rate_bps=str(fee),
                slippage_bps="0",
                reduce_only=bool(j),
                event_time_unix=asof + j,
            )
            session.apply_fill(fill)
        pnl.append(session.realized_pnl - session.cumulative_fees)
        # Original Accounting persistence/reload, with the actual numeric values.
        restored = ProductiveFuturesAccountingSessionV1.from_durable_dict(session.to_durable_dict())
        assert restored.realized_pnl - restored.cumulative_fees == pnl[-1]
    assert numbers[0] == numbers[1]
    assert pnl[0] != pnl[1]
    assert numbers[0]["realized_return"] == math.log(120 / 110)
    assert numbers[0]["error"] != numbers[0]["realized_return"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_class", "REAL_PUBLIC_OBSERVATION"),
        ("source_class", "REPLAY_HISTORICAL"),
        ("n_bars", 1),
        ("max_attempts", True),
        ("account_identity", ""),
    ],
)
def test_unverified_profiles_and_unbound_policies_do_not_create_jobs(tmp_path, field, value):
    args, _ = _case(tmp_path)
    with pytest.raises(OfflineOutcomeError):
        create_explicit_offline_pending_v1(**{**args, field: value})
    assert not list(args["retention_root"].glob("jobs_v1/*/capsule_v1.json"))


def test_same_decision_target_rejects_policy_change_and_retains_original_capsule(tmp_path):
    args, _ = _case(tmp_path)
    root = create_explicit_offline_pending_v1(**args)
    before = (root / "capsule_v1.json").read_bytes()
    with pytest.raises(OfflineOutcomeError, match="CONFLICT"):
        create_explicit_offline_pending_v1(**{**args, "max_attempts": 11})
    assert (root / "capsule_v1.json").read_bytes() == before
    purge_lane_local_artifacts_for_release_v1(args["source_lane_root"])
    assert create_explicit_offline_pending_v1(**args) == root


def test_single_missing_bar_waits_and_cannot_shift_fixed_horizon(tmp_path):
    from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
        load_all_facts_v1,
        default_store_paths_v1,
        append_fact_v1,
    )

    args, t = _case(tmp_path)
    facts = load_all_facts_v1(default_store_paths_v1(Path(args["source"].store_root)))
    o4 = sorted(
        (f for f in facts if f["fact_kind"] == "FinalizedPt1hO4BarFactV1"),
        key=lambda f: f["bar"]["bar_open_time"],
    )
    incomplete = tmp_path / "missing-one-bar-facts"
    for f in o4[:-1]:
        append_fact_v1(default_store_paths_v1(incomplete), f)
    args["source"] = replace(args["source"], store_root=str(incomplete.resolve()))
    root = create_explicit_offline_pending_v1(**args)
    out = advance_explicit_offline_pending_v1(root=root, as_of_unix=t, source=args["source"])
    assert out["stage"] == "WAITING_HORIZON" and out["independent_sample_count"] == 0
    assert not (root / "offline_measurement_v1.json").exists()
    append_fact_v1(default_store_paths_v1(incomplete), o4[-1])
    assert (
        advance_explicit_offline_pending_v1(
            root=root, as_of_unix=t + 1, source=args["source"].at_v1(round((t + 1) * 1000))
        )["stage"]
        == "INGESTED"
    )


def test_different_store_cannot_turn_reingest_into_an_independent_job(tmp_path):
    args, _ = _case(tmp_path)
    root = create_explicit_offline_pending_v1(**args)
    source = replace(args["source"], store_root=str((tmp_path / "second-store").resolve()))
    with pytest.raises(OfflineOutcomeError, match="CONFLICT"):
        create_explicit_offline_pending_v1(**{**args, "source": source})
    assert len(list((args["retention_root"] / "jobs_v1").iterdir())) == 1
    assert read_explicit_offline_pending_v1(root)["independent_sample_count"] == 0
