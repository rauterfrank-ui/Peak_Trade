import json
import subprocess
from datetime import timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1 import (
    run_f2_research_backtest_cost_grid_offline_v1,
)
from src.experiments.canonical_meta_learning_v1 import (
    QUESTION_COST_MODEL_REALITY_UNDERESTIMATION,
    build_canonical_meta_learning_v1,
    canonical_meta_learning_policy_v1,
    canonical_record_payload_v1,
)
from src.experiments.canonical_research_prepared_execution_v1 import publish_v1, read_v1
from src.experiments.f2_meta_cost_model_follow_up_v1 import (
    build_f2_fill_fee_meta_follow_up_v1,
    build_f2_meta_cost_model_follow_up_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.experiments.test_canonical_f2_research_backtest_cost_grid_v1 import (
    f2_bound_archive,  # noqa: F401
    f2_clean_git_provenance,  # noqa: F401
)
from tests.experiments.test_canonical_meta_learning_v1 import _identity, _request
from tests.governance.d27_native_baseline_fixtures_v1 import (
    build_fixture_native_baseline_evidence_v1,
)
from tests.ops.test_execution_reconciliation_get_provenance_v1 import (
    NOW,
    _bound,
    _fetch,
    _receipt_args,
    authenticated_host,  # noqa: F401
    proof_root,  # noqa: F401
)

ROOT = Path(__file__).resolve().parents[2]


def _meta_investigation(result, *, matching=True):
    baseline = next(item for item in result["candidates"] if item["is_baseline"])
    config = json.loads((ROOT / result["source_step29m_config_ref"]).read_bytes())
    fee_model_source_digest = compute_content_sha256(
        {
            "f2_config_binding": "fee_model",
            "payload": {
                "fee_model_version": config["backtest"]["fee_model_version"],
                "fee_bps": baseline["fee_bps"],
            },
        }
    )
    identities = tuple(
        _identity(
            seed=seed,
            dataset_digest=result["f2_config_authority"]["dataset_digest"],
            fee_model_digest=fee_model_source_digest if matching else "9" * 64,
        )
        for seed in (11, 12, 13)
    )
    record = canonical_record_payload_v1(
        build_canonical_meta_learning_v1(
            _request(identities, policy=canonical_meta_learning_policy_v1())
        )
    )
    proposal = next(
        item
        for item in record["research_proposals"]
        if item["question_id"] == QUESTION_COST_MODEL_REALITY_UNDERESTIMATION
    )
    return record, proposal["proposal_id"]


@pytest.fixture
def f2_result(f2_bound_archive, tmp_path):
    archive, _, _, _ = f2_bound_archive
    result = dict(
        run_f2_research_backtest_cost_grid_offline_v1(
            native_baseline_evidence_v1=build_fixture_native_baseline_evidence_v1(),
            research_dataset_dir_v1=archive,
        )
    )
    path = tmp_path / "f2.json"
    publish_v1(path, result)
    return result, path


def test_original_meta_cost_proposal_consumes_f2_receipt_after_restart(f2_result, tmp_path):
    result, f2_path = f2_result
    meta, proposal = _meta_investigation(result)
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(meta))
    output = tmp_path / "follow-up.json"
    args = [
        "./scripts/pt",
        "scripts/ops/run_f2_meta_cost_model_follow_up_v1.py",
        "--meta-record",
        str(meta_path),
        "--meta-identity",
        meta["meta_learning_identity"],
        "--proposal-id",
        proposal,
        "--f2-result",
        str(f2_path),
        "--f2-execution-digest",
        result["execution_digest"],
        "--output",
        str(output),
    ]
    originals = (meta_path.read_bytes(), f2_path.read_bytes())
    cold = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    assert cold.returncode == 0, cold.stderr
    assert cold.stdout.splitlines()[-1] == "REQUIRE_OOS_TRADE_EVIDENCE"
    follow_up = read_v1(output)
    assert follow_up["authority"] == "NONE"
    assert follow_up["proposal_id"] == proposal
    assert follow_up["native_instrument_id"] == "ETH-USDT-SWAP"
    assert [row["fee_bps"] for row in follow_up["scenarios"]] == [8.0, 10.0, 12.0]
    assert {row["slippage_bps"] for row in follow_up["scenarios"]} == {5.0}
    assert all(row["oos_net_return_delta_ratio"] is None for row in follow_up["scenarios"])
    assert all(row["oos_trade_count"] == 0 for row in follow_up["scenarios"])
    first = output.read_bytes()
    subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True)
    assert output.read_bytes() == first
    assert (meta_path.read_bytes(), f2_path.read_bytes()) == originals


def test_meta_follow_up_rejects_an_unbound_model_and_archive(f2_result):
    result, f2_path = f2_result
    meta, proposal = _meta_investigation(result, matching=False)
    args = {
        "meta_record": meta,
        "expected_meta_identity": meta["meta_learning_identity"],
        "proposal_id": proposal,
        "f2_result_path": f2_path,
    }
    with pytest.raises(ValueError, match="F2_META_COST_MODEL_NOT_BOUND_TO_BASELINE"):
        build_f2_meta_cost_model_follow_up_v1(
            **args, expected_f2_execution_digest=result["execution_digest"]
        )
    with pytest.raises(ValueError, match="F2_META_EXECUTION_DIGEST_MISMATCH"):
        build_f2_meta_cost_model_follow_up_v1(**args, expected_f2_execution_digest="0" * 64)


def test_measured_scenario_deltas_hold_the_other_axis_fixed(f2_result, tmp_path):
    result, _ = f2_result
    meta, proposal = _meta_investigation(result)
    # Controlled values exercise the comparison arithmetic independently of the engine.
    grid = result["parameter_sensitivity_result"]
    for point in grid["points"]:
        fee, slip = (point["parameter_values"][key] for key in ("fee_bps", "slippage_bps"))
        point["trade_count"] = {"semantic": "COMPUTED", "value": 2.0}
        point["net_return"] = {"semantic": "COMPUTED", "value": (15.0 - fee - slip) / 100}
    grid["result_digest"] = compute_content_sha256(
        {
            key: grid[key]
            for key in ("grid_digest", "combination_count", "seed", "pipeline_status", "points")
        }
    )
    result["parameter_sensitivity_result_digest"] = grid["result_digest"]
    result.pop("execution_digest")
    result["execution_digest"] = compute_content_sha256(result)
    packet = tmp_path / "controlled-scenarios.json"
    publish_v1(packet, result)
    report = build_f2_meta_cost_model_follow_up_v1(
        meta_record=meta,
        expected_meta_identity=meta["meta_learning_identity"],
        proposal_id=proposal,
        f2_result_path=packet,
        expected_f2_execution_digest=result["execution_digest"],
    )
    assert report["disposition"] == "REVIEW_MODELED_COST_SENSITIVITY"
    assert [row["oos_net_return_delta_ratio"] for row in report["scenarios"]] == pytest.approx(
        [0.02, 0.0, -0.02]
    )


@pytest.fixture
def confirmed_fee_archive(authenticated_host, proof_root, tmp_path, monkeypatch, request):
    case = getattr(request, "param", "duplicate")
    host, attempt, opener, scope, held = authenticated_host
    original_body = opener.body
    fill_time = NOW - timedelta(seconds=1)
    quantity = Decimal(attempt.final_quantity)
    long = attempt.selected_side == "LONG"
    position = {
        "instId": attempt.native_id,
        "instType": "SWAP",
        "pos": str(quantity if long else -quantity),
        "posSide": "net",
        "mgnMode": "cross",
        "avgPx": "2000",
        "uTime": str(int(fill_time.timestamp() * 1000)),
    }
    host.fetch = _fetch(uid=scope.account, positions=(position,))

    def body(path, params):
        response = json.loads(original_body(path, params))
        if path.endswith(("/order", "orders-history", "/fills")):
            for row in response["data"]:
                row.update(state="filled", accFillSz=str(quantity))
        if path.endswith("/fills"):
            (fill,) = response["data"]
            fill.update(
                fillSz=str(quantity),
                fillPx="2000",
                fillTime=str(int(fill_time.timestamp() * 1000)),
                side="buy" if long else "sell",
                fee=str(quantity * Decimal("0.04" if case == "within-model" else "-0.24")),
                feeCcy="USD" if case == "currency" else "USDT",
                execType="T",
            )
            if case in {"duplicate", "conflicting-duplicate"}:
                second = dict(fill)
                if case == "conflicting-duplicate":
                    second["fee"] = "-0.01"
                response["data"].append(second)
        if path.endswith("/positions"):
            response["data"] = [position]
        return json.dumps(response).encode()

    monkeypatch.setattr(opener, "body", body)
    _, proofs = host.observe_authenticated_execution_reconciliation_v1(
        {"LANE_1": _bound()}, proof_root=proof_root
    )
    proof = proofs[attempt.portfolio_reservation_id]
    assert host.owner.active_sum_v1() == held
    args = _receipt_args(host, scope, attempt, proof_root, proof.revision_ref)
    host.close()
    metadata_path = tmp_path / "historical-instruments.json"
    metadata_path.write_text(
        json.dumps(
            {
                "venue_host": proof.venue_host,
                "endpoint": "/api/v5/public/instruments",
                "known_at_utc": (fill_time - timedelta(seconds=1)).isoformat(),
                "response": {
                    "code": "0",
                    "data": [
                        {
                            "instId": attempt.native_id,
                            "instType": "SWAP",
                            "ctType": "linear",
                            "ctVal": "" if case == "missing-notional" else "0.1",
                            "ctMult": "1",
                            "ctValCcy": "ETH",
                            "settleCcy": "USDT",
                        }
                    ],
                },
            }
        )
    )
    return args, metadata_path, quantity


def _fee_args(f2_result, confirmed_fee_archive):
    result, f2_path = f2_result
    proof_args, metadata_path, _ = confirmed_fee_archive
    baseline = next(item for item in result["candidates"] if item["is_baseline"])
    return {
        "proof_args": proof_args,
        "metadata_path": metadata_path,
        "expected_metadata_sha256": sha256(metadata_path.read_bytes()).hexdigest(),
        "f2_result_path": f2_path,
        "expected_f2_execution_digest": result["execution_digest"],
        "expected_fee_model_digest": baseline["experiment_identity"]["fee_model_digest"],
        "as_of_utc": NOW.isoformat(),
        "offline_fixture": True,
    }


def test_archived_fill_drives_existing_meta_and_f2_after_process_restart(
    f2_result, confirmed_fee_archive, tmp_path
):
    args = _fee_args(f2_result, confirmed_fee_archive)
    packet = tmp_path / "fill-input.json"
    packet.write_text(
        json.dumps(
            {
                **args["proof_args"],
                "metadata_path": args["metadata_path"],
                "metadata_sha256": args["expected_metadata_sha256"],
                "fee_model_digest": args["expected_fee_model_digest"],
                "as_of_utc": args["as_of_utc"],
            },
            default=str,
        )
    )
    proof_args, metadata, quantity = confirmed_fee_archive
    raw_proof = proof_args["root"] / f"{proof_args['revision_ref'][1]}.json"
    budget = proof_args["budget_owner_root"] / "reservations.sqlite3"
    original_paths = (raw_proof, budget, metadata, args["f2_result_path"])
    originals = [path.read_bytes() for path in original_paths]
    output = tmp_path / "fill-follow-up.json"
    cold_entry = """
import runpy
import socket
import sys

def deny_network(*args, **kwargs):
    raise AssertionError("Offline follow-up attempted network")

socket.socket.connect = deny_network
socket.create_connection = deny_network
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""
    command = [
        "./scripts/pt",
        "-c",
        cold_entry,
        "scripts/ops/run_f2_meta_cost_model_follow_up_v1.py",
        "--output",
        str(output),
    ]
    build = [
        *command,
        "--fill-input",
        str(packet),
        "--f2-result",
        str(args["f2_result_path"]),
        "--f2-execution-digest",
        args["expected_f2_execution_digest"],
        "--offline-fixture",
    ]
    first = subprocess.run(build, cwd=ROOT, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    report = read_v1(output)
    assert report["evidence_profile"] == "OFFLINE_FIXTURE"
    assert report["disposition"] == "REQUIRE_OOS_TRADE_EVIDENCE"
    assert len(report["fee_observation"]["fills"]) == 1
    assert report["fee_measurement"]["fee_bps_exact"] == "12"
    assert report["fee_measurement"]["notional_quote_exact"] == str(int(quantity * 200))
    (dimension,) = report["reality_gap"]["dimension_results"]
    assert (dimension["observed"], dimension["expected"], dimension["unit"]) == (12, 10, "bps")
    assert report["consumed_fee_finding"]["underestimation_count"] == 1
    assert report["consumed_fee_finding"]["sample_size"] == 1
    assert report["consumed_fee_finding"]["cost_model_digest"] == args["expected_fee_model_digest"]
    follow_up = report["follow_up"]
    assert follow_up["meta_learning_identity"] == report["meta_record"]["meta_learning_identity"]
    assert follow_up["cost_model_digest"] == args["expected_fee_model_digest"]
    assert [row["fee_bps"] for row in follow_up["scenarios"]] == [8.0, 10.0, 12.0]
    assert all(row["oos_net_return_delta_ratio"] is None for row in follow_up["scenarios"])
    saved = output.read_bytes()
    cold = subprocess.run([*command, "--readback"], cwd=ROOT, capture_output=True, text=True)
    assert cold.returncode == 0, cold.stderr
    assert json.loads(cold.stdout.splitlines()[-1]) == report
    subprocess.run(build, cwd=ROOT, capture_output=True, text=True, check=True)
    assert output.read_bytes() == saved
    assert [path.read_bytes() for path in original_paths] == originals


@pytest.mark.parametrize(
    "confirmed_fee_archive,reason",
    [
        ("missing-notional", "FILL_FEE_MISSING_OR_INVALID:ctVal"),
        ("currency", "FILL_FEE_CURRENCY_NOT_COMPARABLE"),
        ("conflicting-duplicate", "FILL_FEE_CONFLICTING_TRADE_ID"),
    ],
    indirect=["confirmed_fee_archive"],
)
def test_unusable_fills_do_not_reach_meta(f2_result, confirmed_fee_archive, reason):
    with pytest.raises(ValueError, match=reason):
        build_f2_fill_fee_meta_follow_up_v1(**_fee_args(f2_result, confirmed_fee_archive))


def test_fill_rejects_foreign_model_and_lookahead(f2_result, confirmed_fee_archive):
    args = _fee_args(f2_result, confirmed_fee_archive)
    with pytest.raises(ValueError, match="F2_META_COST_MODEL_NOT_BOUND_TO_BASELINE"):
        build_f2_fill_fee_meta_follow_up_v1(**{**args, "expected_fee_model_digest": "9" * 64})
    with pytest.raises(ValueError, match="F2_META_FILL_LOOKAHEAD"):
        build_f2_fill_fee_meta_follow_up_v1(
            **{**args, "as_of_utc": (NOW - timedelta(milliseconds=1)).isoformat()}
        )
    with pytest.raises(ValueError, match="FILL_FEE_METADATA_DIGEST_MISMATCH"):
        build_f2_fill_fee_meta_follow_up_v1(**{**args, "expected_metadata_sha256": "9" * 64})


@pytest.mark.parametrize("confirmed_fee_archive", ["within-model"], indirect=True)
def test_rebate_retains_sign_and_generates_no_investigation(f2_result, confirmed_fee_archive):
    result = build_f2_fill_fee_meta_follow_up_v1(**_fee_args(f2_result, confirmed_fee_archive))
    assert result["fee_measurement"]["fee_bps_exact"] == "-2"
    assert result["consumed_fee_finding"]["underestimation_count"] == 0
    assert result["follow_up"] is None
    assert result["disposition"] == "NO_FEE_UNDERESTIMATION_OBSERVED"
