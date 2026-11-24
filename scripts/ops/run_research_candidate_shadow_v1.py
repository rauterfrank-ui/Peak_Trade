#!/usr/bin/env python3
"""Freeze a GVEF pair for a prospective, no-order replay on public OKX EEA data."""

from __future__ import annotations

import argparse
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from http.client import HTTPSConnection
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlencode

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

from src.backtest.admissible_versioned_futures_dataset_v1 import (  # noqa: E402
    load_profile_binding_from_cfg,
    validate_profile_binding_consistency,
)
from src.backtest.mv2_research_wiring_v1 import run_mv2_research_backtest_wiring_v1  # noqa: E402
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (  # noqa: E402
    EvaluationReceiptArchiveV1,
    validate_numeric_packet_v1,
)
from src.experiments.canonical_experiment_identity_v1 import inspect_code_provenance_v1  # noqa: E402
from src.experiments.canonical_native_research_measurements_v1 import (  # noqa: E402
    native_research_input_hashes_v1,
)
from src.experiments.canonical_research_prepared_execution_v1 import (  # noqa: E402
    digest_v1,
    publish_v1,
    read_v1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (  # noqa: E402
    HTTP_MAX_RESPONSE_BYTES,
    HTTP_TIMEOUT_SECONDS,
    PUBLIC_HTTP_HOST,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.candidate_observation_v1 import (  # noqa: E402
    HOUR,
    LAST_ENDPOINT,
    PLAN_SCHEMA,
    _milliseconds,
    _utc,
)
from src.research.offline_recorded_mark_horizon_source_v1 import (  # noqa: E402
    recorded_mark_price_unit_v1,
)
from src.research.panel_sequential_signal_density_research_adapter_v0 import (  # noqa: E402
    _materialize_research_panel_volatility_estimate_columns_v0,
)
from src.trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import (  # noqa: E402
    LOOKBACK_BARS,
)

ROLE_PATHS = {
    "last": LAST_ENDPOINT,
    "mark": "/api/v5/market/history-mark-price-candles",
    "index": "/api/v5/market/history-index-candles",
    "funding": "/api/v5/public/funding-rate-history",
}


def _clock():
    return datetime.now(timezone.utc)


def _absolute(path):
    if not path.is_absolute() or path.resolve() != path:
        raise ValueError("CANONICAL_ABSOLUTE_PATH_REQUIRED")
    return path


def _head():
    code = inspect_code_provenance_v1(REPO)
    if code.working_tree_status != "CLEAN":
        raise ValueError("CLEAN_FORWARD_REPLAY_CHECKOUT_REQUIRED")
    return code.git_sha


def _config_hash(cfg):
    return native_research_input_hashes_v1(pd.DataFrame(), cfg)["config_sha256"]


def _pair(campaign, evidence_digest, config):
    if not re.fullmatch(r"[0-9a-f]{64}", evidence_digest):
        raise ValueError("LEARNING_DIGEST_REQUIRED")
    campaign = EvaluationReceiptArchiveV1(_absolute(campaign))
    completed = read_v1(campaign.safe_path_v1(Path("completed") / f"{evidence_digest}.json"))
    run = EvaluationReceiptArchiveV1(
        campaign.safe_path_v1(Path("offline-ddo-research") / evidence_digest)
    )
    result = read_v1(run.safe_path_v1("result.json"))
    request = read_v1(run.safe_path_v1("request.json"))
    if (
        result["status"] != "MECHANISM_PASS"
        or result["learning_evidence_digest"] != evidence_digest
        or completed["learning_digest"] != evidence_digest
        or completed["result_digest"] != digest_v1(result)
        or result["request_digest"] != digest_v1(request)
        or request["request"]["config_sha256"] != _config_hash(config)
    ):
        raise ValueError("RESEARCH_FORWARD_PARENT_MISMATCH")
    evaluation = result["evaluation"]
    evidence = EvaluationReceiptArchiveV1(run.safe_path_v1("gvef/evidence"))
    system = evidence.get_v1("system", evaluation["receipt_id"])
    domain_id = system["domains"]["self_learning"]["receipt_id"]
    domain = evidence.get_v1("domain", domain_id)
    if (
        system["mechanism_status"] != "PASS"
        or domain["status"] != "PASS"
        or domain_id != evaluation["domain_receipt_id"]
        or [ref["original_artifact_id"] for ref in domain["numeric_evidence"]]
        != [result["first_artifact_id"], result["next_artifact_id"]]
    ):
        raise ValueError("RESEARCH_FORWARD_GVEF_PAIR_MISMATCH")

    profiles = {}
    base = request["request"]
    latest_parent_bar = _utc(base["bars_known_at"])
    for role, ref in zip(("reference", "candidate"), domain["numeric_evidence"], strict=True):
        receipt = validate_numeric_packet_v1(evidence, ref)
        cfg = deepcopy(config)
        cfg["economic_evaluation_v1"]["strategy_params"] = receipt["parameters"]
        if (
            (receipt["instrument_id"], receipt["strategy_id"], receipt["strategy_version"])
            != (base["instrument_id"], base["strategy_id"], base["strategy_version"])
            or receipt["source_hashes"]["config_sha256"] != _config_hash(cfg)
            or receipt["source_hashes"]["dataset_sha256"] != base["dataset_sha256"]
            or receipt["productive_apply_authorized"] is not False
        ):
            raise ValueError("RESEARCH_FORWARD_CONFIG_MISMATCH")
        profiles[role] = {
            "packet": ref["original_artifact_id"],
            "experiment_id": receipt["experiment_id"],
            "parameters": receipt["parameters"],
            "admission_mode": receipt["instrument_admission_mode"],
            "config": cfg,
        }
        latest_parent_bar = max(latest_parent_bar, _utc(receipt["runs"][0]["period_end"]) + HOUR)
    if profiles["reference"]["parameters"] == profiles["candidate"]["parameters"]:
        raise ValueError("DISTINCT_RESEARCH_PARAMETERS_REQUIRED")
    source_revision = request["identity"]["fields"]["git_sha"]
    return {
        "gvef_receipt": evaluation["receipt_id"],
        "learning_digest": evidence_digest,
        "parent_revision": source_revision,
        "parent_dataset_sha256": base["dataset_sha256"],
        "candidate_known_at_utc": completed["completed_at_utc"],
        "parent_data_known_at_utc": latest_parent_bar.isoformat(),
        "instrument_id": base["instrument_id"],
        "strategy_id": base["strategy_id"],
        "strategy_version": base["strategy_version"],
        "profiles": profiles,
    }


def _require_original_replay_code(parent_revision, revision):
    checked = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            parent_revision,
            revision,
            "--",
            "src/backtest",
            "src/trading",
            "src/strategies",
        ],
        cwd=REPO,
        check=False,
    )
    if checked.returncode:
        raise ValueError("FORWARD_REPLAY_OWNERS_CHANGED_SINCE_PARENT")


def _reality_gap_policy_window(policy, *, registered, start, end):
    """Validate the precommitment before it is incorporated into a Shadow plan."""
    expected = tuple(_utc(policy[f"expected_window_{bound}_utc"]) for bound in ("start", "end"))
    observed = tuple(_utc(policy[f"observed_window_{bound}_utc"]) for bound in ("start", "end"))
    policy_at = _utc(policy["registered_at_utc"])
    if (
        policy["schema_version"] != "i17_reality_gap_policy.v1"
        or any(
            not re.fullmatch(r"[0-9a-f]{64}", policy[key])
            for key in ("expected_plan_digest", "expected_receipt_digest")
        )
        or not expected[0] < expected[1] <= policy_at <= registered < start
        or not start <= observed[0] < observed[1] <= end
        or expected[1] - expected[0] != observed[1] - observed[0]
        or type(policy["minimum_cycles"]) is not int
        or policy["minimum_cycles"] < 2
        or type(policy["minimum_fills_per_profile"]) is not int
        or policy["minimum_fills_per_profile"] < 0
    ):
        raise ValueError("I17_REALITY_GAP_PREDECLARED_POLICY_REQUIRED")
    numbers = []
    for key in ("max_boundary_skew_seconds", "max_abs_net_return_gap"):
        try:
            number = Decimal(str(policy[key]))
        except InvalidOperation as exc:
            raise ValueError("I17_REALITY_GAP_POLICY_NUMBER_INVALID") from exc
        if not number.is_finite() or number < 0:
            raise ValueError("I17_REALITY_GAP_POLICY_NUMBER_INVALID")
        numbers.append(number)
    return expected, observed, *numbers


def prepare_v1(
    workspace,
    *,
    campaign,
    evidence_digest,
    config,
    binding,
    start,
    hours,
    revision,
    now,
    reality_gap_policy=None,
):
    pair = _pair(campaign, evidence_digest, config)
    _require_original_replay_code(pair["parent_revision"], revision)
    instrument = pair["instrument_id"]
    price_unit = recorded_mark_price_unit_v1(
        instrument_binding=binding,
        canonical_instrument_id=instrument,
        native_instrument_id=instrument,
    )
    if binding["instrument_metadata"]["instType"] != "FUTURES":
        raise ValueError("FORWARD_XPERP_MARKET_REQUIRED")
    index_id = binding["instrument_metadata"]["uly"]
    target = workspace.safe_path_v1("plan.json")
    registered = _utc(read_v1(target)["registered_at_utc"]) if target.exists() else now
    start = _utc(start)
    if (
        start
        <= max(
            registered, _utc(pair["candidate_known_at_utc"]), _utc(pair["parent_data_known_at_utc"])
        )
        or start != start.replace(minute=0, second=0, microsecond=0)
        or not 2 <= hours <= 100 - (LOOKBACK_BARS + 1)
    ):
        raise ValueError("FUTURE_GRID_ALIGNED_BOUNDED_WINDOW_REQUIRED")
    plan = {
        "schema_version": PLAN_SCHEMA,
        "authority": "NONE",
        "mode": "PROSPECTIVE_PUBLIC_DATA_OFFLINE_REPLAY",
        "registered_at_utc": registered.isoformat(),
        "start_utc": start.isoformat(),
        "end_utc": (start + hours * HOUR).isoformat(),
        "warmup_start_utc": (start - (LOOKBACK_BARS + 1) * HOUR).isoformat(),
        "revision": revision,
        "public_source": {"host": PUBLIC_HTTP_HOST, "index_id": index_id, "price_unit": price_unit},
        "instrument_binding": binding,
        **pair,
    }
    if reality_gap_policy is not None:
        _reality_gap_policy_window(
            reality_gap_policy, registered=registered, start=start, end=_utc(plan["end_utc"])
        )
        plan["reality_gap_policy_digest"] = digest_v1(reality_gap_policy)
        if not target.exists() or "gap_return_campaign" in read_v1(target):
            plan["gap_return_campaign"] = str(_absolute(campaign))
    publish_v1(target, plan)
    return read_v1(target)


def _requests(plan):
    cursor = str(_milliseconds(_utc(plan["end_utc"])))
    for role, path in ROLE_PATHS.items():
        instrument = plan["public_source"]["index_id"] if role == "index" else plan["instrument_id"]
        query = {"instId": instrument, "after": cursor, "limit": "100"}
        if role != "funding":
            query["bar"] = "1H"
        yield role, path, query


def _public_get(path, query):
    with closing(HTTPSConnection(PUBLIC_HTTP_HOST, timeout=HTTP_TIMEOUT_SECONDS)) as conn:
        conn.request("GET", f"{path}?{urlencode(query)}", headers={"Accept": "application/json"})
        with conn.getresponse() as response:
            raw = response.read(HTTP_MAX_RESPONSE_BYTES + 1)
            if response.status != 200 or len(raw) > HTTP_MAX_RESPONSE_BYTES:
                raise ValueError(f"FORWARD_PUBLIC_GET_FAILED:{response.status}")
            return raw


def _capture(workspace, plan, fetch, clock):
    if clock() < _utc(plan["end_utc"]):
        raise ValueError("FORWARD_WINDOW_NOT_CLOSED")
    records = {}
    for role, path, query in _requests(plan):
        requested = clock()
        raw = fetch(path, query)
        received = clock()
        # Hex preserves the original bytes and keeps all four sources in one atomic packet.
        records[role] = {
            "host": PUBLIC_HTTP_HOST,
            "endpoint": path,
            "query": query,
            "requested_at_utc": requested.isoformat(),
            "received_at_utc": received.isoformat(),
            "raw_sha256": sha256(raw).hexdigest(),
            "raw_hex": raw.hex(),
        }
    archive = {"plan_digest": digest_v1(plan), "records": records}
    _bars(plan, archive)
    publish_v1(workspace.safe_path_v1("public-input.json"), archive)
    return archive


def _raw_rows(plan, archive):
    if archive["plan_digest"] != digest_v1(plan) or set(archive["records"]) != set(ROLE_PATHS):
        raise ValueError("FORWARD_ARCHIVE_PLAN_MISMATCH")
    for role, path, query in _requests(plan):
        record = archive["records"][role]
        raw = bytes.fromhex(record["raw_hex"])
        if (
            (record["host"], record["endpoint"], record["query"]) != (PUBLIC_HTTP_HOST, path, query)
            or not _utc(plan["end_utc"])
            <= _utc(record["requested_at_utc"])
            <= _utc(record["received_at_utc"])
            or sha256(raw).hexdigest() != record["raw_sha256"]
        ):
            raise ValueError("FORWARD_ORIGINAL_REQUEST_MISMATCH")
        payload = json.loads(raw)
        if payload["code"] != "0" or not isinstance(payload["data"], list):
            raise ValueError("FORWARD_OKX_SOURCE_REJECTED")
        yield role, payload["data"]


def _bars(plan, archive):
    start = _utc(plan["warmup_start_utc"])
    end = _utc(plan["end_utc"])
    opened = pd.date_range(start, end, freq="h", inclusive="left")
    grid = {_milliseconds(ts) for ts in opened}
    sources = {}
    funding = {}
    for role, rows in _raw_rows(plan, archive):
        if role == "funding":
            for row in rows:
                time = int(row["fundingTime"])
                rate = float(row["realizedRate"])
                if (
                    row["instId"] != plan["instrument_id"]
                    or row["instType"] != "FUTURES"
                    or not math.isfinite(rate)
                    or time in funding
                ):
                    raise ValueError("FORWARD_FUNDING_SOURCE_MISMATCH")
                funding[time] = rate
            continue
        values = {}
        for row in rows:
            expected_width = 9 if role == "last" else 6
            if not isinstance(row, list) or len(row) != expected_width:
                raise ValueError("FORWARD_CANDLE_SHAPE_MISMATCH")
            time = int(row[0])
            if time not in grid:
                continue
            o, high, low, close = map(float, row[1:5])
            if (
                row[-1] != "1"
                or time in values
                or not all(math.isfinite(price) and price > 0 for price in (o, high, low, close))
                or not low <= min(o, close) <= max(o, close) <= high
            ):
                raise ValueError("FORWARD_CANDLE_FINALITY_OR_VALUE_MISMATCH")
            if role == "last":
                volume = float(row[6])
                if not math.isfinite(volume) or volume < 0:
                    raise ValueError("FORWARD_BASE_VOLUME_INVALID")
                values[time] = (o, high, low, close, volume)
            else:
                values[time] = close
        if set(values) != grid:
            raise ValueError(f"FORWARD_INCOMPLETE_CANDLE_COVERAGE:{role}")
        sources[role] = values

    # Use the funding event time for context. Publication timing and cashflows are unverified.
    records = []
    for ts in opened:
        time = _milliseconds(ts)
        known = max((item for item in funding if item <= time), default=None)
        if known is None:
            raise ValueError("FORWARD_FUNDING_AT_OPEN_MISSING")
        o, high, low, close, volume = sources["last"][time]
        records.append(
            (
                o,
                high,
                low,
                close,
                volume,
                sources["mark"][time],
                sources["index"][time],
                funding[known],
                True,
                "1h",
            )
        )
    # The last, mark and index close first exist at the end of the source hour.
    frame = pd.DataFrame(
        records,
        index=opened + HOUR,
        columns=(
            "open",
            "high",
            "low",
            "close",
            "volume",
            "mark_price",
            "index_price",
            "funding_rate",
            "is_final",
            "bar_interval",
        ),
    )
    return _materialize_research_panel_volatility_estimate_columns_v0(frame)


def _run_profile(plan, bars, profile):
    cfg = deepcopy(profile["config"])
    binding = load_profile_binding_from_cfg(cfg)
    if not validate_profile_binding_consistency(binding, reason_codes=[]):
        raise ValueError("FORWARD_UNSUPPORTED_RESEARCH_PROFILE")
    wiring = run_mv2_research_backtest_wiring_v1(
        bars.copy(deep=True),
        strategy_id=plan["strategy_id"],
        cfg=cfg,
        instrument_id=plan["instrument_id"],
        profile_binding=binding,
        step29l_instrument_admission_mode=profile["admission_mode"],
    )
    provenance = wiring.strategy_signal_provenance
    if (
        dict(provenance.effective_strategy_params) != profile["parameters"]
        or dict(provenance.configured_strategy_params) != profile["parameters"]
        or provenance.strategy_version != plan["strategy_version"]
    ):
        raise ValueError("FORWARD_EXECUTED_PARAMETERS_MISMATCH")

    start, end = _utc(plan["start_utc"]), _utc(plan["end_utc"])
    times = pd.date_range(start, end, freq="h")
    equity = wiring.backtest_result.equity_curve.loc[times]
    signals = wiring.signals.loc[times[1:]]
    if (
        not equity.index.equals(times)
        or not signals.index.equals(times[1:])
        or not all(math.isfinite(value) and value > 0 for value in equity)
    ):
        raise ValueError("FORWARD_SCORED_BARS_OR_EQUITY_MISMATCH")
    return {
        "packet": profile["packet"],
        "strategy_provenance": provenance.to_dict(),
        "engine_signal_digest": wiring.backtest_engine_signal_digest,
        "engine_signals": [
            {"close_utc": ts.isoformat(), "value": int(value)} for ts, value in signals.items()
        ],
        "engine_equity": [
            {"close_utc": ts.isoformat(), "value": float(value)} for ts, value in equity.items()
        ],
        "engine_pre_funding_return": float(equity.iloc[-1] / equity.iloc[0] - 1.0),
    }


def observe_v1(workspace, *, revision, verify=False, fetch=_public_get, clock=_clock):
    plan = read_v1(workspace.safe_path_v1("plan.json"))
    if (
        plan["schema_version"] != PLAN_SCHEMA
        or plan["authority"] != "NONE"
        or plan["revision"] != revision
        or plan["public_source"]["host"] != PUBLIC_HTTP_HOST
        or not _utc(plan["registered_at_utc"]) < _utc(plan["start_utc"]) < _utc(plan["end_utc"])
    ):
        raise ValueError("FORWARD_PLAN_REVISION_OR_SCOPE_MISMATCH")
    input_file = workspace.safe_path_v1("public-input.json")
    result_file = workspace.safe_path_v1("result.json")
    with workspace.lease_v1():
        if verify or input_file.exists():
            archive = read_v1(input_file)
        else:
            archive = _capture(workspace, plan, fetch, clock)
        bars = _bars(plan, archive)
        profiles = {
            role: _run_profile(plan, bars, profile) for role, profile in plan["profiles"].items()
        }
        result = {
            "schema_version": "native_research_candidate_forward_replay.v1",
            "authority": "NONE",
            "mode": plan["mode"],
            "plan_digest": digest_v1(plan),
            "public_input_digest": digest_v1(archive),
            "source_data_known_at_utc": max(
                row["received_at_utc"] for row in archive["records"].values()
            ),
            "public_mark_log_return": {
                "from_close_utc": plan["start_utc"],
                "to_close_utc": plan["end_utc"],
                "value": math.log(
                    bars.loc[_utc(plan["end_utc"]), "mark_price"]
                    / bars.loc[_utc(plan["start_utc"]), "mark_price"]
                ),
            },
            "profiles": profiles,
            "engine_pre_funding_return_difference": (
                profiles["candidate"]["engine_pre_funding_return"]
                - profiles["reference"]["engine_pre_funding_return"]
            ),
            "reality_gap_status": "INCOMPLETE",
            "economic_qualification_status": "BLOCKED",
        }
        if verify:
            if digest_v1(read_v1(result_file)) != digest_v1(result):
                raise ValueError("FORWARD_REPLAY_READBACK_MISMATCH")
        else:
            publish_v1(result_file, result)
        return read_v1(result_file)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    subcommands = parser.add_subparsers(dest="action", required=True)
    prepare = subcommands.add_parser("prepare")
    prepare.add_argument("--campaign-state", type=Path, required=True)
    prepare.add_argument("--learning-digest", required=True)
    prepare.add_argument("--config", type=Path, required=True)
    prepare.add_argument("--instrument-binding", type=Path, required=True)
    prepare.add_argument("--start-utc", required=True)
    prepare.add_argument("--hours", type=int, required=True)
    prepare.add_argument("--reality-gap-policy", type=Path)
    subcommands.add_parser("observe")
    subcommands.add_parser("verify")
    args = parser.parse_args(argv)
    try:
        state = _absolute(args.state)
        if state.is_relative_to(REPO) or REPO.is_relative_to(state):
            raise ValueError("FORWARD_STATE_OUTSIDE_REPOSITORY_REQUIRED")
        workspace = EvaluationReceiptArchiveV1(state)
        revision = _head()
        if args.action == "prepare":
            campaign = _absolute(args.campaign_state)
            source_paths = (campaign, _absolute(args.config), _absolute(args.instrument_binding))
            policy = _absolute(args.reality_gap_policy) if args.reality_gap_policy else None
            inputs = source_paths + ((policy,) if policy is not None else ())
            if any(path.is_relative_to(state) or state.is_relative_to(path) for path in inputs):
                raise ValueError("FORWARD_STATE_MUST_BE_SEPARATE_FROM_INPUTS")
            config, binding = (json.loads(path.read_bytes()) for path in source_paths[1:])
            plan = prepare_v1(
                workspace,
                campaign=campaign,
                evidence_digest=args.learning_digest,
                config=config,
                binding=binding,
                start=args.start_utc,
                hours=args.hours,
                revision=revision,
                now=_clock(),
                reality_gap_policy=json.loads(policy.read_bytes()) if policy else None,
            )
            payload = {
                "plan_digest": digest_v1(plan),
                "start_utc": plan["start_utc"],
                "end_utc": plan["end_utc"],
                "authority": "NONE",
            }
        else:
            result = observe_v1(workspace, revision=revision, verify=args.action == "verify")
            payload = {
                "result_digest": digest_v1(result),
                "economic_qualification_status": result["economic_qualification_status"],
                "reality_gap_status": result["reality_gap_status"],
                "authority": "NONE",
            }
        print(json.dumps(payload, sort_keys=True), flush=True)
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        parser.exit(2, f"Candidate forward replay stopped: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
